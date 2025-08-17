# API REST para Consulta de Datos de Sensores - IoT Middleware

## Descripción

La API REST del IoT Middleware proporciona endpoints para consultar datos de sensores almacenados en la base de datos. Permite filtrar por tópico, rango de fechas, calidad de datos y otros parámetros, retornando los resultados en formato JSON estándar con paginación y metadatos.

## Características Principales

### 🔍 **Consulta de Datos**
- **Endpoint principal** `GET /data` para consultar datos de sensores
- **Filtros avanzados** por tópico, fechas, calidad y estado
- **Paginación completa** con límites configurables
- **Ordenamiento** por timestamp descendente (más reciente primero)

### 📡 **Filtros por Tópico**
- **Sintaxis de comodines** usando `+` para cualquier valor
- **Ejemplo**: `iot/proyecto_001/+/+/+/canal_temperatura`
- **Mapeo automático** a entidades de base de datos
- **Búsqueda eficiente** con índices optimizados

### 📅 **Filtros por Fecha**
- **Formato ISO 8601** para fechas (ej: `2024-01-15T10:30:00Z`)
- **Rangos flexibles** desde/hasta
- **Validación automática** de fechas
- **Zona horaria UTC** por defecto

### 🛡️ **Seguridad y Auditoría**
- **Auditoría automática** de todas las consultas
- **Sanitización** de parámetros de entrada
- **Manejo robusto** de errores
- **Logging estructurado** para monitoreo

## Endpoints Disponibles

### 1. **GET /** - Información de la API
```http
GET /
```
**Respuesta:**
```json
{
  "message": "IoT Middleware API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

### 2. **GET /health** - Estado de Salud
```http
GET /health
```
**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:35:00Z",
  "version": "1.0.0",
  "database_status": "healthy",
  "uptime_seconds": 3600
}
```

### 3. **GET /data** - Consulta de Datos de Sensores
```http
GET /data?topic=iot/proyecto_001/+/+/+/canal_temperatura&fecha_desde=2024-01-15T00:00:00Z&limit=100
```

**Parámetros de Query:**
- `topic` (opcional): Filtro de tópico con comodines
- `fecha_desde` (opcional): Fecha desde (ISO 8601)
- `fecha_hasta` (opcional): Fecha hasta (ISO 8601)
- `limit` (opcional): Número máximo de registros (1-1000, default: 100)
- `offset` (opcional): Número de registros a omitir (default: 0)
- `calidad` (opcional): Filtro por calidad (OK, WARNING, ERROR)
- `procesado` (opcional): Filtro por estado de procesamiento (true/false)
- `validado` (opcional): Filtro por estado de validación (true/false)

