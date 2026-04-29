# Capa CRUD y Validación de Tipos - IoT Middleware

## 📋 **Descripción General**

Este módulo implementa una capa completa de repositorios CRUD para todas las entidades del sistema IoT Middleware, incluyendo validación automática de tipos de datos y rangos para la inserción en `registros_datos`.

## 🏗️ **Arquitectura del Sistema**

### **Estructura de Repositorios**

```
src/iot_middleware/storage/repositories/
├── __init__.py                    # Exportaciones del paquete
├── base_repository.py            # Repositorio base genérico
├── cliente_repository.py         # Operaciones CRUD para clientes
├── proyecto_repository.py        # Operaciones CRUD para proyectos
├── unidad_proyecto_repository.py # Operaciones CRUD para unidades
├── sesion_repository.py          # Operaciones CRUD para sesiones
├── dispositivo_repository.py     # Operaciones CRUD para dispositivos
├── dispositivo_proyecto_repository.py # Operaciones CRUD para dispositivos_proyecto
├── canal_repository.py           # Operaciones CRUD para canales + validación
├── evento_alarma_repository.py   # Operaciones CRUD para eventos_alarmas
├── config_middleware_repository.py # Operaciones CRUD para config_middleware
└── registro_datos_repository.py  # Operaciones CRUD para registros_datos + validación
```

## 🔧 **Funcionalidades Implementadas**

### **1. Repositorio Base Genérico (`BaseRepository`)**

Proporciona operaciones CRUD estándar para todas las entidades:

- ✅ **Create**: Crear nuevas entidades
- ✅ **Read**: Obtener por ID, listar todas, buscar por criterios
- ✅ **Update**: Actualizar entidades existentes
- ✅ **Delete**: Eliminar entidades
- ✅ **Search**: Búsqueda por criterios múltiples
- ✅ **Count**: Contar entidades con filtros
- ✅ **Exists**: Verificar existencia de entidades

### **2. Repositorios Especializados**

#### **ClienteRepository**
- Búsqueda por sector e industria
- Clientes activos/inactivos
- Clientes con proyectos
- Búsqueda por información de contacto
- Resumen completo con estadísticas

#### **ProyectoRepository**
- Proyectos por cliente
- Proyectos por estado y prioridad
- Filtros por rango de fechas y presupuesto
- Detalles completos con relaciones
- Estadísticas generales

#### **CanalRepository**
- Canales por dispositivo y proyecto
- Validación de tipos de datos
- Validación de rangos (min/max)
- Información completa para validación
- Estadísticas por tipo de dato

#### **RegistroDatosRepository**
- Inserción con validación automática
- Validación de tipos según canal
- Validación de rangos configurados
- Metadatos enriquecidos automáticamente
- Consultas por canal y proyecto
- Estadísticas detalladas

## 🎯 **Validación Automática de Tipos**

### **Tipos de Datos Soportados**

| Tipo Canal | Valores Aceptados | Conversión Automática |
|------------|-------------------|----------------------|
| `int` | Enteros, strings numéricos | Conversión a `int` |
| `float` | Flotantes, strings numéricos | Conversión a `float` |
| `bool` | Booleanos, strings, números | Conversión a `bool` |
| `string` | Cualquier valor | Conversión a `str` |
| `json` | Diccionarios, JSON strings | Conversión a `dict` |
| `binary` | Cualquier valor | Conversión a `str` |
| `timestamp` | Datetime, strings de fecha | Conversión a `str` ISO |

### **Validación de Rangos**

```python
# Ejemplo de validación automática
canal_info = {
    'tipo': TipoDato.FLOAT,
    'rango_min': 0.0,
    'rango_max': 100.0
}

# Valor válido
resultado = canal_repo.validate_channel_value(canal_id, 50.5)
# ✅ {'valid': True, 'valor_validado': 50.5, ...}

# Valor fuera de rango
resultado = canal_repo.validate_channel_value(canal_id, 150.0)
# ❌ {'valid': False, 'error': 'Valor 150.0 está por encima del rango máximo 100.0', ...}
```

### **Metadatos Enriquecidos**

