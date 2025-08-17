# Modelos SQLAlchemy - IoT Middleware

## 📋 Descripción General

Este módulo contiene todos los modelos SQLAlchemy que reflejan la estructura de la base de datos PostgreSQL del sistema IoT Middleware. Los modelos están diseñados para trabajar con FastAPI y proporcionan una interfaz Python nativa para todas las entidades del sistema.

## 🏗️ Arquitectura

### Estructura del Módulo
```
models/
├── __init__.py          # Exporta todos los modelos y enums
├── base.py              # Configuración base de SQLAlchemy
├── enums.py             # Enums nativos de PostgreSQL
├── entities.py          # Modelos de entidades principales
└── README.md            # Esta documentación
```

### Características Principales
- ✅ **Enums nativos**: Sincronizados con tipos PostgreSQL
- 🔗 **Relaciones completas**: Con backrefs y cascadas
- 🆔 **UUIDs**: Claves primarias usando UUID v4
- 📊 **JSONB**: Campos flexibles para metadatos
- 🗄️ **Esquema**: Todos los modelos en `iot_schema`
- 🔍 **Índices**: Optimizados para consultas frecuentes

## 🔧 Enums Nativos

### EstadoProyecto
```python
class EstadoProyecto(Enum):
    PLANIFICADO = 'planificado'
    ACTIVO = 'activo'
    PAUSADO = 'pausado'
    CERRADO = 'cerrado'
    CANCELADO = 'cancelado'
```

### ProtocoloComunicacion
```python
class ProtocoloComunicacion(Enum):
    MQTT = 'MQTT'
    BLE = 'BLE'
    HTTP = 'HTTP'
    RF = 'RF'
    LORA = 'LoRa'
    MODBUS = 'Modbus'
    OPC_UA = 'OPC_UA'
    OTRO = 'Otro'
```

### TipoDato
```python
class TipoDato(Enum):
    INT = 'int'
    FLOAT = 'float'
    BOOL = 'bool'
    STRING = 'string'
    JSON = 'json'
    BINARY = 'binary'
    TIMESTAMP = 'timestamp'
```

### RolSistema
```python
class RolSistema(Enum):
    ADMIN = 'admin'
    TECNICO = 'tecnico'
    CLIENTE = 'cliente'
    LECTURA = 'lectura'
    SUPERVISOR = 'supervisor'
```

### CalidadDato (OPC UA)
```python
class CalidadDato(Enum):
    OK = 'OK'
    GOOD = 'GOOD'
    UNCERTAIN = 'UNCERTAIN'
    BAD = 'BAD'
    SUSPECTO = 'SUSPECTO'
    MALO = 'MALO'
```

### SeveridadEvento
```python
class SeveridadEvento(Enum):
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'
    FATAL = 'fatal'
```

### EstadoDispositivo
```python
class EstadoDispositivo(Enum):
    ACTIVO = 'activo'
    INACTIVO = 'inactivo'
    MANTENIMIENTO = 'mantenimiento'
    ERROR = 'error'
    DESCONECTADO = 'desconectado'
```

## 🗄️ Modelos de Entidades

### 1. Cliente
**Propósito**: Organizaciones o personas que utilizan el sistema

**Campos principales**:
- `id`: UUID único del cliente
- `nombre`: Nombre de la organización
- `sector` / `industria`: Clasificación del cliente
- `contacto_principal`: JSONB con información del contacto principal
- `contactos_adicionales`: Array JSONB de contactos secundarios
- `direccion`: JSONB con información de ubicación
- `configuracion`: Configuraciones específicas del cliente

**Relaciones**:
- `proyectos`: Lista de proyectos del cliente
- `usuarios_scope`: Usuarios con acceso al cliente

**Ejemplo de uso**:
```python
cliente = Cliente(
    nombre="Industrias Tecnológicas S.A.",
    sector="Tecnología",
    contacto_principal={
        "nombre": "Ana Martínez",
        "email": "ana@indutech.com",
        "telefono": "+34 91 123 4567"
    }
)
```

### 2. Proyecto
**Propósito**: Proyectos asociados a clientes

**Campos principales**:
- `id`: UUID único del proyecto
- `cliente_id`: Referencia al cliente
- `nombre` / `descripcion`: Información del proyecto
- `estado`: Enum de estado del proyecto
- `fecha_inicio` / `fecha_fin`: Cronograma del proyecto
- `presupuesto` / `prioridad`: Información de gestión

