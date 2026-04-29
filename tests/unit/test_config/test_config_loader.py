"""
Unit Tests - ConfigLoader
========================

Pruebas unitarias para la clase ConfigLoader y funciones relacionadas.
"""

import pytest
import yaml
import tempfile
import os
from unittest.mock import patch, mock_open
from pydantic import ValidationError

from iot_middleware.config import (
    ConfigLoader,
    load_config,
    validate_config_file,
    IoTMiddlewareConfig,
    MQTTConfig,
    InfluxDBConfig,
    PostgreSQLConfig,
    APIConfig,
    LoggingConfig,
    ProcessingConfig,
    StorageConfig,
    SecurityConfig,
    MonitoringConfig
)


class TestConfigLoader:
    """Pruebas para la clase ConfigLoader"""
    
    def test_init_default(self):
        """Prueba inicialización por defecto"""
        loader = ConfigLoader()
        assert loader is not None
        assert loader.config is None
    
    def test_init_with_config_path(self, config_file_path):
        """Prueba inicialización con ruta de configuración"""
        loader = ConfigLoader(config_file_path)
        assert loader.config_path == config_file_path
    
    def test_find_config_file_exists(self, config_file_path):
        """Prueba búsqueda de archivo de configuración existente"""
        loader = ConfigLoader()
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                result = loader.find_config_file()
                assert result is not None
    
    def test_find_config_file_not_exists(self):
        """Prueba búsqueda de archivo de configuración inexistente"""
        loader = ConfigLoader()
        
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                loader.find_config_file()
    
    def test_load_config_success(self, valid_config_dict, config_file_path):
        """Prueba carga exitosa de configuración"""
        loader = ConfigLoader(config_file_path)
        
        with patch('builtins.open', mock_open(read_data=yaml.dump(valid_config_dict))):
            with patch('yaml.safe_load', return_value=valid_config_dict):
                result = loader.load_config()
                assert isinstance(result, IoTMiddlewareConfig)
                assert loader.config is not None
    
    def test_load_config_file_not_found(self):
        """Prueba carga de configuración con archivo no encontrado"""
        loader = ConfigLoader('/path/that/does/not/exist.yaml')
        
        with pytest.raises(FileNotFoundError):
            loader.load_config()
    
    def test_load_config_invalid_yaml(self, config_file_path):
        """Prueba carga de configuración con YAML inválido"""
        loader = ConfigLoader(config_file_path)
        
        with patch('builtins.open', mock_open(read_data='invalid: yaml: content: [')):
            with pytest.raises(Exception):  # yaml.YAMLError o similar
                loader.load_config()
    
    def test_load_config_validation_error(self, invalid_config_dict, config_file_path):
        """Prueba carga de configuración con error de validación"""
        loader = ConfigLoader(config_file_path)
        
        with patch('builtins.open', mock_open(read_data=yaml.dump(invalid_config_dict))):
            with patch('yaml.safe_load', return_value=invalid_config_dict):
                with pytest.raises(ValidationError):
                    loader.load_config()
    
    def test_get_mqtt_config(self, valid_config_dict, config_file_path):
        """Prueba obtención de configuración MQTT"""
        loader = ConfigLoader(config_file_path)
        loader.config = IoTMiddlewareConfig(**valid_config_dict)
        
        mqtt_config = loader.get_mqtt_config()
        assert mqtt_config is not None
        assert isinstance(mqtt_config, MQTTConfig)
        assert mqtt_config.broker['host'] == 'localhost'
        assert mqtt_config.broker['port'] == 1883
    
    def test_get_influxdb_config(self, valid_config_dict, config_file_path):
        """Prueba obtención de configuración InfluxDB"""
        loader = ConfigLoader(config_file_path)
        loader.config = IoTMiddlewareConfig(**valid_config_dict)
        
        influxdb_config = loader.get_influxdb_config()
        assert influxdb_config is not None
        assert isinstance(influxdb_config, InfluxDBConfig)
        assert influxdb_config.url == 'http://localhost:8086'
        assert influxdb_config.token == 'test_token'
    
    def test_get_postgresql_config(self, valid_config_dict, config_file_path):
        """Prueba obtención de configuración PostgreSQL"""
        loader = ConfigLoader(config_file_path)
        loader.config = IoTMiddlewareConfig(**valid_config_dict)
        
        postgresql_config = loader.get_postgresql_config()
        assert postgresql_config is not None
        assert isinstance(postgresql_config, PostgreSQLConfig)
        assert postgresql_config.host == 'localhost'
        assert postgresql_config.port == 5432
    
    def test_reload_config(self, valid_config_dict, config_file_path):
        """Prueba recarga de configuración"""
        loader = ConfigLoader(config_file_path)
        loader.config = IoTMiddlewareConfig(**valid_config_dict)
        
        with patch('builtins.open', mock_open(read_data=yaml.dump(valid_config_dict))):
            with patch('yaml.safe_load', return_value=valid_config_dict):
                result = loader.reload_config()
                assert isinstance(result, IoTMiddlewareConfig)


