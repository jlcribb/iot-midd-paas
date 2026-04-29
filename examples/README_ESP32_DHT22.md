# ESP32 + DHT22 + MQTT - Guía Rápida

## 📋 Resumen

Código MicroPython para ESP32 que lee datos de temperatura y humedad del sensor DHT22 y los publica vía MQTT al middleware.

## 🔌 Conexiones Físicas

### Esquema Simplificado

```
DHT22                    ESP32
─────────────────────────────────────
VCC  (Pin 1)  ────────→  3.3V
DATA (Pin 2)  ────────→  GPIO 4 (26)
      (4.7kΩ) ──┬─────→  3.3V
                │
GND  (Pin 4)  ────────→  GND
```

### Conexiones Detalladas

| Pin DHT22 | Conecta a ESP32 | Notas |
|-----------|-----------------|-------|
| **VCC** | **3.3V** | Alimentación positiva |
| **DATA** | **GPIO 4** | Señal de datos |
| **4.7kΩ** | Entre DATA y 3.3V | Resistencia pull-up (si el módulo no la trae) |
| **GND** | **GND** | Tierra común |

## ⚙️ Configuración Rápida

### 1. Ajustar configuración en el código

Abrir `micropython_esp32_dht22.py` y ajustar:

```python
# WiFi
WIFI_SSID = "tu_wifi_ssid"
WIFI_PASSWORD = "tu_wifi_password"

W
# MQTT (servidor del middleware)
MQTT_BROKER = "192.168.1.100"  # IP del servidor
MQTT_USERNAME = "iot_user"
MQTT_PASSWORD = "iot_password"

# Pin del sensor (si cambias el pin)
DHT_PIN = 4  # GPIO 4
```

### 2. Subir código a ESP32

**Con Thonny IDE (Recomendado):**
1. Abrir Thonny
2. Seleccionar intérprete: Tools → Options → Interpreter → MicroPython (ESP32)
3. Abrir `micropython_esp32_dht22.py`
4. Guardar como: File → Save As → "main.py" (guardará en ESP32)
5. Ejecutar: Run → Run current script

**Con ampy:**
```bash
ampy --port /dev/ttyUSB0 put micropython_esp32_dht22.py main.py
ampy --port /dev/ttyUSB0 reset
```

### 3. Verificar funcionamiento

Abrir monitor serie (115200 baudios):

**Con Thonny:**
- Ver logs en la consola inferior

**Con screen:**
```bash
screen /dev/ttyUSB0 115200
```

Deberías ver:
```
✅ WiFi conectado
✅ Conectado al broker MQTT
📤 Temperatura: 24.50°C
📤 Humedad: 65.20%
```

## 🔍 Verificar en el Middleware

### 1. Ver logs del ingestor

```bash
docker logs -f iotmw-ingestor
```

### 2. Consultar datos vía API

```bash
# Temperatura
curl "http://localhost:8000/api/data/time-series?canal_id=temperatura&limit=10"

# Humedad
curl "http://localhost:8000/api/data/time-series?canal_id=humedad&limit=10"
```

### 3. Suscribirse a tópicos MQTT

```bash
mosquitto_sub -h 192.168.1.100 -p 1883 -u iot_user -P iot_password \
  -t "iot/proyecto_demo/casa_living/dht22_esp32/#" -v
```

## 🐛 Problemas Comunes

### No se conecta a WiFi
- Verificar SSID y contraseña
- Verificar que el router esté encendido
- Verificar señal WiFi

### No se conecta a MQTT
- Verificar IP del servidor (`ping 192.168.1.100`)
- Verificar que el servidor MQTT esté corriendo
- Verificar credenciales

### Error leyendo sensor
- Verificar conexiones (VCC, DATA, GND)
- Verificar que el pin sea correcto
- Verificar resistencia pull-up
- Probar con otro sensor

## 📝 Tópicos MQTT

El código publica en estos tópicos:

- **Temperatura:** `iot/proyecto_demo/casa_living/dht22_esp32/temperatura`
- **Humedad:** `iot/proyecto_demo/casa_living/dht22_esp32/humedad`
- **Estado:** `iot/proyecto_demo/casa_living/dht22_esp32/status`

**Formato del middleware:** `iot/{proyecto}/{unidad}/{dispositivo}/{canal}`

## 📚 Documentación Completa

Para más detalles, ver:
- `ESQUEMA_CONEXION_ESP32_DHT22.md` - Esquema completo de conexión
- `micropython_esp32_dht22.py` - Código fuente comentado

## ✅ Checklist

- [ ] MicroPython instalado en ESP32
- [ ] DHT22 conectado (VCC, DATA, GND)
- [ ] Resistencia 4.7kΩ (si necesario)
- [ ] Código configurado (WiFi, MQTT)
- [ ] Código subido a ESP32
- [ ] Monitor serie abierto
- [ ] Servidor MQTT funcionando

¡Listo! 🚀
