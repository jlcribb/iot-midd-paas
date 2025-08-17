# Módulo de Configuración - IoT Middleware

## 📋 Descripción

El módulo `config_loader.py` proporciona una interfaz robusta y validada para cargar y gestionar la configuración del IoT Middleware desde archivos YAML. Utiliza Pydantic para validación de esquemas y manejo de errores.

## 🚀 Características Principales

- ✅ **Validación Automática**: Esquemas Pydantic para validar configuración
- 🔍 **Búsqueda Automática**: Encuentra archivos de configuración automáticamente
- 🛡️ **Manejo de Errores**: Errores claros y descriptivos
- 📊 **Tipado Fuerte**: Soporte completo de type hints
- 🔄 **Recarga en Caliente**: Capacidad de recargar configuración
- 📝 **Logging Integrado**: Logging automático de operaciones

## 🏗️ Arquitectura

### Clases de Configuración

#### `IoTMiddlewareConfig`
Configuración principal que contiene todas las subconfiguraciones:

- **MQTT**: Broker, tópicos, QoS, retención
- **InfluxDB**: URL, token, organización, bucket
- **PostgreSQL**: Host, puerto, base de datos, usuario
- **API**: Host, puerto, debug, CORS
- **Logging**: Nivel, formato, archivo
- **Processing**: Batch size, workers, timeouts
- **Storage**: Proveedores de almacenamiento
- **Security**: Configuración de seguridad
- **Monitoring**: Health checks, métricas, alertas

#### `ConfigLoader`
Clase principal para cargar y gestionar configuración:

- Búsqueda automática de archivos
- Carga y validación
- Métodos getters para cada sección
- Recarga de configuración
- Manejo de errores

## 📖 Uso Básico

### 1. Carga Simple
```python
from iot_middleware.config import load_config

# Cargar configuración automáticamente
config = load_config()

# Acceder a configuraciones
mqtt_host = config.mqtt.broker['host']
influxdb_url = config.influxdb.url
```

### 2. Uso con ConfigLoader
```python
from iot_middleware.config import ConfigLoader

# Crear instancia
loader = ConfigLoader()

# Buscar archivo automáticamente
config_path = loader.find_config_file()

# Cargar configuración
config = loader.load_config()

# Obtener configuraciones específicas
mqtt_config = loader.get_mqtt_config()
postgresql_config = loader.get_postgresql_config()
```

### 3. Validación de Archivos
```python
from iot_middleware.config import validate_config_file

# Validar archivo sin cargarlo
is_valid = validate_config_file("config.yaml")
if is_valid:
    print("✅ Archivo de configuración válido")
else:
    print("❌ Archivo de configuración inválido")
```

## 🔧 Configuración del Archivo YAML

### Estructura Mínima Requerida

```yaml
mqtt:
  broker:
    host: "localhost"
    port: 1883
  topics:
    subscribe: ["iot/+/+/data"]
    publish: ["iot/+/+/response"]

influxdb:
  url: "http://localhost:8086"
  token: "your-token"
  org: "your-org"
  bucket: "iot"

postgresql:
  host: "localhost"
  port: 5432
  database: "iot_middleware"
  username: "user"
  password: "password"

api:
  host: "0.0.0.0"
  port: 8000

storage:
  timeseries:
    provider: "influxdb"
  relational:
    provider: "postgresql"
  metadata:
    provider: "postgresql"
```

### Configuración Completa

Ver `examples/config_simple.yaml` para un ejemplo completo con todas las opciones disponibles.

## 🧪 Pruebas

### Ejecutar Pruebas
```bash
# Desde el directorio raíz
python3 scripts/test_config_loader.py

# O desde el directorio containers
python3 ../scripts/test_config_loader.py
```

### Pruebas Incluidas

1. **ConfigLoader**: Creación y funcionamiento básico
2. **Carga Directa**: Función de conveniencia `load_config()`
3. **Validación**: Validación de archivos de configuración
4. **Acceso**: Acceso a configuraciones específicas
5. **Métodos**: Métodos del ConfigLoader
6. **Manejo de Errores**: Casos de error y excepciones

