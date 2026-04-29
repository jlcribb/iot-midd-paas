"""
Publicador MQTT para ESP32 con MicroPython y sensor DHT22
==========================================================

Este script está diseñado específicamente para ESP32 con MicroPython.
Publica datos de temperatura y humedad del sensor DHT22 a un broker MQTT.

Requisitos:
    - ESP32 con MicroPython instalado
    - Sensor DHT22
    - Librería dht (incluida en MicroPython)
    - Librería umqtt.simple (incluida en MicroPython)

Instalación:
    1. Instalar MicroPython en ESP32
    2. Subir este archivo a la placa usando Thonny IDE o ampy
    3. Ajustar las variables de configuración
    4. Ejecutar el script

Conexiones DHT22:
    - VCC  -> 3.3V (ESP32)
    - DATA -> GPIO 4 (ajustar si necesario)
    - GND  -> GND
    - Resistencia 4.7kΩ entre DATA y VCC (si no viene en el módulo)
"""

import network
import time
import json
import machine
from machine import Pin
from dht import DHT22
from umqtt.simple import MQTTClient

# ============================================
# CONFIGURACIÓN - AJUSTAR SEGÚN TU ENTORNO
# ============================================

# Configuración WiFi
# WIFI_SSID = "tu_wifi_ssid"           # Nombre de tu red WiFi
# WIFI_PASSWORD = "tu_wifi_password"   # Contraseña de tu WiFi

WIFI_SSID = "fh_b80950"
WIFI_PASSWORD = "wlan47f6af"


# Configuración MQTT (servidor del middleware)
MQTT_BROKER = "192.168.1.100"        # IP del servidor con el middleware
MQTT_PORT = 1883
MQTT_USERNAME = "iot_user"           # Usuario MQTT (según config.yaml)
MQTT_PASSWORD = "iot_password"       # Contraseña MQTT (según config.yaml)
MQTT_CLIENT_ID = "esp32_dht22_001"

# Configuración del sensor DHT22
DHT_PIN = 4                          # GPIO donde está conectado el sensor (ajustar si necesario)
DHT_READ_RETRIES = 3                 # Reintentos de lectura
DHT_READ_DELAY_MS = 2000             # DHT22 requiere ~2s entre lecturas

# Configuración de tópicos MQTT (formato del middleware)
# Formato: iot/{proyecto}/{unidad}/{dispositivo}/{canal}
MQTT_TOPIC_TEMPERATURE = b"iot/proyecto_demo/casa_living/dht22_esp32/temperatura"
MQTT_TOPIC_HUMIDITY = b"iot/proyecto_demo/casa_living/dht22_esp32/humedad"
MQTT_TOPIC_STATUS = b"iot/proyecto_demo/casa_living/dht22_esp32/status"

# Intervalo de lectura (segundos)
READ_INTERVAL = 30                   # Enviar datos cada 30 segundos

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def connect_wifi():
    """Conectar a WiFi verificando existencia de red y clave"""
    wlan = network.WLAN(network.STA_IF)
    try:
        wlan.active(False)
        time.sleep(1)
        wlan.active(True)
        time.sleep(1)
    except Exception:
        pass
    
    # Verificar si la red existe
    scan_attempts = 3
    scan_delay = 3
    ssid_found = False
    while scan_attempts > 0 and not ssid_found:
        try:
            networks = wlan.scan()
        except Exception as e:
            print(f"⚠️  No se pudo escanear redes WiFi: {e}")
            try:
                wlan.active(False)
                time.sleep(1)
                wlan.active(True)
                time.sleep(1)
            except Exception:
                pass
            networks = []
        
        # Mostrar redes detectadas (para depuración)
        try:
            detected_ssids = []
            for net in networks:
                try:
                    detected_ssids.append(net[0].decode("utf-8"))
                except Exception:
                    detected_ssids.append(str(net[0]))
            if detected_ssids:
                print("📡 Redes detectadas:", ", ".join(detected_ssids))
        except Exception:
            pass
        
        for net in networks:
            try:
                ssid = net[0].decode("utf-8")
            except Exception:
                ssid = str(net[0])
            if ssid.strip().lower() == WIFI_SSID.strip().lower():
                ssid_found = True
                break
        
        if not ssid_found:
            scan_attempts -= 1
            if scan_attempts > 0:
                print(f"⚠️  Red no encontrada, reintentando en {scan_delay}s...")
                time.sleep(scan_delay)
    
    if not ssid_found:
        print(f"⚠️  Red no encontrada en el escaneo: {WIFI_SSID}")
        print("   Continuando intento de conexión (puede ser red oculta o nombre diferente)")
    
    if not wlan.isconnected():
        print(f"Conectando a WiFi: {WIFI_SSID}")
        try:
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        except OSError as e:
            print(f"❌ Error interno WiFi al conectar: {e}")
            try:
                wlan.active(False)
                time.sleep(2)
                wlan.active(True)
                time.sleep(2)
                wlan.connect(WIFI_SSID, WIFI_PASSWORD)
            except Exception as e2:
                print(f"❌ Reintento fallido: {e2}")
                return False
        
        # Esperar conexión (máximo 20 segundos)
        timeout = 25
        elapsed = 0
        while not wlan.isconnected() and elapsed < timeout:
            time.sleep(1)
            elapsed += 1
            print(".", end="")
        
        if wlan.isconnected():
            print("\n✅ WiFi conectado")
            config = wlan.ifconfig()
            print(f"   📡 IP: {config[0]}")
            print(f"   📡 Gateway: {config[2]}")
            print(f"   📡 DNS: {config[3]}")
            return True
        else:
            status = wlan.status()
            if status in (-3, -4):
                print("\n❌ Clave WiFi incorrecta o fallo de autenticación")
            else:
                print("\n❌ Error conectando a WiFi")
            return False
    else:
        config = wlan.ifconfig()
        print(f"✅ Ya conectado a WiFi")
        print(f"   📡 IP: {config[0]}")
        return True