class TestLoadConfig:
    """Pruebas para la función load_config"""
    
    def test_load_config_success(self, valid_config_dict, config_file_path):
        """Prueba carga exitosa de configuración"""
        with patch('iot_middleware.config.ConfigLoader') as mock_loader_class:
            mock_loader = mock_loader_class.return_value
            mock_config = IoTMiddlewareConfig(**valid_config_dict)
            mock_loader.load_config.return_value = mock_config
            mock_loader.config = mock_config
            
            result = load_config(config_file_path)
            assert result is not None
            assert isinstance(result, IoTMiddlewareConfig)
    
    def test_load_config_failure(self, config_file_path):
        """Prueba fallo en carga de configuración"""
        # load_config lanza excepciones, no retorna None
        # Usar un path que no existe para forzar el error
        with pytest.raises(FileNotFoundError):
            load_config('/path/that/does/not/exist/config.yaml')
    
    def test_load_config_default_path(self, valid_config_dict, tmp_path):
        """Prueba carga de configuración con ruta por defecto"""
        # Crear un archivo de configuración temporal
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(valid_config_dict))
        
        # Cambiar al directorio temporal para que encuentre el archivo
        original_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            result = load_config()
            assert result is not None
            assert isinstance(result, IoTMiddlewareConfig)
        finally:
            os.chdir(original_cwd)


class TestValidateConfigFile:
    """Pruebas para la función validate_config_file"""
    
    def test_validate_config_file_valid(self, valid_config_dict, config_file_path):
        """Prueba validación de archivo de configuración válido"""
        with patch('builtins.open', mock_open(read_data=yaml.dump(valid_config_dict))):
            with patch('yaml.safe_load', return_value=valid_config_dict):
                result = validate_config_file(config_file_path)
                assert result is True
    
    def test_validate_config_file_invalid(self, invalid_config_dict, config_file_path):
        """Prueba validación de archivo de configuración inválido"""
        with patch('builtins.open', mock_open(read_data=yaml.dump(invalid_config_dict))):
            with patch('yaml.safe_load', return_value=invalid_config_dict):
                result = validate_config_file(config_file_path)
                assert result is False
    
    def test_validate_config_file_not_found(self):
        """Prueba validación de archivo no encontrado"""
        result = validate_config_file('/path/that/does/not/exist.yaml')
        assert result is False
    
    def test_validate_config_file_invalid_yaml(self, config_file_path):
        """Prueba validación de archivo con YAML inválido"""
        with patch('builtins.open', mock_open(read_data='invalid: yaml: content: [')):
            result = validate_config_file(config_file_path)
            assert result is False


class TestIoTMiddlewareConfig:
    """Pruebas para la clase IoTMiddlewareConfig"""
    
    def test_config_creation_valid(self, valid_config_dict):
        """Prueba creación de configuración válida"""
        config = IoTMiddlewareConfig(**valid_config_dict)
        assert config is not None
        assert config.mqtt.broker['host'] == 'localhost'
        assert config.influxdb.url == 'http://localhost:8086'
        assert config.postgresql.host == 'localhost'
    
    def test_config_creation_invalid(self, invalid_config_dict):
        """Prueba creación de configuración inválida"""
        with pytest.raises(ValidationError):
            IoTMiddlewareConfig(**invalid_config_dict)
    
    def test_config_creation_minimal(self, minimal_config_dict):
        """Prueba creación de configuración mínima"""
        config = IoTMiddlewareConfig(**minimal_config_dict)
        assert config is not None
        assert config.mqtt.broker['host'] == 'localhost'
        assert config.influxdb.url == 'http://localhost:8086'
        assert config.postgresql.host == 'localhost'
    
    def test_config_serialization(self, valid_config_dict):
        """Prueba serialización de configuración"""
        config = IoTMiddlewareConfig(**valid_config_dict)
        # Pydantic v2 usa model_dump() en lugar de dict()
        try:
            config_dict = config.model_dump()
        except AttributeError:
            # Fallback para Pydantic v1
            config_dict = config.dict()
        assert isinstance(config_dict, dict)
        assert 'mqtt' in config_dict
        assert 'influxdb' in config_dict
        assert 'postgresql' in config_dict
    
    def test_config_json_serialization(self, valid_config_dict):
        """Prueba serialización JSON de configuración"""
        config = IoTMiddlewareConfig(**valid_config_dict)
        # Pydantic v2 usa model_dump_json() en lugar de json()
        try:
            config_json = config.model_dump_json()
        except AttributeError:
            # Fallback para Pydantic v1
            config_json = config.json()
        assert isinstance(config_json, str)
        assert 'mqtt' in config_json
        assert 'influxdb' in config_json
        assert 'postgresql' in config_json


