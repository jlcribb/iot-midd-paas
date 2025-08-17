# Sistema de Auditoría - IoT Middleware

## Descripción

El sistema de auditoría del IoT Middleware es una utilidad completa que registra automáticamente todos los cambios realizados en entidades críticas del sistema. Cada cambio se estructura como `{antes: {}, despues: {}}` y se guarda con información completa del usuario e IP de origen.

## Características Principales

### 🔍 **Auditoría Automática**
- **Registro automático** de cambios en entidades críticas
- **Estructura de cambios** `{antes: {}, despues: {}}`
- **Contexto completo** (usuario, IP, timestamp, headers)
- **Sanitización automática** de datos sensibles

### 🏗️ **Entidades Auditadas**
- **config_middleware**: Configuraciones del sistema
- **canales**: Sensores y canales de datos
- **eventos_alarmas**: Eventos y alarmas del sistema
- **dispositivos**: Dispositivos IoT
- **proyectos**: Proyectos del sistema
- **usuarios**: Usuarios del sistema
- **clientes**: Clientes/organizaciones

### 🛡️ **Seguridad y Privacidad**
- **Sanitización automática** de contraseñas, tokens, claves
- **Filtrado de datos sensibles** en logs y reportes
- **Control de acceso** a registros de auditoría
- **Encriptación** de datos críticos

### 📊 **Reportes y Consultas**
- **Múltiples formatos**: JSON, CSV, HTML
- **Filtros avanzados** por entidad, usuario, fecha, acción
- **Estadísticas automáticas** de actividad
- **Exportación** de datos para análisis

## Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Aplicación    │    │   Servicio de    │    ┌   Base de      │
│   (API/CLI)    │───▶│   Auditoría      │───▶│   Datos        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Middleware    │    │   Decoradores    │    │   Context      │
│   FastAPI       │    │   Automáticos    │    │   Managers     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Instalación

### Requisitos Previos
- Python 3.8+
- Base de datos PostgreSQL con esquema `iot_schema`
- Tabla `auditoria` creada según el esquema

### Instalación de Dependencias
```bash
pip install -r requirements.txt
```

### Configuración de Base de Datos
```sql
-- Verificar que existe la tabla auditoria
SELECT * FROM iot_schema.auditoria LIMIT 1;

-- Crear índices si no existen
CREATE INDEX IF NOT EXISTS idx_auditoria_entidad_ts 
ON iot_schema.auditoria(entidad, ts);

CREATE INDEX IF NOT EXISTS idx_auditoria_usuario_ts 
ON iot_schema.auditoria(usuario_id, ts);
```

## Uso Básico

### 1. Crear Servicio de Auditoría
```python
from iot_middleware.utils.auditoria import create_auditoria_service
from iot_middleware.storage.db_handler import create_database_handler

# Crear manejador de base de datos
db_handler = create_database_handler(config.storage)

# Crear servicio de auditoría
auditoria_service = create_auditoria_service(db_handler)
```

### 2. Establecer Contexto de Auditoría
```python
from iot_middleware.utils.auditoria import ContextoAuditoria

# Crear contexto
contexto = ContextoAuditoria(
    usuario_id="usuario_001",
    ip_origen="192.168.1.100",
    user_agent="AdminTool/1.0",
    endpoint="/api/configuracion",
    metodo_http="POST"
)

# Establecer contexto
auditoria_service.set_contexto(contexto)
```

### 3. Registrar Cambios
```python
from iot_middleware.utils.auditoria import AccionAuditoria, EntidadAuditable

# Auditoría de configuración
success = auditoria_service.auditar_config_middleware(
    config_id="config_001",
    accion=AccionAuditoria.CREAR,
    antes={},
    despues={
        'clave': 'temperatura_maxima',
        'valor': 85.0,
        'descripcion': 'Temperatura máxima permitida'
    }
)

# Auditoría de canal
success = auditoria_service.auditar_canal(
    canal_id="canal_001",
    accion=AccionAuditoria.CONFIGURAR,
    antes={'umbral_alto': 80.0},
    despues={'umbral_alto': 85.0}
)

# Auditoría de evento de alarma
success = auditoria_service.auditar_evento_alarma(
    evento_id="alarma_001",
    accion=AccionAuditoria.RECONOCER,
    antes={'estado': 'activa'},
    despues={'estado': 'reconocida'}
)
```

## Uso Avanzado

