# Comparación: Python vs MicroPython vs Arduino para DHT22

Esta guía explica las diferencias entre las tres plataformas y cuándo usar cada una.

## 📊 Comparación Rápida

| Característica | Python (CPython) | MicroPython | Arduino (.ino) |
|---------------|------------------|-------------|----------------|
| **Placas compatibles** | Raspberry Pi, Orange Pi, etc. | ESP32, ESP8266, Pico | Arduino, ESP32, ESP8266 |
| **Sistema operativo** | Linux completo | Sin SO (bare metal) | Sin SO (bare metal) |
| **Memoria RAM** | 512MB+ | 100KB - 500KB | 2KB - 520KB |
| **Almacenamiento** | SD card/SSD | Flash interna | Flash interna |
| **Conexión WiFi** | Nativa (Linux) | Nativa (ESP) | Nativa (ESP) o shield |
| **Facilidad de uso** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Rendimiento** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Consumo energía** | Alto | Bajo | Muy bajo |
| **Costo** | $35-100 | $5-15 | $3-10 |

## 🎯 ¿Cuál elegir?

### Usa **Python (CPython)** si:
- ✅ Tienes una **Raspberry Pi** o similar (SBC completa)
- ✅ Necesitas **múltiples sensores** o procesamiento complejo
- ✅ Quieres **fácil desarrollo** y debugging
- ✅ Necesitas **almacenamiento local** o base de datos
- ✅ El **consumo de energía** no es crítico
- ✅ Tienes **presupuesto** para una SBC ($35+)

**Archivo:** `sbc_dht22_publisher.py`

### Usa **MicroPython** si:
- ✅ Tienes una **ESP32, ESP8266, o Raspberry Pi Pico**
- ✅ Necesitas **bajo consumo** de energía
- ✅ Quieres **código Python** pero en hardware más económico
- ✅ El **presupuesto** es limitado ($5-15)
- ✅ Necesitas **conectividad WiFi** integrada
- ✅ No necesitas **procesamiento complejo**

**Archivo:** `micropyton_dht22_publisher.py`

### Usa **Arduino (.ino)** si:
- ✅ Tienes una **placa Arduino** tradicional
- ✅ Prefieres **C++** sobre Python
- ✅ Necesitas **máximo control** del hardware
- ✅ Quieres **máximo rendimiento** y bajo consumo
- ✅ Tienes **experiencia con Arduino**
- ✅ Necesitas **compatibilidad** con shields Arduino

**Archivo:** `arduino_dht22_publisher.ino`

## 📝 Diferencias Técnicas

### 1. Instalación y Setup

#### Python (CPython)
```bash
# En Raspberry Pi
sudo apt-get install python3-pip
pip3 install paho-mqtt Adafruit_Python_DHT
python3 sbc_dht22_publisher.py
```

#### MicroPython
```python
# Subir archivo a la placa usando Thonny o ampy
# Configurar WiFi en el código
# Ejecutar directamente desde la placa
```

#### Arduino
```cpp
// Instalar librerías desde Arduino Library Manager:
// - DHT sensor library
// - PubSubClient
// - ArduinoJson
// Compilar y subir con Arduino IDE
```

### 2. Gestión de Memoria

- **Python**: Gestión automática, sin preocupaciones
- **MicroPython**: Gestión automática pero limitada (puede causar problemas con JSON grandes)
- **Arduino**: Gestión manual, control total pero más complejo

### 3. Manejo de Errores

- **Python**: Try/except completo, logging avanzado
- **MicroPython**: Try/except básico, print para debugging
- **Arduino**: Verificación manual, Serial.print para debugging

### 4. Timestamps

- **Python**: `datetime.now(timezone.utc).isoformat()` - preciso
- **MicroPython**: Requiere NTP o RTC externo para precisión
- **Arduino**: Requiere NTP o RTC externo, o usar epoch time

## 🔧 Requisitos de Hardware

### Python (CPython)
```
✅ Raspberry Pi 3/4 (recomendado)
✅ Orange Pi
✅ Cualquier SBC con Linux
✅ Alimentación: 5V 2.5A mínimo
✅ SD card: 8GB+ recomendado
```

