"""
Configuración Global de Pytest - IoT Middleware
==============================================

Este archivo contiene la configuración global de pytest, incluyendo
fixtures reutilizables y configuración de mocks para todas las pruebas.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone
from typing import Dict, Any, List

# Agregar src al path para importaciones
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Importar fixtures de configuración
# Usar importlib para cargar el módulo directamente desde la ruta del archivo
import importlib.util
fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'config_fixtures.py')
spec = importlib.util.spec_from_file_location("config_fixtures", fixtures_path)
config_fixtures_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_fixtures_module)

# Copiar todos los atributos públicos (fixtures) al namespace actual
# pytest detectará automáticamente las funciones decoradas con @pytest.fixture
for attr_name in dir(config_fixtures_module):
    if not attr_name.startswith('_'):
        attr = getattr(config_fixtures_module, attr_name)
        # Copiar todas las funciones (los fixtures son funciones decoradas)
        if callable(attr) or hasattr(attr, '_pytestfixturefunction'):
            globals()[attr_name] = attr

# =============================================================================
# FIXTURES DE CONFIGURACIÓN
# =============================================================================

@pytest.fixture
def mock_config():
    """Fixture para configuración mock completa"""
    return {
        'mqtt': {
            'broker': 'localhost',
            'port': 1883,
            'username': None,
            'password': None,
            'topics': ['test/+/+', 'iot/+/+/+/+'],
            'qos': 1,
            'retain': False,
            'clean_session': True,
            'client_id': 'test_client'
        },
        'influxdb': {
            'url': 'http://localhost:8086',
            'token': 'test_token',
            'org': 'test_org',
            'bucket': 'test_bucket',
            'timeout': 30,
            'retries': 3
        },
        'postgresql': {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'username': 'test_user',
            'password': 'test_pass',
            'ssl_mode': 'disable',
            'pool_size': 10,
            'max_overflow': 20
        },
        'api': {
            'host': '0.0.0.0',
            'port': 8000,
            'debug': False,
            'cors_enabled': True,
            'cors_origins': ['*']
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'test.log',
            'max_size': '10MB',
            'backup_count': 5
        },
        'processing': {
            'batch_size': 100,
            'batch_timeout': 5.0,
            'max_workers': 4,
            'validation_enabled': True
        },
        'storage': {
            'providers': ['postgresql', 'influxdb'],
            'default_provider': 'postgresql'
        },
        'security': {
            'tls_enabled': False,
            'authentication': {
                'enabled': False,
                'jwt_secret': 'test_secret'
            }
        },
        'monitoring': {
            'health_check_interval': 30,
            'metrics_interval': 60,
            'alerting': {}
        }
    }

@pytest.fixture
def mock_mqtt_config():
    """Fixture para configuración MQTT específica"""
    return {
        'broker': 'localhost',
        'port': 1883,
        'username': None,
        'password': None,
        'topics': ['test/+/+'],
        'qos': 1,
        'retain': False,
        'clean_session': True,
        'client_id': 'test_mqtt_client'
    }

@pytest.fixture
def mock_database_config():
    """Fixture para configuración de base de datos"""
    return {
        'postgresql': {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'username': 'test_user',
            'password': 'test_pass'
        },
        'influxdb': {
            'url': 'http://localhost:8086',
            'token': 'test_token',
            'org': 'test_org',
            'bucket': 'test_bucket'
        }
    }

# =============================================================================
# FIXTURES DE MOCKS
# =============================================================================

@pytest.fixture
def mock_mqtt_client():
    """Fixture para cliente MQTT mock"""
    client = Mock()
    client.connect.return_value = True
    client.disconnect.return_value = True
    client.publish.return_value = True
    client.subscribe.return_value = True
    client.unsubscribe.return_value = True
    client._connected = True
    client._client_id = 'test_client'
    client._broker = 'localhost'
    client._port = 1883
    
    # Métricas mock
    client.metrics = {
        'messages_sent': 0,
        'messages_received': 0,
        'connection_attempts': 0,
        'last_activity': None
    }
    
    return client

@pytest.fixture
def mock_database():
    """Fixture para base de datos mock"""
    db = Mock()
    db.connect.return_value = True
    db.disconnect.return_value = True
    db.insert.return_value = True
    db.query.return_value = []
    db.execute.return_value = True
    db.commit.return_value = True
    db.rollback.return_value = True
    
    # Estado mock
    db._connected = True
    db._connection_count = 0
    
    return db

@pytest.fixture
def mock_postgresql_handler():
    """Fixture para PostgreSQL handler mock"""
    handler = Mock()
    handler.connect.return_value = True
    handler.disconnect.return_value = True
    handler.insert_data.return_value = True
    handler.query_data.return_value = []
    handler._connected = True
    handler._connection_status = 'connected'
    
    return handler

@pytest.fixture
def mock_influxdb_handler():
    """Fixture para InfluxDB handler mock"""
    handler = Mock()
    handler.connect.return_value = True
    handler.disconnect.return_value = True
    handler.write_data.return_value = True
    handler.query_data.return_value = []
    handler._connected = True
    handler._connection_status = 'connected'
    
    return handler

# =============================================================================
# FIXTURES DE DATOS
# =============================================================================

@pytest.fixture
def sample_mqtt_message():
    """Fixture para mensaje MQTT de prueba"""
    return {
        'topic': 'test/sensor/temperature',
        'payload': '{"temperature": 25.5, "humidity": 60.0}',
        'qos': 1,
        'retain': False,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'message_id': 12345
    }

@pytest.fixture
def sample_unified_data():
    """Fixture para datos unificados de prueba"""
    from iot_middleware.input import UnifiedDataFormat, DataQuality
    
    return UnifiedDataFormat(
        device_id="test_device_001",
        project_id="test_project",
        timestamp=datetime.now(timezone.utc).isoformat(),
        measurements={"temperature": 25.5, "humidity": 60.0},
        source_address="test://localhost:8080",
        quality=DataQuality.VALID
    )

@pytest.fixture
def sample_device_data():
    """Fixture para datos de dispositivo de prueba"""
    return {
        'device_id': 'sensor_001',
        'project_id': 'proyecto_clima',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'measurements': {
            'temperature': 23.5,
            'humidity': 65.0,
            'pressure': 1013.25
        },
        'metadata': {
            'location': 'indoor',
            'calibration_date': '2025-01-01'
        }
    }

@pytest.fixture
def sample_protocol_data():
    """Fixture para datos de diferentes protocolos"""
    return {
        'mqtt': {
            'topic': 'iot/proyecto/sensor/data',
            'payload': '{"temperature": 25.5, "humidity": 60.0}'
        },
        'http': {
            'endpoint': '/ingest',
            'method': 'POST',
            'data': {'temperature': 25.5, 'humidity': 60.0}
        },
        'ble': {
            'device_address': '00:11:22:33:44:55',
            'rssi': -45,
            'battery': 85
        },
        'lora': {
            'gateway': 'gateway_001',
            'application': 'app_001',
            'device': 'node_001',
            'data': {'soil_moisture': 45.2}
        },
        'midi': {
            'channel': 0,
            'note': 'C4',
            'velocity': 127,
            'message_type': 'note_on'
        },
        'modbus': {
            'slave_id': 1,
            'register': 40001,
            'value': 25.5,
            'data_type': 'float'
        },
        'zigbee': {
            'coordinator': 'coordinator_001',
            'device': 'bulb_001',
            'command': 'on',
            'brightness': 75
        }
    }

# =============================================================================
# FIXTURES DE CONFIGURACIÓN DE PRUEBAS
# =============================================================================

@pytest.fixture
def test_config_path(tmp_path):
    """Fixture para archivo de configuración de prueba"""
    config_file = tmp_path / "test_config.yaml"
    config_content = """