**Respuesta:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "canal_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-01-15T10:30:00Z",
      "valor": 25.5,
      "tipo_valor": "numeric",
      "calidad": "OK",
      "calidad_porcentaje": 100,
      "topic": "iot/proyecto_001/unidad_001/dispositivo_001/canal_temperatura",
      "metadatos": {
        "unidad_medida": "celsius",
        "ubicacion": "sala_principal"
      },
      "procesado": true,
      "validado": true
    }
  ],
  "metadata": {
    "total_registros": 1,
    "filtros_aplicados": {
      "topic": "iot/proyecto_001/+/+/+/canal_temperatura",
      "fecha_desde": "2024-01-15T00:00:00Z",
      "fecha_hasta": null,
      "calidad": null,
      "procesado": null,
      "validado": null
    },
    "timestamp_consulta": "2024-01-15T10:35:00Z"
  },
  "pagination": {
    "pagina_actual": 1,
    "total_paginas": 1,
    "registros_por_pagina": 100,
    "total_registros": 1,
    "offset": 0
  }
}
```

### 4. **GET /data/{canal_id}** - Datos por Canal Específico
```http
GET /data/550e8400-e29b-41d4-a716-446655440000?limit=50
```

**Parámetros de Query:**
- `fecha_desde` (opcional): Fecha desde
- `fecha_hasta` (opcional): Fecha hasta
- `limit` (opcional): Número máximo de registros
- `offset` (opcional): Número de registros a omitir

### 5. **GET /topics** - Tópicos Disponibles
```http
GET /topics
```

**Respuesta:**
```json
{
  "success": true,
  "topics": [
    {
      "topic": "iot/proyecto_001/unidad_001/dispositivo_001/canal_temperatura",
      "canal_id": "550e8400-e29b-41d4-a716-446655440000",
      "proyecto": "proyecto_001",
      "unidad": "unidad_001",
      "dispositivo": "dispositivo_001",
      "canal": "canal_temperatura"
    }
  ],
  "total_topics": 1,
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### 6. **GET /stats** - Estadísticas de Datos
```http
GET /stats?topic=iot/proyecto_001/+/+/+/canal_temperatura
```

**Respuesta:**
```json
{
  "success": true,
  "stats": {
    "total_registros": 1000,
    "por_calidad": {
      "OK": 950,
      "WARNING": 40,
      "ERROR": 10
    },
    "por_tipo": {
      "numeric": 1000,
      "integer": 0,
      "boolean": 0,
      "text": 0,
      "json": 0
    },
    "procesamiento": {
      "total": 1000,
      "procesados": 950,
      "validados": 900,
      "porcentaje_procesados": 95.0,
      "porcentaje_validados": 90.0
    }
  },
  "filtros_aplicados": {
    "topic": "iot/proyecto_001/+/+/+/canal_temperatura",
    "fecha_desde": null,
    "fecha_hasta": null
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

## Sintaxis de Filtros de Tópico

### Comodines Disponibles
- `+` : Cualquier valor en esa posición
- `*` : No soportado (use `+` en su lugar)

### Ejemplos de Filtros

#### 1. **Tópico Específico**
```
iot/proyecto_001/unidad_001/dispositivo_001/canal_temperatura
```
Retorna solo datos del canal específico.

#### 2. **Cualquier Unidad**
```
iot/proyecto_001/+/dispositivo_001/canal_temperatura
```
Retorna datos de cualquier unidad del proyecto.

#### 3. **Cualquier Dispositivo**
```
iot/proyecto_001/unidad_001/+/canal_temperatura
```
Retorna datos de cualquier dispositivo de la unidad.

#### 4. **Cualquier Canal de Temperatura**
```
iot/proyecto_001/+/+/+/canal_temperatura
```
Retorna datos de cualquier canal de temperatura del proyecto.

#### 5. **Todos los Canales de un Proyecto**
```
iot/proyecto_001/+/+/+/+
```
Retorna datos de todos los canales del proyecto.

## Formato de Respuesta Estándar

### Estructura General
Todas las respuestas siguen un formato estándar:

```json
{
  "success": boolean,
  "data": array | null,
  "metadata": object,
  "pagination": object | null,
  "error": string | null
}
```

### Campos de Respuesta

#### `success`
- **Tipo**: `boolean`
- **Descripción**: Indica si la operación fue exitosa
- **Valores**: `true` para éxito, `false` para error

#### `data`
- **Tipo**: `array` o `null`
- **Descripción**: Array de registros de datos o `null` si hay error
- **Contenido**: Objetos con datos de sensores

#### `metadata`
- **Tipo**: `object`
- **Descripción**: Metadatos de la consulta
- **Campos**:
  - `total_registros`: Número total de registros que coinciden con los filtros
  - `filtros_aplicados`: Filtros utilizados en la consulta
  - `timestamp_consulta`: Timestamp de cuando se ejecutó la consulta

#### `pagination`
- **Tipo**: `object` o `null`
- **Descripción**: Información de paginación
- **Campos**:
  - `pagina_actual`: Número de página actual
  - `total_paginas`: Número total de páginas
  - `registros_por_pagina`: Registros por página
  - `total_registros`: Total de registros
  - `offset`: Número de registros omitidos

#### `error`
- **Tipo**: `string` o `null`
- **Descripción**: Mensaje de error si `success` es `false`

## Estructura de Datos de Sensores

### Campos del Registro
```json
{
  "id": 1,
  "canal_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-15T10:30:00Z",
  "valor": 25.5,
  "tipo_valor": "numeric",
  "calidad": "OK",
  "calidad_porcentaje": 100,
  "topic": "iot/proyecto_001/unidad_001/dispositivo_001/canal_temperatura",
  "metadatos": {
    "unidad_medida": "celsius",
    "ubicacion": "sala_principal"
  },
  "procesado": true,
  "validado": true
}
```

### Tipos de Valor Soportados
- **`numeric`**: Valores numéricos de punto flotante
- **`integer`**: Valores enteros
- **`boolean`**: Valores booleanos (true/false)
- **`text`**: Valores de texto
- **`json`**: Valores JSON estructurados

### Calidades de Datos
- **`OK`**: Datos de buena calidad
- **`WARNING`**: Datos con advertencias
- **`ERROR`**: Datos con errores

## Paginación

### Parámetros de Paginación
- **`limit`**: Número máximo de registros por página (1-1000)
- **`offset`**: Número de registros a omitir

### Ejemplo de Paginación
```http
# Primera página (10 registros)
GET /data?limit=10&offset=0

# Segunda página (10 registros)
GET /data?limit=10&offset=10

# Tercera página (10 registros)
GET /data?limit=10&offset=20
```

### Información de Paginación
```json
{
  "pagination": {
    "pagina_actual": 2,
    "total_paginas": 5,
    "registros_por_pagina": 10,
    "total_registros": 50,
    "offset": 10
  }
}
```

## Filtros Avanzados

### Filtro por Calidad
```http
GET /data?calidad=OK&limit=100
```

### Filtro por Estado de Procesamiento
```http
GET /data?procesado=true&limit=100
```

### Filtro por Estado de Validación
```http
GET /data?validado=true&limit=100
```

### Combinación de Filtros
```http
GET /data?topic=iot/proyecto_001/+/+/+/canal_temperatura&fecha_desde=2024-01-15T00:00:00Z&calidad=OK&procesado=true&limit=50
```

## Manejo de Errores

### Códigos de Estado HTTP
- **`200 OK`**: Consulta exitosa
- **`400 Bad Request`**: Parámetros inválidos
- **`500 Internal Server Error`**: Error interno del servidor

### Respuesta de Error
```json
{
  "success": false,
  "error": "Formato de fecha inválido para fecha_desde: fecha-invalida. Use formato ISO 8601.",
  "error_code": "HTTP_400",
  "timestamp": "2024-01-15T10:35:00Z",
  "details": null
}
```

### Errores Comunes

#### 1. **Fecha Inválida**
```json
{
  "error": "Formato de fecha inválido para fecha_desde: fecha-invalida. Use formato ISO 8601."
}
```

#### 2. **Rango de Fechas Inválido**
```json
{
  "error": "fecha_hasta debe ser posterior a fecha_desde"
}
```

#### 3. **Calidad Inválida**
```json
{
  "error": "Calidad inválida: INVALID. Valores válidos: ['OK', 'WARNING', 'ERROR']"
}
```

#### 4. **Límite Excedido**
```json
{
  "error": "ensure this value is less than or equal to 1000"
}
```

## Instalación y Configuración

### Requisitos Previos
- Python 3.8+
- FastAPI
- Uvicorn
- Base de datos PostgreSQL configurada
- Dependencias del IoT Middleware

### Instalación de Dependencias
```bash
pip install fastapi uvicorn requests
```

### Configuración
La API se configura automáticamente usando la configuración del IoT Middleware:

```python
from iot_middleware.api.api import initialize_api

# Inicializar con configuración específica
initialize_api("config.yaml")

# O usar configuración por defecto
initialize_api()
```

### Ejecución
```bash
# Ejecutar directamente
python src/iot_middleware/api/api.py

# O con uvicorn
uvicorn iot_middleware.api.api:app --host 0.0.0.0 --port 8000 --reload
```

## Uso con Cliente HTTP

### Ejemplo con cURL
```bash
# Consulta básica
curl "http://localhost:8000/data?limit=10"

# Filtro por tópico
curl "http://localhost:8000/data?topic=iot/proyecto_001/+/+/+/canal_temperatura&limit=20"

# Filtro por fechas
curl "http://localhost:8000/data?fecha_desde=2024-01-15T00:00:00Z&fecha_hasta=2024-01-15T23:59:59Z&limit=50"

# Estadísticas
curl "http://localhost:8000/stats?topic=iot/proyecto_001/+/+/+/canal_temperatura"
```

### Ejemplo con Python Requests
```python
import requests

# Cliente de la API
client = requests.Session()
base_url = "http://localhost:8000"

# Consulta básica
response = client.get(f"{base_url}/data", params={
    'topic': 'iot/proyecto_001/+/+/+/canal_temperatura',
    'limit': 100,
    'fecha_desde': '2024-01-15T00:00:00Z'
})

if response.status_code == 200:
    data = response.json()
    print(f"Total de registros: {data['metadata']['total_registros']}")
    print(f"Registros retornados: {len(data['data'])}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

## Monitoreo y Logging

### Logs de la API
La API genera logs estructurados para monitoreo:

```
2024-01-15 10:35:00 - iot_middleware.api.api - INFO - 🚀 Iniciando IoT Middleware API...
2024-01-15 10:35:01 - iot_middleware.api.api - INFO - ✅ Base de datos inicializada
2024-01-15 10:35:01 - iot_middleware.api.api - INFO - ✅ Servicio de auditoría inicializado
2024-01-15 10:35:01 - iot_middleware.api.api - INFO - 🚀 API inicializada exitosamente
```

### Métricas Disponibles
- **Total de consultas** por endpoint
- **Tiempo de respuesta** promedio
- **Errores** por tipo
- **Uso de filtros** más comunes

## Auditoría

### Registro Automático
Todas las consultas se registran automáticamente en la tabla de auditoría:

```json
{
  "entidad": "api_query",
  "accion": "CONSULTAR",
  "cambios": {
    "antes": {},
    "despues": {
      "endpoint": "/data",
      "parametros": {
        "topic": "iot/proyecto_001/+/+/+/canal_temperatura",
        "limit": 100
      }
    }
  },
  "ip_origen": "192.168.1.100",
  "user_agent": "IoT-Middleware-API-Client/1.0"
}
```

### Información Auditada
- **Endpoint** consultado
- **Parámetros** de la consulta
- **IP de origen** del cliente
- **User-Agent** del cliente
- **Timestamp** de la consulta

## Performance y Optimización

### Índices de Base de Datos
La API utiliza índices optimizados para consultas rápidas:

```sql
-- Índices principales
CREATE INDEX idx_reg_datos_canal_ts ON iot_schema.registros_datos(canal_id, ts);
CREATE INDEX idx_reg_datos_ts ON iot_schema.registros_datos(ts);
CREATE INDEX idx_reg_datos_calidad ON iot_schema.registros_datos(calidad);

-- Índices para filtros de tópico
CREATE INDEX idx_canales_dispositivo ON iot_schema.canales(dispositivo_id);
CREATE INDEX idx_dispositivos_unidad ON iot_schema.dispositivos(unidad_proyecto_id);
CREATE INDEX idx_unidades_proyecto ON iot_schema.unidades_proyecto(proyecto_id);
```

### Estrategias de Optimización
- **Lazy loading** de relaciones
- **Query optimization** con SQLAlchemy
- **Connection pooling** para base de datos
- **Caching** de consultas frecuentes

## Seguridad

### Validación de Entrada
- **Sanitización** de parámetros
- **Validación** de tipos de datos
- **Límites** en tamaños de consulta
- **Escape** de caracteres especiales

### Control de Acceso
- **Rate limiting** (configurable)
- **Autenticación** (preparado para implementar)
- **Autorización** por roles
- **Auditoría** completa de acceso

## Troubleshooting

### Problemas Comunes

#### 1. **API no responde**
```bash
# Verificar estado
curl http://localhost:8000/health

# Verificar logs
tail -f logs/api.log
```

#### 2. **Error de base de datos**
```bash
# Verificar conexión
psql -h localhost -U iot_user -d iot_middleware -c "SELECT 1"

# Verificar esquema
psql -h localhost -U iot_user -d iot_middleware -c "\dt iot_schema.*"
```

#### 3. **Consultas lentas**
```sql
-- Verificar índices
SELECT schemaname, tablename, indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'iot_schema';

-- Analizar consultas
EXPLAIN ANALYZE SELECT * FROM iot_schema.registros_datos 
WHERE ts >= '2024-01-15'::timestamp;
```

### Logs de Debug
```python
import logging
logging.getLogger('iot_middleware.api.api').setLevel(logging.DEBUG)
```

## Ejemplos de Uso

### Ejemplo 1: Dashboard de Temperatura
```python
import requests
from datetime import datetime, timedelta

# Obtener datos de temperatura del último día
fecha_hasta = datetime.now()
fecha_desde = fecha_hasta - timedelta(days=1)

response = requests.get("http://localhost:8000/data", params={
    'topic': 'iot/+/+/+/+/canal_temperatura',
    'fecha_desde': fecha_desde.isoformat(),
    'fecha_hasta': fecha_hasta.isoformat(),
    'limit': 1000
})

if response.status_code == 200:
    data = response.json()
    
    # Calcular estadísticas
    valores = [r['valor'] for r in data['data'] if r['valor'] is not None]
    if valores:
        temp_min = min(valores)
        temp_max = max(valores)
        temp_avg = sum(valores) / len(valores)
        
        print(f"Temperatura mínima: {temp_min}°C")
        print(f"Temperatura máxima: {temp_max}°C")
        print(f"Temperatura promedio: {temp_avg:.1f}°C")
```

### Ejemplo 2: Monitoreo de Calidad
```python
import requests

# Obtener estadísticas de calidad
response = requests.get("http://localhost:8000/stats")

if response.status_code == 200:
    stats = response.json()
    calidad_stats = stats['stats']['por_calidad']
    
    total = sum(calidad_stats.values())
    
    print("Estado de calidad de datos:")
    for calidad, count in calidad_stats.items():
        porcentaje = (count / total) * 100
        print(f"  {calidad}: {count} ({porcentaje:.1f}%)")
```

### Ejemplo 3: Exportación de Datos
```python
import requests
import csv
from datetime import datetime

# Obtener datos para exportar
response = requests.get("http://localhost:8000/data", params={
    'topic': 'iot/proyecto_001/+/+/+/canal_temperatura',
    'fecha_desde': '2024-01-01T00:00:00Z',
    'fecha_hasta': '2024-01-31T23:59:59Z',
    'limit': 10000
})

if response.status_code == 200:
    data = response.json()
    
    # Exportar a CSV
    with open('datos_temperatura.csv', 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'valor', 'calidad', 'topic', 'metadatos']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for registro in data['data']:
            writer.writerow({
                'timestamp': registro['timestamp'],
                'valor': registro['valor'],
                'calidad': registro['calidad'],
                'topic': registro['topic'],
                'metadatos': str(registro['metadatos'])
            })
    
    print(f"Datos exportados a datos_temperatura.csv")
```

## Contribución

### Guías de Desarrollo
1. **Fork** del repositorio
2. **Crear branch** para feature: `git checkout -b feature/nueva-funcionalidad-api`
3. **Commit** cambios: `git commit -am 'Agregar nueva funcionalidad a la API'`
4. **Push** al branch: `git push origin feature/nueva-funcionalidad-api`
5. **Crear Pull Request**

### Estándares de Código
- **PEP 8** para estilo de Python
- **Type hints** para todas las funciones
- **Docstrings** completos
- **Tests unitarios** para nueva funcionalidad
- **Logging** estructurado

## Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

### Canales de Soporte
- **Issues de GitHub**: Para bugs y feature requests
- **Discussions**: Para preguntas y discusiones
- **Wiki**: Documentación adicional
- **Email**: soporte@iot-middleware.com

### Comunidad
- **Slack**: #iot-middleware
- **Discord**: Servidor oficial
- **Meetups**: Eventos locales
- **Conferencias**: Presentaciones técnicas

---

**Nota**: Esta API REST es parte del ecosistema IoT Middleware. Para más información sobre otros componentes, consulta la [documentación principal](README.md).
