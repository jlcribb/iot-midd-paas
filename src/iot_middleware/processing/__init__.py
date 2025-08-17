"""
Módulo de Procesamiento - IoT Middleware
========================================

Este módulo proporciona funcionalidades para el procesamiento y normalización
de datos IoT, incluyendo validación de esquemas, normalización automática
y preparación para inserción en base de datos.
"""

from .processor import (
    DataProcessor,
    DataNormalizer,
    MessageSchema,
    FieldSchema,
    DataType,
    ValidationLevel,
    create_data_processor,
    process_message
)

__all__ = [
    'DataProcessor',
    'DataNormalizer',
    'MessageSchema',
    'FieldSchema',
    'DataType',
    'ValidationLevel',
    'create_data_processor',
    'process_message'
]

__version__ = "1.0.0"
__author__ = "IoT Middleware Team"
