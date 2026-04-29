#!/usr/bin/env python3
"""
Publicador MQTT para SBC con sensor DHT22
==========================================

Este script lee datos del sensor DHT22 y los publica en MQTT
para que el IoT Middleware los procese.

Requisitos:
    pip install paho-mqtt Adafruit_DHT

Instalación en SBC:
    1. Instalar dependencias:
       sudo apt-get update
       sudo apt-get install python3-pip python3-dev
       pip3 install paho-mqtt Adafruit_DHT
    
    2. Dar permisos de ejecución:
       chmod +x sbc_dht22_publisher.py
    
    3. Configurar como servicio systemd (opcional):
       Ver ejemplo al final del archivo
"""

import json
import time
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: paho-mqtt no está instalado. Instalar con: pip3 install paho-mqtt")
    sys.exit(1)

try:
    import Adafruit_DHT
except ImportError:
    print("Error: Adafruit_DHT no está instalado. Instalar con: pip3 install Adafruit_DHT")
    sys.exit(1)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACIÓN - Ajustar según tu entorno
# ============================================

# Configuración MQTT
MQTT_BROKER = "192.168.1.100"  # IP o hostname del broker MQTT
MQTT_PORT = 1883
MQTT_USERNAME = "iot_user"      # Opcional, None si no requiere autenticación
MQTT_PASSWORD = "iot_password"  # Opcional, None si no requiere autenticación
MQTT_CLIENT_ID = f"dht22_sbc_{int(time.time())}"

# Configuración del sensor DHT22
DHT_SENSOR = Adafruit_DHT.DHT22  # Tipo de sensor
DHT_PIN = 4  # Pin GPIO donde está conectado el sensor (ajustar según tu conexión)

# Configuración de tópicos MQTT
# Opción 1: Formato estructurado (recomendado)
# iot/{proyecto}/{unidad}/{dispositivo}/{canal}
MQTT_TOPIC_TEMPERATURE = "iot/proyecto_demo/casa_living/dht22_sbc/temperatura"
MQTT_TOPIC_HUMIDITY = "iot/proyecto_demo/casa_living/dht22_sbc/humedad"

# Opción 2: Formato simplificado (alternativa)
# sensors/{tipo}/{ubicacion}/{id}
# MQTT_TOPIC_TEMPERATURE = "sensors/temperature/living_room/dht22_001"
# MQTT_TOPIC_HUMIDITY = "sensors/humidity/living_room/dht22_001"

# Intervalo de lectura (segundos)
READ_INTERVAL = 30  # Leer cada 30 segundos

# QoS MQTT
MQTT_QOS = 1

# ============================================
# CLASE PUBLICADOR MQTT
# ============================================