class TestMQTTConfig:
    """Pruebas para la clase MQTTConfig"""
    
    def test_mqtt_config_creation_valid(self, mqtt_config_dict):
        """Prueba creación de configuración MQTT válida"""
        config = MQTTConfig(**mqtt_config_dict)
        assert config is not None
        assert config.broker['host'] == 'localhost'
        assert config.broker['port'] == 1883
        assert config.qos == 1
    
    def test_mqtt_config_creation_invalid(self):
        """Prueba creación de configuración MQTT inválida"""
        invalid_config = {
            'broker': {
                'host': 'localhost',
                'port': 'invalid_port'  # Puerto inválido
            },
            'topics': {
                'subscribe': [],  # Lista vacía
                'publish': []
            }
        }
        
        with pytest.raises(ValidationError):
            MQTTConfig(**invalid_config)
    
    def test_mqtt_config_defaults(self):
        """Prueba valores por defecto de configuración MQTT"""
        config = MQTTConfig(
            broker={
                'host': 'localhost',
                'port': 1883
            },
            topics={
                'subscribe': ['test/+/+'],
                'publish': ['test/output/+']  # publish no puede estar vacío según validación
            }
        )
        assert config.qos == 1
        assert config.retain is False
        assert config.broker['host'] == 'localhost'
        assert config.broker['port'] == 1883


class TestDatabaseConfigs:
    """Pruebas para configuraciones de base de datos"""
    
    def test_postgresql_config_creation(self, database_config_dict):
        """Prueba creación de configuración PostgreSQL"""
        config = PostgreSQLConfig(**database_config_dict['postgresql'])
        assert config is not None
        assert config.host == 'localhost'
        assert config.port == 5432
        assert config.database == 'test_db'
    
    def test_influxdb_config_creation(self, database_config_dict):
        """Prueba creación de configuración InfluxDB"""
        config = InfluxDBConfig(**database_config_dict['influxdb'])
        assert config is not None
        assert config.url == 'http://localhost:8086'
        assert config.token == 'test_token'
        assert config.org == 'test_org'
        assert config.bucket == 'test_bucket'


class TestAPIConfig:
    """Pruebas para la clase APIConfig"""
    
    def test_api_config_creation(self, api_config_dict):
        """Prueba creación de configuración API"""
        config = APIConfig(**api_config_dict)
        assert config is not None
        assert config.host == '0.0.0.0'
        assert config.port == 8000
        assert config.debug is False
        assert isinstance(config.cors, dict)
        assert config.cors.get('enabled') is True


class TestLoggingConfig:
    """Pruebas para la clase LoggingConfig"""
    
    def test_logging_config_creation(self, logging_config_dict):
        """Prueba creación de configuración de logging"""
        config = LoggingConfig(**logging_config_dict)
        assert config is not None
        assert config.level == 'INFO'
        assert config.file == 'test.log'
        assert config.max_size == '10MB'
        assert config.backup_count == 5


class TestProcessingConfig:
    """Pruebas para la clase ProcessingConfig"""
    
    def test_processing_config_creation(self, processing_config_dict):
        """Prueba creación de configuración de procesamiento"""
        config = ProcessingConfig(**processing_config_dict)
        assert config is not None
        assert config.batch_size == 100
        assert config.timeout == 30
        assert config.max_workers == 4
        assert config.retry_attempts == 3


class TestSecurityConfig:
    """Pruebas para la clase SecurityConfig"""
    
    def test_security_config_creation(self, security_config_dict):
        """Prueba creación de configuración de seguridad"""
        config = SecurityConfig(**security_config_dict)
        assert config is not None
        assert isinstance(config.mqtt, dict)
        assert isinstance(config.api, dict)
        assert isinstance(config.database, dict)
        assert config.mqtt.get('tls_enabled') is False


class TestMonitoringConfig:
    """Pruebas para la clase MonitoringConfig"""
    
    def test_monitoring_config_creation(self, monitoring_config_dict):
        """Prueba creación de configuración de monitoreo"""
        config = MonitoringConfig(**monitoring_config_dict)
        assert config is not None
        assert config.health_check_interval == 30
        assert config.metrics_collection is True
        assert isinstance(config.alerting, dict)
