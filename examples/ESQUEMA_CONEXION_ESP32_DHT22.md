# Esquema de Conexión ESP32 + DHT22 + MQTT

## 📋 Resumen

Este documento describe la conexión física del sensor DHT22 al ESP32 y la configuración del código MicroPython para publicar datos vía MQTT al middleware.

## 🔌 Esquema de Conexión Física

### Componentes necesarios

1. **ESP32** (cualquier variante: ESP32-DevKitC, ESP32-WROOM-32, etc.)
2. **Sensor DHT22** (también conocido como AM2302)
3. **Resistencia pull-up de 4.7kΩ** (opcional si el módulo DHT22 ya la trae)
4. **Cables jumper** (macho-macho)
5. **Fuente de alimentación** (USB para ESP32 o 5V externa)

### Conexiones DHT22 → ESP32

```
┌─────────────────┐         ┌──────────────────┐
│     DHT22       │         │      ESP32       │
├─────────────────┤         ├──────────────────┤
│ VCC  (Pin 1)    │────────→│ 3.3V             │
│ DATA (Pin 2)    │────────→│ GPIO 4           │
│      (4.7kΩ)    │──┬──┐   │                  │
│                 │  │  └──→│ 3.3V             │
│ NC   (Pin 3)    │  │      │                  │
│                 │  │      │                  │
│ GND  (Pin 4)    │────────→│ GND              │
└─────────────────┘         └──────────────────┘
     (Vista frontal)           (Vista superior)
```

### Detalle de conexiones

| Pin DHT22 | Pin ESP32 | Descripción |
|-----------|-----------|-------------|
| **VCC** (Pin 1) | **3.3V** | Alimentación positiva (3.3V para ESP32) |
| **DATA** (Pin 2) | **GPIO 4** | Señal de datos (ajustable en código) |
| **NC** (Pin 3) | *No conectado* | No usado |
| **GND** (Pin 4) | **GND** | Tierra común |

### Resistencia Pull-up

- **Valor:** 4.7kΩ (4700 ohmios)
- **Ubicación:** Entre el pin DATA del DHT22 y 3.3V
- **Nota:** Si tu módulo DHT22 ya trae la resistencia (módulos comunes la incluyen), NO necesitas agregarla externamente.

### Vista esquemática simplificada

```
                    ┌─────────────┐
                    │   DHT22     │
                    │   Sensor    │
                    └─────────────┘
                         │
                    ┌────┴────┐
                    │         │
                   DATA      VCC
                    │         │
          ┌─────────┘         └────────┐
          │                            │
    ┌─────┴─────┐                ┌─────┴─────┐
    │  GPIO 4   │                │   3.3V    │
    └───────────┘                └───────────┘
          │                            │
          │                            │
    ┌─────┴───────────────────────────┴─────┐
    │             ESP32                     │
    │  ┌───────────────────────────────┐   │
    │  │  GPIO 4  ←─┐                  │   │
    │  │            │                  │   │
    │  │  3.3V  ←──┼──┤ 4.7kΩ         │   │
    │  │            │                  │   │
    │  │  GND  ←────┘                  │   │
    │  └───────────────────────────────┘   │
    └───────────────────────────────────────┘
```

## 🔧 Configuración del Código

### Configuración WiFi

Abre el archivo `micropython_esp32_dht22.py` y ajusta estas líneas:

```python
WIFI_SSID = "tu_wifi_ssid"           # Nombre de tu red WiFi
WIFI_PASSWORD = "tu_wifi_password"   # Contraseña de tu WiFi
```

### Configuración MQTT

Ajusta la IP del servidor del middleware:

```python
MQTT_BROKER = "192.168.1.100"        # IP del servidor con el middleware
MQTT_PORT = 1883
MQTT_USERNAME = "iot_user"           # Usuario MQTT (según config.yaml)
MQTT_PASSWORD = "iot_password"       # Contraseña MQTT (según config.yaml)
```

**Para encontrar la IP del servidor:**
```bash
# En el servidor del middleware
hostname -I
# o
ip addr show
```

### Configuración del Pin del Sensor

Si conectas el DHT22 a un pin diferente a GPIO 4, ajusta:

```python
DHT_PIN = 4  # Cambiar si usas otro pin (ej: 2, 5, 18, 19, 21, 22, 23)
```

