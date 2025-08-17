# Sistema de Particiones Mensuales - IoT Middleware

## Descripción General

El sistema de particiones mensuales implementa una estrategia de particionado automático para la tabla `registros_datos` del IoT Middleware. Este sistema mejora significativamente el rendimiento de consultas y la gestión de datos históricos mediante la división automática de datos por mes.

## Características Principales

### 🚀 **Creación Automática de Particiones**
- **Particionado por tiempo**: División automática de datos por mes (formato: `YYYY_MM`)
- **Creación proactiva**: Genera particiones para el mes actual y el siguiente
- **Trigger automático**: Crea particiones on-the-fly si no existen al insertar datos

### 📊 **Gestión Inteligente**
- **Tabla de control**: Seguimiento centralizado de todas las particiones
- **Estados de partición**: Activa, archivada, retrasada
- **Estadísticas en tiempo real**: Conteo de registros y tamaño de cada partición

### 🔧 **Mantenimiento Automatizado**
- **Limpieza inteligente**: Archiva particiones antiguas según política de retención
- **Monitoreo continuo**: Vista de monitoreo con estado operativo
- **Health checks**: Verificación automática de la salud del sistema

## Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                    Sistema de Particiones                   │
├─────────────────────────────────────────────────────────────┤
│  📅 Funciones SQL (PL/pgSQL)                               │
│  ├── fn_crear_particion_registros(fecha)                   │
│  ├── fn_crear_particiones_automaticas()                    │
│  ├── fn_validar_particion_registros()                      │
│  ├── fn_limpiar_particiones_antiguas(meses)                │
│  └── fn_estadisticas_particiones()                         │
├─────────────────────────────────────────────────────────────┤
│  🎯 Trigger Automático                                      │
│  └── tr_validar_particion_registros                        │
├─────────────────────────────────────────────────────────────┤
│  📋 Tabla de Control                                        │
│  └── control_particiones                                    │
├─────────────────────────────────────────────────────────────┤
│  👁️  Vistas de Monitoreo                                   │
│  └── v_monitoreo_particiones                               │
└─────────────────────────────────────────────────────────────┘
```

### Estructura de Particiones

```
registros_datos (tabla principal)
├── registros_datos_2025_01 (partición enero 2025)
├── registros_datos_2025_02 (partición febrero 2025)
├── registros_datos_2025_03 (partición marzo 2025)
├── registros_datos_2025_04 (partición abril 2025)
└── ... (particiones futuras)
```

## Instalación y Configuración

### 1. Aplicar Migración Alembic

```bash
# Aplicar la migración del sistema de particiones
alembic upgrade 0002
```

### 2. Verificar Instalación

```bash
# Verificar que el sistema esté funcionando
python scripts/partitions.py health
```

### 3. Crear Particiones Iniciales

```bash
# Crear particiones para el mes actual y siguiente
python scripts/partitions.py create
```

## Uso del Sistema

### Script de Gestión (`scripts/partitions.py`)

#### Comandos Disponibles

```bash
# Crear particiones automáticamente
python scripts/partitions.py create [--months-ahead N]

# Listar todas las particiones
python scripts/partitions.py list

# Mostrar estadísticas detalladas
python scripts/partitions.py stats

# Limpiar particiones antiguas
python scripts/partitions.py cleanup [--retention-months N]

# Monitorear estado del sistema
python scripts/partitions.py monitor

# Verificar salud del sistema
python scripts/partitions.py health
```

#### Opciones de Configuración

```bash
# Especificar archivo de configuración
python scripts/partitions.py create --config /path/to/config.yaml

# Crear particiones para más meses futuros
python scripts/partitions.py create --months-ahead 3

# Configurar política de retención
python scripts/partitions.py cleanup --retention-months 24
```

### Ejemplo de Uso Completo

```bash
# 1. Verificar estado del sistema
python scripts/partitions.py health

# 2. Crear particiones para los próximos 2 meses
python scripts/partitions.py create --months-ahead 2

# 3. Verificar particiones creadas
python scripts/partitions.py list

# 4. Monitorear estado
python scripts/partitions.py monitor

# 5. Limpiar particiones de más de 18 meses
python scripts/partitions.py cleanup --retention-months 18
```

## Funciones SQL Disponibles

### `fn_crear_particion_registros(fecha DATE)`

Crea una partición específica para un mes dado.

```sql
-- Crear partición para enero 2025
SELECT iot_schema.fn_crear_particion_registros('2025-01-01');