mqtt:
  broker: localhost
  port: 1883
  topics: ['test/+/+']
influxdb:
  url: http://localhost:8086
  token: test_token
  org: test_org
  bucket: test_bucket
postgresql:
  host: localhost
  port: 5432
  database: test_db
  username: test_user
  password: test_pass
"""
    config_file.write_text(config_content)
    return str(config_file)

@pytest.fixture
def test_log_file(tmp_path):
    """Fixture para archivo de log de prueba"""
    log_file = tmp_path / "test.log"
    return str(log_file)

# =============================================================================
# FIXTURES DE PATCHES
# =============================================================================

@pytest.fixture
def patch_mqtt_client():
    """Fixture para patchear cliente MQTT"""
    with patch('iot_middleware.mqtt.mqtt_client.IoTMQTTClient') as mock:
        yield mock

@pytest.fixture
def patch_database_handlers():
    """Fixture para patchear handlers de base de datos"""
    with patch('iot_middleware.storage.db_handler.PostgreSQLHandler') as mock_pg, \
         patch('iot_middleware.storage.db_handler.InfluxDBHandler') as mock_influx:
        yield mock_pg, mock_influx

@pytest.fixture
def patch_logging():
    """Fixture para patchear logging"""
    with patch('logging.getLogger') as mock:
        yield mock

# =============================================================================
# CONFIGURACIÓN DE PYTEST
# =============================================================================

def pytest_configure(config):
    """Configuración de pytest"""
    config.addinivalue_line(
        "markers", "unit: marca pruebas unitarias"
    )
    config.addinivalue_line(
        "markers", "integration: marca pruebas de integración"
    )
    config.addinivalue_line(
        "markers", "performance: marca pruebas de rendimiento"
    )
    config.addinivalue_line(
        "markers", "security: marca pruebas de seguridad"
    )
    config.addinivalue_line(
        "markers", "slow: marca pruebas lentas"
    )

def pytest_collection_modifyitems(config, items):
    """Modificar items de colección de pruebas"""
    for item in items:
        # Agregar marcador 'unit' a pruebas en directorio unit/
        if 'unit' in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Agregar marcador 'integration' a pruebas en directorio integration/
        if 'integration' in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Agregar marcador 'performance' a pruebas en directorio performance/
        if 'performance' in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        
        # Agregar marcador 'security' a pruebas en directorio security/
        if 'security' in str(item.fspath):
            item.add_marker(pytest.mark.security)
