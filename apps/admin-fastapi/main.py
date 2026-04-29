"""
Interfaz de Administración CRUD - IoT Middleware
================================================

Aplicación web para administrar proyectos, unidades, dispositivos y usuarios.
"""

import sys
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

import os
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from iot_middleware.storage.db_handler import DatabaseHandler
from iot_middleware.config.config_loader import load_config
from iot_middleware.core_backend.router import router as core_backend_router
from containers.admin.routers import (
    admin_router,
    proyectos_router,
    unidades_router,
    dispositivos_router,
    usuarios_router,
    dashboard_router,
    core_router,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directorios
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Configuración global
db_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    global db_handler
    
    # Inicio
    logger.info("🚀 Iniciando Interfaz de Administración...")
    
    try:
        # Cargar configuración
        # Buscar el config.yaml principal (no el de examples)
        config_path = os.getenv("CONFIG_PATH")
        
        if not config_path:
            # Buscar en diferentes ubicaciones, priorizando el principal
            search_paths = [
                "/app/config.yaml",  # En contenedor (directorio raíz montado)
                os.path.join(BASE_DIR.parent.parent, "config.yaml"),  # Desde apps/admin-fastapi -> raíz
                os.path.join(os.path.dirname(BASE_DIR.parent.parent), "config.yaml"),
                "config.yaml",
            ]
            
            for path in search_paths:
                if os.path.exists(path):
                    # Verificar que no sea el examples/config.yaml (simple)
                    try:
                        import yaml
                        with open(path, 'r') as f:
                            test_config = yaml.safe_load(f)
                            # Verificar si tiene la estructura completa (mqtt.broker, no solo mqtt.host)
                            if test_config.get('mqtt', {}).get('broker') is not None:
                                config_path = path
                                logger.info(f"📁 Config.yaml completo encontrado en: {path}")
                                break
                    except:
                        continue
            
            if not config_path:
                # Si no encontramos un config completo, usar el que existe y construir la config mínima
                for path in search_paths:
                    if os.path.exists(path):
                        config_path = path
                        logger.warning(f"⚠️  Usando config.yaml simple en: {path}. Se complementará con variables de entorno.")
                        break
        
        if not config_path or not os.path.exists(config_path):
            raise FileNotFoundError(f"No se encontró ningún archivo config.yaml. Buscado en: {search_paths}")
        
        logger.info(f"📁 Cargando configuración desde: {config_path}")
        
        # Verificar si el archivo tiene la estructura completa
        try:
            import yaml
            with open(config_path, 'r') as f:
                raw_config = yaml.safe_load(f)
            
            # Si el archivo es simple (tiene mqtt.host pero no mqtt.broker), construir config completa
            if raw_config.get('mqtt', {}).get('host') and not raw_config.get('mqtt', {}).get('broker'):
                logger.warning("⚠️  Archivo config.yaml simple detectado. Construyendo configuración completa...")
                
                # Construir configuración completa a partir del simple + variables de entorno
                full_config = {
                    'mqtt': {
                        'broker': {
                            'host': raw_config.get('mqtt', {}).get('host', 'mosquitto'),
                            'port': raw_config.get('mqtt', {}).get('port', 1883),
                            'username': raw_config.get('mqtt', {}).get('username'),
                            'password': raw_config.get('mqtt', {}).get('password'),
                            'keepalive': 60,
                            'tls_enabled': False,
                        },
                        'topics': {
                            'subscribe': ['iot/+/+/+/+/+'],
                            'publish': ['iot/status/ingesta']
                        },
                        'qos': 1,
                    },
                    'postgresql': {
                        'host': os.getenv('POSTGRES_HOST', raw_config.get('postgresql', {}).get('host', 'postgresql')),
                        'port': int(os.getenv('POSTGRES_PORT', raw_config.get('postgresql', {}).get('port', 5432))),
                        'database': os.getenv('POSTGRES_DB', raw_config.get('postgresql', {}).get('database', 'iot_middleware')),
                        'username': os.getenv('POSTGRES_USER', raw_config.get('postgresql', {}).get('username', 'iot_user')),
                        'password': os.getenv('POSTGRES_PASSWORD', raw_config.get('postgresql', {}).get('password', 'iot_password_2024')),
                        'db_schema': 'iot_schema',
                        'pool_size': 10,
                        'max_overflow': 20,
                    },
                    'influxdb': {
                        'url': raw_config.get('influxdb', {}).get('url', 'http://influxdb:8086'),
                        'token': raw_config.get('influxdb', {}).get('token', 'dev-token'),
                        'org': raw_config.get('influxdb', {}).get('org', 'my-org'),
                        'bucket': raw_config.get('influxdb', {}).get('bucket', 'iot'),
                        'retention_policy': '30d',
                    },
                    'storage': {
                        'timeseries': {'provider': 'influxdb', 'enabled': True},
                        'relational': {'provider': 'postgresql', 'enabled': True},
                        'metadata': {'provider': 'postgresql', 'enabled': True},
                    },
                    'api': {
                        'host': raw_config.get('api', {}).get('host', '0.0.0.0'),
                        'port': raw_config.get('api', {}).get('port', 8000),
                        'cors': {'enabled': True, 'allow_origins': ['*']},
                    },
                }
                
                # Guardar temporalmente para cargar
                import tempfile
                temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
                yaml.dump(full_config, temp_config)
                temp_config_path = temp_config.name
                temp_config.close()
                config_path = temp_config_path
                logger.info("✅ Configuración completa construida")
            else:
                temp_config_path = None
        except Exception as e:
            logger.warning(f"⚠️  No se pudo verificar estructura del archivo: {e}")
            temp_config_path = None
        
        config = load_config(config_path)
        logger.info(f"✅ Configuración cargada exitosamente")
        
        # Limpiar archivo temporal si se creó
        if 'temp_config_path' in locals() and temp_config_path and os.path.exists(temp_config_path):
            try:
                os.unlink(temp_config_path)
            except:
                pass
        
        # Sobrescribir configuración con variables de entorno si están disponibles (para contenedores)
        if os.getenv("POSTGRES_HOST"):
            config.postgresql.host = os.getenv("POSTGRES_HOST")
            logger.info(f"📝 PostgreSQL host sobrescrito: {os.getenv('POSTGRES_HOST')}")
        if os.getenv("POSTGRES_PORT"):
            config.postgresql.port = int(os.getenv("POSTGRES_PORT"))
        if os.getenv("POSTGRES_DB"):
            config.postgresql.database = os.getenv("POSTGRES_DB")
        if os.getenv("POSTGRES_USER"):
            config.postgresql.username = os.getenv("POSTGRES_USER")
        if os.getenv("POSTGRES_PASSWORD"):
            config.postgresql.password = os.getenv("POSTGRES_PASSWORD")
        
        # Inicializar base de datos
        db_handler = DatabaseHandler(
            postgresql_config=config.postgresql,
            influxdb_config=config.influxdb,
            storage_config=config.storage
        )
        
        # Verificar estado de conexión
        health = db_handler.health_check()
        if health['databases'].get('postgresql', {}).get('connected', False):
            logger.info("✅ Conexión a PostgreSQL establecida")
        else:
            logger.warning("⚠️  PostgreSQL no está conectado, pero el servicio continuará")
            if db_handler.postgresql_handler:
                status = db_handler.postgresql_handler.get_connection_status()
                logger.warning(f"Estado de PostgreSQL: {status.value}")
        
        # Guardar en app state
        app.state.db_handler = db_handler
        app.state.config = config
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error durante inicio: {e}")
        raise
    finally:
        # Cierre
        logger.info("🛑 Cerrando Interfaz de Administración...")
        if db_handler:
            db_handler.close()


# Crear aplicación FastAPI
app = FastAPI(
    title="IoT Middleware - Panel de Administración",
    description="Interfaz CRUD para administrar proyectos, unidades, dispositivos y usuarios",
    version="1.0.0",
    lifespan=lifespan
)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Normaliza error de payload inválido a HTTP 400 para contratos REST de backend core."""
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation_error",
            "message": "invalid request payload",
            "details": exc.errors(),
        },
    )

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Página principal"""
    response = templates.TemplateResponse("index.html", {"request": request})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


# Incluir routers
app.include_router(admin_router.router, prefix="/api/admin", tags=["Admin"])
app.include_router(proyectos_router.router, prefix="/api/proyectos", tags=["Proyectos"])
app.include_router(unidades_router.router, prefix="/api/unidades", tags=["Unidades"])
app.include_router(dispositivos_router.router, prefix="/api/dispositivos", tags=["Dispositivos"])
app.include_router(usuarios_router.router, prefix="/api/usuarios", tags=["Usuarios"])
app.include_router(dashboard_router.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(core_router.router, prefix="/api/core", tags=["Core"])
# Core backend queda expuesto solo bajo namespace transicional.
app.include_router(core_backend_router, prefix="/api/transition/core-backend", tags=["Core Backend Transition"])


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("ADMIN_PORT", "9000"))
    host = os.getenv("ADMIN_HOST", "0.0.0.0")
    
    uvicorn.run(
        "containers.admin.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