**Relaciones**:
- `cliente`: Cliente al que pertenece
- `unidades`: Unidades del proyecto
- `dispositivos_proyecto`: Dispositivos asignados
- `eventos_alarmas`: Eventos del proyecto

**Ejemplo de uso**:
```python
proyecto = Proyecto(
    nombre="Monitoreo Inteligente de Edificios",
    descripcion="Sistema IoT para monitoreo de temperatura y humedad",
    estado=EstadoProyecto.ACTIVO,
    fecha_inicio=datetime.now().date(),
    prioridad=3
)
```

### 3. UnidadProyecto
**Propósito**: Subdivisiones físicas y lógicas de proyectos

**Campos principales**:
- `id`: UUID único de la unidad
- `proyecto_id`: Referencia al proyecto
- `nombre` / `descripcion`: Información de la unidad
- `ubicacion`: Descripción textual de la ubicación
- `responsable`: Persona responsable de la unidad
- `lat` / `lon`: Coordenadas GPS (opcional)

**Relaciones**:
- `proyecto`: Proyecto al que pertenece
- `sesiones`: Sesiones de la unidad
- `dispositivos_proyecto`: Dispositivos en la unidad

### 4. Sesion
**Propósito**: Períodos de recolección de datos

**Campos principales**:
- `id`: UUID único de la sesión
- `unidad_id`: Referencia a la unidad
- `nombre` / `descripcion`: Información de la sesión
- `inicio` / `fin`: Período de la sesión
- `estado`: Estado de la sesión
- `observaciones`: Notas adicionales

**Relaciones**:
- `unidad`: Unidad del proyecto

### 5. Dispositivo
**Propósito**: Catálogo de dispositivos IoT

**Campos principales**:
- `id`: UUID único del dispositivo
- `tipo`: Categoría del dispositivo
- `fabricante` / `modelo`: Información del fabricante
- `identificador_unico`: MAC, Serial, UUID del equipo
- `protocolo`: Protocolo de comunicación
- `vida_util_meses`: Tiempo estimado de vida útil
- `especificaciones_tecnicas`: JSONB con datasheet completo

**Relaciones**:
- `canales`: Canales/sensores del dispositivo
- `dispositivos_proyecto`: Asignaciones a proyectos
- `eventos_alarmas`: Eventos relacionados

**Ejemplo de uso**:
```python
dispositivo = Dispositivo(
    tipo="sensor",
    fabricante="Sensirion",
    modelo="SHT30",
    identificador_unico="SENSOR_TEMP_001",
    protocolo=ProtocoloComunicacion.MQTT,
    vida_util_meses=60,
    especificaciones_tecnicas={
        "temperatura": {"rango": [-40, 125], "precision": "±0.2°C"},
        "humedad": {"rango": [0, 100], "precision": "±2%RH"}
    }
)
```

### 6. DispositivoProyecto
**Propósito**: Asignación de dispositivos a proyectos específicos

**Campos principales**:
- `id`: UUID único de la asignación
- `proyecto_id`: Referencia al proyecto
- `dispositivo_id`: Referencia al dispositivo
- `unidad_id`: Referencia a la unidad (opcional)
- `nombre_personalizado`: Nombre específico en el proyecto
- `fecha_instalacion` / `fecha_retiro`: Ciclo de vida
- `estado`: Estado actual del dispositivo

**Relaciones**:
- `proyecto`: Proyecto de la asignación
- `dispositivo`: Dispositivo asignado
- `unidad`: Unidad donde está ubicado

### 7. Canal
**Propósito**: Sensores o canales de datos de dispositivos

**Campos principales**:
- `id`: UUID único del canal
- `dispositivo_id`: Referencia al dispositivo
- `nombre` / `etiqueta`: Identificación del canal
- `unidad_medida`: Unidad de medida (°C, %RH, hPa, etc.)
- `tipo`: Tipo de dato (int, float, bool, string, json, etc.)
- `rango_min` / `rango_max`: Rango esperado de valores
- `precision_valor`: Número de decimales
- `frecuencia_muestreo`: Frecuencia en segundos
- `umbral_alto` / `umbral_bajo`: Umbrales para alarmas

**Relaciones**:
- `dispositivo`: Dispositivo al que pertenece
- `registros_datos`: Datos capturados por el canal
- `eventos_alarmas`: Eventos relacionados

