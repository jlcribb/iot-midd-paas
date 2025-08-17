# IoT Middleware

Sistema de middleware para IoT que proporciona capacidades de procesamiento, almacenamiento y comunicación para dispositivos IoT.

## Características Principales

### 🚀 **Procesamiento de Datos**
- Normalización y validación automática de datos IoT
- Procesamiento en tiempo real con múltiples estrategias
- Pipeline configurable para transformación de datos

### 🗄️ **Capa CRUD Completa**
- Repositorios especializados para todas las entidades del sistema
- Validación automática de tipos de datos según configuración del canal
- Validación de rangos (min/max) para valores numéricos
- Metadatos enriquecidos automáticamente con contexto del proyecto
- Operaciones CRUD optimizadas con consultas relacionales avanzadas

### 💾 **Almacenamiento Inteligente**
- **Sistema de particiones mensuales** para optimización de rendimiento
- Base de datos PostgreSQL con esquema escalable
- Gestión automática de datos históricos
- Backup y recuperación granular por partición

### 📡 **Comunicación MQTT**
- Cliente MQTT robusto con reconexión automática
- Soporte para múltiples brokers y tópicos
- Manejo de mensajes offline y colas de retransmisión

### ⚙️ **Configuración Flexible**
- Sistema de configuración basado en YAML
- Configuración por entorno (desarrollo, producción, testing)
- Validación automática de configuración

## Sistema de Particiones Mensuales

### 🎯 **Beneficios Clave**
- **Rendimiento**: Consultas 10x más rápidas en datos históricos
- **Escalabilidad**: Crecimiento automático sin degradación de rendimiento
- **Mantenimiento**: Gestión automatizada del ciclo de vida de datos

### 📊 **Características**
- Creación automática de particiones por mes
- Trigger inteligente para creación on-the-fly
- Monitoreo en tiempo real del estado del sistema
- Limpieza automática de particiones antiguas

### 🛠️ **Herramientas de Gestión**
```bash
# Verificar salud del sistema
python scripts/partitions.py health

# Crear particiones automáticamente
python scripts/partitions.py create

# Monitorear estado
python scripts/partitions.py monitor
```

**📖 [Documentación Completa del Sistema de Particiones](README_PARTITIONING.md)**

## Capa CRUD y Validación de Tipos

### 🎯 **Funcionalidades Clave**
- **Validación Automática**: Tipos de datos y rangos según configuración del canal
- **Metadatos Enriquecidos**: Contexto automático del proyecto, dispositivo y unidad
- **Operaciones Optimizadas**: Consultas relacionales con JOINs inteligentes
- **Manejo de Errores**: Logging detallado y respuestas estructuradas

### 🛠️ **Uso Rápido**
```python
from iot_middleware.storage.repositories import RegistroDatosRepository

# Inserción con validación automática
registro = registro_repo.insert_record(
    canal_id='uuid-canal',
    valor=25.5,  # Se valida según el tipo del canal
    metadata={'source': 'sensor_1'},
    qos=1,
    ip='192.168.1.100'
)
```

### 📊 **Tipos de Datos Soportados**
- **Numéricos**: `int`, `float` con validación de rangos
- **Booleanos**: Conversión automática desde múltiples formatos
- **Texto**: `string`, `json` con validación de formato
- **Temporales**: `timestamp` con conversión ISO automática

**📖 [Documentación Completa de la Capa CRUD](README_CRUD_REPOSITORIES.md)**

## Instalación Rápida

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd iot-middleware
```

### 2. Configurar Base de Datos
```bash
# Aplicar esquema inicial
alembic upgrade 0001

# Aplicar sistema de particiones
alembic upgrade 0002
```

### 3. Verificar Instalación
```bash
# Verificar sistema de particiones
python scripts/partitions.py health

# Ejecutar ejemplo de particionado
python examples/partitioning_example.py