### Decoradores para Auditoría Automática
```python
from iot_middleware.utils.auditoria import auditar_cambios

class ConfiguracionService:
    def __init__(self, auditoria_service):
        self.auditoria_service = auditoria_service
    
    @auditar_cambios(EntidadAuditable.CONFIG_MIDDLEWARE, AccionAuditoria.CREAR)
    def crear_configuracion(self, id: str, config_data: dict) -> bool:
        # La auditoría se ejecuta automáticamente
        return True
    
    @auditar_cambios(EntidadAuditable.CONFIG_MIDDLEWARE, AccionAuditoria.ACTUALIZAR)
    def actualizar_configuracion(self, id: str, config_data: dict) -> bool:
        # La auditoría se ejecuta automáticamente
        return True
```

### Context Managers para Auditoría
```python
from iot_middleware.utils.auditoria import contexto_auditoria

# Usar context manager
with contexto_auditoria(
    auditoria_service=auditoria_service,
    usuario_id="usuario_admin_001",
    ip_origen="10.0.0.50",
    endpoint="/admin/configuracion",
    metodo_http="PUT"
) as audit_service:
    
    # Todas las operaciones dentro de este bloque se auditan automáticamente
    audit_service.auditar_dispositivo(
        dispositivo_id="device_001",
        accion=AccionAuditoria.ACTIVAR,
        antes={'estado': 'inactivo'},
        despues={'estado': 'activo'}
    )
    
    audit_service.auditar_proyecto(
        proyecto_id="proyecto_001",
        accion=AccionAuditoria.CONFIGURAR,
        antes={'version': '1.0'},
        despues={'version': '2.0'}
    )

# El contexto se libera automáticamente al salir del bloque
```

### Middleware para FastAPI
```python
from fastapi import FastAPI
from iot_middleware.utils.auditoria_middleware import create_auditoria_middleware

app = FastAPI()

# Crear middleware de auditoría
auditoria_middleware = create_auditoria_middleware(
    auditoria_service=auditoria_service,
    exclude_paths=['/health', '/metrics', '/docs']
)

# Agregar middleware a la aplicación
app.add_middleware(auditoria_middleware)
```

## Consultas y Reportes

### Consultas Básicas
```python
# Obtener todos los registros recientes
registros = auditoria_service.obtener_auditoria(limite=100)

# Filtrar por entidad
registros_config = auditoria_service.obtener_auditoria(
    entidad='config_middleware',
    limite=50
)

# Filtrar por acción
registros_crear = auditoria_service.obtener_auditoria(
    accion='CREAR',
    limite=50
)

# Filtrar por usuario
registros_usuario = auditoria_service.obtener_auditoria(
    usuario_id='usuario_001',
    limite=50
)

# Filtrar por período
from datetime import datetime, timedelta

fecha_desde = datetime.now() - timedelta(days=7)
fecha_hasta = datetime.now()

registros_periodo = auditoria_service.obtener_auditoria(
    fecha_desde=fecha_desde,
    fecha_hasta=fecha_hasta,
    limite=1000
)
```

### Generación de Reportes
```python
# Reporte en JSON
reporte_json = auditoria_service.generar_reporte_auditoria(
    fecha_desde=fecha_desde,
    fecha_hasta=fecha_hasta,
    formato='json'
)

# Reporte en CSV
reporte_csv = auditoria_service.generar_reporte_auditoria(
    fecha_desde=fecha_desde,
    fecha_hasta=fecha_hasta,
    formato='csv'
)

# Reporte en HTML
reporte_html = auditoria_service.generar_reporte_auditoria(
    fecha_desde=fecha_desde,
    fecha_hasta=fecha_hasta,
    formato='html'
)

# Guardar reportes en archivos
with open('auditoria.json', 'w') as f:
    json.dump(reporte_json, f, indent=2)

with open('auditoria.csv', 'w') as f:
    f.write(reporte_csv)

with open('auditoria.html', 'w') as f:
    f.write(reporte_html)
```

## Configuración

### Configuración del Servicio
```python
# Configurar opciones del servicio
auditoria_service.auditoria_habilitada = True
auditoria_service.auditoria_sensible = True
auditoria_service.max_tamano_cambios = 15000  # 15KB

# Configurar logging
import logging
logging.getLogger('iot_middleware.utils.auditoria').setLevel(logging.DEBUG)
```

