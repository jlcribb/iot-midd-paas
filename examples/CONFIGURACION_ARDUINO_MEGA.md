# Configuración Arduino Mega 2560 + DHT22 + MQTT

## 📋 Análisis de tu código original

### ✅ Lo que está bien configurado:

1. **MQTT Broker:**
   ```cpp
   const char* mqtt_server = "192.168.1.100";  // ✅ Correcto
   const int mqtt_port = 1883;                  // ✅ Correcto
   const char* mqtt_user = "iot_user";          // ✅ Correcto (según config.yaml)
   const char* mqtt_password = "iot_password";   // ✅ Correcto (según config.yaml)
   ```

2. **Tópicos MQTT:**
   ```cpp
   const char* topic_temp = "iot/proyecto_demo/casa_living/dht22_arduino/temperatura";  // ✅ Correcto
   const char* topic_hum = "iot/proyecto_demo/casa_living/dht22_arduino/humedad";        // ✅ Correcto
   ```
   Estos tópicos coinciden con el formato que espera el middleware: `iot/{proyecto}/{unidad}/{dispositivo}/{canal}`

3. **Sensor DHT22:**
   ```cpp
   #define DHTPIN 4           // ✅ Pin correcto
   #define DHTTYPE DHT22      // ✅ Tipo correcto
   ```

### ❌ Problemas detectados:

1. **Arduino Mega NO tiene WiFi nativo:**
   - Tu código usa `#include <WiFi.h>` que solo funciona en ESP32/ESP8266
   - Arduino Mega necesita **Ethernet Shield** o **WiFi Shield**

2. **Variables faltantes:**
   - El código usa `ssid` y `password` pero no están definidas

3. **Formato JSON incompleto:**
   - Tu JSON no incluye todos los campos que espera el middleware:
     - Falta `"tipo"` (temperatura/humedad)
     - Falta `"metadata"` con información del sensor
     - El formato no coincide exactamente

## 🔧 Solución: Código corregido

He creado `arduino_mega_dht22_publisher.ino` que corrige todos estos problemas.

### Configuración actual en el código corregido:

#### 1. MQTT (igual que tu código)
```cpp
const char* mqtt_server = "192.168.1.100";  // IP del servidor del middleware
const int mqtt_port = 1883;
const char* mqtt_user = "iot_user";
const char* mqtt_password = "iot_password";
```

#### 2. Tópicos MQTT (igual que tu código)
```cpp
const char* topic_temp = "iot/proyecto_demo/casa_living/dht22_arduino/temperatura";
const char* topic_hum = "iot/proyecto_demo/casa_living/dht22_arduino/humedad";
```

#### 3. Sensor DHT22 (igual que tu código)
```cpp
#define DHTPIN 4
#define DHTTYPE DHT22
```

#### 4. Intervalo de envío
```cpp
const long interval = 30000;  // 30 segundos (tu código tenía 10 segundos)
```

## 🔌 Opciones de conexión para Arduino Mega

### Opción 1: Ethernet Shield (Recomendado)

**Ventajas:**
- ✅ Más estable
- ✅ No requiere configuración WiFi
- ✅ Menor consumo
- ✅ Mejor para aplicaciones fijas

**Configuración:**
```cpp
// En el código corregido, ajusta estas líneas:
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(192, 168, 1, 50);  // IP estática de tu Arduino
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);
```

**Hardware necesario:**
- Arduino Mega 2560
- Ethernet Shield (compatible con Arduino)
- Cable Ethernet

### Opción 2: WiFi Shield

**Ventajas:**
- ✅ Sin cables
- ✅ Más flexible en ubicación

**Configuración:**
```cpp
// Descomentar en el código:
const char* WIFI_SSID = "tu_wifi_ssid";
const char* WIFI_PASSWORD = "tu_wifi_password";
```

**Hardware necesario:**
- Arduino Mega 2560
- Arduino WiFi Shield (oficial o compatible)

### Opción 3: Módulo ESP8266 como cliente WiFi

**Ventajas:**
- ✅ Más económico
- ✅ WiFi integrado

**Desventajas:**
- ⚠️ Requiere comunicación serial entre Arduino y ESP8266
- ⚠️ Más complejo de configurar

## 📦 Instalación de librerías

En Arduino IDE, instala estas librerías desde **Library Manager**:

1. **DHT sensor library** (por Adafruit)
   - Tools → Manage Libraries → Buscar "DHT sensor library"
   - Instalar versión por Adafruit

