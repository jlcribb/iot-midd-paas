"""
Alembic Environment Configuration - IoT Middleware
=================================================

Este archivo configura el entorno de Alembic para las migraciones
de la base de datos del sistema IoT Middleware.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Agregar el directorio src al path para importar los modelos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Importar los modelos SQLAlchemy
from iot_middleware.models import Base
from iot_middleware.models.entities import (
    Cliente, Proyecto, UnidadProyecto, Sesion,
    Dispositivo, DispositivoProyecto, Canal,
    RegistroDatos, EventoAlarma, Usuario,
    UsuarioScope, ConfigMiddleware, Auditoria
)
from iot_middleware.models.enums import (
    EstadoProyecto, ProtocoloComunicacion, TipoDato,
    RolSistema, CalidadDato, SeveridadEvento, EstadoDispositivo
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """Obtener la URL de conexión a la base de datos"""
    # Compatibilidad con ambos esquemas de variables de entorno:
    # - DB_* (alembic legacy)
    # - POSTGRES_* (compose/runtime actual)
    db_host = os.getenv('DB_HOST') or os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('DB_PORT') or os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('DB_NAME') or os.getenv('POSTGRES_DB', 'iot_middleware')
    db_user = os.getenv('DB_USER') or os.getenv('POSTGRES_USER', 'iot_user')
    db_password = os.getenv('DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD', 'iot_password')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Configuraciones específicas para PostgreSQL
        compare_type=True,
        compare_server_default=True,
        include_schemas=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Actualizar la URL en la configuración
    config.set_main_option("sqlalchemy.url", get_url())
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Configuraciones específicas para PostgreSQL
            compare_type=True,
            compare_server_default=True,
            include_schemas=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