**Ejemplo de uso**:
```python
canal = Canal(
    nombre="temperature",
    etiqueta="Temperatura Ambiente",
    tipo=TipoDato.FLOAT,
    unidad_medida="°C",
    rango_min=-40.0,
    rango_max=125.0,
    precision_valor=1,
    frecuencia_muestreo=60,
    umbral_alto=30.0,
    umbral_bajo=15.0,
    metadatos={
        "topic": "iot/sensor_001/temperature",
        "qos": 1,
        "retain": False
    }
)
```

### 8. RegistroDatos
**Propósito**: Datos capturados por los canales (particionado por tiempo)

**Campos principales**:
- `id`: ID secuencial único
- `canal_id`: Referencia al canal
- `ts`: Timestamp de la medición
- `valor_num` / `valor_int` / `valor_bool` / `valor_text` / `valor_json`: Valor según tipo
- `calidad`: Calidad del dato (estándar OPC UA)
- `calidad_porcentaje`: Porcentaje de calidad (0-100)
- `metadata`: JSONB con información adicional
- `procesado` / `validado`: Estados del procesamiento

**Relaciones**:
- `canal`: Canal que generó el dato

**Nota**: Este modelo está diseñado para particionamiento temporal mensual.

### 9. EventoAlarma
**Propósito**: Eventos y alarmas del sistema

**Campos principales**:
- `id`: UUID único del evento
- `proyecto_id`: Referencia al proyecto
- `canal_id` / `unidad_id` / `dispositivo_id`: Referencias opcionales
- `ts`: Timestamp del evento
- `severidad`: Nivel de severidad
- `titulo` / `descripcion`: Información del evento
- `detalles`: JSONB con valores que dispararon el evento
- `estado`: Estado del evento
- `reconocida_por` / `resuelta_por`: Usuarios que gestionan el evento

**Relaciones**:
- `proyecto`: Proyecto del evento
- `canal`: Canal relacionado (opcional)
- `unidad`: Unidad relacionada (opcional)
- `dispositivo`: Dispositivo relacionado (opcional)

### 10. Usuario
**Propósito**: Cuentas de usuario del sistema

**Campos principales**:
- `id`: UUID único del usuario
- `email`: Email único del usuario
- `nombre` / `apellido`: Información personal
- `password_hash`: Hash de la contraseña (encriptada)
- `rol`: Rol del sistema
- `activo`: Estado de la cuenta
- `configuracion`: JSONB con preferencias del usuario

**Relaciones**:
- `usuarios_scope`: Alcance del usuario en clientes/proyectos
- `configuraciones_creadas`: Configuraciones creadas por el usuario
- `configuraciones_actualizadas`: Configuraciones actualizadas por el usuario

### 11. UsuarioScope
**Propósito**: Alcance de usuarios en clientes/proyectos

**Campos principales**:
- `id`: UUID único del scope
- `usuario_id`: Referencia al usuario
- `cliente_id` / `proyecto_id`: Referencias opcionales
- `permisos`: JSONB con permisos específicos en este scope
- `activo`: Estado del scope

**Relaciones**:
- `usuario`: Usuario del scope
- `cliente`: Cliente del scope (opcional)
- `proyecto`: Proyecto del scope (opcional)

### 12. ConfigMiddleware
**Propósito**: Configuraciones del middleware IoT

**Campos principales**:
- `id`: UUID único de la configuración
- `clave`: Clave de la configuración
- `valor`: JSONB con el valor de la configuración
- `descripcion`: Descripción de la configuración
- `categoria`: Agrupación de configuraciones
- `version`: Versión de la configuración
- `sensible`: Si la configuración contiene información sensible
- `vigente`: Si la configuración está activa

**Relaciones**:
- `creado_por_usuario`: Usuario que creó la configuración
- `actualizado_por_usuario`: Usuario que actualizó la configuración

### 13. Auditoria
**Propósito**: Registro de cambios para auditoría

**Campos principales**:
- `id`: ID secuencial único
- `usuario_id`: Usuario que realizó el cambio
- `entidad`: Nombre de la tabla modificada
- `entidad_id`: ID del registro modificado
- `accion`: Tipo de acción (INSERT, UPDATE, DELETE)
- `cambios`: JSONB con diff de los cambios
- `ip_origen` / `user_agent`: Información del cliente
- `ts`: Timestamp del cambio

**Relaciones**:
- `usuario`: Usuario que realizó el cambio

## 🔗 Relaciones y Cascadas