-- Resultado: "Partición registros_datos_2025_01 creada exitosamente para el rango 2025-01-01 a 2025-01-31"
```

### `fn_crear_particiones_automaticas()`

Crea automáticamente particiones para el mes actual y siguiente.

```sql
SELECT iot_schema.fn_crear_particiones_automaticas();
```

### `fn_estadisticas_particiones()`

Retorna estadísticas detalladas de todas las particiones.

```sql
SELECT * FROM iot_schema.fn_estadisticas_particiones();
```

### `fn_limpiar_particiones_antiguas(meses_retener INTEGER)`

Archiva particiones más antiguas que el número de meses especificado.

```sql
-- Mantener solo los últimos 12 meses
SELECT iot_schema.fn_limpiar_particiones_antiguas(12);
```

## Vistas de Monitoreo

### `v_monitoreo_particiones`

Vista principal para monitorear el estado del sistema de particiones.

```sql
SELECT * FROM iot_schema.v_monitoreo_particiones;
```

**Campos disponibles:**
- `nombre_particion`: Nombre de la partición
- `fecha_inicio/fecha_fin`: Rango temporal de la partición
- `estado`: Estado actual (activa, archivada)
- `registros_totales`: Número de registros en la partición
- `tamaño_mb`: Tamaño en MB de la partición
- `estado_operativo`: Estado operativo (actual, futura, retrasada)

## Configuración del Sistema

### Parámetros de Configuración

El sistema se configura a través de la tabla `config_middleware`:

```sql
-- Ver configuración actual
SELECT valor FROM iot_schema.config_middleware 
WHERE clave = 'partitioning.auto_create';

-- Configuración por defecto:
{
  "enabled": true,
  "months_ahead": 1,
  "retention_months": 12
}
```

### Personalización de Configuración

```sql
-- Modificar configuración
UPDATE iot_schema.config_middleware 
SET valor = '{"enabled": true, "months_ahead": 3, "retention_months": 24}'
WHERE clave = 'partitioning.auto_create';
```

## Beneficios del Particionado

### 🚀 **Rendimiento**
- **Consultas más rápidas**: Filtrado automático por partición relevante
- **Índices optimizados**: Cada partición tiene sus propios índices
- **Paralelización**: Consultas pueden ejecutarse en paralelo en múltiples particiones

### 💾 **Gestión de Datos**
- **Mantenimiento simplificado**: Operaciones por partición individual
- **Backup granular**: Backup de particiones específicas por mes
- **Recuperación selectiva**: Restauración de períodos específicos

### 📈 **Escalabilidad**
- **Crecimiento horizontal**: Nuevas particiones se crean automáticamente
- **Balanceo de carga**: Distribución de datos en múltiples archivos
- **Optimización de almacenamiento**: Archivo de particiones antiguas

## Ejemplos de Consultas

### Consulta en Partición Específica

```sql
-- Consulta directa en partición de enero 2025
SELECT COUNT(*), AVG(valor_num)
FROM iot_schema.registros_datos_2025_01
WHERE canal_id = 'uuid-del-canal'
  AND ts >= '2025-01-01' AND ts < '2025-02-01';
```

### Consulta en Tabla Principal (Particionado Automático)

```sql
-- PostgreSQL selecciona automáticamente las particiones relevantes
SELECT COUNT(*), AVG(valor_num)
FROM iot_schema.registros_datos
WHERE canal_id = 'uuid-del-canal'
  AND ts >= '2025-01-01' AND ts < '2025-02-01';
```

### Análisis de Tendencias por Mes

```sql
-- Análisis de tendencias mensuales
SELECT 
    TO_CHAR(ts, 'YYYY-MM') as mes,
    COUNT(*) as registros,
    AVG(valor_num) as promedio,
    MIN(valor_num) as minimo,
    MAX(valor_num) as maximo
FROM iot_schema.registros_datos
WHERE canal_id = 'uuid-del-canal'
  AND ts >= '2024-01-01'
GROUP BY TO_CHAR(ts, 'YYYY-MM')
ORDER BY mes;
```

## Mantenimiento y Monitoreo

### Tareas de Mantenimiento Recomendadas

#### Diario
```bash
# Verificar estado del sistema
python scripts/partitions.py health
```

#### Semanal
```bash
# Monitorear estado de particiones
python scripts/partitions.py monitor

# Ver estadísticas de uso
python scripts/partitions.py stats
```

#### Mensual
```bash
# Crear particiones para el mes siguiente
python scripts/partitions.py create --months-ahead 2

# Limpiar particiones antiguas
python scripts/partitions.py cleanup --retention-months 12
```

### Alertas y Monitoreo

El sistema proporciona indicadores de salud:

- 🟢 **Actual**: Partición del mes en curso
- 🟡 **Futura**: Partición del mes siguiente
- 🔴 **Retrasada**: Partición que debería estar activa pero no lo está

### Logs y Auditoría

```sql
-- Ver historial de creación de particiones
SELECT 
    nombre_particion,
    creada_en,
    estado,
    registros_totales