**Pines recomendados en ESP32:**
- GPIO 4 (por defecto)
- GPIO 2
- GPIO 5
- GPIO 18
- GPIO 19
- GPIO 21
- GPIO 22
- GPIO 23

**Pines NO recomendados:**
- GPIO 0 (BOOT - puede causar problemas en arranque)
- GPIO 34, 35, 36, 39 (solo entrada, sin pull-up interno)

### Configuración de Tópicos MQTT

Los tópicos ya están configurados según el formato del middleware:

```python
MQTT_TOPIC_TEMPERATURE = b"iot/proyecto_demo/casa_living/dht22_esp32/temperatura"
MQTT_TOPIC_HUMIDITY = b"iot/proyecto_demo/casa_living/dht22_esp32/humedad"
MQTT_TOPIC_STATUS = b"iot/proyecto_demo/casa_living/dht22_esp32/status"
```

**Formato del middleware:** `iot/{proyecto}/{unidad}/{dispositivo}/{canal}`

### Intervalo de Envío

```python
READ_INTERVAL = 30  # Enviar datos cada 30 segundos (ajustable)
```

**Recomendaciones:**
- Mínimo: 10 segundos (el DHT22 necesita tiempo entre lecturas)
- Recomendado: 30 segundos
- Máximo: según tus necesidades

## 📦 Instalación

### 1. Instalar MicroPython en ESP32

1. **Descargar firmware MicroPython:**
   - Ir a https://micropython.org/download/esp32/
   - Descargar el firmware más reciente (ej: `esp32-xxxxxx.bin`)

2. **Instalar esptool:**
   ```bash
   pip install esptool
   ```

3. **Subir firmware:**
   ```bash
   # Borrar firmware anterior
   esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
   
   # Subir nuevo firmware
   esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-xxxxxx.bin
   ```
   
   **Nota:** Ajustar el puerto (`/dev/ttyUSB0`, `/dev/ttyACM0`, `COM3`, etc.) según tu sistema.

### 2. Subir código a ESP32

**Opción A: Usando Thonny IDE (Recomendado para principiantes)**

1. **Instalar Thonny:**
   - Windows: https://thonny.org/
   - macOS: `brew install --cask thonny`
   - Linux: `sudo apt install thonny`

2. **Conectar ESP32:**
   - Conectar ESP32 vía USB
   - Abrir Thonny
   - Seleccionar el intérprete: Tools → Options → Interpreter → MicroPython (ESP32)
   - Seleccionar el puerto correcto

3. **Subir código:**
   - Abrir `micropython_esp32_dht22.py`
   - Guardar como: File → Save As → "main.py" (guardará en ESP32)
   - O ejecutar directamente: Run → Run current script

**Opción B: Usando ampy**

1. **Instalar ampy:**
   ```bash
   pip install adafruit-ampy
   ```

2. **Subir código:**
   ```bash
   ampy --port /dev/ttyUSB0 put micropython_esp32_dht22.py main.py
   ```

3. **Resetear ESP32:**
   ```bash
   ampy --port /dev/ttyUSB0 reset
   ```

### 3. Verificar funcionamiento

Abre el monitor serie (Thonny o `screen`/`minicom`):

```bash
# Ver logs
screen /dev/ttyUSB0 115200
```

Deberías ver:
```
==================================================
🚀 Publicador DHT22 MQTT - ESP32 MicroPython
==================================================
📌 Sensor: DHT22 en GPIO pin 4
📌 Intervalo: 30 segundos
📌 Broker MQTT: 192.168.1.100:1883
==================================================
Conectando a WiFi: tu_wifi_ssid
✅ WiFi conectado
   📡 IP: 192.168.1.50
Conectando a MQTT broker: 192.168.1.100:1883
✅ Conectado al broker MQTT
📤 Estado publicado: online
📤 Temperatura: 24.50°C
📤 Humedad: 65.20%
✅ Datos publicados: Temp=24.50°C, Hum=65.20%
```

## 🔍 Verificación en el Middleware

### 1. Verificar logs del ingestor

En el servidor del middleware:

```bash
docker logs -f iotmw-ingestor
```

Deberías ver mensajes como:
```
✅ Mensaje recibido en iot/proyecto_demo/casa_living/dht22_esp32/temperatura
📊 Datos procesados y almacenados
```

### 2. Consultar datos mediante API

```bash
# Consultar temperatura
curl "http://localhost:8000/api/data/time-series?canal_id=temperatura&limit=10"

# Consultar humedad
curl "http://localhost:8000/api/data/time-series?canal_id=humedad&limit=10"
```