class DHT22Publisher:
    """Publicador de datos DHT22 a MQTT"""
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.reconnect_delay = 5
        
    def connect(self) -> bool:
        """Conectar al broker MQTT"""
        try:
            self.client = mqtt.Client(client_id=MQTT_CLIENT_ID)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish
            
            if MQTT_USERNAME and MQTT_PASSWORD:
                self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            
            logger.info(f"Conectando a MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.client.loop_start()
            
            # Esperar conexión
            timeout = 10
            elapsed = 0
            while not self.connected and elapsed < timeout:
                time.sleep(0.5)
                elapsed += 0.5
            
            if self.connected:
                logger.info("✅ Conectado al broker MQTT")
                return True
            else:
                logger.error("❌ Timeout al conectar al broker MQTT")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conectando a MQTT: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker"""
        if rc == 0:
            self.connected = True
            logger.info("✅ Conexión MQTT establecida")
        else:
            self.connected = False
            logger.error(f"❌ Error de conexión MQTT. Código: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta del broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"⚠️  Desconexión inesperada del broker MQTT. Código: {rc}")
        else:
            logger.info("Desconectado del broker MQTT")
    
    def _on_publish(self, client, userdata, mid):
        """Callback cuando se publica un mensaje"""
        logger.debug(f"✅ Mensaje publicado con ID: {mid}")
    
    def read_sensor(self) -> Optional[Dict[str, Any]]:
        """
        Leer datos del sensor DHT22
        
        Returns:
            Diccionario con temperatura y humedad, o None si hay error
        """
        try:
            humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            
            if humidity is not None and temperature is not None:
                return {
                    'temperature': round(temperature, 2),
                    'humidity': round(humidity, 2),
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'sensor_type': 'DHT22',
                    'sensor_id': MQTT_CLIENT_ID
                }
            else:
                logger.warning("⚠️  No se pudieron leer los datos del sensor")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error leyendo sensor DHT22: {e}")
            return None
    
    def publish_data(self, data: Dict[str, Any]) -> bool:
        """
        Publicar datos en MQTT
        
        Args:
            data: Diccionario con los datos del sensor
            
        Returns:
            True si se publicó correctamente, False en caso contrario
        """
        if not self.connected:
            logger.error("❌ No hay conexión MQTT activa")
            return False
        
        try:
            timestamp = data.get('timestamp', datetime.now(timezone.utc).isoformat())
            
            # Preparar payload para temperatura
            temp_payload = {
                'valor': data['temperature'],
                'unidad': 'celsius',
                'timestamp': timestamp,
                'tipo': 'temperatura',
                'sensor_id': data.get('sensor_id', MQTT_CLIENT_ID),
                'metadata': {
                    'sensor_type': 'DHT22',
                    'location': 'living_room',  # Ajustar según tu ubicación
                    'pin': DHT_PIN
                }
            }
            
            # Preparar payload para humedad
            hum_payload = {
                'valor': data['humidity'],
                'unidad': 'porcentaje',
                'timestamp': timestamp,
                'tipo': 'humedad',
                'sensor_id': data.get('sensor_id', MQTT_CLIENT_ID),
                'metadata': {
                    'sensor_type': 'DHT22',
                    'location': 'living_room',  # Ajustar según tu ubicación
                    'pin': DHT_PIN
                }
            }
            
            # Publicar temperatura
            result_temp = self.client.publish(
                MQTT_TOPIC_TEMPERATURE,
                json.dumps(temp_payload),
                qos=MQTT_QOS,
                retain=False
            )
            
            if result_temp.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"📤 Temperatura publicada: {data['temperature']}°C en {MQTT_TOPIC_TEMPERATURE}")
            else:
                logger.error(f"❌ Error publicando temperatura. Código: {result_temp.rc}")
            
            # Publicar humedad
            result_hum = self.client.publish(
                MQTT_TOPIC_HUMIDITY,
                json.dumps(hum_payload),
                qos=MQTT_QOS,
                retain=False
            )
            
            if result_hum.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"📤 Humedad publicada: {data['humidity']}% en {MQTT_TOPIC_HUMIDITY}")
            else:
                logger.error(f"❌ Error publicando humedad. Código: {result_hum.rc}")
            
            return result_temp.rc == mqtt.MQTT_ERR_SUCCESS and result_hum.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            logger.error(f"❌ Error publicando datos: {e}")
            return False
    
    def run(self):
        """Ejecutar el loop principal de lectura y publicación"""
        logger.info("🚀 Iniciando publicador DHT22 MQTT...")
        logger.info(f"📌 Sensor: DHT22 en GPIO pin {DHT_PIN}")
        logger.info(f"📌 Intervalo de lectura: {READ_INTERVAL} segundos")
        logger.info(f"📌 Broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
        
        # Conectar al broker
        if not self.connect():
            logger.error("❌ No se pudo conectar al broker. Abortando.")
            return
        
        # Loop principal
        consecutive_errors = 0
        max_errors = 5
        
        try:
            while True:
                # Leer sensor
                data = self.read_sensor()
                
                if data:
                    # Publicar datos
                    if self.publish_data(data):
                        consecutive_errors = 0
                        logger.info(f"✅ Datos publicados: Temp={data['temperature']}°C, Hum={data['humidity']}%")
                    else:
                        consecutive_errors += 1
                        logger.warning(f"⚠️  Error publicando datos (intento {consecutive_errors}/{max_errors})")
                else:
                    consecutive_errors += 1
                    logger.warning(f"⚠️  Error leyendo sensor (intento {consecutive_errors}/{max_errors})")
                
                # Si hay muchos errores consecutivos, intentar reconectar
                if consecutive_errors >= max_errors:
                    logger.error(f"❌ Demasiados errores consecutivos. Reconectando...")
                    self.client.loop_stop()
                    time.sleep(self.reconnect_delay)
                    if self.connect():
                        consecutive_errors = 0
                    else:
                        logger.error("❌ No se pudo reconectar. Esperando antes de reintentar...")
                        time.sleep(self.reconnect_delay * 2)
                
                # Esperar antes de la siguiente lectura
                time.sleep(READ_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("🛑 Deteniendo publicador...")
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
        finally:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
            logger.info("✅ Publicador detenido")


# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == "__main__":
    publisher = DHT22Publisher()
    publisher.run()

# ============================================
# CONFIGURACIÓN COMO SERVICIO SYSTEMD
# ============================================
"""
Para ejecutar como servicio en systemd, crear el archivo:
/etc/systemd/system/dht22-mqtt.service

[Unit]
Description=DHT22 MQTT Publisher
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/iot-middleware
ExecStart=/usr/bin/python3 /home/pi/iot-middleware/examples/sbc_dht22_publisher.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

Luego ejecutar:
sudo systemctl daemon-reload
sudo systemctl enable dht22-mqtt.service
sudo systemctl start dht22-mqtt.service
sudo systemctl status dht22-mqtt.service
"""