# Ejecutar ejemplo de la capa CRUD
python examples/crud_validation_example.py examples/config_partitioning.yaml
```

## Estructura del Proyecto

```
iot-middleware/
├── alembic/                    # Migraciones de base de datos
│   ├── versions/
│   │   ├── 0001_initial_schema.py
│   │   ├── 0002_partitioning_system.py  # 🆕 Sistema de particiones
│   │   └── 0003_convert_to_partitioned.py # 🆕 Conversión a particionado
├── src/                        # Código fuente
│   └── iot_middleware/
│       └── storage/
│           └── repositories/   # 🆕 Capa CRUD completa
│               ├── base_repository.py
│               ├── cliente_repository.py
│               ├── proyecto_repository.py
│               ├── canal_repository.py
│               └── registro_datos_repository.py
├── scripts/                    # Scripts utilitarios
│   ├── partitions.py          # 🆕 Gestor de particiones
│   └── ...
├── examples/                   # Ejemplos de uso
│   ├── partitioning_example.py # 🆕 Demo del sistema de particiones
│   ├── crud_validation_example.py # 🆕 Demo de la capa CRUD
│   └── ...
├── README_PARTITIONING.md     # 🆕 Documentación de particiones
└── README_CRUD_REPOSITORIES.md # 🆕 Documentación de la capa CRUD
```

## Uso Rápido

### Configuración Básica
```yaml
# config.yaml
database:
  host: localhost
  port: 5432
  name: iot_middleware
  user: iot_user
  password: iot_password

mqtt:
  broker: localhost
  port: 1883
  topics: ["iot/+/data"]
```

### Ejemplo de Particionado
```python
from iot_middleware.storage.db_handler import DatabaseHandler

# El sistema crea automáticamente particiones mensuales
db = DatabaseHandler(config['database'])

# Insertar datos (se distribuyen automáticamente por partición)
db.execute_query("""
    INSERT INTO iot_schema.registros_datos (canal_id, ts, valor_num)
    VALUES (%s, %s, %s)
""", (canal_id, timestamp, value))
```

## Monitoreo y Mantenimiento

### Comandos de Monitoreo
```bash
# Estado general del sistema
python scripts/partitions.py health

# Estadísticas de uso
python scripts/partitions.py stats

# Limpieza automática
python scripts/partitions.py cleanup --retention-months 12
```

### Tareas de Mantenimiento
- **Diario**: Verificar salud del sistema
- **Semanal**: Monitorear estadísticas de particiones
- **Mensual**: Crear particiones futuras y limpiar antiguas

## Desarrollo

### Requisitos
- Python 3.8+
- PostgreSQL 12+
- Podman (para contenedores)

### Configuración de Desarrollo
```bash
# Levantar servicios con Podman
podman-compose -f containers/podman-compose.yaml up -d

# Aplicar migraciones
alembic upgrade head

# Ejecutar tests
python -m pytest tests/
```

### Estructura de Migraciones
- **0001**: Esquema inicial completo del sistema IoT
- **0002**: Sistema de particiones mensuales automático

## Documentación

- [📖 Sistema de Particiones](README_PARTITIONING.md) - Documentación completa del particionado
- [📖 Base de Datos](README_POSTGRESQL.md) - Esquema y configuración de BD
- [📖 Desarrollo](DEVELOPMENT_SUMMARY_PROCESSOR.md) - Guía de desarrollo del procesador
- [📖 Almacenamiento](DEVELOPMENT_SUMMARY_STORAGE.md) - Guía de desarrollo del almacenamiento

## Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

Para soporte técnico o preguntas sobre el sistema de particiones:
- Revisar [README_PARTITIONING.md](README_PARTITIONING.md)
- Ejecutar `python scripts/partitions.py health` para diagnóstico
- Abrir issue en el repositorio con logs de error

---

**🚀 El sistema de particiones mensuales está diseñado para escalar automáticamente y mantener el rendimiento óptimo incluso con millones de registros IoT.**
