"""
Servicio de Monitoreo - IoT Middleware
======================================

Este servicio recopila métricas de todos los componentes del sistema
y las publica en RabbitMQ para consumo en tiempo real por el dashboard.
"""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from ..messaging import RabbitMQClient, MonitoringEvent, EventType, create_rabbitmq_client
from ..config import RabbitMQConfig

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """Métricas del sistema"""
    messages_processed: int = 0
    messages_failed: int = 0
    database_operations: int = 0
    database_errors: int = 0
    active_protocols: int = 0
    active_devices: int = 0
    uptime_seconds: int = 0
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MonitoringService:
    """Servicio de monitoreo que publica eventos en RabbitMQ"""
    
    def __init__(self, rabbitmq_config: RabbitMQConfig):
        """
        Inicializa el servicio de monitoreo
        
        Args:
            rabbitmq_config: Configuración de RabbitMQ
        """
        self.rabbitmq_config = rabbitmq_config
        self.rabbitmq_client: Optional[RabbitMQClient] = None
        
        # Métricas del sistema
        self.metrics = SystemMetrics()
        
        # Estado del servicio
        self.running = False
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Intervalo de publicación de métricas (segundos)
        self.metrics_interval = 5.0
        
        # Referencias a servicios para recopilar métricas
        self.ingestor_service = None
        self.db_handler = None
        self.input_manager = None
        
        logger.info("📊 Servicio de monitoreo inicializado")
    
    def initialize(self) -> bool:
        """
        Inicializa el servicio de monitoreo
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            if not self.rabbitmq_config.enable_monitoring:
                logger.info("⚠️  Monitoreo deshabilitado en configuración")
                return False
            
            # Crear cliente RabbitMQ
            self.rabbitmq_client = create_rabbitmq_client(self.rabbitmq_config)
            
            # Conectar a RabbitMQ
            if not self.rabbitmq_client.connect():
                logger.error("❌ No se pudo conectar a RabbitMQ")
                return False
            
            logger.info("✅ Servicio de monitoreo inicializado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando servicio de monitoreo: {e}")
            return False
    
    def register_service(self, service_name: str, service_instance: Any):
        """
        Registra un servicio para recopilar métricas
        
        Args:
            service_name: Nombre del servicio
            service_instance: Instancia del servicio
        """
        if service_name == "ingestor":
            self.ingestor_service = service_instance
        elif service_name == "db_handler":
            self.db_handler = service_instance
        elif service_name == "input_manager":
            self.input_manager = service_instance
        
        logger.info(f"✅ Servicio registrado: {service_name}")
    
    def publish_metric(self, metric_name: str, value: Any, service: str = "monitoring", **kwargs):
        """
        Publica una métrica en RabbitMQ
        
        Args:
            metric_name: Nombre de la métrica
            value: Valor de la métrica
            service: Nombre del servicio que genera la métrica
            **kwargs: Metadatos adicionales
        """
        if not self.rabbitmq_client or not self.rabbitmq_client.connected:
            return
        
        event = MonitoringEvent(
            event_type=EventType.METRIC,
            service=service,
            timestamp=datetime.now(timezone.utc),
            data={
                "metric": metric_name,
                "value": value,
                **kwargs
            },
            severity="info"
        )
        
        self.rabbitmq_client.publish_event(event)
    
    def publish_status(self, service: str, status: str, details: Optional[Dict[str, Any]] = None):
        """
        Publica el estado de un servicio
        
        Args:
            service: Nombre del servicio
            status: Estado del servicio (online, offline, error, etc.)
            details: Detalles adicionales del estado
        """
        if not self.rabbitmq_client or not self.rabbitmq_client.connected:
            return
        
        event = MonitoringEvent(
            event_type=EventType.STATUS,
            service=service,
            timestamp=datetime.now(timezone.utc),
            data={
                "status": status,
                "details": details or {}
            },
            severity="info" if status == "online" else "warning"
        )
        
        self.rabbitmq_client.publish_event(event)
    
    def publish_alert(self, service: str, message: str, severity: str = "warning", **kwargs):
        """
        Publica una alerta
        
        Args:
            service: Nombre del servicio
            message: Mensaje de la alerta
            severity: Severidad (info, warning, error, critical)
            **kwargs: Metadatos adicionales
        """
        if not self.rabbitmq_client or not self.rabbitmq_client.connected:
            return
        
        event = MonitoringEvent(
            event_type=EventType.ALERT,
            service=service,
            timestamp=datetime.now(timezone.utc),
            data={
                "message": message,
                **kwargs
            },
            severity=severity
        )
        
        self.rabbitmq_client.publish_event(event)
    
    def collect_metrics(self) -> SystemMetrics:
        """
        Recopila métricas de todos los servicios registrados
        
        Returns:
            Métricas del sistema
        """
        metrics = SystemMetrics()
        metrics.last_update = datetime.now(timezone.utc)
        
        # Recopilar métricas del servicio de ingesta
        if self.ingestor_service and hasattr(self.ingestor_service, 'metrics'):
            ingesta_metrics = self.ingestor_service.metrics
            metrics.messages_processed = getattr(ingesta_metrics, 'messages_processed', 0)
            metrics.messages_failed = getattr(ingesta_metrics, 'messages_failed', 0)
            metrics.database_operations = getattr(ingesta_metrics, 'database_inserts', 0)
            metrics.database_errors = getattr(ingesta_metrics, 'database_errors', 0)
        
        # Recopilar métricas del input manager
        if self.input_manager and hasattr(self.input_manager, 'get_metrics'):
            input_metrics = self.input_manager.get_metrics()
            metrics.active_protocols = input_metrics.get('active_protocols', 0)
            metrics.active_devices = input_metrics.get('total_devices', 0)
        
        # Calcular uptime
        if hasattr(self, 'start_time'):
            metrics.uptime_seconds = int((datetime.now(timezone.utc) - self.start_time).total_seconds())
        
        return metrics
    
    def _monitor_loop(self):
        """Loop principal de monitoreo"""
        self.start_time = datetime.now(timezone.utc)
        
        while self.running and not self._stop_event.is_set():
            try:
                # Recopilar métricas
                metrics = self.collect_metrics()
                self.metrics = metrics
                
                # Publicar métricas del sistema
                self.publish_metric(
                    "system.messages_processed",
                    metrics.messages_processed,
                    service="monitoring"
                )
                
                self.publish_metric(
                    "system.messages_failed",
                    metrics.messages_failed,
                    service="monitoring"
                )
                
                self.publish_metric(
                    "system.database_operations",
                    metrics.database_operations,
                    service="monitoring"
                )
                
                self.publish_metric(
                    "system.active_protocols",
                    metrics.active_protocols,
                    service="monitoring"
                )
                
                self.publish_metric(
                    "system.active_devices",
                    metrics.active_devices,
                    service="monitoring"
                )
                
                self.publish_metric(
                    "system.uptime_seconds",
                    metrics.uptime_seconds,
                    service="monitoring"
                )
                
                # Publicar estado del sistema
                self.publish_status(
                    "system",
                    "online",
                    {
                        "metrics": {
                            "messages_processed": metrics.messages_processed,
                            "messages_failed": metrics.messages_failed,
                            "active_protocols": metrics.active_protocols,
                            "active_devices": metrics.active_devices
                        }
                    }
                )
                
                # Esperar antes de la siguiente iteración
                self._stop_event.wait(self.metrics_interval)
                
            except Exception as e:
                logger.error(f"❌ Error en loop de monitoreo: {e}")
                time.sleep(self.metrics_interval)
    
    def start(self):
        """Inicia el servicio de monitoreo"""
        if self.running:
            logger.warning("⚠️  El servicio de monitoreo ya está ejecutándose")
            return
        
        if not self.rabbitmq_client or not self.rabbitmq_client.connected:
            logger.error("❌ No se puede iniciar: RabbitMQ no conectado")
            return
        
        self.running = True
        self._stop_event.clear()
        
        # Iniciar thread de monitoreo
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="MonitoringService",
            daemon=True
        )
        self._monitor_thread.start()
        
        logger.info("🚀 Servicio de monitoreo iniciado")
    
    def stop(self):
        """Detiene el servicio de monitoreo"""
        if not self.running:
            return
        
        self.running = False
        self._stop_event.set()
        
        # Esperar que termine el thread
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        
        # Desconectar RabbitMQ
        if self.rabbitmq_client:
            self.rabbitmq_client.disconnect()
        
        logger.info("🛑 Servicio de monitoreo detenido")
    
    def get_metrics(self) -> SystemMetrics:
        """
        Obtiene las métricas actuales del sistema
        
        Returns:
            Métricas del sistema
        """
        return self.collect_metrics()


def create_monitoring_service(rabbitmq_config: RabbitMQConfig) -> MonitoringService:
    """
    Crea una instancia del servicio de monitoreo
    
    Args:
        rabbitmq_config: Configuración de RabbitMQ
    
    Returns:
        Instancia de MonitoringService
    """
    return MonitoringService(rabbitmq_config)