Cada registro se enriquece automáticamente con:

```json
{
    "canal_nombre": "Temperatura_Sensor_1",
    "tipo_dato": "float",
    "unidad_medida": "°C",
    "proyecto_id": "uuid-proyecto",
    "unidad_id": "uuid-unidad",
    "dispositivo_id": "uuid-dispositivo",
    "proyecto_nombre": "Monitoreo Industrial",
    "unidad_nombre": "Planta Principal",
    "timestamp_insertion": "2025-08-16T00:00:00",
    "validated": true,
    "qos": 1,
    "ip": "192.168.1.100",
    "source": "demo_device"
}
```

## 🚀 **Uso de los Repositorios**

### **Inicialización**

```python
from iot_middleware.storage.db_handler import DatabaseHandler
from iot_middleware.storage.repositories import (
    ClienteRepository,
    ProyectoRepository,
    CanalRepository,
    RegistroDatosRepository
)

# Inicializar conexión
db = DatabaseHandler(config['postgresql'])

# Crear repositorios
cliente_repo = ClienteRepository(db)
proyecto_repo = ProyectoRepository(db)
canal_repo = CanalRepository(db)
registro_repo = RegistroDatosRepository(db)
```

### **Operaciones CRUD Básicas**

```python
# Crear
cliente = cliente_repo.create({
    'nombre': 'Nuevo Cliente',
    'sector': 'Industrial',
    'contacto_principal': {'email': 'cliente@example.com'}
})

# Leer
cliente = cliente_repo.get_by_id(cliente_id)
clientes_activos = cliente_repo.get_active_clients()

# Actualizar
cliente_actualizado = cliente_repo.update(cliente_id, {
    'sector': 'Tecnología Industrial'
})

# Eliminar
eliminado = cliente_repo.delete(cliente_id)
```

### **Inserción con Validación Automática**

```python
# El repositorio valida automáticamente el tipo y rango
registro = registro_repo.insert_record(
    canal_id='uuid-canal',
    valor=25.5,  # Se valida según el tipo del canal
    calidad=CalidadDato.OK,
    metadata={'source': 'sensor_1'},
    qos=1,
    ip='192.168.1.100'
)

if registro:
    print(f"✅ Registro creado: {registro.id}")
else:
    print("❌ Error de validación")
```

### **Validación Manual de Canales**

```python
# Validar valor antes de insertar
resultado = canal_repo.validate_channel_value(canal_id, valor)

if resultado['valid']:
    print(f"✅ Valor válido: {resultado['valor_validado']}")
    print(f"   Tipo convertido: {resultado['tipo_convertido']}")
    print(f"   Unidad: {resultado['unidad_medida']}")
else:
    print(f"❌ Error: {resultado['error']}")
```

## 📊 **Consultas Avanzadas**

### **Búsqueda por Criterios**

```python
# Buscar proyectos por múltiples criterios
proyectos = proyecto_repo.find_by_criteria({
    'estado': 'activo',
    'cliente_id': cliente_id,
    'activo': True
})

# Búsqueda de texto
clientes = cliente_repo.search_clients('tecnología')
proyectos = proyecto_repo.search_projects('monitoreo')
```

### **Consultas con Relaciones**

```python
# Obtener canales de un proyecto
canales = canal_repo.get_channels_by_project(proyecto_id)

# Obtener registros de un proyecto
registros = registro_repo.get_records_by_project(proyecto_id)

# Obtener detalles completos
detalles = proyecto_repo.get_project_details(proyecto_id)
```

### **Estadísticas y Resúmenes**

```python
# Resumen general de proyectos
resumen_proyectos = proyecto_repo.get_projects_summary()

# Estadísticas de canales
stats_canales = canal_repo.get_channels_summary()

# Estadísticas de registros por canal
stats_registros = registro_repo.get_statistics_by_canal(canal_id)
```

## 🧪 **Ejemplo de Uso Completo**

### **Ejecutar la Demostración**

```bash
# Desde el directorio raíz del proyecto
python examples/crud_validation_example.py examples/config_partitioning.yaml
```

### **Flujo de Trabajo Típico**

