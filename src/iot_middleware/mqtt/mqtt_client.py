"""
Cliente MQTT para IoT Middleware
================================

Este módulo proporciona un cliente MQTT robusto que se conecta al broker
configurado, se suscribe a tópicos específicos y procesa mensajes JSON.
"""

import json
import time
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion
import threading
from datetime import datetime

# Importar configuración
try:
    from ..config import MQTTConfig
except ImportError:
    # Fallback para importación directa
    from iot_middleware.config import MQTTConfig

# Configurar logging
logger = logging.getLogger(__name__)


@dataclass
class MQTTMessage:
    """Estructura de datos para mensajes MQTT"""
    topic: str
    payload: Dict[str, Any]
    qos: int
    retain: bool
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: Optional[int] = None


class MQTTCallbackHandler:
    """Manejador de callbacks para eventos MQTT"""
    
    def __init__(self, client: 'IoTMQTTClient'):
        self.client = client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker"""
        if rc == 0:
            self.logger.info("✅ Conectado exitosamente al broker MQTT")
            self.client._connected = True
            self.client._connection_time = datetime.now()
            
            # Suscribirse a tópicos configurados
            self._subscribe_to_topics()
        else:
            self.logger.error(f"❌ Error de conexión MQTT: {rc}")
            self.client._connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta del broker"""
        self.logger.warning(f"⚠️  Desconectado del broker MQTT: {rc}")
        self.client._connected = False
        self.client._connection_time = None
    
    def on_message(self, client, userdata, message):
        """Callback cuando se recibe un mensaje"""
        try:
            # Parsear payload JSON
            payload = json.loads(message.payload.decode('utf-8'))
            
            # Crear objeto de mensaje
            mqtt_message = MQTTMessage(
                topic=message.topic,
                payload=payload,
                qos=message.qos,
                retain=message.retain,
                message_id=message.mid
            )
            
            self.logger.debug(f"📨 Mensaje recibido en {message.topic}: {payload}")
            
            # Procesar mensaje
            if self.client.message_processor:
                self.client.message_processor(mqtt_message)
            else:
                self.logger.warning("⚠️  No hay procesador de mensajes configurado")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Error al parsear JSON del mensaje: {e}")
            self.logger.error(f"   Payload: {message.payload}")
        except Exception as e:
            self.logger.error(f"❌ Error inesperado al procesar mensaje: {e}")
    
    def on_publish(self, client, userdata, mid):
        """Callback cuando se publica un mensaje"""
        self.logger.debug(f"📤 Mensaje publicado con ID: {mid}")
    
    def on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback cuando se suscribe a un tópico"""
        self.logger.info(f"📋 Suscrito a tópicos con QoS: {granted_qos}")
    
    def on_unsubscribe(self, client, userdata, mid):
        """Callback cuando se desuscribe de un tópico"""
        self.logger.info(f"📋 Desuscrito de tópicos")
    
    def on_log(self, client, userdata, level, buf):
        """Callback para logs del cliente MQTT"""
        if level <= mqtt_client.MQTT_LOG_WARNING:
            self.logger.warning(f"MQTT Log: {buf}")
        else:
            self.logger.debug(f"MQTT Log: {buf}")
    
    def _subscribe_to_topics(self):
        """Suscribirse a tópicos configurados"""
        if not self.client.config:
            self.logger.error("❌ No hay configuración MQTT disponible")
            return
        
        topics = self.client.config.topics.get('subscribe', [])
        if not topics:
            self.logger.warning("⚠️  No hay tópicos de suscripción configurados")
            return
        
        # Suscribirse a cada tópico
        for topic in topics:
            try:
                result, mid = self.client.client.subscribe(
                    topic, 
                    qos=self.client.config.qos
                )
                if result == mqtt_client.MQTT_ERR_SUCCESS:
                    self.logger.info(f"📋 Suscrito a tópico: {topic}")
                else:
                    self.logger.error(f"❌ Error al suscribirse a {topic}: {result}")
            except Exception as e:
                self.logger.error(f"❌ Excepción al suscribirse a {topic}: {e}")


class IoTMQTTClient:
    """Cliente MQTT para IoT Middleware"""
    
    def __init__(self, config: MQTTConfig, client_id: Optional[str] = None):
        """
        Inicializar cliente MQTT
        
        Args:
            config: Configuración MQTT
            client_id: ID único del cliente (opcional)
        """
        self.config = config
        self.client_id = client_id or f"iot_middleware_{int(time.time())}"
        self.message_processor: Optional[Callable[[MQTTMessage], None]] = None
        
        # Estado de conexión
        self._connected = False
        self._connection_time: Optional[datetime] = None
        self._last_message_time: Optional[datetime] = None
        self._message_count = 0
        
        # Crear cliente MQTT
        self.client = mqtt_client.Client(
            callback_api_version=CallbackAPIVersion.VERSION1,
            client_id=self.client_id,
            clean_session=True,
            protocol=mqtt_client.MQTTv311
        )
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Configurar callbacks
        self._setup_callbacks()
        
        # Configurar opciones de conexión
        self._setup_connection_options()
        
        # Thread para reconexión automática
        self._reconnect_thread = None
        self._stop_reconnect = False
    
    def _setup_callbacks(self):
        """Configurar callbacks del cliente MQTT"""
        self.callback_handler = MQTTCallbackHandler(self)
        
        self.client.on_connect = self.callback_handler.on_connect
        self.client.on_disconnect = self.callback_handler.on_disconnect
        self.client.on_message = self.callback_handler.on_message
        self.client.on_publish = self.callback_handler.on_publish
        self.client.on_subscribe = self.callback_handler.on_subscribe
        self.client.on_unsubscribe = self.callback_handler.on_unsubscribe
        self.client.on_log = self.callback_handler.on_log
    
    def _setup_connection_options(self):
        """Configurar opciones de conexión"""
        # Configurar keepalive
        self.client.keepalive = self.config.broker.get('keepalive', 60)
        
        # Configurar credenciales si están disponibles
        username = self.config.broker.get('username')
        password = self.config.broker.get('password')
        
        if username and password:
            self.client.username_pw_set(username, password)
            self.logger.info("🔐 Credenciales MQTT configuradas")
        
        # Configurar TLS si está habilitado
        tls_enabled = self.config.broker.get('tls_enabled', False)
        if tls_enabled:
            ca_certs = self.config.broker.get('ca_certs')
            certfile = self.config.broker.get('certfile')
            keyfile = self.config.broker.get('keyfile')
            
            try:
                self.client.tls_set(
                    ca_certs=ca_certs,
                    certfile=certfile,
                    keyfile=keyfile
                )
                self.logger.info("🔒 TLS configurado para MQTT")
            except Exception as e:
                self.logger.error(f"❌ Error al configurar TLS: {e}")
    
    def connect(self, max_retries: int = 3, retry_delay: float = 5.0) -> bool:
        """
        Conectar al broker MQTT
        
        Args:
            max_retries: Número máximo de intentos de conexión
            retry_delay: Delay entre intentos en segundos
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
        """
        host = self.config.broker['host']
        port = self.config.broker['port']
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"🔌 Intentando conexión MQTT a {host}:{port} (intento {attempt + 1}/{max_retries})")
                
                # Conectar al broker
                result = self.client.connect(host, port)
                
                if result == mqtt_client.MQTT_ERR_SUCCESS:
                    # Iniciar loop en thread separado
                    self.client.loop_start()
                    
                    # Esperar a que se establezca la conexión
                    timeout = 10  # segundos
                    start_time = time.time()
                    
                    while not self._connected and (time.time() - start_time) < timeout:
                        time.sleep(0.1)
                    
                    if self._connected:
                        self.logger.info(f"✅ Conectado exitosamente a {host}:{port}")
                        
                        # Iniciar thread de reconexión
                        self._start_reconnect_thread()
                        
                        return True
                    else:
                        self.logger.error("❌ Timeout en la conexión MQTT")
                        self.client.loop_stop()
                else:
                    self.logger.error(f"❌ Error de conexión MQTT: {result}")
                
            except Exception as e:
                self.logger.error(f"❌ Excepción durante la conexión: {e}")
            
            # Esperar antes del siguiente intento
            if attempt < max_retries - 1:
                self.logger.info(f"⏳ Esperando {retry_delay} segundos antes del siguiente intento...")
                time.sleep(retry_delay)
        
        self.logger.error(f"❌ Falló la conexión después de {max_retries} intentos")
        return False
    
    def disconnect(self):
        """Desconectar del broker MQTT"""
        try:
            self.logger.info("🔌 Desconectando del broker MQTT...")
            
            # Detener thread de reconexión
            self._stop_reconnect_thread()
            
            # Desconectar cliente
            self.client.loop_stop()
            self.client.disconnect()
            
            self._connected = False
            self._connection_time = None
            
            self.logger.info("✅ Desconectado del broker MQTT")
            
        except Exception as e:
            self.logger.error(f"❌ Error al desconectar: {e}")
    
    def publish(self, topic: str, payload: Dict[str, Any], qos: Optional[int] = None, 
                retain: Optional[bool] = None) -> bool:
        """
        Publicar mensaje en un tópico
        
        Args:
            topic: Tópico donde publicar
            payload: Datos a publicar (se convertirán a JSON)
            qos: Calidad de servicio (usa la configurada si es None)
            retain: Si el mensaje debe retenerse (usa la configurada si es None)
        
        Returns:
            True si la publicación fue exitosa, False en caso contrario
        """
        if not self._connected:
            self.logger.error("❌ No hay conexión MQTT activa")
            return False
        
        try:
            # Usar valores por defecto de la configuración
            qos = qos if qos is not None else self.config.qos
            retain = retain if retain is not None else self.config.retain
            
            # Convertir payload a JSON
            json_payload = json.dumps(payload, ensure_ascii=False)
            
            # Publicar mensaje
            result = self.client.publish(topic, json_payload, qos=qos, retain=retain)
            
            if result.rc == mqtt_client.MQTT_ERR_SUCCESS:
                self.logger.debug(f"📤 Mensaje publicado en {topic}: {payload}")
                return True
            else:
                self.logger.error(f"❌ Error al publicar mensaje: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Excepción al publicar mensaje: {e}")
            return False
    
    def subscribe(self, topic: str, qos: Optional[int] = None) -> bool:
        """
        Suscribirse a un tópico específico
        
        Args:
            topic: Tópico al cual suscribirse
            qos: Calidad de servicio (usa la configurada si es None)
        
        Returns:
            True si la suscripción fue exitosa, False en caso contrario
        """
        if not self._connected:
            self.logger.error("❌ No hay conexión MQTT activa")
            return False
        
        try:
            qos = qos if qos is not None else self.config.qos
            
            result, mid = self.client.subscribe(topic, qos=qos)
            
            if result == mqtt_client.MQTT_ERR_SUCCESS:
                self.logger.info(f"📋 Suscrito a tópico: {topic}")
                return True
            else:
                self.logger.error(f"❌ Error al suscribirse a {topic}: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Excepción al suscribirse a {topic}: {e}")
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """
        Desuscribirse de un tópico
        
        Args:
            topic: Tópico del cual desuscribirse
        
        Returns:
            True si la desuscripción fue exitosa, False en caso contrario
        """
        if not self._connected:
            self.logger.error("❌ No hay conexión MQTT activa")
            return False
        
        try:
            result, mid = self.client.unsubscribe(topic)
            
            if result == mqtt_client.MQTT_ERR_SUCCESS:
                self.logger.info(f"📋 Desuscrito de tópico: {topic}")
                return True
            else:
                self.logger.error(f"❌ Error al desuscribirse de {topic}: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Excepción al desuscribirse de {topic}: {e}")
            return False
    
    def set_message_processor(self, processor: Callable[[MQTTMessage], None]):
        """
        Establecer el procesador de mensajes
        
        Args:
            processor: Función que procesará los mensajes recibidos
        """
        self.message_processor = processor
        self.logger.info("🔧 Procesador de mensajes configurado")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Obtener estado de la conexión
        
        Returns:
            Diccionario con información del estado de la conexión
        """
        return {
            'connected': self._connected,
            'client_id': self.client_id,
            'broker_host': self.config.broker['host'],
            'broker_port': self.config.broker['port'],
            'connection_time': self._connection_time.isoformat() if self._connection_time else None,
            'last_message_time': self._last_message_time.isoformat() if self._last_message_time else None,
            'message_count': self._message_count,
            'subscribed_topics': self.config.topics.get('subscribe', [])
        }
    
    def _start_reconnect_thread(self):
        """Iniciar thread de reconexión automática"""
        if self._reconnect_thread is None or not self._reconnect_thread.is_alive():
            self._stop_reconnect = False
            self._reconnect_thread = threading.Thread(
                target=self._reconnect_loop,
                daemon=True,
                name="MQTT_Reconnect"
            )
            self._reconnect_thread.start()
            self.logger.info("🔄 Thread de reconexión iniciado")
    
    def _stop_reconnect_thread(self):
        """Detener thread de reconexión"""
        self._stop_reconnect = True
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            self._reconnect_thread.join(timeout=5.0)
            self.logger.info("🔄 Thread de reconexión detenido")
    
    def _reconnect_loop(self):
        """Loop de reconexión automática"""
        while not self._stop_reconnect:
            try:
                if not self._connected:
                    self.logger.info("🔄 Intentando reconexión automática...")
                    
                    # Detener loop actual
                    self.client.loop_stop()
                    
                    # Intentar reconectar
                    if self.connect(max_retries=1):
                        self.logger.info("✅ Reconexión exitosa")
                    else:
                        self.logger.warning("⚠️  Reconexión falló, reintentando en 30 segundos...")
                        time.sleep(30)
                else:
                    # Conexión activa, esperar
                    time.sleep(10)
                    
            except Exception as e:
                self.logger.error(f"❌ Error en loop de reconexión: {e}")
                time.sleep(30)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


