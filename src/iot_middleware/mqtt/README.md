# Módulo MQTT - IoT Middleware

## 📋 Descripción

El módulo MQTT proporciona un cliente robusto y completo para la comunicación con brokers MQTT. Está diseñado específicamente para el IoT Middleware, con soporte para reconexión automática, manejo de mensajes JSON, y integración completa con el sistema de configuración.

## 🚀 Características Principales

- ✅ **Cliente MQTT Robusto**: Basado en paho-mqtt con manejo de errores avanzado
- 🔄 **Reconexión Automática**: Thread dedicado para reconexión automática
- 📨 **Manejo de Mensajes JSON**: Parseo automático de payloads JSON
- 🔧 **Procesador de Mensajes Configurable**: Callback personalizable para procesar mensajes
- 📋 **Suscripción Automática**: Se suscribe automáticamente a tópicos configurados
- 🛡️ **Manejo de Errores**: Manejo robusto de errores de conexión y mensajes
- 🔐 **Soporte TLS**: Configuración de seguridad TLS opcional
- 📊 **Monitoreo de Estado**: Estado de conexión y estadísticas en tiempo real
- 🎯 **Context Manager**: Soporte para `with` statement

## 🏗️ Arquitectura

### Clases Principales

#### `IoTMQTTClient`
Cliente principal MQTT que maneja la conexión, suscripciones y publicación:

- **Conexión**: Conecta al broker configurado con reintentos automáticos
- **Suscripciones**: Se suscribe automáticamente a tópicos configurados
- **Publicación**: Publica mensajes con diferentes niveles de QoS
- **Reconexión**: Thread dedicado para reconexión automática
- **Estado**: Monitoreo del estado de conexión y estadísticas

#### `MQTTMessage`
Estructura de datos para mensajes MQTT recibidos:

- **topic**: Tópico del mensaje
- **payload**: Contenido del mensaje (JSON parseado)
- **qos**: Calidad de servicio del mensaje
- **retain**: Si el mensaje está retenido
- **timestamp**: Timestamp de recepción
- **message_id**: ID único del mensaje

#### `MQTTCallbackHandler`
Manejador de callbacks para eventos MQTT:

- **on_connect**: Cuando se conecta al broker
- **on_disconnect**: Cuando se desconecta del broker
- **on_message**: Cuando se recibe un mensaje
- **on_publish**: Cuando se publica un mensaje
- **on_subscribe**: Cuando se suscribe a un tópico
- **on_unsubscribe**: Cuando se desuscribe de un tópico

## 📖 Uso Básico

### 1. Crear Cliente MQTT
```python
from iot_middleware.config import load_config
from iot_middleware.mqtt import create_mqtt_client

# Cargar configuración
config = load_config()
mqtt_config = config.mqtt

# Crear cliente
client = create_mqtt_client(mqtt_config, "mi_cliente")
```

### 2. Conectar al Broker
```python
# Conectar con reintentos automáticos
if client.connect():
    print("✅ Conectado al broker MQTT")
else:
    print("❌ Error de conexión")
```

### 3. Configurar Procesador de Mensajes
```python
def mi_procesador(mensaje):
    print(f"Mensaje recibido en {mensaje.topic}: {mensaje.payload}")

# Configurar procesador
client.set_message_processor(mi_procesador)
```

### 4. Publicar Mensajes
```python
# Mensaje simple
mensaje = {"temperatura": 23.5, "humedad": 65}
client.publish("iot/sensor/001/data", mensaje)

# Con QoS específico
client.publish("iot/sensor/001/status", {"status": "online"}, qos=2)

# Mensaje retenido
client.publish("iot/system/info", {"version": "1.0.0"}, retain=True)
```

### 5. Usar Context Manager
```python
# Conexión automática y desconexión
with create_mqtt_client(mqtt_config) as client:
    if client.connect():
        client.publish("iot/test", {"mensaje": "Hola"})
        # Se desconecta automáticamente al salir del context
```

## 🔧 Configuración

### Estructura de Configuración MQTT
```yaml
mqtt:
  broker:
    host: "mosquitto"
    port: 1883
    keepalive: 60
    username: null
    password: null
    tls_enabled: false
    ca_certs: null
    certfile: null
    keyfile: null
  topics:
    subscribe: ["iot/+/+/data", "iot/+/+/status"]
    publish: ["iot/+/+/response", "iot/+/+/command"]
  qos: 1
  retain: false
```