### Relaciones Principales
- **Cliente → Proyectos**: `cascade="all, delete-orphan"`
- **Proyecto → Unidades**: `cascade="all, delete-orphan"`
- **Proyecto → DispositivosProyecto**: `cascade="all, delete-orphan"`
- **Proyecto → EventosAlarmas**: `cascade="all, delete-orphan"`
- **Dispositivo → Canales**: `cascade="all, delete-orphan"`
- **Canal → RegistrosDatos**: `cascade="all, delete-orphan"`
- **Usuario → UsuariosScope**: `cascade="all, delete-orphan"`

### Backrefs Automáticos
- `cliente.proyectos` ↔ `proyecto.cliente`
- `proyecto.unidades` ↔ `unidad.proyecto`
- `proyecto.dispositivos_proyecto` ↔ `dispositivo_proyecto.proyecto`
- `dispositivo.canales` ↔ `canal.dispositivo`
- `canal.registros_datos` ↔ `registro.canal`

## 📊 Índices y Performance

### Índices Automáticos
- **Claves primarias**: UUID para entidades principales, compuesta para registros
- **Claves foráneas**: Para todas las relaciones
- **Campos de búsqueda**: Email, nombres, estados
- **Campos temporales**: Timestamps para consultas históricas
- **JSONB**: Índices GIN para búsquedas en metadatos

### Optimizaciones
- **Particionamiento**: Registros de datos por tiempo
- **Índices compuestos**: Para consultas frecuentes
- **Índices GIN**: Para búsquedas en campos JSONB
- **Relaciones lazy**: Carga bajo demanda para optimizar memoria

## 🚀 Uso con FastAPI

### Configuración de Base de Datos
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from iot_middleware.models import Base

# Crear engine
engine = create_engine(
    "postgresql://user:password@localhost:5432/iot_middleware",
    echo=True
)

# Crear tablas
Base.metadata.create_all(engine)

# Crear session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### Uso en Endpoints
```python
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from iot_middleware.models import Cliente, Proyecto

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/clientes/{cliente_id}/proyectos")
def get_proyectos_cliente(cliente_id: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return cliente.proyectos
```

### Creación de Entidades
```python
@app.post("/clientes/")
def crear_cliente(cliente_data: dict, db: Session = Depends(get_db)):
    cliente = Cliente(**cliente_data)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente
```

## 🔧 Migraciones con Alembic

### Configuración
```bash
# Instalar Alembic
pip install alembic

# Inicializar (ya configurado)
alembic init alembic

# Crear migración
alembic revision --autogenerate -m "Descripción de cambios"

# Aplicar migración
alembic upgrade head

# Revertir migración
alembic downgrade -1
```

### Migración Inicial
Ya se ha creado la migración inicial (`0001_initial_schema.py`) que incluye:
- Creación del esquema `iot_schema`
- Creación de todos los tipos ENUM
- Creación de todas las tablas
- Creación de todos los índices
- Creación de vistas útiles
- Inserción de datos iniciales

## 🧪 Testing

### Script de Pruebas
```bash
# Ejecutar pruebas de modelos
python3 scripts/test_sqlalchemy_models.py
```

### Pruebas Incluidas
- ✅ Creación de modelos
- ✅ Valores de enums
- ✅ Atributos de modelos
- ✅ Relaciones entre modelos
- ✅ Metadatos de tablas
- ✅ Validación de modelos

## 📋 Requisitos

### Dependencias
```bash
pip install sqlalchemy psycopg2-binary alembic
```

### Extensiones PostgreSQL
- `uuid-ossp`: Para generación de UUIDs
- `pgcrypto`: Para encriptación de contraseñas

## 🔮 Próximos Pasos

### Funcionalidades Planificadas
- [ ] **Validación Pydantic**: Integración con FastAPI para validación automática
- [ ] **Métodos de negocio**: Funciones específicas para operaciones comunes
- [ ] **Eventos**: Hooks para auditoría automática
- [ ] **Cache**: Integración con Redis para consultas frecuentes
- [ ] **Soft deletes**: Marcado de registros como eliminados sin borrarlos

### Integración
- [ ] **Con FastAPI**: Endpoints REST completos
- [ ] **Con MQTT**: Inserción automática de datos
- [ ] **Con procesamiento**: Validación y normalización
- [ ] **Con dashboards**: Vistas optimizadas para visualización

---

**Nota**: Estos modelos están diseñados para ser escalables y mantenibles. Para implementaciones en producción, se recomienda revisar y ajustar los índices según los patrones de consulta específicos de cada instalación.