### 3. Verificar con mosquitto_sub (opcional)

```bash
# Suscribirse a todos los tópicos del dispositivo
mosquitto_sub -h 192.168.1.100 -p 1883 -u iot_user -P iot_password -t "iot/proyecto_demo/casa_living/dht22_esp32/#" -v
```

## 🐛 Solución de Problemas

### Error: "Error conectando a WiFi"

**Causas posibles:**
- SSID o contraseña incorrectos
- WiFi fuera de alcance
- Router WiFi apagado

**Solución:**
1. Verificar SSID y contraseña
2. Verificar que el ESP32 esté cerca del router
3. Probar con otro dispositivo WiFi

### Error: "Error conectando a MQTT"

**Causas posibles:**
- IP del broker incorrecta
- Puerto incorrecto
- Credenciales incorrectas
- Servidor MQTT no disponible

**Solución:**
1. Verificar IP del servidor: `ping 192.168.1.100`
2. Verificar que el servidor MQTT esté corriendo:
   ```bash
   docker ps | grep mosquitto
   ```
3. Verificar credenciales en `config.yaml`
4. Probar conexión desde otro dispositivo:
   ```bash
   mosquitto_pub -h 192.168.1.100 -p 1883 -u iot_user -P iot_password -t "test" -m "test"
   ```

### Error: "Error leyendo sensor DHT22"

**Causas posibles:**
- Pin incorrecto
- Conexiones mal hechas
- Sensor defectuoso
- Falta resistencia pull-up

**Solución:**
1. Verificar que el pin sea correcto (`DHT_PIN = 4`)
2. Verificar todas las conexiones:
   - VCC → 3.3V
   - DATA → GPIO 4
   - GND → GND
   - Resistencia 4.7kΩ entre DATA y 3.3V
3. Probar con otro sensor DHT22
4. Verificar que el sensor no esté defectuoso

### Error: "No se pudieron leer los datos del sensor"

**Causas posibles:**
- Lectura muy rápida (DHT22 necesita tiempo entre lecturas)
- Sensor defectuoso
- Interferencias

**Solución:**
1. Aumentar `READ_INTERVAL` a 30 segundos o más
2. Verificar conexiones
3. Probar con otro sensor

### Los datos no aparecen en el middleware

**Verificar:**
1. Los tópicos coinciden exactamente
2. El formato JSON es válido
3. El middleware está escuchando el tópico correcto
4. Los logs del ingestor no muestran errores
5. El servidor MQTT está funcionando correctamente

## 📝 Resumen de Configuración

| Parámetro | Valor | Ubicación |
|-----------|-------|-----------|
| **Pin DHT22** | GPIO 4 | `DHT_PIN = 4` |
| **Alimentación** | 3.3V | Conexión física |
| **Resistencia Pull-up** | 4.7kΩ | Entre DATA y 3.3V |
| **WiFi SSID** | tu_wifi_ssid | `WIFI_SSID` |
| **WiFi Password** | tu_wifi_password | `WIFI_PASSWORD` |
| **MQTT Broker** | 192.168.1.100:1883 | `MQTT_BROKER`, `MQTT_PORT` |
| **MQTT User** | iot_user | `MQTT_USERNAME` |
| **MQTT Password** | iot_password | `MQTT_PASSWORD` |
| **Tópico Temp** | iot/proyecto_demo/casa_living/dht22_esp32/temperatura | `MQTT_TOPIC_TEMPERATURE` |
| **Tópico Hum** | iot/proyecto_demo/casa_living/dht22_esp32/humedad | `MQTT_TOPIC_HUMIDITY` |
| **Intervalo** | 30 segundos | `READ_INTERVAL` |

## ✅ Checklist antes de probar

- [ ] MicroPython instalado en ESP32
- [ ] DHT22 conectado correctamente (VCC, DATA, GND)
- [ ] Resistencia 4.7kΩ entre DATA y 3.3V (si el módulo no la trae)
- [ ] Código subido a ESP32 (`main.py`)
- [ ] WiFi SSID y contraseña configurados
- [ ] IP del servidor MQTT correcta
- [ ] Credenciales MQTT correctas
- [ ] Servidor MQTT funcionando
- [ ] Monitor serie abierto (115200 baudios)

¡Listo para probar! 🚀