### Parámetros de Conexión
- **host**: Host del broker MQTT
- **port**: Puerto del broker MQTT
- **keepalive**: Intervalo de keepalive en segundos
- **username/password**: Credenciales de autenticación (opcional)
- **tls_enabled**: Habilitar TLS para conexión segura
- **ca_certs/certfile/keyfile**: Certificados TLS (opcional)

### Configuración de Tópicos
- **subscribe**: Lista de tópicos a los que suscribirse automáticamente
- **publish**: Lista de tópicos para publicación
- **qos**: Calidad de servicio por defecto (0, 1, o 2)
- **retain**: Si los mensajes deben retenerse por defecto

## 🧪 Pruebas

### Ejecutar Pruebas
```bash
# Desde el directorio raíz
python3 scripts/test_mqtt_client.py

# O desde el directorio containers
python3 ../scripts/test_mqtt_client.py
```

### Pruebas Incluidas

1. **Creación del Cliente**: Creación y configuración básica
2. **Conexión MQTT**: Conexión al broker
3. **Suscripción a Tópicos**: Verificación de suscripciones automáticas
4. **Publicación de Mensajes**: Publicación con diferentes QoS
5. **Procesador Personalizado**: Procesador de mensajes personalizado
6. **Desconexión MQTT**: Desconexión limpia
7. **Context Manager**: Uso del context manager

## 📚 Ejemplos de Uso

### Ejecutar Ejemplos
```bash
# Desde el directorio raíz
python3 examples/mqtt_usage_example.py

# O desde el directorio containers
python3 ../examples/mqtt_usage_example.py
```

### Ejemplos Incluidos

1. **Uso Básico**: Conexión simple y publicación
2. **Simulación de Dispositivos**: Múltiples dispositivos simulados
3. **Procesamiento de Mensajes**: Procesador de datos IoT
4. **Características Avanzadas**: QoS, mensajes retenidos, suscripciones

## 🔄 Reconexión Automática

El cliente MQTT incluye un sistema de reconexión automática:

- **Thread Dedicado**: Thread separado para manejar reconexiones
- **Reintentos Inteligentes**: Espera entre reintentos para evitar spam
- **Estado Persistente**: Mantiene suscripciones y configuración
- **Logging Detallado**: Registra todos los intentos de reconexión

### Configuración de Reconexión
```python
# Conectar con parámetros personalizados
client.connect(max_retries=5, retry_delay=10.0)

# El thread de reconexión se inicia automáticamente
# y se detiene al desconectar
```

## 📊 Monitoreo y Estado

### Estado de Conexión
```python
status = client.get_connection_status()
print(f"Conectado: {status['connected']}")
print(f"Broker: {status['broker_host']}:{status['broker_port']}")
print(f"Tópicos suscritos: {status['subscribed_topics']}")
print(f"Contador de mensajes: {status['message_count']}")
```

### Logging Integrado
```python
import logging

# Configurar nivel de logging
logging.basicConfig(level=logging.INFO)

# Los mensajes se mostrarán automáticamente
client.connect()
```

## 🚨 Manejo de Errores

### Errores de Conexión
```python
try:
    if not client.connect():
        print("❌ Falló la conexión inicial")
        # El cliente intentará reconectar automáticamente
except Exception as e:
    print(f"❌ Error inesperado: {e}")
```

### Errores de Mensajes
```python
def procesador_seguro(mensaje):
    try:
        # Procesar mensaje
        procesar_datos(mensaje.payload)
    except Exception as e:
        logger.error(f"Error al procesar mensaje: {e}")
        # Continuar procesando otros mensajes
```

### Validación de Payload
```python
def procesador_validado(mensaje):
    # Verificar campos requeridos
    if 'device_id' not in mensaje.payload:
        logger.warning("Mensaje sin device_id")
        return
    
    if 'value' not in mensaje.payload:
        logger.warning("Mensaje sin valor")
        return
    
    # Procesar mensaje válido
    procesar_sensor(mensaje.payload)
```

## 🔐 Seguridad

### Autenticación
```yaml
mqtt:
  broker:
    username: "usuario_iot"
    password: "contraseña_segura"
```

### TLS/SSL
```yaml
mqtt:
  broker:
    tls_enabled: true
    ca_certs: "/path/to/ca.crt"
    certfile: "/path/to/client.crt"
    keyfile: "/path/to/client.key"
```

## 🎯 Casos de Uso

