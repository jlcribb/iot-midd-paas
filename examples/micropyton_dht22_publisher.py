"""
Publicador MQTT para MicroPython con sensor DHT22
==================================================

Este script está diseñado para placas con MicroPython como:
- ESP32
- ESP8266
- Raspberry Pi Pico
- Otras placas compatibles con MicroPython

Requisitos:
    - MicroPython instalado en la placa
    - Librería dht (incluida en MicroPython)
    - Librería umqtt.simple (incluida en MicroPython o instalar)

Instalación:
    1. Subir este archivo a la placa usando Thonny, ampy, o rshell
    2. Asegurarse de tener conexión WiFi configurada
    3. Ajustar las variables de configuración
"""

import network
import time
import json
from machine import Pin
from dht import DHT22
from umqtt.simple import MQTTClient
from datetime import datetime

# ============================================
# CONFIGURACIÓN - Ajustar según tu entorno
# ============================================

# Configuración WiFi
WIFI_SSID = "tu_wifi_ssid"
WIFI_PASSWORD = "tu_wifi_password"

# Configuración MQTT
MQTT_BROKER = "192.168.1.100"  # IP del servidor con el middleware
MQTT_PORT = 1883
MQTT_USERNAME = "iot_user"      # Opcional, None si no requiere autenticación
MQTT_PASSWORD = "iot_password"  # Opcional, None si no requiere autenticación
MQTT_CLIENT_ID = "dht22_esp32_001"

# Configuración del sensor DHT22
DHT_PIN = 4  # Pin GPIO donde está conectado el sensor

# Configuración de tópicos MQTT
MQTT_TOPIC_TEMPERATURE = b"iot/proyecto_demo/casa_living/dht22_esp32/temperatura"
MQTT_TOPIC_HUMIDITY = b"iot/proyecto_demo/casa_living/dht22_esp32/humedad"