### MicroPython
```
✅ ESP32 (recomendado - WiFi integrado)
✅ ESP8266 (más económico)
✅ Raspberry Pi Pico W (con WiFi)
✅ Alimentación: 3.3V o 5V USB
✅ Flash: 4MB+ recomendado
```

### Arduino
```
✅ ESP32 (recomendado - WiFi integrado)
✅ ESP8266 (más económico)
✅ Arduino Uno/Nano + Ethernet Shield
✅ Arduino Mega + WiFi Shield
✅ Alimentación: 5V o 3.3V según placa
```

## 📦 Librerías Necesarias

### Python (CPython)
```bash
pip3 install paho-mqtt Adafruit_Python_DHT
```

### MicroPython
```python
# Incluidas en MicroPython:
# - dht (para DHT22)
# - umqtt.simple (para MQTT)
# - network (para WiFi)
```

### Arduino
```
Librerías a instalar desde Arduino Library Manager:
- DHT sensor library (por Adafruit)
- PubSubClient (por Nick O'Leary)
- ArduinoJson (por Benoit Blanchon)
```

## 💡 Ejemplos de Uso

### Escenario 1: Casa Inteligente
**Recomendación:** Python en Raspberry Pi
- Múltiples sensores (temperatura, humedad, movimiento)
- Procesamiento local
- Base de datos local
- Interfaz web

### Escenario 2: Sensor Remoto con Batería
**Recomendación:** MicroPython en ESP32
- Un solo sensor
- Bajo consumo
- WiFi integrado
- Bajo costo

### Escenario 3: Proyecto Educativo
**Recomendación:** Arduino (.ino)
- Aprendizaje de programación embebida
- Control total del hardware
- Gran comunidad y recursos

## 🚀 Rendimiento

### Tiempo de Lectura DHT22
- **Python**: ~2-3 segundos (incluye overhead del SO)
- **MicroPython**: ~1-2 segundos
- **Arduino**: ~0.5-1 segundo (más rápido)

### Consumo de Energía (idle)
- **Python (Raspberry Pi)**: ~1-2W
- **MicroPython (ESP32)**: ~10-50mW
- **Arduino (ESP32)**: ~10-50mW

### Latencia MQTT
- **Python**: ~50-100ms
- **MicroPython**: ~100-200ms
- **Arduino**: ~50-150ms

## 🔍 Debugging

### Python
```python
# Logging completo
import logging
logging.basicConfig(level=logging.DEBUG)
logger.debug("Mensaje de debug")
```

### MicroPython
```python
# Print statements
print("Debug: valor =", valor)
```

### Arduino
```cpp
// Serial monitor
Serial.begin(115200);
Serial.println("Debug: valor = " + String(valor));
```

## 📚 Recursos Adicionales

### Python
- [Documentación Python](https://docs.python.org/3/)
- [paho-mqtt docs](https://www.eclipse.org/paho/clients/python/)
- [Raspberry Pi GPIO](https://www.raspberrypi.org/documentation/usage/gpio/)

### MicroPython
- [MicroPython docs](https://docs.micropython.org/)
- [ESP32 MicroPython](https://docs.micropython.org/en/latest/esp32/quickref.html)
- [Thonny IDE](https://thonny.org/)

### Arduino
- [Arduino Reference](https://www.arduino.cc/reference/en/)
- [ESP32 Arduino](https://docs.espressif.com/projects/arduino-esp32/en/latest/)
- [Arduino IDE](https://www.arduino.cc/en/software)

## ✅ Resumen

| Si tienes... | Usa... | Archivo |
|--------------|--------|---------|
| Raspberry Pi | Python | `sbc_dht22_publisher.py` |
| ESP32/ESP8266 | MicroPython o Arduino | `micropyton_dht22_publisher.py` o `arduino_dht22_publisher.ino` |
| Arduino Uno | Arduino | `arduino_dht22_publisher.ino` |
| Presupuesto bajo | MicroPython/Arduino | `micropyton_dht22_publisher.py` |
| Múltiples sensores | Python | `sbc_dht22_publisher.py` |
| Bajo consumo | MicroPython/Arduino | `micropyton_dht22_publisher.py` |

**Todos los códigos publican en el mismo formato MQTT y son compatibles con el middleware.**
