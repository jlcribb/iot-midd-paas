"""
Pipeline de Datos - IoT Middleware
==================================

Este módulo implementa el flujo completo de datos desde la entrada
hasta la persistencia, incluyendo normalización y almacenamiento.
"""

import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from queue import Queue
import uuid

from ..input.base_connector import UnifiedDataFormat, DataQuality
from ..storage.db_handler import PostgreSQLHandler, InfluxDBHandler
from ..models.entities import Cliente, Proyecto, UnidadProyecto, Dispositivo
from ..config.config_loader import PostgreSQLConfig, InfluxDBConfig


@dataclass
class PipelineConfig:
    """Configuración del pipeline de datos"""
    enabled: bool = True
    name: str = "data_pipeline"
    batch_size: int = 100
    batch_timeout: float = 5.0
    enable_postgresql: bool = True
    enable_influxdb: bool = True
    enable_audit: bool = True
    data_validation: bool = True
    error_handling: bool = True
    metrics_collection: bool = True


@dataclass
class PipelineMetrics:
    """Métricas del pipeline de datos"""
    total_messages: int = 0
    processed_messages: int = 0
    failed_messages: int = 0
    postgresql_operations: int = 0
    influxdb_operations: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None
    processing_rate: float = 0.0  # mensajes por segundo
    error_rate: float = 0.0  # porcentaje de errores


