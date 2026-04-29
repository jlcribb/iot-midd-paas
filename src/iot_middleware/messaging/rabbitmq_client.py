"""
Cliente RabbitMQ - IoT Middleware
=================================

Este módulo implementa un cliente RabbitMQ para comunicación asíncrona
entre microservicios del IoT Middleware.
"""

import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum
import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Tipos de eventos de monitoreo"""
    METRIC = "metric"
    ALERT = "alert"
    STATUS = "status"
    DATA = "data"
    SYSTEM = "system"
    PROTOCOL = "protocol"
    PROCESSING = "processing"
    STORAGE = "storage"


@dataclass
class MonitoringEvent:
    """Evento de monitoreo para publicación en RabbitMQ"""
    event_type: EventType
    service: str
    timestamp: datetime
    data: Dict[str, Any]
    severity: str = "info"
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a diccionario para serialización"""
        return {
            "event_type": self.event_type.value,
            "service": self.service,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "severity": self.severity,
            "metadata": self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonitoringEvent':
        """Crea un evento desde un diccionario"""
        return cls(
            event_type=EventType(data.get("event_type", "metric")),
            service=data.get("service", "unknown"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
            data=data.get("data", {}),
            severity=data.get("severity", "info"),
            metadata=data.get("metadata")
        )


class RabbitMQClient:
    """Cliente RabbitMQ para comunicación asíncrona"""
    
    def __init__(self, config):
        """
        Inicializa el cliente RabbitMQ
        
        Args:
            config: Configuración de RabbitMQ (RabbitMQConfig)
        """
        self.config = config
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self.exchange = config.exchange
        self.queue_prefix = config.queue_prefix
        
        # Estado de conexión
        self.connected = False
        self.reconnecting = False
        self._lock = threading.Lock()
        
        # Callbacks de eventos
        self.event_callbacks: Dict[EventType, List[Callable]] = {}
        
        # Thread de reconexión
        self._reconnect_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        logger.info(f"🔌 Cliente RabbitMQ inicializado: {config.host}:{config.port}")

    def _ensure_connected(self) -> bool:
        """Garantiza que exista una conexión usable antes de operar."""
        if self.connected and self.channel and not self.channel.is_closed:
            return True
        return self.connect()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def connect(self) -> bool:
        """
        Conecta al servidor RabbitMQ
        
        Returns:
            True si la conexión fue exitosa, False en caso contrario
        """
        try:
            with self._lock:
                if self.connected:
                    return True
                
                logger.info(f"🔌 Conectando a RabbitMQ: {self.config.host}:{self.config.port}")
                
                # Parámetros de conexión
                credentials = pika.PlainCredentials(
                    username=self.config.username,
                    password=self.config.password
                )
                
                parameters = pika.ConnectionParameters(
                    host=self.config.host,
                    port=self.config.port,
                    virtual_host=self.config.virtual_host,
                    credentials=credentials,
                    heartbeat=self.config.heartbeat,
                    connection_attempts=self.config.connection_attempts,
                    retry_delay=self.config.retry_delay
                )
                
                # Crear conexión
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Declarar exchange
                self.channel.exchange_declare(
                    exchange=self.exchange,
                    exchange_type='topic',
                    durable=True
                )
                
                logger.info(f"✅ Conectado a RabbitMQ exitosamente")
                self.connected = True
                self.reconnecting = False
                
                return True
                
        except AMQPConnectionError as e:
            logger.error(f"❌ Error de conexión a RabbitMQ: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado conectando a RabbitMQ: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Desconecta del servidor RabbitMQ"""
        try:
            with self._lock:
                self._stop_event.set()
                
                if self.channel and not self.channel.is_closed:
                    self.channel.close()
                
                if self.connection and not self.connection.is_closed:
                    self.connection.close()
                
                self.connected = False
                logger.info("🔌 Desconectado de RabbitMQ")
                
        except Exception as e:
            logger.error(f"❌ Error desconectando de RabbitMQ: {e}")
    
    def publish_event(self, event: MonitoringEvent, routing_key: Optional[str] = None) -> bool:
        """
        Publica un evento en RabbitMQ
        
        Args:
            event: Evento de monitoreo a publicar
            routing_key: Clave de enrutamiento (opcional, se genera automáticamente)
        
        Returns:
            True si la publicación fue exitosa, False en caso contrario
        """
        try:
            if not self.connected:
                if not self.connect():
                    logger.warning("⚠️  No se pudo conectar a RabbitMQ, evento no publicado")
                    return False
            
            # Generar routing key si no se proporciona
            if routing_key is None:
                routing_key = f"{self.queue_prefix}.{event.event_type.value}.{event.service}"
            
            # Serializar evento
            message = json.dumps(event.to_dict())
            
            # Publicar mensaje
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Hacer el mensaje persistente
                    timestamp=int(time.time()),
                    content_type='application/json'
                )
            )
            
            logger.debug(f"📤 Evento publicado: {routing_key} - {event.event_type.value}")
            return True
            
        except AMQPChannelError as e:
            logger.error(f"❌ Error de canal RabbitMQ: {e}")
            self.connected = False
            self._start_reconnect()
            return False
        except Exception as e:
            logger.error(f"❌ Error publicando evento: {e}")
            return False

    def declare_topic_queue(
        self,
        queue_name: str,
        routing_keys: Optional[List[str]] = None,
        durable: bool = True,
        auto_delete: bool = False,
        exclusive: bool = False,
    ) -> bool:
        """
        Declara una cola topic y la vincula al exchange actual.

        Si no se pasan routing keys, se usa el mismo nombre de cola.
        """
        try:
            if not self._ensure_connected():
                return False

            self.channel.queue_declare(
                queue=queue_name,
                durable=durable,
                auto_delete=auto_delete,
                exclusive=exclusive,
            )

            bindings = routing_keys or [queue_name]
            for routing_key in bindings:
                self.channel.queue_bind(
                    exchange=self.exchange,
                    queue=queue_name,
                    routing_key=routing_key,
                )

            return True
        except Exception as e:
            logger.error(f"❌ Error declarando cola topic {queue_name}: {e}")
            return False

    def publish_json(
        self,
        routing_key: str,
        payload: Dict[str, Any],
        queue_name: Optional[str] = None,
        durable_queue: bool = True,
    ) -> bool:
        """
        Publica un payload JSON arbitrario en el exchange topic actual.

        Opcionalmente declara una cola homónima para asegurar que exista un
        destino persistente aun si el consumidor todavía no arrancó.
        """
        try:
            if not self._ensure_connected():
                logger.warning("⚠️  No se pudo conectar a RabbitMQ, payload no publicado")
                return False

            if queue_name is not None:
                if not self.declare_topic_queue(
                    queue_name=queue_name,
                    routing_keys=[routing_key],
                    durable=durable_queue,
                ):
                    return False

            message = json.dumps(payload, ensure_ascii=False, default=str)
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    timestamp=int(time.time()),
                    content_type="application/json",
                ),
            )
            logger.debug(f"📤 Payload JSON publicado: {routing_key}")
            return True
        except Exception as e:
            logger.error(f"❌ Error publicando payload JSON: {e}")
            return False

    def get_json_message(self, queue_name: str, auto_ack: bool = False) -> Optional[Dict[str, Any]]:
        """
        Lee un mensaje JSON de una cola usando polling (`basic_get`).

        Retorna el payload más el `delivery_tag` cuando `auto_ack=False`.
        """
        try:
            if not self._ensure_connected():
                return None

            method_frame, _, body = self.channel.basic_get(
                queue=queue_name,
                auto_ack=auto_ack,
            )
            if method_frame is None:
                return None

            decoded = json.loads(body.decode("utf-8"))
            message = {
                "payload": decoded,
                "routing_key": getattr(method_frame, "routing_key", None),
            }
            if not auto_ack:
                message["delivery_tag"] = method_frame.delivery_tag
            return message
        except Exception as e:
            logger.error(f"❌ Error leyendo payload JSON desde {queue_name}: {e}")
            return None

    def ack_message(self, delivery_tag: int) -> bool:
        """Confirma manualmente un mensaje leído con auto_ack=False."""
        try:
            if not self._ensure_connected():
                return False
            self.channel.basic_ack(delivery_tag=delivery_tag)
            return True
        except Exception as e:
            logger.error(f"❌ Error confirmando mensaje RabbitMQ: {e}")
            return False

    def purge_queue(self, queue_name: str) -> bool:
        """Vacía una cola existente, útil para smokes y diagnósticos."""
        try:
            if not self._ensure_connected():
                return False
            self.channel.queue_purge(queue=queue_name)
            return True
        except Exception as e:
            logger.error(f"❌ Error purgando cola {queue_name}: {e}")
            return False
    
    def subscribe_to_events(
        self,
        event_types: List[EventType],
        callback: Callable[[MonitoringEvent], None],
        queue_name: Optional[str] = None
    ) -> bool:
        """
        Se suscribe a eventos de monitoreo
        
        Args:
            event_types: Lista de tipos de eventos a suscribir
            callback: Función callback que se ejecutará cuando llegue un evento
            queue_name: Nombre de la cola (opcional, se genera automáticamente)
        
        Returns:
            True si la suscripción fue exitosa, False en caso contrario
        """
        try:
            if not self.connected:
                if not self.connect():
                    return False
            
            # Generar nombre de cola si no se proporciona
            if queue_name is None:
                queue_name = f"{self.queue_prefix}_consumer_{int(time.time())}"
            
            # Declarar cola
            result = self.channel.queue_declare(
                queue=queue_name,
                durable=True,
                exclusive=False,
                auto_delete=False
            )
            
            # Suscribirse a cada tipo de evento
            for event_type in event_types:
                routing_key = f"{self.queue_prefix}.{event_type.value}.*"
                
                # Vincular cola al exchange
                self.channel.queue_bind(
                    exchange=self.exchange,
                    queue=queue_name,
                    routing_key=routing_key
                )
                
                # Registrar callback
                if event_type not in self.event_callbacks:
                    self.event_callbacks[event_type] = []
                self.event_callbacks[event_type].append(callback)
            
            # Configurar consumidor
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self._on_message,
                auto_ack=True
            )
            
            logger.info(f"✅ Suscrito a eventos: {[et.value for et in event_types]}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error suscribiéndose a eventos: {e}")
            return False
    
    def _on_message(self, ch, method, properties, body):
        """Manejador de mensajes recibidos"""
        try:
            # Deserializar mensaje
            data = json.loads(body)
            event = MonitoringEvent.from_dict(data)
            
            # Ejecutar callbacks registrados
            if event.event_type in self.event_callbacks:
                for callback in self.event_callbacks[event.event_type]:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(f"❌ Error en callback de evento: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
    
    def start_consuming(self):
        """Inicia el consumo de mensajes (bloqueante)"""
        try:
            if not self.connected:
                if not self.connect():
                    return
            
            logger.info("🔄 Iniciando consumo de mensajes RabbitMQ...")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("🛑 Consumo de mensajes interrumpido")
            self.stop_consuming()
        except Exception as e:
            logger.error(f"❌ Error consumiendo mensajes: {e}")
    
    def stop_consuming(self):
        """Detiene el consumo de mensajes"""
        try:
            if self.channel:
                self.channel.stop_consuming()
            logger.info("🛑 Consumo de mensajes detenido")
        except Exception as e:
            logger.error(f"❌ Error deteniendo consumo: {e}")
    
    def _start_reconnect(self):
        """Inicia el thread de reconexión"""
        if self.reconnecting:
            return
        
        self.reconnecting = True
        self._reconnect_thread = threading.Thread(
            target=self._reconnect_loop,
            daemon=True
        )
        self._reconnect_thread.start()
    
    def _reconnect_loop(self):
        """Loop de reconexión en background"""
        while not self._stop_event.is_set() and not self.connected:
            try:
                logger.info("🔄 Intentando reconectar a RabbitMQ...")
                if self.connect():
                    logger.info("✅ Reconexión exitosa")
                    break
                else:
                    time.sleep(self.config.retry_delay)
            except Exception as e:
                logger.error(f"❌ Error en reconexión: {e}")
                time.sleep(self.config.retry_delay)
        
        self.reconnecting = False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica el estado de salud de la conexión
        
        Returns:
            Diccionario con el estado de salud
        """
        return {
            "connected": self.connected,
            "reconnecting": self.reconnecting,
            "exchange": self.exchange,
            "host": self.config.host,
            "port": self.config.port
        }


def create_rabbitmq_client(config) -> RabbitMQClient:
    """
    Crea una instancia del cliente RabbitMQ
    
    Args:
        config: Configuración de RabbitMQ
    
    Returns:
        Instancia de RabbitMQClient
    """
    return RabbitMQClient(config)
