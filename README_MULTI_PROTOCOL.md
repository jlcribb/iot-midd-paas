# Arquitectura Multi-Protocolo - IoT Middleware

## 🎯 Visión General

Esta implementación extiende tu IoT Middleware existente con una arquitectura modular que permite recibir datos desde múltiples protocolos IoT sin cambiar el core del sistema. Cada protocolo se traduce al mismo formato unificado antes de entrar al procesamiento central.

## 🏗️ Arquitectura

### Capa de Adquisición (Input Layer)
- **Conectores de Protocolos**: Cada protocolo tiene su propio conector que implementa la interfaz `BaseConnector`
- **Traducción Unificada**: Todos los datos se convierten al formato `UnifiedDataFormat` antes de entrar al core
- **Gestión Centralizada**: El `InputManager` coordina todos los conectores y proporciona una interfaz unificada

### Capa de Normalización (Middleware Core)
- **Formato Unificado**: Todos los datos entran con la misma estructura
- **Procesamiento Consistente**: Tu lógica existente funciona sin cambios
- **Validación Centralizada**: Sistema de validación unificado para todos los protocolos

### Capa de Exposición (API/Streaming)
- **API REST**: Endpoints para consultas y gestión
- **Streaming en Tiempo Real**: WebSocket/MQTT para notificaciones
- **Métricas Unificadas**: Estado y salud de todos los conectores

## 🔌 Protocolos Soportados

### 1. MQTT (Ya Implementado)
- Broker MQTT estándar
- Suscripción a tópicos configurados
- QoS configurable
- Reconexión automática

### 2. HTTP/REST
- Endpoints para ingesta directa
- Autenticación por token
- Rate limiting configurable
- CORS habilitado
- SSL/TLS opcional

### 3. BLE (Bluetooth Low Energy)
- Requiere bridge (Raspberry Pi, ESP32)
- Filtros por MAC address
- Parsing de datos del fabricante
- Descubrimiento automático

### 4. LoRa (LoRaWAN)
- Gateways ChirpStack, The Things Stack
- Filtros por aplicación y dispositivo
- Decodificación de payloads
- Información de recepción

### 5. MIDI
- Dispositivos musicales
- Filtros por canal y tipo de mensaje
- Conversión de notas a frecuencias
- Parsing de controladores

### 6. Modbus
- TCP, RTU, ASCII
- Lectura periódica de registros
- Tipos de datos configurables
- Reconexión automática

### 7. ZigBee
- Coordinadores Zigbee2MQTT, deCONZ
- Filtros por tipo de dispositivo
- Parsing de sensores y actuadores
- Estado de batería y disponibilidad

## 🚀 Instalación

### Dependencias
```bash
pip install pymodbus mido paho-mqtt pyyaml
```

### Estructura de Archivos
```
src/iot_middleware/input/
├── __init__.py
├── base_connector.py          # Clase base para todos los conectores
├── connector_factory.py       # Fábrica de conectores
├── input_manager.py           # Gestor principal
└── protocols/                 # Conectores específicos
    ├── __init__.py
    ├── mqtt_connector.py
    ├── http_connector.py
    ├── ble_connector.py
    ├── lora_connector.py
    ├── midi_connector.py
    ├── modbus_connector.py
    └── zigbee_connector.py
```

## 📋 Configuración

### Archivo de Configuración Principal
```yaml
# config_multi_protocol.yaml
input_manager:
  enabled: true
  name: "multi_protocol_manager"
  max_connectors: 20
  health_check_interval: 30.0
  metrics_interval: 60.0

connectors:
  - name: "mqtt_main"
    protocol: "mqtt"
    enabled: true
    broker_host: "localhost"
    broker_port: 1883
    topics_subscribe: ["iot/+/+/+/+"]

  - name: "http_ingest"
    protocol: "http"
    enabled: true
    host: "0.0.0.0"
    port: 8080
    endpoint: "/ingest"
    auth_enabled: true
    auth_token: "your_token"

  - name: "ble_bridge"
    protocol: "ble"
    enabled: true
    bridge_type: "mqtt"
    bridge_address: "192.168.1.100"
    device_whitelist: ["AA:BB:CC:DD:EE:FF"]
```

### Configuración por Protocolo

#### MQTT
```yaml
- name: "mqtt_connector"
  protocol: "mqtt"
  broker_host: "localhost"
  broker_port: 1883
  topics_subscribe: ["iot/+/+/+/+"]
  qos: 1
  auto_reconnect: true
```

#### HTTP/REST
```yaml
- name: "http_connector"
  protocol: "http"
  host: "0.0.0.0"
  port: 8080
  endpoint: "/ingest"
  auth_enabled: true
  auth_token: "your_token"
  rate_limit_enabled: true
  rate_limit_requests: 100
```

#### BLE
```yaml
- name: "ble_connector"
  protocol: "ble"
  bridge_type: "mqtt"
  bridge_address: "192.168.1.100"
  device_whitelist: ["AA:BB:CC:DD:EE:FF"]
  auto_discovery: true
  scan_interval: 10.0
```

