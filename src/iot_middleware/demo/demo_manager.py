"""
Gestor de Demostración - IoT Middleware
========================================

Este módulo orquesta la demostración completa del flujo de datos,
incluyendo simuladores, pipeline de procesamiento y generación de informes.
"""

import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import os

from .data_simulators import (
    MQTTSimulator, HTTPSimulator, BLESimulator, LoRaSimulator,
    MIDISimulator, ModbusSimulator, ZigBeeSimulator, SimulatorConfig
)
from .data_pipeline import DataPipeline, PipelineConfig
from .report_generator import ReportGenerator
from ..input.base_connector import UnifiedDataFormat


@dataclass
class DemoConfig:
    """Configuración de la demostración"""
    name: str = "IoT Middleware Demo"
    duration_minutes: int = 10
    enable_protocols: List[str] = field(default_factory=lambda: [
        "mqtt", "http", "ble", "lora", "midi", "modbus", "zigbee"
    ])
    data_interval: float = 2.0  # Segundos entre datos por protocolo
    data_count_per_protocol: int = 50  # Datos por protocolo
    enable_pipeline: bool = True
    enable_postgresql: bool = True
    enable_influxdb: bool = True
    output_directory: str = "demo_outputs"
    generate_reports: bool = True
    real_time_monitoring: bool = True