class DataNormalizer:
    """Normalizador de datos que convierte UnifiedDataFormat al modelo interno"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.cache = {}  # Cache para entidades frecuentemente usadas
        
    def normalize_data(self, unified_data: UnifiedDataFormat) -> Dict[str, Any]:
        """Normalizar datos unificados al modelo interno"""
        try:
            # Extraer información del device_id y project_id
            device_info = self._parse_device_id(unified_data.device_id)
            project_info = self._parse_project_id(unified_data.project_id)
            
            # Crear estructura normalizada
            normalized = {
                "cliente": {
                    "nombre": project_info.get("cliente", "Demo Cliente"),
                    "sector": "Tecnología",
                    "industria": "IoT",
                    "activo": True
                },
                "proyecto": {
                    "nombre": project_info.get("proyecto", "Demo Proyecto"),
                    "descripcion": f"Proyecto de demostración para {unified_data.source_protocol}",
                    "estado": "ACTIVO",
                    "activo": True
                },
                "unidad": {
                    "nombre": project_info.get("unidad", "Unidad Principal"),
                    "descripcion": "Unidad de demostración",
                    "activo": True
                },
                "sesion": {
                    "nombre": f"Sesión {unified_data.source_protocol}",
                    "descripcion": f"Sesión de datos {unified_data.source_protocol}",
                    "activo": True
                },
                "dispositivo": {
                    "nombre": device_info.get("nombre", unified_data.device_id),
                    "tipo": device_info.get("tipo", "sensor"),
                    "protocolo": unified_data.source_protocol,
                    "direccion": unified_data.source_address,
                    "activo": True
                },
                "lectura": {
                    "timestamp": unified_data.timestamp,
                    "mediciones": unified_data.measurements,
                    "calidad": unified_data.quality.value,
                    "metadata": unified_data.metadata,
                    "raw_data": unified_data.raw_data
                }
            }
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error normalizando datos: {e}")
            return None
            
    def _parse_device_id(self, device_id: str) -> Dict[str, str]:
        """Parsear device_id para extraer información"""
        if device_id.startswith("mqtt_device_"):
            return {"nombre": device_id, "tipo": "sensor"}
        elif device_id.startswith("http_device_"):
            return {"nombre": device_id, "tipo": "actuador"}
        elif device_id.startswith("ble_"):
            return {"nombre": device_id, "tipo": "sensor_ble"}
        elif device_id.startswith("lora_"):
            return {"nombre": device_id, "tipo": "sensor_lora"}
        elif device_id.startswith("midi_channel_"):
            return {"nombre": device_id, "tipo": "controlador_midi"}
        elif device_id.startswith("modbus_device_"):
            return {"nombre": device_id, "tipo": "dispositivo_modbus"}
        elif device_id.startswith("zigbee_"):
            return {"nombre": device_id, "tipo": "dispositivo_zigbee"}
        else:
            return {"nombre": device_id, "tipo": "dispositivo"}
            
    def _parse_project_id(self, project_id: str) -> Dict[str, str]:
        """Parsear project_id para extraer información"""
        if project_id.startswith("demo_"):
            protocol = project_id.split("_")[1]
            return {
                "cliente": "Demo Cliente",
                "proyecto": f"Demo {protocol.upper()}",
                "unidad": "Unidad Principal"
            }
        else:
            return {
                "cliente": "Cliente Default",
                "proyecto": project_id,
                "unidad": "Unidad Default"
            }


class DataValidator:
    """Validador de datos antes de la persistencia"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def validate_data(self, unified_data: UnifiedDataFormat) -> Dict[str, Any]:
        """Validar datos unificados"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "quality_score": 1.0
        }
        
        # Validar campos requeridos
        if not unified_data.device_id:
            validation_result["valid"] = False
            validation_result["errors"].append("device_id es requerido")
            
        if not unified_data.project_id:
            validation_result["valid"] = False
            validation_result["errors"].append("project_id es requerido")
            
        if not unified_data.timestamp:
            validation_result["valid"] = False
            validation_result["errors"].append("timestamp es requerido")
            
        if not unified_data.measurements:
            validation_result["valid"] = False
            validation_result["errors"].append("measurements es requerido")
            
        # Validar calidad de datos
        if unified_data.quality == DataQuality.ERROR:
            validation_result["warnings"].append("Datos marcados como error")
            validation_result["quality_score"] *= 0.5
            
        if unified_data.quality == DataQuality.INVALID:
            validation_result["warnings"].append("Datos marcados como inválidos")
            validation_result["quality_score"] *= 0.3
            
        # Validar timestamp (no debe ser futuro)
        if unified_data.timestamp > datetime.now() + timedelta(minutes=5):
            validation_result["warnings"].append("Timestamp en el futuro")
            validation_result["quality_score"] *= 0.8
            
        # Validar measurements (debe ser dict)
        if not isinstance(unified_data.measurements, dict):
            validation_result["valid"] = False
            validation_result["errors"].append("measurements debe ser un diccionario")
            
        return validation_result


class DataPipeline:
    """Pipeline principal de procesamiento de datos"""
    
    def __init__(self, config: PipelineConfig, 
                 postgresql_config: Optional[PostgreSQLConfig] = None,
                 influxdb_config: Optional[InfluxDBConfig] = None):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Componentes del pipeline
        self.normalizer = DataNormalizer()
        self.validator = DataValidator()
        
        # Almacenamiento
        self.postgresql_handler = None
        self.influxdb_handler = None
        
        if config.enable_postgresql and postgresql_config:
            try:
                self.postgresql_handler = PostgreSQLHandler(postgresql_config)
                self.logger.info("PostgreSQL handler inicializado")
            except Exception as e:
                self.logger.error(f"Error inicializando PostgreSQL: {e}")
                
        if config.enable_influxdb and influxdb_config:
            try:
                self.influxdb_handler = InfluxDBHandler(influxdb_config)
                self.logger.info("InfluxDB handler inicializado")
            except Exception as e:
                self.logger.error(f"Error inicializando InfluxDB: {e}")
                
        # Cola de procesamiento
        self.data_queue = Queue(maxsize=1000)
        self.processing_thread = None
        self.running = False
        
        # Métricas
        self.metrics = PipelineMetrics()
        self.metrics_thread = None
        
    def start(self):
        """Iniciar el pipeline"""
        if self.running:
            return False
            
        self.running = True
        
        # Iniciar thread de procesamiento
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        # Iniciar thread de métricas
        if self.config.metrics_collection:
            self.metrics_thread = threading.Thread(target=self._metrics_loop, daemon=True)
            self.metrics_thread.start()
            
        self.logger.info("Data pipeline iniciado")
        return True
        
    def stop(self):
        """Detener el pipeline"""
        self.running = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=10.0)
            
        if self.metrics_thread:
            self.metrics_thread.join(timeout=5.0)
            
        self.logger.info("Data pipeline detenido")
        
    def process_data(self, unified_data: UnifiedDataFormat):
        """Procesar datos unificados (interfaz pública)"""
        try:
            self.data_queue.put(unified_data, timeout=1.0)
            self.metrics.total_messages += 1
        except Exception as e:
            self.logger.error(f"Error encolando datos: {e}")
            self.metrics.failed_messages += 1
            
    def _processing_loop(self):
        """Bucle principal de procesamiento"""
        batch = []
        last_batch_time = time.time()
        
        while self.running:
            try:
                # Obtener datos de la cola
                try:
                    data = self.data_queue.get(timeout=1.0)
                    batch.append(data)
                except:
                    continue
                    
                # Procesar batch si está lleno o ha pasado el timeout
                current_time = time.time()
                if (len(batch) >= self.config.batch_size or 
                    (batch and current_time - last_batch_time >= self.config.batch_timeout)):
                    
                    self._process_batch(batch)
                    batch = []
                    last_batch_time = current_time
                    
            except Exception as e:
                self.logger.error(f"Error en bucle de procesamiento: {e}")
                time.sleep(1.0)
                
        # Procesar batch final
        if batch:
            self._process_batch(batch)
            
    def _process_batch(self, batch: List[UnifiedDataFormat]):
        """Procesar un lote de datos"""
        for data in batch:
            try:
                # Validar datos
                validation = self.validator.validate_data(data)
                if not validation["valid"]:
                    self.logger.warning(f"Datos inválidos: {validation['errors']}")
                    self.metrics.failed_messages += 1
                    continue
                    
                # Normalizar datos
                normalized = self.normalizer.normalize_data(data)
                if not normalized:
                    self.logger.error("Error normalizando datos")
                    self.metrics.failed_messages += 1
                    continue
                    
                # Persistir datos
                self._persist_data(normalized, data)
                
                self.metrics.processed_messages += 1
                self.metrics.last_activity = datetime.now()
                
            except Exception as e:
                self.logger.error(f"Error procesando datos: {e}")
                self.metrics.failed_messages += 1
                
    def _persist_data(self, normalized: Dict[str, Any], original_data: UnifiedDataFormat):
        """Persistir datos normalizados"""
        try:
            # Persistir en PostgreSQL si está habilitado
            if self.postgresql_handler and self.config.enable_postgresql:
                self._persist_to_postgresql(normalized, original_data)
                
            # Persistir en InfluxDB si está habilitado
            if self.influxdb_handler and self.config.enable_influxdb:
                self._persist_to_influxdb(normalized, original_data)
                
        except Exception as e:
            self.logger.error(f"Error persistiendo datos: {e}")
            
    def _persist_to_postgresql(self, normalized: Dict[str, Any], original_data: UnifiedDataFormat):
        """Persistir datos en PostgreSQL"""
        try:
            # Aquí implementarías la lógica de persistencia usando los modelos SQLAlchemy
            # Por ahora, solo registramos la operación
            self.metrics.postgresql_operations += 1
            
            # TODO: Implementar persistencia real con SQLAlchemy
            # - Crear/actualizar Cliente
            # - Crear/actualizar Proyecto
            # - Crear/actualizar UnidadProyecto
            # - Crear/actualizar SesionDispositivo
            # - Crear/actualizar Dispositivo
            # - Crear LecturaDatos
            
        except Exception as e:
            self.logger.error(f"Error persistencia PostgreSQL: {e}")
            
    def _persist_to_influxdb(self, normalized: Dict[str, Any], original_data: UnifiedDataFormat):
        """Persistir datos en InfluxDB"""
        try:
            # Preparar datos para InfluxDB
            point_data = {
                "measurement": "iot_data",
                "tags": {
                    "cliente": normalized["cliente"]["nombre"],
                    "proyecto": normalized["proyecto"]["nombre"],
                    "unidad": normalized["unidad"]["nombre"],
                    "dispositivo": normalized["dispositivo"]["nombre"],
                    "protocolo": original_data.source_protocol,
                    "calidad": original_data.quality.value
                },
                "fields": {
                    **original_data.measurements,
                    "device_id": original_data.device_id,
                    "project_id": original_data.project_id
                },
                "time": original_data.timestamp
            }
            
            # Enviar a InfluxDB
            if self.influxdb_handler:
                # TODO: Implementar envío real a InfluxDB
                # self.influxdb_handler.write_point(point_data)
                self.metrics.influxdb_operations += 1
                
        except Exception as e:
            self.logger.error(f"Error persistencia InfluxDB: {e}")
            
    def _metrics_loop(self):
        """Bucle de actualización de métricas"""
        while self.running:
            try:
                # Calcular métricas
                uptime = (datetime.now() - self.metrics.start_time).total_seconds()
                if uptime > 0:
                    self.metrics.processing_rate = self.metrics.processed_messages / uptime
                    
                if self.metrics.total_messages > 0:
                    self.metrics.error_rate = (self.metrics.failed_messages / self.metrics.total_messages) * 100
                    
                # Log métricas cada minuto
                if self.metrics.last_activity:
                    time_since_activity = (datetime.now() - self.metrics.last_activity).total_seconds()
                    if time_since_activity < 60:  # Solo si ha habido actividad reciente
                        self.logger.info(f"Métricas: {self.metrics.processed_messages} procesados, "
                                       f"{self.metrics.failed_messages} fallidos, "
                                       f"Rate: {self.metrics.processing_rate:.2f} msg/s")
                        
                time.sleep(60)  # Actualizar cada minuto
                
            except Exception as e:
                self.logger.error(f"Error en bucle de métricas: {e}")
                time.sleep(60)
                
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del pipeline"""
        return {
            "total_messages": self.metrics.total_messages,
            "processed_messages": self.metrics.processed_messages,
            "failed_messages": self.metrics.failed_messages,
            "postgresql_operations": self.metrics.postgresql_operations,
            "influxdb_operations": self.metrics.influxdb_operations,
            "start_time": self.metrics.start_time.isoformat(),
            "last_activity": self.metrics.last_activity.isoformat() if self.metrics.last_activity else None,
            "processing_rate": self.metrics.processing_rate,
            "error_rate": self.metrics.error_rate,
            "queue_size": self.data_queue.qsize(),
            "running": self.running
        }
        
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del pipeline"""
        return {
            "name": self.config.name,
            "enabled": self.config.enabled,
            "running": self.running,
            "postgresql_connected": self.postgresql_handler is not None,
            "influxdb_connected": self.influxdb_handler is not None,
            "metrics": self.get_metrics()
        }