#### LoRa
```yaml
- name: "lora_connector"
  protocol: "lora"
  gateway_type: "chirpstack"
  gateway_address: "192.168.1.200"
  mqtt_topic: "application/+/device/+/event/+"
  application_whitelist: ["app_001"]
  parse_payload: true
  decode_base64: true
```

#### MIDI
```yaml
- name: "midi_connector"
  protocol: "midi"
  port_name: "USB MIDI Controller"
  channel_filter: [1, 2, 3, 4]
  message_types: ["note_on", "note_off", "control_change"]
  note_range: [21, 108]
  velocity_threshold: 10
```

#### Modbus
```yaml
- name: "modbus_connector"
  protocol: "modbus"
  protocol_type: "tcp"
  host: "192.168.1.50"
  port: 502
  device_id: 1
  scan_interval: 5.0
  registers:
    - address: 0
      count: 10
      type: "holding"
      name: "temperatures"
```

#### ZigBee
```yaml
- name: "zigbee_connector"
  protocol: "zigbee"
  coordinator_type: "zigbee2mqtt"
  coordinator_address: "192.168.1.150"
  mqtt_topic: "zigbee2mqtt/+/+"
  device_whitelist: ["living_room_sensor"]
  device_types: ["sensor", "switch", "light"]
```

## 💻 Uso Básico

### Inicialización Simple
```python
from src.iot_middleware.input import InputManager

# Configuración básica
configs = [
    {
        'name': 'mqtt_main',
        'protocol': 'mqtt',
        'broker_host': 'localhost',
        'topics_subscribe': ['iot/+/+/+/+']
    },
    {
        'name': 'http_ingest',
        'protocol': 'http',
        'host': '0.0.0.0',
        'port': 8080
    }
]

# Callback para datos unificados
def data_callback(unified_data):
    print(f"Datos de {unified_data.source_protocol}: {unified_data.measurements}")

# Crear y iniciar gestor
input_manager = InputManager(configs, data_callback)
input_manager.start()
```

### Uso con Configuración Completa
```python
import yaml
from src.iot_middleware.input import InputManager, InputManagerConfig

# Cargar configuración
with open('config_multi_protocol.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Crear gestor
input_manager = InputManager(
    configs=config['connectors'],
    data_callback=data_callback,
    manager_config=InputManagerConfig(**config['input_manager'])
)

# Iniciar
input_manager.start()

# Obtener estado
status = input_manager.get_manager_status()
print(f"Conectores activos: {status['active_connectors']}")

# Detener
input_manager.stop()
```

## 🔧 Gestión de Conectores

### Estado y Métricas
```python
# Estado general del gestor
status = input_manager.get_manager_status()
print(f"Total mensajes: {status['total_messages']}")
print(f"Uptime: {status['uptime_seconds']}s")

# Estado de conectores individuales
connectors_status = input_manager.get_all_connectors_status()
for name, status in connectors_status.items():
    print(f"{name}: {status['status']}")

# Estado de un conector específico
mqtt_status = input_manager.get_connector_status('mqtt_main')
print(f"MQTT conectado: {mqtt_status['connected']}")
```

### Gestión Dinámica
```python
# Agregar nuevo conector
new_config = {
    'name': 'new_ble',
    'protocol': 'ble',
    'bridge_address': '192.168.1.200'
}
input_manager.add_connector(new_config)

# Reiniciar conector
input_manager.restart_connector('mqtt_main')

# Remover conector
input_manager.remove_connector('old_connector')
```

## 📊 Formato de Datos Unificado

Todos los protocolos traducen sus datos al mismo formato:

```python
@dataclass
class UnifiedDataFormat:
    device_id: str           # ID único del dispositivo
    project_id: str          # ID del proyecto
    timestamp: datetime      # Timestamp de los datos
    measurements: Dict       # Mediciones/valores
    metadata: Dict          # Metadatos específicos del protocolo
    quality: DataQuality     # Calidad de los datos
    source_protocol: str     # Protocolo de origen
    source_address: str      # Dirección de origen
    raw_data: Any           # Datos originales del protocolo
```

### Ejemplo de Datos MQTT
```json
{
  "device_id": "sensor_001",
  "project_id": "lab_test",
  "timestamp": "2025-08-16T12:00:00Z",
  "measurements": {
    "temperature": 22.5,
    "humidity": 60
  },
  "metadata": {
    "topic": "iot/lab_test/main/sensor_001/temperature",
    "qos": 1,
    "topic_info": {
      "proyecto_id": "lab_test",
      "unidad_id": "main",
      "dispositivo_id": "sensor_001",
      "canal_id": "temperature"
    }
  },
  "quality": "valid",
  "source_protocol": "mqtt",
  "source_address": "localhost:1883"
}
```