# Intervalo de lectura (segundos)
READ_INTERVAL = 30

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def connect_wifi():
    """Conectar a WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print(f"Conectando a WiFi: {WIFI_SSID}")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        # Esperar conexión (máximo 20 segundos)
        timeout = 20
        elapsed = 0
        while not wlan.isconnected() and elapsed < timeout:
            time.sleep(1)
            elapsed += 1
            print(".", end="")
        
        if wlan.isconnected():
            print(f"\n✅ Conectado a WiFi")
            print(f"   IP: {wlan.ifconfig()[0]}")
            return True
        else:
            print(f"\n❌ Error conectando a WiFi")
            return False
    else:
        print(f"✅ Ya conectado a WiFi: {wlan.ifconfig()[0]}")
        return True

def get_timestamp():
    """Obtener timestamp ISO8601 (requiere RTC configurado o NTP)"""
    try:
        # Intentar usar RTC si está configurado
        import ntptime
        ntptime.settime()  # Sincronizar con NTP
        now = time.localtime()
        return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z".format(
            now[0], now[1], now[2], now[3], now[4], now[5]
        )
    except:
        # Si no hay NTP, usar tiempo relativo
        return f"epoch_{time.time()}"

# ============================================
# CLASE PUBLICADOR MQTT
# ============================================

class DHT22Publisher:
    """Publicador de datos DHT22 a MQTT para MicroPython"""
    
    def __init__(self):
        self.client = None
        self.dht = DHT22(Pin(DHT_PIN))
        self.connected = False
        
    def connect_mqtt(self):
        """Conectar al broker MQTT"""
        try:
            self.client = MQTTClient(
                client_id=MQTT_CLIENT_ID,
                server=MQTT_BROKER,
                port=MQTT_PORT,
                user=MQTT_USERNAME if MQTT_USERNAME else None,
                password=MQTT_PASSWORD if MQTT_PASSWORD else None,
                keepalive=60
            )
            
            print(f"Conectando a MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
            self.client.connect()
            self.connected = True
            print("✅ Conectado al broker MQTT")
            return True
            
        except Exception as e:
            print(f"❌ Error conectando a MQTT: {e}")
            self.connected = False
            return False
    
    def read_sensor(self):
        """Leer datos del sensor DHT22"""
        try:
            self.dht.measure()
            temperature = self.dht.temperature()
            humidity = self.dht.humidity()
            
            if temperature is not None and humidity is not None:
                return {
                    'temperature': round(temperature, 2),
                    'humidity': round(humidity, 2),
                    'timestamp': get_timestamp(),
                    'sensor_type': 'DHT22',
                    'sensor_id': MQTT_CLIENT_ID
                }
            else:
                print("⚠️  No se pudieron leer los datos del sensor")
                return None
                
        except Exception as e:
            print(f"❌ Error leyendo sensor DHT22: {e}")
            return None
    
    def publish_data(self, data):
        """Publicar datos en MQTT"""
        if not self.connected:
            print("❌ No hay conexión MQTT activa")
            return False
        
        try:
            timestamp = data.get('timestamp', get_timestamp())
            
            # Preparar payload para temperatura
            temp_payload = {
                'valor': data['temperature'],
                'unidad': 'celsius',
                'timestamp': timestamp,
                'tipo': 'temperatura',
                'sensor_id': data.get('sensor_id', MQTT_CLIENT_ID),
                'metadata': {
                    'sensor_type': 'DHT22',
                    'location': 'living_room',
                    'pin': DHT_PIN,
                    'platform': 'micropython'
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
                    'location': 'living_room',
                    'pin': DHT_PIN,
                    'platform': 'micropython'
                }
            }
            
            # Publicar temperatura
            try:
                self.client.publish(
                    MQTT_TOPIC_TEMPERATURE,
                    json.dumps(temp_payload).encode('utf-8'),
                    qos=1
                )
                print(f"📤 Temperatura: {data['temperature']}°C")
            except Exception as e:
                print(f"❌ Error publicando temperatura: {e}")
            
            # Publicar humedad
            try:
                self.client.publish(
                    MQTT_TOPIC_HUMIDITY,
                    json.dumps(hum_payload).encode('utf-8'),
                    qos=1
                )
                print(f"📤 Humedad: {data['humidity']}%")
            except Exception as e:
                print(f"❌ Error publicando humedad: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error publicando datos: {e}")
            return False
    
    def run(self):
        """Ejecutar el loop principal"""
        print("🚀 Iniciando publicador DHT22 MQTT (MicroPython)...")
        print(f"📌 Sensor: DHT22 en GPIO pin {DHT_PIN}")
        print(f"📌 Intervalo: {READ_INTERVAL} segundos")
        
        # Conectar WiFi
        if not connect_wifi():
            print("❌ No se pudo conectar a WiFi. Abortando.")
            return
        
        # Conectar MQTT
        if not self.connect_mqtt():
            print("❌ No se pudo conectar a MQTT. Abortando.")
            return
        
        # Loop principal
        consecutive_errors = 0
        max_errors = 5
        
        try:
            while True:
                # Leer sensor
                data = self.read_sensor()
                
                if data:
                    # Verificar conexión MQTT
                    if not self.connected:
                        print("⚠️  Reconectando a MQTT...")
                        self.connect_mqtt()
                    
                    # Publicar datos
                    if self.publish_data(data):
                        consecutive_errors = 0
                        print(f"✅ Datos publicados: Temp={data['temperature']}°C, Hum={data['humidity']}%")
                    else:
                        consecutive_errors += 1
                        print(f"⚠️  Error publicando (intento {consecutive_errors}/{max_errors})")
                else:
                    consecutive_errors += 1
                    print(f"⚠️  Error leyendo sensor (intento {consecutive_errors}/{max_errors})")
                
                # Si hay muchos errores, intentar reconectar
                if consecutive_errors >= max_errors:
                    print("❌ Demasiados errores. Reconectando...")
                    try:
                        self.client.disconnect()
                    except:
                        pass
                    time.sleep(5)
                    if self.connect_mqtt():
                        consecutive_errors = 0
                    else:
                        time.sleep(10)
                
                # Esperar antes de la siguiente lectura
                time.sleep(READ_INTERVAL)
                
        except KeyboardInterrupt:
            print("🛑 Deteniendo publicador...")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
        finally:
            if self.client:
                try:
                    self.client.disconnect()
                except:
                    pass
            print("✅ Publicador detenido")


# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == "__main__":
    publisher = DHT22Publisher()
    publisher.run()
