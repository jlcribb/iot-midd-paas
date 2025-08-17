"""
Conector Modbus - IoT Middleware
================================

Permite recibir datos desde dispositivos industriales que usan el protocolo Modbus.
Soporta Modbus TCP, Modbus RTU, y Modbus ASCII.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

from ..base_connector import BaseConnector, ConnectorConfig, UnifiedDataFormat, DataQuality, ConnectorStatus


@dataclass
class ModbusConnectorConfig(ConnectorConfig):
    """Configuración específica para el conector Modbus"""
    # Configuración de conexión
    protocol: str = "tcp"  # "tcp", "rtu", "ascii"
    host: str = "localhost"
    port: int = 502  # Puerto por defecto para Modbus TCP
    
    # Configuración de dispositivo
    device_id: int = 1  # ID del dispositivo Modbus
    timeout: float = 3.0
    retries: int = 3
    retry_delay: float = 1.0
    
    # Configuración de registros a leer
    registers: List[Dict[str, Any]] = None  # Lista de registros a monitorear
    scan_interval: float = 5.0  # Segundos entre lecturas
    
    # Configuración de datos
    parse_registers: bool = True
    scale_values: bool = True
    data_types: Dict[str, str] = None  # Mapeo de registros a tipos de datos
    
    def __post_init__(self):
        if self.registers is None:
            # Registros por defecto para un dispositivo típico
            self.registers = [
                {'address': 0, 'count': 10, 'type': 'holding', 'name': 'temperatures'},
                {'address': 10, 'count': 5, 'type': 'input', 'name': 'pressures'},
                {'address': 20, 'count': 3, 'type': 'holding', 'name': 'status'}
            ]
        if self.data_types is None:
            self.data_types = {}


class ModbusConnector(BaseConnector):
    """
    Conector Modbus que recibe datos desde dispositivos industriales
    
    Este conector se conecta a dispositivos Modbus y lee registros
    de forma periódica para obtener datos de sensores y equipos.
    """
    
    def __init__(self, config: ModbusConnectorConfig, data_callback=None):
        super().__init__(config, data_callback)
        
        # Configuración específica de Modbus
        self.modbus_config = ModbusConnectorConfig(**config.__dict__) if isinstance(config, ConnectorConfig) else config
        
        # Cliente Modbus
        self.modbus_client = None
        
        # Estado de conexión
        self.last_scan_time: Optional[datetime] = None
        self.scan_thread: Optional[threading.Thread] = None
        
        # Cache de registros
        self.register_cache: Dict[str, Any] = {}
        
        # Logging específico
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def connect(self) -> bool:
        """Conecta al dispositivo Modbus"""
        try:
            self.logger.info(f"🔌 Conectando a dispositivo Modbus ({self.modbus_config.protocol}) en {self.modbus_config.host}:{self.modbus_config.port}")
            
            # Crear cliente Modbus según el protocolo
            if self.modbus_config.protocol.lower() == "tcp":
                self.modbus_client = self._create_tcp_client()
            elif self.modbus_config.protocol.lower() == "rtu":
                self.modbus_client = self._create_rtu_client()
            elif self.modbus_config.protocol.lower() == "ascii":
                self.modbus_client = self._create_ascii_client()
            else:
                self.logger.error(f"Protocolo Modbus no soportado: {self.modbus_config.protocol}")
                return False
            
            if not self.modbus_client:
                self.logger.error("No se pudo crear el cliente Modbus")
                return False
            
            # Conectar al dispositivo
            if self._modbus_connect():
                self.status = ConnectorStatus.CONNECTED
                self.connected = True
                self.last_connection_time = datetime.now(timezone.utc)
                
                # Iniciar thread de escaneo
                self._start_scan_thread()
                
                self.logger.info(f"✅ Conectado al dispositivo Modbus en {self.modbus_config.host}:{self.modbus_config.port}")
                return True
            else:
                self.logger.error("❌ No se pudo conectar al dispositivo Modbus")
                self.status = ConnectorStatus.ERROR
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error conectando a Modbus: {e}")
            self.status = ConnectorStatus.ERROR
            self._handle_connection_error(e)
            return False
    
    def disconnect(self) -> bool:
        """Desconecta del dispositivo Modbus"""
        try:
            # Detener thread de escaneo
            if self.scan_thread and self.scan_thread.is_alive():
                self.scan_thread.join(timeout=5.0)
            
            # Desconectar cliente Modbus
            if self.modbus_client:
                self._modbus_disconnect()
                self.modbus_client = None
            
            self.status = ConnectorStatus.DISCONNECTED
            self.connected = False
            self.register_cache.clear()
            
            self.logger.info("✅ Desconectado del dispositivo Modbus")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error desconectando de Modbus: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Verifica si está conectado al dispositivo Modbus"""
        return self.connected and self.modbus_client is not None
    
    def _receive_data(self) -> Optional[Any]:
        """
        Recibe datos del dispositivo Modbus
        
        Los datos se reciben de forma periódica a través del thread de escaneo.
        No necesitamos implementar polling aquí.
        """
        return None
    
    def _parse_raw_data(self, raw_data: Any) -> Optional[UnifiedDataFormat]:
        """
        Parsea datos Modbus al formato unificado
        
        Args:
            raw_data: Datos Modbus (dict con registros leídos)
            
        Returns:
            Datos en formato unificado
        """
        try:
            if not isinstance(raw_data, dict):
                self.logger.warning(f"Formato de datos Modbus no reconocido: {type(raw_data)}")
                return None
            
            # Extraer información básica
            timestamp = raw_data.get('timestamp', datetime.now(timezone.utc))
            registers = raw_data.get('registers', {})
            
            # Parsear registros según la configuración
            measurements = self._parse_modbus_registers(registers)
            
            # Crear datos unificados
            unified_data = UnifiedDataFormat(
                device_id=f"modbus_{self.modbus_config.device_id}",
                project_id="industrial",
                timestamp=timestamp,
                measurements=measurements,
                metadata={
                    'protocol': self.modbus_config.protocol,
                    'host': self.modbus_config.host,
                    'port': self.modbus_config.port,
                    'device_id': self.modbus_config.device_id,
                    'registers_read': len(registers),
                    'scan_time': timestamp.isoformat()
                },
                quality=DataQuality.VALID,
                source_protocol='modbus',
                source_address=f"{self.modbus_config.host}:{self.modbus_config.port}",
                raw_data=raw_data
            )
            
            return unified_data
            
        except Exception as e:
            self.logger.error(f"Error parseando datos Modbus: {e}")
            return None
    
    def _parse_modbus_registers(self, registers: Dict[str, Any]) -> Dict[str, Any]:
        """Parsea los registros Modbus leídos"""
        try:
            measurements = {}
            
            for register_name, register_data in registers.items():
                try:
                    if self.modbus_config.parse_registers:
                        # Parsear según el tipo de registro
                        parsed_value = self._parse_register_value(register_name, register_data)
                        if parsed_value is not None:
                            measurements[register_name] = parsed_value
                    else:
                        # Usar valor crudo
                        measurements[register_name] = register_data
                        
                except Exception as e:
                    self.logger.warning(f"Error parseando registro {register_name}: {e}")
                    measurements[f"{register_name}_error"] = str(e)
            
            return measurements
            
        except Exception as e:
            self.logger.error(f"Error parseando registros Modbus: {e}")
            return {'error': str(e)}
    
    def _parse_register_value(self, register_name: str, register_data: Any) -> Any:
        """Parsea un valor de registro específico"""
        try:
            # Obtener tipo de dato configurado
            data_type = self.modbus_config.data_types.get(register_name, 'auto')
            
            if data_type == 'auto':
                # Detectar tipo automáticamente
                if isinstance(register_data, (list, tuple)):
                    if len(register_data) == 1:
                        return register_data[0]
                    elif len(register_data) == 2:
                        # Combinar dos registros de 16 bits en uno de 32 bits
                        return (register_data[0] << 16) | register_data[1]
                    else:
                        return register_data
                else:
                    return register_data
            
            elif data_type == 'int16':
                return int(register_data) if isinstance(register_data, (list, tuple)) else register_data
            
            elif data_type == 'int32':
                if isinstance(register_data, (list, tuple)) and len(register_data) >= 2:
                    return (register_data[0] << 16) | register_data[1]
                return register_data
            
            elif data_type == 'float32':
                if isinstance(register_data, (list, tuple)) and len(register_data) >= 2:
                    # Convertir dos registros de 16 bits a float de 32 bits
                    import struct
                    raw_bytes = struct.pack('>HH', register_data[0], register_data[1])
                    return struct.unpack('>f', raw_bytes)[0]
                return float(register_data)
            
            elif data_type == 'boolean':
                return bool(register_data)
            
            else:
                return register_data
                
        except Exception as e:
            self.logger.error(f"Error parseando valor del registro {register_name}: {e}")
            return register_data
    
    def _create_tcp_client(self):
        """Crea un cliente Modbus TCP"""
        try:
            from pymodbus.client import ModbusTcpClient
            
            client = ModbusTcpClient(
                host=self.modbus_config.host,
                port=self.modbus_config.port,
                timeout=self.modbus_config.timeout,
                retries=self.modbus_config.retries,
                retry_on_empty=True
            )
            
            return client
            
        except ImportError:
            self.logger.error("Biblioteca pymodbus no disponible. Instala con: pip install pymodbus")
            return None
        except Exception as e:
            self.logger.error(f"Error creando cliente Modbus TCP: {e}")
            return None
    
    def _create_rtu_client(self):
        """Crea un cliente Modbus RTU"""
        try:
            from pymodbus.client import ModbusSerialClient
            
            # Configuración por defecto para RTU
            client = ModbusSerialClient(
                method='rtu',
                port='/dev/ttyUSB0',  # Puerto por defecto
                baudrate=9600,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=self.modbus_config.timeout
            )
            
            return client
            
        except ImportError:
            self.logger.error("Biblioteca pymodbus no disponible. Instala con: pip install pymodbus")
            return None
        except Exception as e:
            self.logger.error(f"Error creando cliente Modbus RTU: {e}")
            return None
    
    def _create_ascii_client(self):
        """Crea un cliente Modbus ASCII"""
        try:
            from pymodbus.client import ModbusSerialClient
            
            # Configuración por defecto para ASCII
            client = ModbusSerialClient(
                method='ascii',
                port='/dev/ttyUSB0',  # Puerto por defecto
                baudrate=9600,
                bytesize=7,
                parity='E',
                stopbits=1,
                timeout=self.modbus_config.timeout
            )
            
            return client
            
        except ImportError:
            self.logger.error("Biblioteca pymodbus no disponible. Instala con: pip install pymodbus")
            return None
        except Exception as e:
            self.logger.error(f"Error creando cliente Modbus ASCII: {e}")
            return None
    
    def _modbus_connect(self) -> bool:
        """Conecta el cliente Modbus"""
        try:
            if self.modbus_client:
                return self.modbus_client.connect()
            return False
        except Exception as e:
            self.logger.error(f"Error conectando cliente Modbus: {e}")
            return False
    
    def _modbus_disconnect(self):
        """Desconecta el cliente Modbus"""
        try:
            if self.modbus_client:
                self.modbus_client.close()
        except Exception as e:
            self.logger.error(f"Error desconectando cliente Modbus: {e}")
    
    def _start_scan_thread(self):
        """Inicia el thread de escaneo de registros"""
        self.scan_thread = threading.Thread(
            target=self._scan_registers_loop,
            daemon=True,
            name=f"Modbus_Scanner_{self.config.name}"
        )
        self.scan_thread.start()
        self.logger.info("✅ Thread de escaneo Modbus iniciado")
    
    def _scan_registers_loop(self):
        """Loop principal de escaneo de registros"""
        self.logger.info("🔄 Iniciando loop de escaneo de registros Modbus")
        
        while self.connected and not self.stop_event.is_set():
            try:
                # Leer registros configurados
                self._read_all_registers()
                
                # Esperar hasta el siguiente escaneo
                time.sleep(self.modbus_config.scan_interval)
                
            except Exception as e:
                self.logger.error(f"Error en loop de escaneo Modbus: {e}")
                time.sleep(5)  # Esperar antes de reintentar
        
        self.logger.info("🛑 Loop de escaneo Modbus detenido")
    
    def _read_all_registers(self):
        """Lee todos los registros configurados"""
        try:
            if not self.is_connected():
                return
            
            registers_data = {}
            timestamp = datetime.now(timezone.utc)
            
            for register_config in self.modbus_config.registers:
                try:
                    register_data = self._read_register(register_config)
                    if register_data is not None:
                        registers_data[register_config['name']] = register_data
                        
                except Exception as e:
                    self.logger.warning(f"Error leyendo registro {register_config.get('name', 'unknown')}: {e}")
            
            if registers_data:
                # Crear datos unificados
                raw_data = {
                    'timestamp': timestamp,
                    'registers': registers_data
                }
                
                unified_data = self._parse_raw_data(raw_data)
                if unified_data and self.data_callback:
                    self.data_callback(unified_data)
                
                # Actualizar cache
                self.register_cache.update(registers_data)
                self.last_scan_time = timestamp
                
                self.logger.debug(f"📊 Registros Modbus leídos: {len(registers_data)} registros")
            
        except Exception as e:
            self.logger.error(f"Error leyendo registros Modbus: {e}")
    
    def _read_register(self, register_config: Dict[str, Any]) -> Optional[Any]:
        """Lee un registro específico"""
        try:
            address = register_config['address']
            count = register_config['count']
            register_type = register_config['type']
            
            if register_type == 'holding':
                result = self.modbus_client.read_holding_registers(
                    address=address,
                    count=count,
                    slave=self.modbus_config.device_id
                )
            elif register_type == 'input':
                result = self.modbus_client.read_input_registers(
                    address=address,
                    count=count,
                    slave=self.modbus_config.device_id
                )
            elif register_type == 'coil':
                result = self.modbus_client.read_coils(
                    address=address,
                    count=count,
                    slave=self.modbus_config.device_id
                )
            elif register_type == 'discrete':
                result = self.modbus_client.read_discrete_inputs(
                    address=address,
                    count=count,
                    slave=self.modbus_config.device_id
                )
            else:
                self.logger.warning(f"Tipo de registro no soportado: {register_type}")
                return None
            
            if result.isError():
                self.logger.warning(f"Error leyendo registro {address}: {result}")
                return None
            
            # Extraer valores del resultado
            if hasattr(result, 'registers'):
                return result.registers
            elif hasattr(result, 'bits'):
                return result.bits
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error leyendo registro {register_config.get('name', 'unknown')}: {e}")
            return None
    
    def get_register_cache(self) -> Dict[str, Any]:
        """Obtiene el cache de registros"""
        return self.register_cache.copy()
    
    def get_last_scan_time(self) -> Optional[datetime]:
        """Obtiene el tiempo del último escaneo"""
        return self.last_scan_time
    
    def add_register(self, register_config: Dict[str, Any]) -> bool:
        """Agrega un nuevo registro para monitorear"""
        try:
            # Validar configuración del registro
            required_fields = ['address', 'count', 'type', 'name']
            for field in required_fields:
                if field not in register_config:
                    self.logger.error(f"Campo requerido '{field}' no está presente en la configuración del registro")
                    return False
            
            # Agregar a la lista de registros
            self.modbus_config.registers.append(register_config)
            
            self.logger.info(f"✅ Registro agregado: {register_config['name']} en {register_config['address']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error agregando registro: {e}")
            return False
    
    def remove_register(self, register_name: str) -> bool:
        """Remueve un registro del monitoreo"""
        try:
            # Buscar y remover el registro
            for i, register in enumerate(self.modbus_config.registers):
                if register.get('name') == register_name:
                    del self.modbus_config.registers[i]
                    self.logger.info(f"✅ Registro removido: {register_name}")
                    return True
            
            self.logger.warning(f"Registro no encontrado: {register_name}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error removiendo registro: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del conector Modbus"""
        status = super().get_status()
        status.update({
            'protocol': self.modbus_config.protocol,
            'host': self.modbus_config.host,
            'port': self.modbus_config.port,
            'device_id': self.modbus_config.device_id,
            'registers_monitored': len(self.modbus_config.registers),
            'register_cache_size': len(self.register_cache),
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'scan_interval': self.modbus_config.scan_interval
        })
        return status