@dataclass
class DemoMetrics:
    """Métricas de la demostración"""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_data_generated: int = 0
    total_data_processed: int = 0
    total_data_persisted: int = 0
    protocol_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    pipeline_metrics: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class DemoManager:
    """Gestor principal de la demostración"""
    
    def __init__(self, config: DemoConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Componentes de la demostración
        self.simulators: Dict[str, Any] = {}
        self.pipeline: Optional[DataPipeline] = None
        self.report_generator: Optional[ReportGenerator] = None
        
        # Estado y métricas
        self.metrics = DemoMetrics()
        self.running = False
        self.monitoring_thread = None
        
        # Callback para datos simulados
        self.data_callback = self._on_simulated_data
        
        # Configurar logging
        self._setup_logging()
        
        # Crear directorio de salida
        os.makedirs(self.config.output_directory, exist_ok=True)
        
    def _setup_logging(self):
        """Configurar logging para la demostración"""
        log_file = os.path.join(self.config.output_directory, f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        # Configurar handler de archivo
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Configurar handler de consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Agregar handlers al logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)
        
    def initialize(self) -> bool:
        """Inicializar todos los componentes de la demostración"""
        try:
            self.logger.info("Inicializando demostración...")
            
            # Inicializar pipeline si está habilitado
            if self.config.enable_pipeline:
                self._initialize_pipeline()
                
            # Inicializar simuladores
            self._initialize_simulators()
            
            # Inicializar generador de informes
            if self.config.generate_reports:
                self.report_generator = ReportGenerator(self.config.output_directory)
                
            self.logger.info("Demostración inicializada correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando demostración: {e}")
            return False
            
    def _initialize_pipeline(self):
        """Inicializar el pipeline de datos"""
        try:
            pipeline_config = PipelineConfig(
                enabled=True,
                name="demo_pipeline",
                batch_size=50,
                batch_timeout=2.0,
                enable_postgresql=self.config.enable_postgresql,
                enable_influxdb=self.config.enable_influxdb,
                enable_audit=True,
                data_validation=True,
                error_handling=True,
                metrics_collection=True
            )
            
            # Por ahora, no pasamos configs de BD (usar None)
            self.pipeline = DataPipeline(pipeline_config)
            self.logger.info("Pipeline de datos inicializado")
            
        except Exception as e:
            self.logger.error(f"Error inicializando pipeline: {e}")
            
    def _initialize_simulators(self):
        """Inicializar simuladores para protocolos habilitados"""
        try:
            for protocol in self.config.enable_protocols:
                if protocol == "mqtt":
                    config = SimulatorConfig(
                        enabled=True,
                        name=f"MQTT Simulator",
                        protocol="mqtt",
                        data_interval=self.config.data_interval,
                        data_count=self.config.data_count_per_protocol
                    )
                    self.simulators[protocol] = MQTTSimulator(config, self.data_callback)
                    
                elif protocol == "http":
                    config = SimulatorConfig(
                        enabled=True,
                        name=f"HTTP Simulator",
                        protocol="http",
                        data_interval=self.config.data_interval,
                        data_count=self.config.data_count_per_protocol
                    )
                    self.simulators[protocol] = HTTPSimulator(config, self.data_callback)
                    
                elif protocol == "ble":
                    config = SimulatorConfig(
                        enabled=True,
                        name=f"BLE Simulator",
                        protocol="ble",
                        data_interval=self.config.data_interval,
                        data_count=self.config.data_count_per_protocol
                    )
                    self.simulators[protocol] = BLESimulator(config, self.data_callback)
                    
                elif protocol == "lora":
                    config = SimulatorConfig(
                        enabled=True,
                        name=f"LoRa Simulator",
                        protocol="lora",
                        data_interval=self.config.data_interval,
                        data_count=self.config.data_count_per_protocol
                    )
                    self.simulators[protocol] = LoRaSimulator(config, self.data_callback)
                    
                elif protocol == "midi":
                    config = SimulatorConfig(
                        enabled=True,
                        name=f"MIDI Simulator",
                        protocol="midi",
                        data_interval=self.config.data_interval,
                        data_count=self.config.data_count_per_protocol
                    )
                    self.simulators[protocol] = MIDISimulator(config, self.data_callback)
                    
                elif protocol == "modbus":
                    config = SimulatorConfig(
                        enabled=True,
                        name=f"Modbus Simulator",
                        protocol="modbus",
                        data_interval=self.config.data_interval,
                        data_count=self.config.data_count_per_protocol
                    )
                    self.simulators[protocol] = ModbusSimulator(config, self.data_callback)
                    
                elif protocol == "zigbee":
                    config = SimulatorConfig(
                        enabled=True,
                        name=f"ZigBee Simulator",
                        protocol="zigbee",
                        data_interval=self.config.data_interval,
                        data_count=self.config.data_count_per_protocol
                    )
                    self.simulators[protocol] = ZigBeeSimulator(config, self.data_callback)
                    
                self.logger.info(f"Simulador {protocol} inicializado")
                
        except Exception as e:
            self.logger.error(f"Error inicializando simuladores: {e}")
            
    def start(self) -> bool:
        """Iniciar la demostración"""
        if self.running:
            self.logger.warning("La demostración ya está ejecutándose")
            return False
            
        try:
            self.logger.info("Iniciando demostración...")
            self.running = True
            self.metrics.start_time = datetime.now()
            
            # Iniciar pipeline
            if self.pipeline:
                self.pipeline.start()
                
            # Iniciar simuladores
            for protocol, simulator in self.simulators.items():
                simulator.start()
                self.logger.info(f"Simulador {protocol} iniciado")
                
            # Iniciar monitoreo en tiempo real
            if self.config.real_time_monitoring:
                self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
                self.monitoring_thread.start()
                
            # Programar parada automática
            if self.config.duration_minutes > 0:
                stop_timer = threading.Timer(
                    self.config.duration_minutes * 60, 
                    self.stop
                )
                stop_timer.daemon = True
                stop_timer.start()
                
            self.logger.info(f"Demostración iniciada. Duración: {self.config.duration_minutes} minutos")
            return True
            
        except Exception as e:
            self.logger.error(f"Error iniciando demostración: {e}")
            return False
            
    def stop(self) -> bool:
        """Detener la demostración"""
        if not self.running:
            return False
            
        try:
            self.logger.info("Deteniendo demostración...")
            self.running = False
            self.metrics.end_time = datetime.now()
            
            # Detener simuladores
            for protocol, simulator in self.simulators.items():
                simulator.stop()
                self.logger.info(f"Simulador {protocol} detenido")
                
            # Detener pipeline
            if self.pipeline:
                self.pipeline.stop()
                
            # Generar informe final
            if self.report_generator:
                self._generate_final_report()
                
            self.logger.info("Demostración detenida")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deteniendo demostración: {e}")
            return False
            
    def _on_simulated_data(self, unified_data: UnifiedDataFormat):
        """Callback para datos simulados"""
        try:
            # Actualizar métricas
            self.metrics.total_data_generated += 1
            
            # Actualizar métricas por protocolo
            protocol = unified_data.source_protocol
            if protocol not in self.metrics.protocol_metrics:
                self.metrics.protocol_metrics[protocol] = {
                    "data_generated": 0,
                    "data_processed": 0,
                    "last_data_time": None,
                    "device_count": set()
                }
                
            self.metrics.protocol_metrics[protocol]["data_generated"] += 1
            self.metrics.protocol_metrics[protocol]["last_data_time"] = datetime.now()
            self.metrics.protocol_metrics[protocol]["device_count"].add(unified_data.device_id)
            
            # Enviar al pipeline si está habilitado
            if self.pipeline:
                self.pipeline.process_data(unified_data)
                self.metrics.total_data_processed += 1
                
            # Log cada 10 datos para no saturar
            if self.metrics.total_data_generated % 10 == 0:
                self.logger.info(f"Datos generados: {self.metrics.total_data_generated}, "
                               f"Procesados: {self.metrics.total_data_processed}")
                
        except Exception as e:
            error_msg = f"Error procesando datos simulados: {e}"
            self.logger.error(error_msg)
            self.metrics.errors.append(error_msg)
            
    def _monitoring_loop(self):
        """Bucle de monitoreo en tiempo real"""
        while self.running:
            try:
                # Mostrar estado cada 30 segundos
                self._log_current_status()
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error en monitoreo: {e}")
                time.sleep(30)
                
    def _log_current_status(self):
        """Mostrar estado actual de la demostración"""
        try:
            # Calcular tiempo transcurrido
            elapsed = datetime.now() - self.metrics.start_time
            elapsed_minutes = elapsed.total_seconds() / 60
            
            # Obtener métricas del pipeline
            pipeline_status = "N/A"
            if self.pipeline:
                pipeline_metrics = self.pipeline.get_metrics()
                pipeline_status = f"Rate: {pipeline_metrics['processing_rate']:.2f} msg/s"
                
            # Mostrar resumen
            self.logger.info(f"=== Estado Demo ({elapsed_minutes:.1f} min) ===")
            self.logger.info(f"Total generados: {self.metrics.total_data_generated}")
            self.logger.info(f"Total procesados: {self.metrics.total_data_processed}")
            self.logger.info(f"Pipeline: {pipeline_status}")
            
            # Mostrar por protocolo
            for protocol, metrics in self.metrics.protocol_metrics.items():
                device_count = len(metrics["device_count"])
                self.logger.info(f"  {protocol.upper()}: {metrics['data_generated']} datos, {device_count} dispositivos")
                
        except Exception as e:
            self.logger.error(f"Error mostrando estado: {e}")
            
    def _generate_final_report(self):
        """Generar informe final de la demostración"""
        try:
            if not self.report_generator:
                return
                
            # Preparar datos del informe
            report_data = {
                "demo_config": {
                    "name": self.config.name,
                    "duration_minutes": self.config.duration_minutes,
                    "enabled_protocols": self.config.enable_protocols,
                    "data_interval": self.config.data_interval,
                    "data_count_per_protocol": self.config.data_count_per_protocol
                },
                "demo_metrics": {
                    "start_time": self.metrics.start_time.isoformat(),
                    "end_time": self.metrics.end_time.isoformat() if self.metrics.end_time else None,
                    "total_data_generated": self.metrics.total_data_generated,
                    "total_data_processed": self.metrics.total_data_processed,
                    "total_data_persisted": self.metrics.total_data_persisted,
                    "errors": self.metrics.errors,
                    "warnings": self.metrics.warnings
                },
                "protocol_metrics": {},
                "pipeline_metrics": None
            }
            
            # Agregar métricas por protocolo
            for protocol, metrics in self.metrics.protocol_metrics.items():
                report_data["protocol_metrics"][protocol] = {
                    "data_generated": metrics["data_generated"],
                    "data_processed": metrics["data_processed"],
                    "last_data_time": metrics["last_data_time"].isoformat() if metrics["last_data_time"] else None,
                    "device_count": len(metrics["device_count"]),
                    "devices": list(metrics["device_count"])
                }
                
            # Agregar métricas del pipeline
            if self.pipeline:
                report_data["pipeline_metrics"] = self.pipeline.get_metrics()
                
            # Generar informe
            self.report_generator.generate_demo_report(report_data)
            self.logger.info("Informe final generado")
            
        except Exception as e:
            self.logger.error(f"Error generando informe final: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado completo de la demostración"""
        status = {
            "name": self.config.name,
            "running": self.running,
            "start_time": self.metrics.start_time.isoformat(),
            "elapsed_minutes": 0,
            "total_data_generated": self.metrics.total_data_generated,
            "total_data_processed": self.metrics.total_data_processed,
            "protocols": {},
            "pipeline": None
        }
        
        # Calcular tiempo transcurrido
        if self.metrics.start_time:
            elapsed = datetime.now() - self.metrics.start_time
            status["elapsed_minutes"] = elapsed.total_seconds() / 60
            
        # Estado de protocolos
        for protocol, simulator in self.simulators.items():
            status["protocols"][protocol] = simulator.get_status()
            
        # Estado del pipeline
        if self.pipeline:
            status["pipeline"] = self.pipeline.get_status()
            
        return status
        
    def get_protocol_status(self, protocol: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de un protocolo específico"""
        if protocol in self.simulators:
            return self.simulators[protocol].get_status()
        return None
        
    def get_pipeline_status(self) -> Optional[Dict[str, Any]]:
        """Obtener estado del pipeline"""
        if self.pipeline:
            return self.pipeline.get_status()
        return None
        
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen ejecutivo de la demostración"""
        return {
            "name": self.config.name,
            "status": "running" if self.running else "stopped",
            "duration_minutes": self.config.duration_minutes,
            "enabled_protocols": len(self.config.enable_protocols),
            "total_data_generated": self.metrics.total_data_generated,
            "total_data_processed": self.metrics.total_data_processed,
            "processing_rate": self.metrics.total_data_processed / max(1, (datetime.now() - self.metrics.start_time).total_seconds()),
            "error_count": len(self.metrics.errors),
            "warning_count": len(self.metrics.warnings)
        }