### Ejemplo de Datos HTTP
```json
{
  "device_id": "web_device",
  "project_id": "web_project",
  "timestamp": "2025-08-16T12:00:00Z",
  "measurements": {
    "value": 42.0,
    "status": "active"
  },
  "metadata": {
    "method": "POST",
    "path": "/ingest",
    "client_ip": "192.168.1.100",
    "headers": {
      "Content-Type": "application/json",
      "User-Agent": "IoT-Device/1.0"
    }
  },
  "quality": "valid",
  "source_protocol": "http",
  "source_address": "192.168.1.100:8080"
}
```

## 🧪 Testing y Desarrollo

### Ejecutar Ejemplo Completo
```bash
cd examples
python multi_protocol_example.py
```

### Ejecutar Demo Simple
```bash
python multi_protocol_example.py --demo
```

### Logs y Debugging
```python
import logging

# Habilitar logging detallado
logging.basicConfig(level=logging.DEBUG)

# Logging específico por protocolo
logging.getLogger('src.iot_middleware.input.protocols.mqtt_connector').setLevel(logging.DEBUG)
```

## 🔒 Seguridad

### Autenticación
- **MQTT**: Usuario/contraseña, SSL/TLS
- **HTTP**: Token Bearer, SSL/TLS
- **Otros**: Configuración específica por protocolo

### Filtros
- **Whitelist/Blacklist** por dispositivo
- **Rate limiting** para HTTP
- **Validación de datos** centralizada

### Cifrado
- **SSL/TLS** para conexiones seguras
- **Cifrado de datos** opcional
- **Tokens seguros** para autenticación

## 📈 Monitoreo y Métricas

### Métricas del Sistema
- Mensajes recibidos por protocolo
- Latencia de procesamiento
- Uso de buffer
- Estado de conectores

### Health Checks
- Estado de conexiones
- Tiempo de respuesta
- Errores y reintentos
- Disponibilidad de servicios

### Alertas
- Conectores desconectados
- Errores de procesamiento
- Sobrecarga de buffer
- Problemas de autenticación

## 🚀 Escalabilidad

### Arquitectura Distribuida
- Múltiples instancias del gestor
- Balanceo de carga por protocolo
- Replicación de conectores críticos

### Performance
- Procesamiento asíncrono
- Buffers configurables
- Lotes de procesamiento
- Workers múltiples

### Extensibilidad
- Nuevos protocolos fáciles de agregar
- Plugins personalizados
- APIs para integración
- Webhooks configurables

## 🔧 Troubleshooting

### Problemas Comunes

#### Conector no se conecta
```python
# Verificar estado
status = input_manager.get_connector_status('connector_name')
print(f"Estado: {status['status']}")
print(f"Errores: {status['error_count']}")

# Reiniciar conector
input_manager.restart_connector('connector_name')
```

#### Datos no llegan
```python
# Verificar callback
print(f"Callback configurado: {input_manager.data_callback is not None}")

# Verificar métricas
metrics = input_manager.get_manager_status()
print(f"Mensajes recibidos: {metrics['total_messages']}")
```

#### Problemas de configuración
```python
from src.iot_middleware.input.connector_factory import ConnectorFactory

# Validar configuración
validation = ConnectorFactory.validate_config(connector_config)
if not validation['valid']:
    print(f"Errores: {validation['errors']}")
    print(f"Advertencias: {validation['warnings']}")
```

### Logs de Debug
```python
# Habilitar logging detallado
logging.basicConfig(level=logging.DEBUG)

# Logging específico
logging.getLogger('src.iot_middleware.input').setLevel(logging.DEBUG)
```

## 📚 Referencias

### Documentación
- [README Principal](../README.md)
- [API REST](../README_API_REST.md)
- [Sistema de Auditoría](../README_AUDITORIA.md)
- [Gestión de Datos](../README_INGESTA.md)

### Ejemplos
- [Ejemplo Multi-Protocolo](examples/multi_protocol_example.py)
- [Configuración Completa](examples/config_multi_protocol.yaml)
- [Casos de Uso](examples/)

### Protocolos
- [MQTT](https://mqtt.org/)
- [LoRaWAN](https://lora-alliance.org/)
- [ZigBee](https://zigbee.org/)
- [Modbus](https://modbus.org/)
- [MIDI](https://www.midi.org/)

## 🤝 Contribuciones

### Agregar Nuevos Protocolos
1. Crear nueva clase que extienda `BaseConnector`
2. Implementar métodos abstractos requeridos
3. Registrar en `ConnectorFactory`
4. Agregar configuración de ejemplo
5. Crear tests unitarios

### Reportar Issues
- Usar el sistema de issues del proyecto
- Incluir logs y configuración
- Describir pasos para reproducir
- Especificar versión y entorno

### Pull Requests
- Seguir el estilo de código existente
- Incluir tests para nuevas funcionalidades
- Actualizar documentación
- Verificar que todos los tests pasen

## 📄 Licencia

Este proyecto mantiene la misma licencia que el IoT Middleware principal.

---

**¡Con esta arquitectura modular, tu IoT Middleware ahora puede recibir datos desde prácticamente cualquier protocolo IoT manteniendo la compatibilidad con tu sistema existente!** 🎉