def create_mqtt_client(config: MQTTConfig, client_id: Optional[str] = None) -> IoTMQTTClient:
    """
    Función de conveniencia para crear un cliente MQTT
    
    Args:
        config: Configuración MQTT
        client_id: ID único del cliente (opcional)
    
    Returns:
        Instancia del cliente MQTT
    """
    return IoTMQTTClient(config, client_id)


# Función de ejemplo para procesar mensajes
def process_message(message: MQTTMessage) -> None:
    """
    Función de ejemplo para procesar mensajes MQTT
    
    Args:
        message: Mensaje MQTT recibido
    """
    logger.info(f"📨 Procesando mensaje de {message.topic}")
    logger.info(f"   Payload: {message.payload}")
    logger.info(f"   QoS: {message.qos}")
    logger.info(f"   Timestamp: {message.timestamp}")


# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Cargar configuración
        from iot_middleware.config import load_config
        
        config = load_config()
        mqtt_config = config.mqtt
        
        # Crear cliente MQTT
        mqtt_client = create_mqtt_client(mqtt_config)
        
        # Configurar procesador de mensajes
        mqtt_client.set_message_processor(process_message)
        
        # Conectar al broker
        if mqtt_client.connect():
            print("✅ Cliente MQTT conectado exitosamente")
            
            # Mantener conexión activa
            try:
                while True:
                    time.sleep(1)
                    
                    # Mostrar estado cada 10 segundos
                    if int(time.time()) % 10 == 0:
                        status = mqtt_client.get_connection_status()
                        print(f"📊 Estado: {status['connected']}, Mensajes: {status['message_count']}")
                        
            except KeyboardInterrupt:
                print("\n🛑 Interrumpido por el usuario")
                
        else:
            print("❌ No se pudo conectar al broker MQTT")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