def get_timestamp():
    """Obtener timestamp en segundos desde inicio"""
    # MicroPython no tiene datetime completo, usar tiempo relativo
    return int(time.time())


def publish_status(client, status="online"):
    """Publicar estado del dispositivo"""
    try:
        status_payload = json.dumps({
            "status": status,
            "timestamp": get_timestamp(),
            "device": "esp32_dht22",
            "platform": "micropython"
        })
        client.publish(MQTT_TOPIC_STATUS, status_payload.encode('utf-8'), qos=1)
        print(f"📤 Estado publicado: {status}")
    except Exception as e:
        print(f"⚠️  Error publicando estado: {e}")


# ============================================
# CLASE PUBLICADOR MQTT
# ============================================

class DHT22Publisher:
    """Publicador de datos DHT22 a MQTT para ESP32 con MicroPython"""
    
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
                user=MQTT_USERNAME,
                password=MQTT_PASSWORD,
                keepalive=60
            )
            
            print(f"Conectando a MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
            self.client.connect()
            self.connected = True
            print("✅ Conectado al broker MQTT")
            
            # Publicar estado online
            publish_status(self.client, "online")
            
            return True
            
        except Exception as e:
            print(f"❌ Error conectando a MQTT: {e}")
            self.connected = False
            return False
    
    def read_sensor(self):
        """Leer datos del sensor DHT22"""
        retries = DHT_READ_RETRIES if 'DHT_READ_RETRIES' in globals() else 3
        delay_ms = DHT_READ_DELAY_MS if 'DHT_READ_DELAY_MS' in globals() else 2000
        for attempt in range(1, retries + 1):
            try:
                # DHT22 necesita tiempo entre lecturas
                time.sleep_ms(delay_ms)
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
                print("⚠️  Lectura inválida del sensor")
            except Exception as e:
                print(f"❌ Error leyendo sensor DHT22: {e} (intento {attempt}/{DHT_READ_RETRIES})")
                # Reinstanciar el sensor ante errores
                try:
                    self.dht = DHT22(Pin(DHT_PIN))
                except Exception:
                    pass
        return None
    
    def publish_data(self, data):
        """Publicar datos en MQTT"""
        if not self.connected or not self.client:
            print("❌ No hay conexión MQTT activa")
            return False
        
        try:
            timestamp = data.get('timestamp', get_timestamp())
            
            # ============================================
            # PREPARAR PAYLOAD TEMPERATURA (formato del middleware)
            # ============================================
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
                    'platform': 'micropython_esp32'
                }
            }
            
            # ============================================
            # PREPARAR PAYLOAD HUMEDAD (formato del middleware)
            # ============================================
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
                    'platform': 'micropython_esp32'
                }
            }
            
            # ============================================
            # PUBLICAR DATOS
            # ============================================
            try:
                self.client.publish(
                    MQTT_TOPIC_TEMPERATURE,
                    json.dumps(temp_payload).encode('utf-8'),
                    qos=1
                )
                print(f"📤 Temperatura: {data['temperature']}°C")
            except Exception as e:
                print(f"❌ Error publicando temperatura: {e}")
                return False
            
            try:
                self.client.publish(
                    MQTT_TOPIC_HUMIDITY,
                    json.dumps(hum_payload).encode('utf-8'),
                    qos=1
                )
                print(f"📤 Humedad: {data['humidity']}%")
            except Exception as e:
                print(f"❌ Error publicando humedad: {e}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error publicando datos: {e}")
            return False
    
    def run(self):
        """Ejecutar el loop principal"""
        print("=" * 50)
        print("🚀 Publicador DHT22 MQTT - ESP32 MicroPython")
        print("=" * 50)
        print(f"📌 Sensor: DHT22 en GPIO pin {DHT_PIN}")
        print(f"📌 Intervalo: {READ_INTERVAL} segundos")
        print(f"📌 Broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
        print("=" * 50)
        
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
                    try:
                        if not self.connected:
                            print("⚠️  Reconectando a MQTT...")
                            if self.connect_mqtt():
                                consecutive_errors = 0
                            else:
                                consecutive_errors += 1
                                time.sleep(5)
                                continue
                        
                        # Publicar datos
                        if self.publish_data(data):
                            consecutive_errors = 0
                            print(f"✅ Datos publicados: Temp={data['temperature']}°C, Hum={data['humidity']}%")
                        else:
                            consecutive_errors += 1
                            print(f"⚠️  Error publicando (intento {consecutive_errors}/{max_errors})")
                    except Exception as e:
                        print(f"❌ Error en conexión MQTT: {e}")
                        consecutive_errors += 1
                else:
                    consecutive_errors += 1
                    print(f"⚠️  Error leyendo sensor (intento {consecutive_errors}/{max_errors})")
                
                # Si hay muchos errores, intentar reconectar
                if consecutive_errors >= max_errors:
                    print("❌ Demasiados errores. Reconectando...")
                    try:
                        if self.client:
                            self.client.disconnect()
                    except:
                        pass
                    self.connected = False
                    time.sleep(5)
                    if self.connect_mqtt():
                        consecutive_errors = 0
                    else:
                        time.sleep(10)
                
                # Esperar antes de la siguiente lectura
                time.sleep(READ_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo publicador...")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            import sys
            sys.print_exception(e)
        finally:
            # Publicar estado offline
            try:
                if self.client and self.connected:
                    publish_status(self.client, "offline")
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
