"""
Módulo de Almacenamiento - IoT Middleware
=========================================

Este módulo proporciona funcionalidades para la persistencia de datos IoT
en diferentes tipos de bases de datos.
"""

from .db_handler import (
    DatabaseHandler,
    PostgreSQLHandler,
    InfluxDBHandler,
    DatabaseType,
    ConnectionStatus,
    DatabaseMetrics,
    create_database_handler,
    insert_sensor_data
)

__all__ = [
    'DatabaseHandler',
    'PostgreSQLHandler', 
    'InfluxDBHandler',
    'DatabaseType',
    'ConnectionStatus',
    'DatabaseMetrics',
    'create_database_handler',
    'insert_sensor_data'
]
