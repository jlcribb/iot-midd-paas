# Guía: Conectar SBC con DHT22 al IoT Middleware

Esta guía explica cómo configurar una SBC (Raspberry Pi, Orange Pi, etc.) con un sensor DHT22 para publicar datos al IoT Middleware mediante MQTT.

## 📋 Requisitos

### Hardware
- SBC (Raspberry Pi 3/4, Orange Pi, etc.)
- Sensor DHT22
- Cableado (cables jumper)
- Resistencia pull-up de 4.7kΩ o 10kΩ (algunos módulos DHT22 ya la incluyen)

### Software
- Sistema operativo Linux (Raspbian, Ubuntu, Armbian, etc.)
- Python 3.7+
- pip3

## 🔌 Conexión del Hardware

### Pinout del DHT22
```
DHT22 tiene 4 pines:
1. VCC  -> 3.3V o 5V (depende del módulo)
2. DATA -> GPIO (ej: GPIO 4 = Pin 7)
3. NC   -> No conectado
4. GND  -> GND
```

### Conexión recomendada
```
DHT22           Raspberry Pi
-----           ------------
VCC   ----->    3.3V (Pin 1) o 5V (Pin 2)
DATA  ----->    GPIO 4 (Pin 7)
              + Resistencia 4.7kΩ entre DATA y VCC
GND   ----->    GND (Pin 6)
```

**Nota:** Si usas un módulo DHT22 pre-ensamblado, la resistencia pull-up ya viene incluida.

## 📦 Instalación de Dependencias

### 1. Actualizar el sistema
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Instalar dependencias del sistema
```bash
sudo apt-get install -y python3-pip python3-dev python3-rpi.gpio
```

### 3. Instalar librerías Python
```bash
pip3 install paho-mqtt Adafruit_Python_DHT
```

**Nota:** Si `Adafruit_Python_DHT` no funciona (dependencias de compilación), puedes usar:
```bash
pip3 install paho-mqtt adafruit-circuitpython-dht
# Además, necesitarás:
sudo apt-get install -y libgpiod2
```

## ⚙️ Configuración

### 1. Descargar el script
Copia el archivo `sbc_dht22_publisher.py` a tu SBC:
```bash
scp examples/sbc_dht22_publisher.py pi@192.168.1.XXX:/home/pi/
```

O clona el repositorio:
```bash
git clone <repo_url>
cd iot-middleware
```

### 2. Configurar el script

Edita `sbc_dht22_publisher.py` y ajusta estas variables:

```python
# Configuración MQTT
MQTT_BROKER = "192.168.1.100"  # IP del servidor con el middleware
MQTT_PORT = 1883
MQTT_USERNAME = "iot_user"      # Según tu configuración
MQTT_PASSWORD = "iot_password"  # Según tu configuración

# Configuración del sensor
DHT_PIN = 4  # GPIO pin donde está conectado (4 = Pin 7 en Raspberry Pi)

# Configuración de tópicos
MQTT_TOPIC_TEMPERATURE = "iot/proyecto_demo/casa_living/dht22_sbc/temperatura"
MQTT_TOPIC_HUMIDITY = "iot/proyecto_demo/casa_living/dht22_sbc/humedad"

# Intervalo de lectura (segundos)
READ_INTERVAL = 30
```

### 3. Verificar conexión MQTT

Antes de ejecutar el script, verifica que puedas conectarte al broker MQTT:

```bash
# Instalar mosquitto-clients para pruebas
sudo apt-get install -y mosquitto-clients

# Probar conexión (desde tu SBC)
mosquitto_pub -h 192.168.1.100 -p 1883 -t "test/topic" -m "test message"

# O suscribirse desde el servidor del middleware
mosquitto_sub -h 192.168.1.100 -p 1883 -t "iot/+/+/+/+/+"
```

## 🚀 Ejecución

### Modo manual
```bash
chmod +x sbc_dht22_publisher.py
python3 sbc_dht22_publisher.py
```

### Como servicio systemd (recomendado)

1. Crear archivo de servicio:
```bash
sudo nano /etc/systemd/system/dht22-mqtt.service
```

2. Agregar contenido:
```ini
[Unit]
Description=DHT22 MQTT Publisher para IoT Middleware
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/iot-middleware
ExecStart=/usr/bin/python3 /home/pi/iot-middleware/examples/sbc_dht22_publisher.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

3. Habilitar y iniciar el servicio:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dht22-mqtt.service
sudo systemctl start dht22-mqtt.service
```

4. Verificar estado:
```bash
sudo systemctl status dht22-mqtt.service
```

5. Ver logs:
```bash
sudo journalctl -u dht22-mqtt.service -f
```

## 📊 Formato de Datos

### Tópicos MQTT

El script publica en dos tópicos:

1. **Temperatura:**
   - Tópico: `iot/proyecto_demo/casa_living/dht22_sbc/temperatura`
   - Payload JSON:
   ```json
   {
     "valor": 24.5,
     "unidad": "celsius",
     "timestamp": "2026-01-06T23:45:00.123456+00:00",
     "tipo": "temperatura",
     "sensor_id": "dht22_sbc_1234567890",
     "metadata": {
       "sensor_type": "DHT22",
       "location": "living_room",
       "pin": 4
     }
   }
   ```

2. **Humedad:**
   - Tópico: `iot/proyecto_demo/casa_living/dht22_sbc/humedad`
   - Payload JSON:
   ```json
   {
     "valor": 65.2,
     "unidad": "porcentaje",
     "timestamp": "2026-01-06T23:45:00.123456+00:00",
     "tipo": "humedad",
     "sensor_id": "dht22_sbc_1234567890",
     "metadata": {
       "sensor_type": "DHT22",
       "location": "living_room",
       "pin": 4
     }
   }
   ```

### Estructura del Tópico

El formato del tópico es: `iot/{proyecto}/{unidad}/{dispositivo}/{canal}`

- **proyecto**: Identificador del proyecto (ej: "proyecto_demo")
- **unidad**: Unidad de producción o ubicación (ej: "casa_living")
- **dispositivo**: Identificador del dispositivo (ej: "dht22_sbc")
- **canal**: Tipo de medición (ej: "temperatura" o "humedad")

## 🔍 Verificación

### 1. Verificar que el middleware recibe los datos

En el servidor del middleware, verifica los logs:
```bash
docker logs -f iotmw-ingestor
```

Deberías ver mensajes como:
```
✅ Mensaje recibido en iot/proyecto_demo/casa_living/dht22_sbc/temperatura
📊 Datos procesados y almacenados
```

### 2. Consultar datos mediante la API

```bash
# Consultar temperatura reciente
curl http://localhost:8000/api/data/time-series?canal_id=temperatura&limit=10

# Consultar humedad reciente
curl http://localhost:8000/api/data/time-series?canal_id=humedad&limit=10
```

### 3. Ver datos en el dashboard

Accede al dashboard del middleware:
```
http://localhost:8080
```

## 🐛 Solución de Problemas

### Error: "No se pudieron leer los datos del sensor"

**Causas posibles:**
- Pin GPIO incorrecto
- Conexiones sueltas
- Sensor defectuoso
- Falta resistencia pull-up

**Solución:**
1. Verificar conexiones físicas
2. Cambiar el pin GPIO en la configuración
3. Probar con otro sensor
4. Asegurar que la resistencia pull-up esté conectada

### Error: "No se pudo conectar al broker MQTT"

**Causas posibles:**
- IP del broker incorrecta
- Puerto incorrecto
- Firewall bloqueando la conexión
- Credenciales incorrectas

**Solución:**
1. Verificar IP y puerto del broker
2. Probar conexión con `mosquitto_pub`
3. Verificar firewall: `sudo ufw allow 1883`
4. Verificar credenciales en `config.yaml`

### Error: "ModuleNotFoundError: No module named 'Adafruit_DHT'"

**Solución:**
```bash
# Opción 1: Instalar Adafruit_Python_DHT
pip3 install Adafruit_Python_DHT

# Opción 2: Instalar adafruit-circuitpython-dht (alternativa moderna)
pip3 install adafruit-circuitpython-dht
sudo apt-get install -y libgpiod2
```

### Datos no aparecen en el middleware

**Verificar:**
1. El middleware está escuchando el tópico correcto
2. El formato del tópico coincide con los patrones en `config.yaml`
3. El payload es JSON válido
4. Los logs del ingestor muestran errores

## 📝 Notas Adicionales

### Optimización de Lecturas

El DHT22 puede requerir un pequeño delay entre lecturas. El script usa `read_retry` que hace varios intentos automáticos. Si tienes problemas, puedes:

1. Aumentar el intervalo entre lecturas
2. Agregar delay después de cada lectura
3. Usar un sensor más rápido (DS18B20 para temperatura)

### Múltiples Sensores

Si tienes múltiples sensores DHT22, puedes:

1. Duplicar el script con diferentes pins y tópicos
2. Modificar el script para leer múltiples sensores en el mismo loop
3. Usar diferentes SBCs para cada sensor

### Seguridad

Para producción, considera:

1. Usar TLS/SSL para MQTT
2. Autenticación fuerte en el broker
3. Limitar acceso por IP en el broker
4. Usar certificados para autenticación mutua

## 🔗 Recursos

- [Documentación DHT22](https://www.adafruit.com/product/385)
- [Librería Adafruit DHT](https://github.com/adafruit/Adafruit_Python_DHT)
- [Documentación paho-mqtt](https://www.eclipse.org/paho/clients/python/)
- [Configuración del Middleware](../docs/legacy/README_INGESTA.md)
