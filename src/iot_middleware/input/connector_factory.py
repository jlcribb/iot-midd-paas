"""
Fábrica de Conectores - IoT Middleware
======================================

Permite crear instancias de conectores para diferentes protocolos
según la configuración proporcionada.
"""

import logging
from typing import Dict, Any, Optional, Type
from .base_connector import BaseConnector, ConnectorConfig
from .protocols.mqtt_connector import MQTTConnector
from .protocols.ble_connector import BLEConnector
from .protocols.lora_connector import LoRaConnector
from .protocols.midi_connector import MIDIConnector
from .protocols.modbus_connector import ModbusConnector
from .protocols.zigbee_connector import ZigBeeConnector
from .protocols.http_connector import HTTPConnector


class ConnectorFactory:
    """
    Fábrica para crear conectores de diferentes protocolos
    
    Esta clase centraliza la creación de conectores y permite
    agregar nuevos protocolos de manera modular.
    """
    
    # Registro de protocolos disponibles
    _protocols: Dict[str, Type[BaseConnector]] = {
        'mqtt': MQTTConnector,
        'ble': BLEConnector,
        'lora': LoRaConnector,
        'midi': MIDIConnector,
        'modbus': ModbusConnector,
        'zigbee': ZigBeeConnector,
        'http': HTTPConnector,
        'rest': HTTPConnector,  # Alias para HTTP
    }
    
    @classmethod
    def register_protocol(cls, protocol_name: str, connector_class: Type[BaseConnector]):
        """
        Registra un nuevo protocolo en la fábrica
        
        Args:
            protocol_name: Nombre del protocolo
            connector_class: Clase del conector que implementa BaseConnector
        """
        cls._protocols[protocol_name.lower()] = connector_class
        logging.info(f"Protocolo '{protocol_name}' registrado en la fábrica")
    
    @classmethod
    def get_available_protocols(cls) -> list:
        """
        Obtiene la lista de protocolos disponibles
        
        Returns:
            Lista de nombres de protocolos disponibles
        """
        return list(cls._protocols.keys())
    
    @classmethod
    def create_connector(cls, config: Dict[str, Any], data_callback=None) -> Optional[BaseConnector]:
        """
        Crea un conector según la configuración
        
        Args:
            config: Configuración del conector
            data_callback: Callback para procesar datos recibidos
            
        Returns:
            Instancia del conector o None si no se pudo crear
        """
        try:
            # Extraer información básica de la configuración
            protocol = config.get('protocol', '').lower()
            name = config.get('name', f"{protocol}_connector")
            
            if not protocol:
                logging.error("No se especificó el protocolo en la configuración")
                return None
            
            # Verificar si el protocolo está disponible
            if protocol not in cls._protocols:
                available = cls.get_available_protocols()
                logging.error(f"Protocolo '{protocol}' no está disponible. Protocolos disponibles: {available}")
                return None
            
            # Crear configuración del conector
            connector_config = ConnectorConfig(
                enabled=config.get('enabled', True),
                name=name,
                protocol=protocol,
                auto_reconnect=config.get('auto_reconnect', True),
                reconnect_interval=config.get('reconnect_interval', 5.0),
                max_reconnect_attempts=config.get('max_reconnect_attempts', 10),
                timeout=config.get('timeout', 30.0),
                retry_on_error=config.get('retry_on_error', True),
                max_retries=config.get('max_retries', 3),
                retry_delay=config.get('retry_delay', 1.0),
                buffer_size=config.get('buffer_size', 1000),
                batch_size=config.get('batch_size', 100),
                batch_timeout=config.get('batch_timeout', 5.0)
            )
            
            # Obtener la clase del conector
            connector_class = cls._protocols[protocol]
            
            # Crear instancia del conector
            connector = connector_class(connector_config, data_callback)
            
            logging.info(f"Conector '{name}' creado para protocolo '{protocol}'")
            return connector
            
        except Exception as e:
            logging.error(f"Error creando conector: {e}")
            return None
    
    @classmethod
    def create_connectors_from_config(cls, configs: list, data_callback=None) -> Dict[str, BaseConnector]:
        """
        Crea múltiples conectores desde una lista de configuraciones
        
        Args:
            configs: Lista de configuraciones de conectores
            data_callback: Callback para procesar datos recibidos
            
        Returns:
            Diccionario de conectores creados (nombre -> conector)
        """
        connectors = {}
        
        for config in configs:
            try:
                connector = cls.create_connector(config, data_callback)
                if connector:
                    connectors[connector.config.name] = connector
                    
            except Exception as e:
                logging.error(f"Error creando conector desde configuración {config}: {e}")
        
        logging.info(f"Se crearon {len(connectors)} conectores exitosamente")
        return connectors
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida una configuración de conector
        
        Args:
            config: Configuración a validar
            
        Returns:
            Resultado de la validación con errores y advertencias
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            # Verificar campos requeridos
            required_fields = ['protocol']
            for field in required_fields:
                if field not in config or not config[field]:
                    result['valid'] = False
                    result['errors'].append(f"Campo requerido '{field}' no está presente o está vacío")
            
            # Verificar si el protocolo está disponible
            protocol = config.get('protocol', '').lower()
            if protocol and protocol not in cls._protocols:
                result['valid'] = False
                result['errors'].append(f"Protocolo '{protocol}' no está disponible")
                result['suggestions'].append(f"Protocolos disponibles: {cls.get_available_protocols()}")
            
            # Validar campos opcionales
            if 'timeout' in config and (not isinstance(config['timeout'], (int, float)) or config['timeout'] <= 0):
                result['valid'] = False
                result['errors'].append("El timeout debe ser un número positivo")
            
            if 'buffer_size' in config and (not isinstance(config['buffer_size'], int) or config['buffer_size'] <= 0):
                result['valid'] = False
                result['errors'].append("El buffer_size debe ser un entero positivo")
            
            if 'batch_size' in config and (not isinstance(config['batch_size'], int) or config['batch_size'] <= 0):
                result['valid'] = False
                result['errors'].append("El batch_size debe ser un entero positivo")
            
            # Advertencias para configuraciones no óptimas
            if config.get('buffer_size', 1000) < 100:
                result['warnings'].append("Buffer size muy pequeño puede causar pérdida de datos")
            
            if config.get('batch_timeout', 5.0) > 60.0:
                result['warnings'].append("Batch timeout muy alto puede causar latencia en el procesamiento")
            
            # Sugerencias de mejora
            if 'name' not in config:
                result['suggestions'].append("Considera agregar un nombre descriptivo para el conector")
            
            if 'enabled' not in config:
                result['suggestions'].append("Considera especificar explícitamente si el conector debe estar habilitado")
                
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Error durante la validación: {e}")
        
        return result


def create_input_manager(configs: list, data_callback=None):
    """
    Función de conveniencia para crear un gestor de entrada completo
    
    Args:
        configs: Lista de configuraciones de conectores
        data_callback: Callback para procesar datos recibidos
        
    Returns:
        InputManager con todos los conectores configurados
    """
    from .input_manager import InputManager
    return InputManager(configs, data_callback)