2. **PubSubClient** (por Nick O'Leary)
   - Buscar "PubSubClient"
   - Instalar

3. **ArduinoJson** (por Benoit Blanchon)
   - Buscar "ArduinoJson"
   - Instalar versión 6.x (importante: NO versión 7.x)

4. **Ethernet** (incluida en Arduino IDE)
   - No requiere instalación

## 🔧 Configuración paso a paso

### 1. Configurar IP del Arduino (si usas Ethernet)

En el código, ajusta estas líneas según tu red:

```cpp
IPAddress ip(192, 168, 1, 50);        // IP del Arduino (debe ser única en tu red)
IPAddress gateway(192, 168, 1, 1);    // Gateway de tu router
IPAddress subnet(255, 255, 255, 0);   // Máscara de subred
```

**O usa DHCP (recomendado):**
El código ya está configurado para intentar DHCP primero. Si tu router tiene DHCP habilitado, el Arduino obtendrá una IP automáticamente.

### 2. Verificar IP del servidor MQTT

Asegúrate de que `mqtt_server` apunte a la IP correcta de tu servidor:

```cpp
const char* mqtt_server = "192.168.1.100";  // Cambiar por la IP real
```

**Para encontrar la IP del servidor:**
```bash
# En el servidor del middleware
hostname -I
# o
ip addr show
```

### 3. Verificar credenciales MQTT

Las credenciales deben coincidir con `config.yaml`:

```yaml
# En config.yaml del middleware
mqtt:
  broker:
    username: "iot_user"      # Debe coincidir
    password: "iot_password"  # Debe coincidir
```

### 4. Verificar tópicos

Los tópicos están correctos y coinciden con el formato del middleware:
- ✅ `iot/proyecto_demo/casa_living/dht22_arduino/temperatura`
- ✅ `iot/proyecto_demo/casa_living/dht22_arduino/humedad`

## 📊 Formato JSON enviado

El código corregido envía este formato (compatible con el middleware):

### Temperatura:
```json
{
  "valor": 24.50,
  "unidad": "celsius",
  "timestamp": 1234567890,
  "tipo": "temperatura",
  "sensor_id": "arduino_mega_01",
  "metadata": {
    "sensor_type": "DHT22",
    "location": "living_room",
    "pin": 4,
    "platform": "arduino_mega"
  }
}
```

### Humedad:
```json
{
  "valor": 65.20,
  "unidad": "porcentaje",
  "timestamp": 1234567890,
  "tipo": "humedad",
  "sensor_id": "arduino_mega_01",
  "metadata": {
    "sensor_type": "DHT22",
    "location": "living_room",
    "pin": 4,
    "platform": "arduino_mega"
  }
}
```

## ✅ Verificación de funcionamiento

### 1. Verificar conexión Ethernet/WiFi

Abre el **Serial Monitor** (115200 baudios) y deberías ver:
```
✅ Ethernet conectado
📡 Dirección IP: 192.168.1.50
```

### 2. Verificar conexión MQTT

Deberías ver:
```
🔄 Intentando conexión MQTT...
✅ MQTT conectado
```

### 3. Verificar recepción de datos

En el servidor del middleware, verifica los logs:
```bash
docker logs -f iotmw-ingestor
```

Deberías ver mensajes como:
```
✅ Mensaje recibido en iot/proyecto_demo/casa_living/dht22_arduino/temperatura
📊 Datos procesados y almacenados
```

### 4. Consultar datos mediante API

```bash
# Consultar temperatura
curl "http://localhost:8000/api/data/time-series?canal_id=temperatura&limit=10"

# Consultar humedad
curl "http://localhost:8000/api/data/time-series?canal_id=humedad&limit=10"
```

## 🐛 Solución de problemas

### Error: "Ethernet linkStatus() == LinkOFF"

**Causa:** Cable Ethernet desconectado o router apagado

**Solución:**
- Verificar cable Ethernet
- Verificar que el router esté encendido
- Verificar que el Ethernet Shield esté bien conectado

### Error: "MQTT connection failed"

**Causa:** No puede alcanzar el broker MQTT

**Solución:**
1. Verificar que `mqtt_server` tenga la IP correcta
2. Verificar que el servidor del middleware esté corriendo:
   ```bash
   docker ps | grep mosquitto
   ```
3. Verificar que no haya firewall bloqueando el puerto 1883
4. Probar conectividad desde otro dispositivo:
   ```bash
   mosquitto_pub -h 192.168.1.100 -p 1883 -t "test" -m "test"
   ```

### Error: "Error leyendo sensor DHT22"

**Causa:** Problema con el sensor o conexiones

**Solución:**
1. Verificar que el pin esté correcto (DHTPIN = 4)
2. Verificar conexiones del sensor:
   - VCC → 5V
   - DATA → Pin 4
   - GND → GND
   - Resistencia 4.7kΩ entre DATA y VCC
3. Probar con otro sensor DHT22
4. Verificar que el sensor no esté defectuoso

### Datos no aparecen en el middleware

**Verificar:**
1. Los tópicos coinciden exactamente
2. El formato JSON es válido (usar JSONLint para validar)
3. El middleware está escuchando el tópico correcto
4. Los logs del ingestor no muestran errores

## 📝 Resumen de configuración

| Parámetro | Valor | Ubicación |
|-----------|-------|-----------|
| **MQTT Broker** | 192.168.1.100:1883 | `mqtt_server`, `mqtt_port` |
| **MQTT User** | iot_user | `mqtt_user` |
| **MQTT Password** | iot_password | `mqtt_password` |
| **Tópico Temp** | iot/proyecto_demo/casa_living/dht22_arduino/temperatura | `topic_temp` |
| **Tópico Hum** | iot/proyecto_demo/casa_living/dht22_arduino/humedad | `topic_hum` |
| **DHT22 Pin** | 4 | `DHTPIN` |
| **Intervalo** | 30 segundos | `interval` |

## ✅ Checklist antes de cargar

- [ ] Librerías instaladas (DHT, PubSubClient, ArduinoJson)
- [ ] IP del servidor MQTT correcta
- [ ] Credenciales MQTT correctas
- [ ] Ethernet Shield conectado (o WiFi configurado)
- [ ] Sensor DHT22 conectado en pin 4
- [ ] Código compilado sin errores
- [ ] Serial Monitor abierto (115200 baudios)

¡Listo para probar! 🚀