### Configuración del Middleware
```python
# Rutas a excluir de la auditoría
exclude_paths = [
    '/health',
    '/metrics', 
    '/docs',
    '/redoc',
    '/openapi.json',
    '/static/',
    '/favicon.ico'
]

# Headers a incluir en la auditoría
include_headers = [
    'user-agent',
    'referer',
    'origin',
    'x-forwarded-for',
    'x-real-ip',
    'x-request-id',
    'authorization'
]

# Crear middleware con configuración personalizada
auditoria_middleware = create_auditoria_middleware(
    auditoria_service=auditoria_service,
    exclude_paths=exclude_paths
)
```

## Sanitización de Datos

### Campos Sensibles Automáticos
El sistema sanitiza automáticamente los siguientes campos:
- `password`, `passwd`, `pwd`
- `secret`, `token`, `api_key`
- `private_key`, `certificate`
- `credential`, `auth`
- `database_url`, `redis_password`

### Ejemplo de Sanitización
```python
# Datos originales (con información sensible)
datos_originales = {
    'username': 'admin',
    'password': 'super_secret_password_123',
    'api_key': 'sk-1234567890abcdef',
    'configuracion': {
        'database_url': 'postgresql://user:pass@localhost:5432/db'
    },
    'datos_normales': 'valor'
}

# Al registrar en auditoría, los datos sensibles se sanitizan automáticamente
success = auditoria_service.auditar_config_middleware(
    config_id="config_001",
    accion=AccionAuditoria.CREAR,
    antes={},
    despues=datos_originales
)

# Resultado en la base de datos:
# {
#   'username': 'admin',
#   'password': '***SENSIBLE***',
#   'api_key': '***SENSIBLE***',
#   'configuracion': {
#     'database_url': '***SENSIBLE***'
#   },
#   'datos_normales': 'valor'
# }
```

## Monitoreo y Métricas

### Métricas Disponibles
- **Total de registros** de auditoría
- **Registros por entidad** (config_middleware, canales, etc.)
- **Registros por acción** (CREAR, ACTUALIZAR, etc.)
- **Usuarios únicos** que realizaron cambios
- **Usuario más activo** en el período
- **Distribución temporal** de cambios

### Health Checks
```python
# Verificar estado del servicio
if auditoria_service.auditoria_habilitada:
    print("✅ Auditoría habilitada")
else:
    print("❌ Auditoría deshabilitada")

# Verificar conexión a base de datos
try:
    registros = auditoria_service.obtener_auditoria(limite=1)
    print("✅ Conexión a base de datos OK")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
```

## Troubleshooting

### Problemas Comunes

#### Error: "No hay contexto de auditoría disponible"
```python
# Solución: Establecer contexto antes de auditar
contexto = ContextoAuditoria(
    usuario_id="usuario_001",
    ip_origen="192.168.1.100"
)
auditoria_service.set_contexto(contexto)

# Ahora se puede auditar
auditoria_service.auditar_config_middleware(...)
```

#### Error: "Error insertando auditoría"
```python
# Verificar conexión a base de datos
try:
    with db_handler.get_session() as session:
        session.execute("SELECT 1")
        print("✅ Conexión OK")
except Exception as e:
    print(f"❌ Error de conexión: {e}")

# Verificar esquema de la tabla
try:
    with db_handler.get_session() as session:
        session.execute("SELECT * FROM iot_schema.auditoria LIMIT 1")
        print("✅ Tabla auditoria OK")
except Exception as e:
    print(f"❌ Error en tabla: {e}")
```

#### Auditoría no se ejecuta automáticamente
```python
# Verificar que el decorador esté aplicado correctamente
@auditar_cambios(EntidadAuditable.CONFIG_MIDDLEWARE, AccionAuditoria.CREAR)
def crear_config(self, id: str, data: dict):
    # El método debe tener acceso a self.auditoria_service
    return True

# Verificar que la clase tenga el atributo auditoria_service
class MiServicio:
    def __init__(self, auditoria_service):
        self.auditoria_service = auditoria_service  # ← Importante
```

### Logs de Debug
```python
# Habilitar logging detallado
import logging
logging.getLogger('iot_middleware.utils.auditoria').setLevel(logging.DEBUG)

# Ver logs de auditoría
# 2024-01-15 10:30:00 - iot_middleware.utils.auditoria - DEBUG - ✅ Auditoría registrada: config_middleware - CREAR
```

## Ejemplos Completos