### 1. Dispositivo IoT
```python
class SensorIoT:
    def __init__(self, device_id):
        self.client = create_mqtt_client(config.mqtt, device_id)
        self.client.set_message_processor(self.procesar_comandos)
        
    def iniciar(self):
        if self.client.connect():
            self.publicar_datos()
    
    def publicar_datos(self):
        while True:
            datos = self.leer_sensor()
            self.client.publish(f"iot/{self.device_id}/data", datos)
            time.sleep(60)
```

### 2. Gateway de Datos
```python
class GatewayIoT:
    def __init__(self):
        self.client = create_mqtt_client(config.mqtt, "gateway")
        self.client.set_message_processor(self.procesar_mensaje)
        
    def procesar_mensaje(self, mensaje):
        # Procesar datos del sensor
        datos_procesados = self.normalizar_datos(mensaje.payload)
        
        # Enviar a base de datos
        self.guardar_en_db(datos_procesados)
        
        # Enviar respuesta
        respuesta = {"status": "ok", "timestamp": datetime.now().isoformat()}
        self.client.publish(f"iot/{mensaje.payload['device_id']}/response", respuesta)
```

### 3. Monitor de Sistema
```python
class MonitorSistema:
    def __init__(self):
        self.client = create_mqtt_client(config.mqtt, "monitor")
        self.client.set_message_processor(self.analizar_mensaje)
        
    def analizar_mensaje(self, mensaje):
        # Analizar tipo de mensaje
        if mensaje.payload.get('type') == 'alert':
            self.procesar_alerta(mensaje)
        elif mensaje.payload.get('type') == 'status':
            self.actualizar_estado(mensaje)
        else:
            self.registrar_mensaje(mensaje)
```

## 🔧 Personalización

### Procesador de Mensajes Personalizado
```python
class ProcesadorAvanzado:
    def __init__(self):
        self.contadores = {}
    
    def procesar(self, mensaje):
        # Contar mensajes por tópico
        topic = mensaje.topic
        if topic not in self.contadores:
            self.contadores[topic] = 0
        self.contadores[topic] += 1
        
        # Procesar según el tópico
        if topic.endswith('/data'):
            self.procesar_datos(mensaje)
        elif topic.endswith('/status'):
            self.procesar_estado(mensaje)
        elif topic.endswith('/alerts'):
            self.procesar_alerta(mensaje)
```

### Cliente MQTT Extendido
```python
class ClienteMQTTPersonalizado(IoTMQTTClient):
    def __init__(self, config, client_id=None):
        super().__init__(config, client_id)
        self.mensajes_por_segundo = 0
        self.ultimo_conteo = time.time()
    
    def publicar_con_limite(self, topic, payload, max_por_segundo=10):
        ahora = time.time()
        if ahora - self.ultimo_conteo >= 1.0:
            self.mensajes_por_segundo = 0
            self.ultimo_conteo = ahora
        
        if self.mensajes_por_segundo < max_por_segundo:
            self.mensajes_por_segundo += 1
            return self.publish(topic, payload)
        else:
            logger.warning("Límite de mensajes por segundo alcanzado")
            return False
```

## 📚 Dependencias

- **paho-mqtt**: Cliente MQTT principal
- **iot_middleware.config**: Sistema de configuración
- **json**: Manejo de payloads JSON
- **threading**: Reconexión automática
- **logging**: Sistema de logging integrado

## 🤝 Contribución

Para contribuir al módulo MQTT:

1. Mantener compatibilidad con versiones anteriores
2. Agregar pruebas para nuevas funcionalidades
3. Documentar cambios en este README
4. Seguir las convenciones de código existentes

## 📞 Soporte

Para problemas o preguntas:

1. Revisar este README
2. Ejecutar las pruebas incluidas
3. Verificar la configuración del broker MQTT
4. Revisar los logs de conexión y mensajes

## 🚀 Próximos Pasos

### Funcionalidades Planificadas
- [ ] Soporte para MQTT v5 completo
- [ ] Compresión de mensajes
- [ ] Métricas de rendimiento avanzadas
- [ ] Balanceo de carga entre brokers
- [ ] Persistencia de mensajes offline

### Integración
- [ ] Con el módulo de procesamiento de datos
- [ ] Con el sistema de almacenamiento
- [ ] Con la API REST
- [ ] Con el sistema de alertas

---

**Nota**: Este módulo está diseñado para ser robusto y fácil de usar en entornos de producción. Si encuentras algún problema, por favor reporta el issue con detalles del error y tu configuración.