```python
# 1. Crear cliente
cliente = cliente_repo.create(cliente_data)
cliente_id = str(cliente.id)

# 2. Crear proyecto
proyecto = proyecto_repo.create({
    'cliente_id': cliente_id,
    'nombre': 'Proyecto IoT',
    'estado': 'planificado'
})
proyecto_id = str(proyecto.id)

# 3. Validar canal
resultado = canal_repo.validate_channel_value(canal_id, valor_sensor)
if resultado['valid']:
    # 4. Insertar registro con validación automática
    registro = registro_repo.insert_record(
        canal_id=canal_id,
        valor=valor_sensor,
        metadata={'source': 'sensor_1'}
    )
```

## 🔍 **Manejo de Errores**

### **Tipos de Errores**

- **ValidationError**: Error de validación de tipos o rangos
- **SQLAlchemyError**: Error de base de datos
- **NotFoundError**: Entidad no encontrada
- **ConstraintError**: Violación de restricciones

### **Logging Automático**

Todos los repositorios incluyen logging automático:

```python
logger.info(f"Entidad {table_name} creada exitosamente: {entity_id}")
logger.error(f"Error al crear entidad {table_name}: {e}")
logger.warning(f"Entidad {table_name} no encontrada para actualizar: {entity_id}")
```

## 📈 **Rendimiento y Optimización**

### **Características de Rendimiento**

- **Lazy Loading**: Las relaciones se cargan solo cuando se necesitan
- **Batch Operations**: Operaciones en lote para múltiples entidades
- **Connection Pooling**: Pool de conexiones reutilizable
- **Query Optimization**: Consultas optimizadas con JOINs apropiados

### **Índices Recomendados**

```sql
-- Para búsquedas por criterios comunes
CREATE INDEX idx_clientes_sector ON iot_schema.clientes(sector);
CREATE INDEX idx_proyectos_cliente_estado ON iot_schema.proyectos(cliente_id, estado);
CREATE INDEX idx_canales_dispositivo_tipo ON iot_schema.canales(dispositivo_id, tipo);

-- Para validación de rangos
CREATE INDEX idx_canales_rango ON iot_schema.canales(rango_min, rango_max);
```

## 🚨 **Consideraciones de Seguridad**

### **Validación de Entrada**

- Todos los valores se validan antes de la inserción
- Conversión segura de tipos de datos
- Validación de rangos numéricos
- Sanitización de metadatos JSON

### **Control de Acceso**

- Los repositorios no implementan control de acceso (se debe implementar en la capa de servicios)
- Validación de datos a nivel de repositorio
- Logging de todas las operaciones para auditoría

## 🔮 **Próximas Mejoras**

### **Funcionalidades Planificadas**

- [ ] **Cache Layer**: Implementar caché para consultas frecuentes
- [ ] **Async Support**: Soporte para operaciones asíncronas
- [ ] **Bulk Operations**: Operaciones en lote para mejor rendimiento
- [ ] **Soft Delete**: Eliminación lógica en lugar de física
- [ ] **Audit Trail**: Seguimiento completo de cambios
- [ ] **Data Export**: Exportación de datos en múltiples formatos

### **Optimizaciones de Rendimiento**

- [ ] **Query Caching**: Cache de consultas SQL frecuentes
- [ ] **Connection Pooling**: Mejoras en el pool de conexiones
- [ ] **Index Optimization**: Optimización automática de índices
- [ ] **Query Analysis**: Análisis de rendimiento de consultas

## 📚 **Documentación Adicional**

- [README.md](../../README.md) - Documentación principal del proyecto
- [README_PARTITIONING.md](README_PARTITIONING.md) - Sistema de particiones
- [examples/](examples/) - Ejemplos de uso
- [tests/](tests/) - Tests unitarios y de integración

## 🤝 **Contribución**

Para contribuir al desarrollo de esta capa CRUD:

1. **Fork** el repositorio
2. **Crea** una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/nueva-funcionalidad`)
5. **Crea** un Pull Request

## 📄 **Licencia**

Este proyecto está bajo la licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

**🎯 La capa CRUD está completamente implementada y lista para uso en producción!**