### Ejemplo 1: Servicio de Configuración con Auditoría
```python
from iot_middleware.utils.auditoria import (
    AuditoriaService, 
    AccionAuditoria, 
    EntidadAuditable,
    auditar_cambios
)

class ConfiguracionService:
    def __init__(self, auditoria_service: AuditoriaService):
        self.auditoria_service = auditoria_service
    
    @auditar_cambios(EntidadAuditable.CONFIG_MIDDLEWARE, AccionAuditoria.CREAR)
    def crear_configuracion(self, id: str, config_data: dict) -> bool:
        # Lógica de creación
        print(f"Creando configuración: {id}")
        return True
    
    @auditar_cambios(EntidadAuditable.CONFIG_MIDDLEWARE, AccionAuditoria.ACTUALIZAR)
    def actualizar_configuracion(self, id: str, config_data: dict) -> bool:
        # Lógica de actualización
        print(f"Actualizando configuración: {id}")
        return True
    
    @auditar_cambios(EntidadAuditable.CONFIG_MIDDLEWARE, AccionAuditoria.ELIMINAR)
    def eliminar_configuracion(self, id: str) -> bool:
        # Lógica de eliminación
        print(f"Eliminando configuración: {id}")
        return True
```

### Ejemplo 2: API REST con Auditoría
```python
from fastapi import FastAPI, Depends, HTTPException
from iot_middleware.utils.auditoria import ContextoAuditoria
from iot_middleware.utils.auditoria_middleware import create_auditoria_middleware

app = FastAPI()

# Crear middleware de auditoría
auditoria_middleware = create_auditoria_middleware(auditoria_service)
app.add_middleware(auditoria_middleware)

@app.post("/configuracion")
async def crear_configuracion(
    config_data: dict,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    # El middleware captura automáticamente el contexto
    # y audita la petición
    
    # Lógica de creación
    config_id = "config_001"
    
    # Auditoría manual si es necesario
    auditoria_service.auditar_config_middleware(
        config_id=config_id,
        accion=AccionAuditoria.CREAR,
        antes={},
        despues=config_data
    )
    
    return {"id": config_id, "mensaje": "Configuración creada"}
```

### Ejemplo 3: Script de Auditoría
```python
#!/usr/bin/env python3
"""
Script para consultar y generar reportes de auditoría
"""

from iot_middleware.utils.auditoria import create_auditoria_service
from iot_middleware.storage.db_handler import create_database_handler
from datetime import datetime, timedelta
import json

def main():
    # Configurar servicios
    db_handler = create_database_handler(config.storage)
    auditoria_service = create_auditoria_service(db_handler)
    
    # Generar reporte del último mes
    fecha_hasta = datetime.now()
    fecha_desde = fecha_hasta - timedelta(days=30)
    
    # Reporte en JSON
    reporte = auditoria_service.generar_reporte_auditoria(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        formato='json'
    )
    
    # Guardar reporte
    with open('auditoria_mensual.json', 'w') as f:
        json.dump(reporte, f, indent=2)
    
    # Mostrar estadísticas
    stats = reporte['estadisticas']
    print(f"Total de registros: {stats['total_registros']}")
    print(f"Usuarios únicos: {stats['usuarios_unicos']}")
    
    print("\nRegistros por entidad:")
    for entidad, count in stats['entidades'].items():
        print(f"  {entidad}: {count}")
    
    print("\nRegistros por acción:")
    for accion, count in stats['acciones'].items():
        print(f"  {accion}: {count}")

if __name__ == "__main__":
    main()
```

## Contribución

### Guías de Desarrollo
1. **Fork** del repositorio
2. **Crear branch** para feature: `git checkout -b feature/nueva-funcionalidad-auditoria`
3. **Commit** cambios: `git commit -am 'Agregar nueva funcionalidad de auditoría'`
4. **Push** al branch: `git push origin feature/nueva-funcionalidad-auditoria`
5. **Crear Pull Request**

### Estándares de Código
- **PEP 8** para estilo de Python
- **Type hints** para todas las funciones
- **Docstrings** completos
- **Tests unitarios** para nueva funcionalidad
- **Logging** estructurado

### Reportar Issues
- **Bug reports** con pasos de reproducción
- **Feature requests** con casos de uso
- **Documentación** de mejoras
- **Ejemplos** de configuración

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

**Nota**: Este sistema de auditoría es parte del ecosistema IoT Middleware. Para más información sobre otros componentes, consulta la [documentación principal](README.md).