FROM iot_schema.control_particiones
ORDER BY creada_en DESC;
```

## Solución de Problemas

### Problemas Comunes

#### 1. Error: "Partición no existe"

```bash
# Verificar que el sistema esté funcionando
python scripts/partitions.py health

# Crear particiones manualmente
python scripts/partitions.py create
```

#### 2. Particiones no se crean automáticamente

```sql
-- Verificar configuración
SELECT valor FROM iot_schema.config_middleware 
WHERE clave = 'partitioning.auto_create';

-- Verificar trigger
SELECT * FROM information_schema.triggers 
WHERE trigger_name = 'tr_validar_particion_registros';
```

#### 3. Rendimiento degradado

```bash
# Verificar estadísticas de particiones
python scripts/partitions.py stats

# Limpiar particiones antiguas
python scripts/partitions.py cleanup
```

### Comandos de Diagnóstico

```bash
# Diagnóstico completo del sistema
python scripts/partitions.py health

# Verificar particiones específicas
python scripts/partitions.py list

# Monitoreo en tiempo real
python scripts/partitions.py monitor
```

## Integración con el Sistema

### Con DatabaseHandler

```python
from iot_middleware.storage.db_handler import DatabaseHandler

db = DatabaseHandler(config['database'])

# Crear partición manualmente
result = db.execute_query(
    "SELECT iot_schema.fn_crear_particion_registros(%s)",
    ('2025-05-01',)
)

# Ver estadísticas
stats = db.execute_query("SELECT * FROM iot_schema.fn_estadisticas_particiones()")
```

### Con Alembic

```python
# En migraciones futuras
def upgrade():
    # Crear particiones para fechas específicas
    op.execute("SELECT iot_schema.fn_crear_particion_registros('2025-06-01')")
    op.execute("SELECT iot_schema.fn_crear_particion_registros('2025-07-01')")
```

## Consideraciones de Seguridad

### Permisos de Base de Datos

El sistema requiere los siguientes permisos:

```sql
-- Para funciones de particionado
GRANT EXECUTE ON FUNCTION iot_schema.fn_crear_particion_registros(DATE) TO usuario_app;
GRANT EXECUTE ON FUNCTION iot_schema.fn_crear_particiones_automaticas() TO usuario_app;

-- Para tabla de control
GRANT SELECT, INSERT, UPDATE ON iot_schema.control_particiones TO usuario_app;

-- Para vistas de monitoreo
GRANT SELECT ON iot_schema.v_monitoreo_particiones TO usuario_app;
```

### Auditoría y Logging

```sql
-- Ver cambios en el sistema de particiones
SELECT 
    entidad,
    accion,
    cambios,
    ts
FROM iot_schema.auditoria
WHERE entidad LIKE '%particion%'
ORDER BY ts DESC;
```

## Roadmap y Mejoras Futuras

### Funcionalidades Planificadas

- [ ] **Particionado por hora**: Para sistemas de alta frecuencia
- [ ] **Compresión automática**: Compresión de particiones antiguas
- [ ] **Replicación selectiva**: Replicación de particiones críticas
- [ ] **Métricas avanzadas**: KPIs de rendimiento del sistema
- [ ] **Alertas automáticas**: Notificaciones de problemas

### Optimizaciones Técnicas

- [ ] **Particionado paralelo**: Creación concurrente de múltiples particiones
- [ ] **Balanceo inteligente**: Distribución automática de carga
- [ ] **Cache de metadatos**: Cache de información de particiones
- [ ] **Compresión adaptativa**: Compresión basada en patrones de acceso

## Contribución y Soporte

### Reportar Problemas

Para reportar problemas o solicitar mejoras:

1. Verificar que el problema no esté documentado
2. Ejecutar `python scripts/partitions.py health` para diagnóstico
3. Incluir logs de error y configuración del sistema
4. Describir pasos para reproducir el problema

### Desarrollo

Para contribuir al desarrollo:

1. Revisar el código en `scripts/partitions.py`
2. Probar cambios con `python scripts/partitions.py health`
3. Verificar compatibilidad con versiones anteriores
4. Documentar nuevas funcionalidades

## Referencias y Recursos

### Documentación Relacionada

- [README Principal](../README.md)
- [README de Base de Datos](README_POSTGRESQL.md)
- [Documentación de Alembic](https://alembic.sqlalchemy.org/)

### Recursos Externos

- [PostgreSQL Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [PL/pgSQL Functions](https://www.postgresql.org/docs/current/plpgsql.html)
- [Database Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)

---

**Nota**: Este sistema de particiones está diseñado para funcionar con PostgreSQL 12+ y requiere la migración Alembic 0002 para su funcionamiento completo.
