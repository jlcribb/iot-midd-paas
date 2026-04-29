"""
Fixtures de Configuración - IoT Middleware Tests
===============================================

Fixtures específicas para pruebas de configuración.
"""

import pytest
import yaml
import tempfile
import os
from typing import Dict, Any

@pytest.fixture
def valid_config_dict():
    """Fixture para configuración válida como diccionario"""
    return {
        'mqtt': {
            'broker': {
                'host': 'localhost',
                'port': 1883,
                'username': None,
                'password': None
            },
            'topics': {
                'subscribe': ['test/+/+'],
                'publish': ['test/output/+']
            },
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
            'cors': {
                'enabled': True,
                'origins': ['*']
            }
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
            'timeout': 30,
            'max_workers': 4,
            'retry_attempts': 3,
            'retry_delay': 5
        },
        'storage': {
            'timeseries': {
                'provider': 'influxdb',
                'enabled': True
            },
            'relational': {
                'provider': 'postgresql',
                'enabled': True
            },
            'metadata': {
                'provider': 'postgresql',
                'enabled': True
            }
        },
        'security': {
            'mqtt': {
                'tls_enabled': False
            },
            'api': {
                'authentication': {
                    'enabled': False,
                    'jwt_secret': 'test_secret'
                }
            },
            'database': {}
        },
        'monitoring': {
            'health_check_interval': 30,
            'metrics_collection': True,
            'alerting': {}
        }
    }

@pytest.fixture
def invalid_config_dict():
    """Fixture para configuración inválida como diccionario"""
    return {
        'mqtt': {
            'broker': {
                'host': 'localhost',
                'port': 'invalid_port'  # Puerto inválido
            },
            'topics': {
                'subscribe': [],  # Lista vacía
                'publish': []
            }
        },
        'influxdb': {
            'url': 'invalid_url',  # URL inválida
            'token': '',  # Token vacío
        },
        'postgresql': {
            'host': 'localhost',
            'port': 5432,
            'database': '',  # Base de datos vacía
            'username': 'test_user',
            'password': 'test_pass'
        },
        'api': {
            'host': '0.0.0.0',
            'port': 8000,
            'debug': False,
            'cors': {}
        },
        'storage': {
            'timeseries': {
                'provider': 'influxdb',
                'enabled': True
            },
            'relational': {
                'provider': 'postgresql',
                'enabled': True
            },
            'metadata': {
                'provider': 'postgresql',
                'enabled': True
            }
        }
    }

@pytest.fixture
def minimal_config_dict():
    """Fixture para configuración mínima válida"""
    return {
        'mqtt': {
            'broker': {
                'host': 'localhost',
                'port': 1883
            },
            'topics': {
                'subscribe': ['test/+/+'],
                'publish': ['test/output/+']
            }
        },
        'influxdb': {
            'url': 'http://localhost:8086',
            'token': 'test_token',
            'org': 'test_org',
            'bucket': 'test_bucket'
        },
        'postgresql': {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'username': 'test_user',
            'password': 'test_pass'
        },
        'api': {
            'host': '0.0.0.0',
            'port': 8000,
            'debug': False,
            'cors': {}
        },
        'storage': {
            'timeseries': {
                'provider': 'influxdb',
                'enabled': True
            },
            'relational': {
                'provider': 'postgresql',
                'enabled': True
            },
            'metadata': {
                'provider': 'postgresql',
                'enabled': True
            }
        }
    }

@pytest.fixture
def config_file_path(valid_config_dict):
    """Fixture para archivo de configuración temporal"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(valid_config_dict, f)
        temp_path = f.name
    
    yield temp_path
    
    # Limpiar archivo temporal
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def invalid_config_file_path(invalid_config_dict):
    """Fixture para archivo de configuración inválido temporal"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(invalid_config_dict, f)
        temp_path = f.name
    
    yield temp_path
    
    # Limpiar archivo temporal
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def config_file_not_found():
    """Fixture para ruta de archivo que no existe"""
    return '/path/that/does/not/exist/config.yaml'

@pytest.fixture
def mqtt_config_dict():
    """Fixture para configuración MQTT específica"""
    return {
        'broker': {
            'host': 'localhost',
            'port': 1883,
            'username': 'test_user',
            'password': 'test_pass'
        },
        'topics': {
            'subscribe': ['test/+/+', 'iot/+/+/+/+'],
            'publish': ['test/output/+']
        },
        'qos': 1,
        'retain': False,
        'clean_session': True,
        'client_id': 'test_mqtt_client'
    }

@pytest.fixture
def database_config_dict():
    """Fixture para configuración de base de datos"""
    return {
        'postgresql': {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'username': 'test_user',
            'password': 'test_pass',
            'ssl_mode': 'disable',
            'pool_size': 10,
            'max_overflow': 20,
            'pool_timeout': 30,
            'pool_recycle': 3600
        },
        'influxdb': {
            'url': 'http://localhost:8086',
            'token': 'test_token',
            'org': 'test_org',
            'bucket': 'test_bucket',
            'timeout': 30,
            'retries': 3,
            'verify_ssl': False
        }
    }

@pytest.fixture
def api_config_dict():
    """Fixture para configuración de API"""
    return {
        'host': '0.0.0.0',
        'port': 8000,
        'debug': False,
        'cors': {
            'enabled': True,
            'origins': ['*'],
            'methods': ['GET', 'POST', 'PUT', 'DELETE'],
            'headers': ['*']
        }
    }

@pytest.fixture
def logging_config_dict():
    """Fixture para configuración de logging"""
    return {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'test.log',
        'max_size': '10MB',
        'backup_count': 5,
        'console': True,
        'console_level': 'DEBUG',
        'console_format': '%(levelname)s - %(message)s'
    }

@pytest.fixture
def processing_config_dict():
    """Fixture para configuración de procesamiento"""
    return {
        'batch_size': 100,
        'timeout': 30,
        'max_workers': 4,
        'retry_attempts': 3,
        'retry_delay': 5
    }

@pytest.fixture
def security_config_dict():
    """Fixture para configuración de seguridad"""
    return {
        'mqtt': {
            'tls_enabled': False
        },
        'api': {
            'authentication': {
                'enabled': True,
                'jwt_secret': 'test_secret',
                'token_expiry': 3600
            }
        },
        'database': {}
    }

@pytest.fixture
def monitoring_config_dict():
    """Fixture para configuración de monitoreo"""
    return {
        'health_check_interval': 30,
        'metrics_collection': True,
        'alerting': {
            'enabled': True,
            'email': {
                'enabled': False,
                'smtp_server': 'localhost',
                'smtp_port': 587,
                'username': 'test@example.com',
                'password': 'test_password',
                'recipients': ['admin@example.com']
            },
            'webhook': {
                'enabled': False,
                'url': 'http://localhost:8080/webhook',
                'timeout': 10
            }
        }
    }