## 🚨 Manejo de Errores

### Errores Comunes

#### Archivo No Encontrado
```python
try:
    config = load_config()
except FileNotFoundError as e:
    print(f"Archivo de configuración no encontrado: {e}")
```

#### Validación Fallida
```python
try:
    config = load_config()
except ValidationError as e:
    print("Errores de validación:")
    for error in e.errors():
        print(f"  - {error['loc']}: {error['msg']}")
```

#### Error de YAML
```python
try:
    config = load_config()
except yaml.YAMLError as e:
    print(f"Error en formato YAML: {e}")
```

### Validaciones Implementadas

- **MQTT**: Host y puerto requeridos, puerto positivo
- **InfluxDB**: URL válida, token no vacío
- **PostgreSQL**: Host, puerto, base de datos, usuario y contraseña requeridos
- **API**: Host no vacío, puerto en rango válido
- **Logging**: Nivel de logging válido
- **Processing**: Valores numéricos positivos
- **Storage**: Proveedores requeridos para cada tipo

## 🔄 Recarga de Configuración

```python
loader = ConfigLoader("config.yaml")
config = loader.load_config()

# ... tiempo después ...

# Recargar configuración
config = loader.reload_config()
```

## 📊 Logging

El módulo incluye logging automático:

```python
import logging

# Configurar nivel de logging
logging.basicConfig(level=logging.INFO)

# Los mensajes se mostrarán automáticamente
config = load_config()
```

## 🎯 Casos de Uso

### 1. Aplicación Principal
```python
from iot_middleware.config import load_config

def main():
    # Cargar configuración al inicio
    config = load_config()
    
    # Usar en toda la aplicación
    mqtt_client = create_mqtt_client(config.mqtt)
    db_connection = create_db_connection(config.postgresql)
    api_server = create_api_server(config.api)
```

### 2. Servicios Individuales
```python
from iot_middleware.config import ConfigLoader

class MQTTService:
    def __init__(self):
        self.loader = ConfigLoader()
        self.config = self.loader.get_mqtt_config()
    
    def reload_config(self):
        self.config = self.loader.reload_config().mqtt
```

### 3. Validación de Configuración
```python
from iot_middleware.config import validate_config_file

def check_configuration():
    config_files = ["config.yaml", "config_prod.yaml"]
    
    for config_file in config_files:
        if validate_config_file(config_file):
            print(f"✅ {config_file} es válido")
        else:
            print(f"❌ {config_file} es inválido")
```

## 🔧 Personalización

### Agregar Nuevas Validaciones

```python
class CustomConfig(BaseModel):
    custom_field: str = Field(..., description="Campo personalizado")
    
    @validator('custom_field')
    def validate_custom_field(cls, v):
        if not v.startswith('custom_'):
            raise ValueError("El campo debe comenzar con 'custom_'")
        return v
```

### Extender ConfigLoader

```python
class CustomConfigLoader(ConfigLoader):
    def load_custom_config(self):
        config = self.get_config()
        # Lógica personalizada aquí
        return config
```

## 📚 Dependencias

- **Pydantic**: Validación de esquemas y modelos
- **PyYAML**: Parsing de archivos YAML
- **typing**: Soporte de type hints
- **logging**: Sistema de logging integrado

## 🤝 Contribución

Para contribuir al módulo de configuración:

1. Mantener compatibilidad con versiones anteriores
2. Agregar pruebas para nuevas funcionalidades
3. Documentar cambios en este README
4. Seguir las convenciones de código existentes

## 📞 Soporte

Para problemas o preguntas:

1. Revisar este README
2. Ejecutar las pruebas incluidas
3. Verificar el formato del archivo YAML
4. Revisar los logs de validación

---

**Nota**: Este módulo está diseñado para ser robusto y fácil de usar. Si encuentras algún problema, por favor reporta el issue con detalles del error y tu archivo de configuración.
