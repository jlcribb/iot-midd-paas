"""
Servicio de Ingesta MQTT - IoT Middleware
=========================================

Este módulo implementa un servicio de ingesta que:
- Se suscribe a tópicos MQTT configurados por proyecto/unidad/dispositivo/canal
- Parsea payloads (JSON/string/binario) y los mapea a canal_id
- Valida datos por tipo_dato y rangos
- Inserta en registros_datos y dispara eventos_alarmas si corresponde
- Incluye reconexión, QoS, backpressure y logging estructurado
"""

import json
import logging
import os
import time
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from queue import Queue, Full
from contextlib import contextmanager
import signal
import sys

# Importar módulos del proyecto
try:
    from ..mqtt.mqtt_client import IoTMQTTClient, MQTTMessage, create_mqtt_client
    from ..messaging import create_rabbitmq_client
    from ..storage.db_handler import DatabaseHandler, create_database_handler
    from ..config import load_config, MQTTConfig, StorageConfig
    from ..processing.processor import DataProcessor, create_data_processor
    from ..models.entities import Canal, RegistroDatos, EventoAlarma, Dispositivo, UnidadProyecto
    from ..models.enums import TipoDato, SeveridadEvento, CalidadDato
except ImportError as e:
    logging.error(f"Error al importar módulos: {e}")
    raise

from iot_middleware.services.control_runtime_contract import TELEMETRY_EVENTS_ROUTING_KEY

# Configurar logging
logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _safe_iso_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
        except ValueError:
            return datetime.now(timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()


class ControlTelemetryPublisher:
    """Publica eventos canónicos de telemetría para el control engine."""

    def __init__(self, rabbitmq_config: Any, *, ingesta_config: Optional[Dict[str, Any]] = None):
        ingesta_config = ingesta_config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.enabled = _env_bool(
            "IOT_MW_CONTROL_TELEMETRY_ENABLED",
            bool(ingesta_config.get("control_telemetry_enabled", True)),
        )
        self.routing_key = str(
            os.getenv(
                "IOT_MW_CONTROL_TELEMETRY_ROUTING_KEY",
                ingesta_config.get("control_telemetry_routing_key", TELEMETRY_EVENTS_ROUTING_KEY),
            )
        ).strip() or TELEMETRY_EVENTS_ROUTING_KEY
        self.queue_name = str(
            os.getenv(
                "IOT_MW_CONTROL_TELEMETRY_QUEUE",
                ingesta_config.get("control_telemetry_queue", self.routing_key),
            )
        ).strip() or self.routing_key
        self.source = str(
            os.getenv(
                "IOT_MW_CONTROL_TELEMETRY_SOURCE",
                ingesta_config.get("control_telemetry_source", "runtime.ingestor"),
            )
        ).strip() or "runtime.ingestor"
        self.rabbitmq_config = self._apply_env_overrides(rabbitmq_config)
        self._client = None

    @staticmethod
    def _apply_env_overrides(rabbitmq_config: Any) -> Any:
        overrides: Dict[str, Any] = {}
        env_map = {
            "RABBITMQ_HOST": ("host", str),
            "RABBITMQ_PORT": ("port", int),
            "RABBITMQ_USERNAME": ("username", str),
            "RABBITMQ_PASSWORD": ("password", str),
            "RABBITMQ_VHOST": ("virtual_host", str),
            "RABBITMQ_EXCHANGE": ("exchange", str),
            "RABBITMQ_HEARTBEAT": ("heartbeat", int),
            "RABBITMQ_CONNECTION_ATTEMPTS": ("connection_attempts", int),
            "RABBITMQ_RETRY_DELAY": ("retry_delay", int),
        }

        for env_name, (field_name, caster) in env_map.items():
            raw = os.getenv(env_name)
            if raw is None or raw.strip() == "":
                continue
            overrides[field_name] = caster(raw)

        if not overrides:
            return rabbitmq_config

        if hasattr(rabbitmq_config, "model_copy"):
            return rabbitmq_config.model_copy(update=overrides)
        if hasattr(rabbitmq_config, "copy"):
            return rabbitmq_config.copy(update=overrides)

        for key, value in overrides.items():
            setattr(rabbitmq_config, key, value)
        return rabbitmq_config

    def _get_client(self):
        if self._client is not None:
            return self._client
        client = create_rabbitmq_client(self.rabbitmq_config)
        if not client.connect():
            raise ConnectionError("No se pudo conectar a RabbitMQ para publicar telemetry.events")
        self._client = client
        return client

    def _reset_client(self) -> None:
        if self._client is None:
            return
        try:
            self._client.disconnect()
        except Exception as exc:
            self.logger.debug(f"No se pudo resetear cliente RabbitMQ de telemetría: {exc}")
        finally:
            self._client = None

    def build_event(self, sensor_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        project_id = sensor_record.get("project_id")
        variable = sensor_record.get("sensor_type")
        value = sensor_record.get("value")

        if project_id is None or str(project_id).strip() == "":
            self.logger.warning("Telemetry event omitido: falta project_id en sensor_record")
            return None
        if variable is None or str(variable).strip() == "":
            self.logger.warning("Telemetry event omitido: falta variable/sensor_type para project_id=%s", project_id)
            return None
        if value is None:
            self.logger.warning("Telemetry event omitido: falta value para project_id=%s variable=%s", project_id, variable)
            return None

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            self.logger.warning(
                "Telemetry event omitido: value no numérico project_id=%s variable=%s value=%r",
                project_id,
                variable,
                value,
            )
            return None

        metadata = {
            "topic": sensor_record.get("topic"),
            "quality": sensor_record.get("quality"),
        }
        metadata = {key: value for key, value in metadata.items() if value is not None}

        context: Dict[str, Any] = {}
        for key in ("unit_id", "device_id", "topic", "sector", "location_id", "asset_id", "channel_id"):
            if sensor_record.get(key) is not None:
                context[key] = sensor_record[key]

        base_keys = {
            "project_id",
            "sensor_type",
            "value",
            "timestamp",
            "topic",
            "quality",
            "unit_id",
            "device_id",
            "sector",
            "location_id",
            "asset_id",
            "channel_id",
        }
        for key, item in sensor_record.items():
            if key in base_keys or item is None or isinstance(item, (dict, list, tuple)):
                continue
            if isinstance(item, (str, int, float, bool)):
                context.setdefault(key, item)

        return {
            "event_id": str(sensor_record.get("event_id") or f"evt-{uuid.uuid4()}"),
            "project_id": str(project_id),
            "variable": str(variable),
            "value": numeric_value,
            "timestamp": _safe_iso_timestamp(sensor_record.get("timestamp")),
            "source": self.source,
            "event_kind": "telemetry.observed",
            "quality": str(sensor_record.get("quality") or "raw"),
            "metadata": metadata,
            "context": context,
        }

    def publish_sensor_record(self, sensor_record: Dict[str, Any]) -> bool:
        if not self.enabled:
            self.logger.debug("Publicación de telemetry.events deshabilitada por configuración")
            return False

        event = self.build_event(sensor_record)
        if event is None:
            return False

        for attempt in range(2):
            try:
                client = self._get_client()
                published = client.publish_json(
                    routing_key=self.routing_key,
                    payload=event,
                    queue_name=self.queue_name,
                    durable_queue=True,
                )
                if published:
                    self.logger.info(
                        "telemetry.events publicado project_id=%s variable=%s value=%s queue=%s",
                        event["project_id"],
                        event["variable"],
                        event["value"],
                        self.queue_name,
                    )
                    return True

                self.logger.warning(
                    "No se pudo publicar telemetry.events project_id=%s variable=%s intento=%s/2",
                    event["project_id"],
                    event["variable"],
                    attempt + 1,
                )
            except Exception as exc:
                self.logger.error(
                    "Fallo publicando telemetry.events project_id=%s variable=%s intento=%s/2: %s",
                    event["project_id"],
                    event["variable"],
                    attempt + 1,
                    exc,
                )

            self._reset_client()

        self.logger.error(
            "No se pudo publicar telemetry.events project_id=%s variable=%s tras recrear el cliente RabbitMQ",
            event["project_id"],
            event["variable"],
        )
        return False

    def close(self) -> None:
        self._reset_client()


@dataclass
class IngestaConfig:
    """Configuración del servicio de ingesta"""
    # Configuración MQTT
    mqtt: MQTTConfig
    
    # Configuración de almacenamiento
    storage: StorageConfig
    
    # Configuración de procesamiento
    processing: Dict[str, Any] = field(default_factory=dict)
    
    # Configuración de ingesta
    ingesta: Dict[str, Any] = field(default_factory=lambda: {
        'max_queue_size': 1000,
        'batch_size': 100,
        'batch_timeout': 5.0,
        'max_workers': 4,
        'validation_enabled': True,
        'alarm_thresholds': {},
        'topic_mapping': {},
        'qos': 1,
        'retain': False
    })


@dataclass
class IngestaMetrics:
    """Métricas del servicio de ingesta"""
    messages_received: int = 0
    messages_processed: int = 0
    messages_failed: int = 0
    messages_queued: int = 0
    messages_dropped: int = 0
    database_inserts: int = 0
    database_errors: int = 0
    alarms_triggered: int = 0
    validation_errors: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_message_time: Optional[datetime] = None
    uptime_seconds: int = 0


class TopicMapper:
    """Mapeador de tópicos MQTT a entidades del sistema"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.topic_patterns = config.get('topic_mapping', {})
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def parse_topic(self, topic: str) -> Dict[str, Any]:
        """
        Parsea un tópico MQTT y extrae información del proyecto, unidad, dispositivo y canal
        
        Args:
            topic: Tópico MQTT (ej: "iot/proyecto_001/unidad_001/dispositivo_001/canal_001")
        
        Returns:
            Diccionario con la información extraída
        """
        try:
            # Patrones de tópicos configurados
            for pattern, mapping in self.topic_patterns.items():
                if self._match_pattern(topic, pattern):
                    return self._extract_from_pattern(topic, pattern, mapping)
            
            # Patrón por defecto: iot/{proyecto}/{unidad}/{dispositivo}/{canal}
            parts = topic.split('/')
            if len(parts) >= 5 and parts[0] == 'iot':
                return {
                    'proyecto_id': parts[1],
                    'unidad_id': parts[2],
                    'dispositivo_id': parts[3],
                    'canal_id': parts[4],
                    'pattern_type': 'default'
                }
            
            # Tópico personalizado
            return {
                'topic_raw': topic,
                'pattern_type': 'custom'
            }
            
        except Exception as e:
            self.logger.error(f"Error al parsear tópico {topic}: {e}")
            return {'topic_raw': topic, 'pattern_type': 'error'}
    
    def _match_pattern(self, topic: str, pattern: str) -> bool:
        """Verifica si un tópico coincide con un patrón"""
        try:
            import re
            return bool(re.match(pattern, topic))
        except Exception:
            return pattern in topic
    
    def _extract_from_pattern(self, topic: str, pattern: str, mapping: Dict[str, str]) -> Dict[str, Any]:
        """Extrae información usando un patrón y mapeo específico"""
        try:
            import re
            match = re.match(pattern, topic)
            if match:
                result = {'pattern_type': 'custom'}
                for key, group_name in mapping.items():
                    if group_name in match.groupdict():
                        result[key] = match.group(group_name)
                return result
        except Exception as e:
            self.logger.error(f"Error al extraer con patrón {pattern}: {e}")
        
        return {'topic_raw': topic, 'pattern_type': 'custom'}


class DataValidator:
    """Validador de datos según tipo y rangos configurados"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validation_enabled = config.get('validation_enabled', True)
        self.alarm_thresholds = config.get('alarm_thresholds', {})
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_payload(self, payload: Any, canal_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida un payload según la configuración del canal
        
        Args:
            payload: Datos a validar
            canal_config: Configuración del canal (tipo_dato, rangos, etc.)
        
        Returns:
            Resultado de la validación
        """
        if not self.validation_enabled:
            return {'valid': True, 'quality': CalidadDato.GOOD}
        
        try:
            validation_result = {
                'valid': True,
                'quality': CalidadDato.GOOD,
                'errors': [],
                'warnings': [],
                'alarms': []
            }
            
            # Validar tipo de dato
            tipo_dato = canal_config.get('tipo_dato')
            if tipo_dato:
                type_validation = self._validate_type(payload, tipo_dato)
                if not type_validation['valid']:
                    validation_result['valid'] = False
                    validation_result['quality'] = CalidadDato.BAD
                    validation_result['errors'].extend(type_validation['errors'])
            
            # Validar rangos si es numérico
            if isinstance(payload, (int, float)) and tipo_dato in [TipoDato.NUMERICO, TipoDato.DECIMAL]:
                range_validation = self._validate_range(payload, canal_config)
                if not range_validation['valid']:
                    validation_result['valid'] = False
                    validation_result['quality'] = CalidadDato.UNCERTAIN
                    validation_result['errors'].extend(range_validation['errors'])
                
                # Verificar umbrales de alarma
                alarm_check = self._check_alarm_thresholds(payload, canal_config)
                validation_result['alarms'].extend(alarm_check)
            
            # Validar longitud para strings
            if isinstance(payload, str) and tipo_dato == TipoDato.TEXTO:
                length_validation = self._validate_length(payload, canal_config)
                if not length_validation['valid']:
                    validation_result['valid'] = False
                    validation_result['quality'] = CalidadDato.BAD
                    validation_result['errors'].extend(length_validation['errors'])
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error en validación: {e}")
            return {
                'valid': False,
                'quality': CalidadDato.BAD,
                'errors': [f"Error de validación: {e}"],
                'warnings': [],
                'alarms': []
            }
    
    def _validate_type(self, payload: Any, tipo_dato: TipoDato) -> Dict[str, Any]:
        """Valida el tipo de dato"""
        try:
            if tipo_dato == TipoDato.NUMERICO:
                if not isinstance(payload, (int, float)):
                    return {'valid': False, 'errors': [f"Se esperaba numérico, se recibió {type(payload).__name__}"]}
            elif tipo_dato == TipoDato.TEXTO:
                if not isinstance(payload, str):
                    return {'valid': False, 'errors': [f"Se esperaba texto, se recibió {type(payload).__name__}"]}
            elif tipo_dato == TipoDato.BOOLEANO:
                if not isinstance(payload, bool):
                    return {'valid': False, 'errors': [f"Se esperaba booleano, se recibió {type(payload).__name__}"]}
            elif tipo_dato == TipoDato.JSON:
                if not isinstance(payload, (dict, list)):
                    return {'valid': False, 'errors': [f"Se esperaba JSON, se recibió {type(payload).__name__}"]}
            
            return {'valid': True, 'errors': []}
            
        except Exception as e:
            return {'valid': False, 'errors': [f"Error en validación de tipo: {e}"]}
    
    def _validate_range(self, payload: Union[int, float], canal_config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida rangos numéricos"""
        try:
            min_value = canal_config.get('valor_minimo')
            max_value = canal_config.get('valor_maximo')
            
            if min_value is not None and payload < min_value:
                return {'valid': False, 'errors': [f"Valor {payload} menor al mínimo {min_value}"]}
            
            if max_value is not None and payload > max_value:
                return {'valid': False, 'errors': [f"Valor {payload} mayor al máximo {max_value}"]}
            
            return {'valid': True, 'errors': []}
            
        except Exception as e:
            return {'valid': False, 'errors': [f"Error en validación de rango: {e}"]}
    
    def _validate_length(self, payload: str, canal_config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida longitud de strings"""
        try:
            max_length = canal_config.get('longitud_maxima')
            if max_length and len(payload) > max_length:
                return {'valid': False, 'errors': [f"Longitud {len(payload)} excede máximo {max_length}"]}
            
            return {'valid': True, 'errors': []}
            
        except Exception as e:
            return {'valid': False, 'errors': [f"Error en validación de longitud: {e}"]}
    
    def _check_alarm_thresholds(self, payload: Union[int, float], canal_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verifica umbrales de alarma"""
        alarms = []
        try:
            thresholds = self.alarm_thresholds.get(canal_config.get('id'), [])
            
            for threshold in thresholds:
                threshold_value = threshold.get('valor')
                threshold_type = threshold.get('tipo')  # 'min', 'max', 'critical'
                threshold_severity = threshold.get('severidad', SeveridadEvento.ADVERTENCIA)
                
                if threshold_value is None:
                    continue
                
                triggered = False
                if threshold_type == 'min' and payload < threshold_value:
                    triggered = True
                elif threshold_type == 'max' and payload > threshold_value:
                    triggered = True
                elif threshold_type == 'critical' and payload == threshold_value:
                    triggered = True
                
                if triggered:
                    alarms.append({
                        'threshold': threshold,
                        'value': payload,
                        'severity': threshold_severity,
                        'message': f"Umbral {threshold_type} alcanzado: {payload} {threshold.get('operador', '>=')} {threshold_value}"
                    })
            
        except Exception as e:
            self.logger.error(f"Error al verificar umbrales: {e}")
        
        return alarms


class MessageProcessor:
    """Procesador de mensajes MQTT"""
    
    def __init__(self, config: IngestaConfig, db_handler: DatabaseHandler, 
                 topic_mapper: TopicMapper, data_validator: DataValidator,
                 metrics: Optional[IngestaMetrics] = None):
        self.config = config
        self.db_handler = db_handler
        self.topic_mapper = topic_mapper
        self.data_validator = data_validator
        self.metrics = metrics
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._metrics_lock = threading.Lock()
        self.telemetry_publisher = ControlTelemetryPublisher(
            config.rabbitmq,
            ingesta_config=config.ingesta,
        )
        
        # Cola de procesamiento
        self.message_queue = Queue(maxsize=config.ingesta['max_queue_size'])
        self.batch_size = config.ingesta['batch_size']
        self.batch_timeout = config.ingesta['batch_timeout']
        
        # Workers de procesamiento
        self.max_workers = config.ingesta['max_workers']
        self.workers = []
        self.stop_workers = threading.Event()
        
        # Iniciar workers
        self._start_workers()
    
    def _start_workers(self):
        """Inicia los workers de procesamiento"""
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                daemon=True,
                name=f"MessageProcessor_Worker_{i}"
            )
            worker.start()
            self.workers.append(worker)
            self.logger.info(f"Worker {i} iniciado")
    
    def _worker_loop(self, worker_id: int):
        """Loop principal del worker"""
        self.logger.info(f"Worker {worker_id} iniciando loop de procesamiento")
        
        while not self.stop_workers.is_set():
            try:
                # Procesar mensajes en lotes
                messages = []
                start_time = time.time()
                
                # Recolectar mensajes hasta llenar el lote o timeout
                while len(messages) < self.batch_size and (time.time() - start_time) < self.batch_timeout:
                    try:
                        message = self.message_queue.get(timeout=0.1)
                        messages.append(message)
                        self.message_queue.task_done()
                    except:
                        break
                
                if messages:
                    self._process_batch(messages, worker_id)
                
            except Exception as e:
                self.logger.error(f"Error en worker {worker_id}: {e}")
                time.sleep(1)
        
        self.logger.info(f"Worker {worker_id} detenido")
    
    def _process_batch(self, messages: List[MQTTMessage], worker_id: int):
        """Procesa un lote de mensajes"""
        try:
            self.logger.debug(f"Worker {worker_id} procesando lote de {len(messages)} mensajes")
            
            for message in messages:
                try:
                    self._process_single_message(message)
                except Exception as e:
                    self.logger.error(f"Error procesando mensaje {message.topic}: {e}")
                    self._inc_metric('messages_failed')
                    
        except Exception as e:
            self.logger.error(f"Error procesando lote en worker {worker_id}: {e}")
    
    def _process_single_message(self, message: MQTTMessage):
        """Procesa un mensaje individual"""
        try:
            # Parsear tópico
            topic_info = self.topic_mapper.parse_topic(message.topic)
            
            # Validar payload
            validation_result = self.data_validator.validate_payload(
                message.payload, 
                topic_info
            )
            
            # Preparar datos para inserción
            registro_data = {
                'canal_id': topic_info.get('canal_id'),
                'valor': message.payload,
                'timestamp': message.timestamp,
                'calidad': validation_result['quality'],
                'metadata': {
                    'topic': message.topic,
                    'qos': message.qos,
                    'retain': message.retain,
                    'validation': validation_result,
                    'topic_info': topic_info
                }
            }
            
            # Insertar en base de datos
            insert_ok = self._insert_registro(
                registro_data,
                publish_control_event=bool(validation_result.get('valid', False)),
            )
            if insert_ok:
                self._inc_metric('messages_processed')
            else:
                self._inc_metric('messages_failed')
            
            # Verificar alarmas
            if validation_result['alarms']:
                self._trigger_alarms(registro_data, validation_result['alarms'])
                
        except Exception as e:
            self.logger.error(f"Error procesando mensaje {message.topic}: {e}")
            self._inc_metric('messages_failed')
    
    def _inc_metric(self, field_name: str, delta: int = 1):
        """Incrementa un contador de métricas de forma segura."""
        if not self.metrics:
            return
        try:
            with self._metrics_lock:
                current_value = getattr(self.metrics, field_name, 0)
                setattr(self.metrics, field_name, current_value + delta)
        except Exception as e:
            self.logger.debug(f"No se pudo actualizar métrica {field_name}: {e}")

    @staticmethod
    def _normalize_scalar_value(value: Any) -> Any:
        """Normaliza strings numéricos/booleanos para facilitar persistencia."""
        if isinstance(value, bool):
            # Unificamos a numérico para evitar conflictos de tipo en Influx (bool vs float).
            return 1 if value else 0

        if isinstance(value, str):
            text = value.strip()
            if not text:
                return value
            lowered = text.lower()
            if lowered in {"true", "false"}:
                return 1 if lowered == "true" else 0
            try:
                if "." in text:
                    return float(text)
                return int(text)
            except ValueError:
                return value
        return value

    def _extract_sensor_value(self, payload: Any) -> Any:
        """Extrae un valor escalar del payload MQTT."""
        if isinstance(payload, (int, float, bool, str)):
            return self._normalize_scalar_value(payload)

        if isinstance(payload, dict):
            preferred_keys = (
                "value",
                "valor",
                "signal_value",
                "reading",
                "measurement",
                "open",
                "state",
                "level",
                "level_percent",
                "servo_angle",
                "temperature",
                "humidity",
                "pressure",
            )
            for key in preferred_keys:
                if key in payload and isinstance(payload[key], (int, float, bool, str)):
                    return self._normalize_scalar_value(payload[key])

        return None

    def _build_sensor_record(self, registro_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Construye un registro normalizado para DB/Influx a partir del mensaje."""
        payload = registro_data.get('valor')
        metadata = registro_data.get('metadata') or {}
        topic_info = metadata.get('topic_info') or {}

        scalar_value = self._extract_sensor_value(payload)
        if scalar_value is None:
            self.logger.warning(
                f"No se pudo extraer valor escalar de payload en tópico {metadata.get('topic')}"
            )
            return None

        payload_dict = payload if isinstance(payload, dict) else {}
        sensor_type = (
            payload_dict.get('signal')
            or payload_dict.get('sensor_type')
            or topic_info.get('canal_id')
            or registro_data.get('canal_id')
            or 'value'
        )
        device_id = (
            payload_dict.get('device_ref_id')
            or payload_dict.get('device_id')
            or topic_info.get('dispositivo_id')
            or 'unknown'
        )
        topic = metadata.get('topic') or payload_dict.get('topic') or 'unknown'
        timestamp = payload_dict.get('timestamp') or registro_data.get('timestamp')

        sensor_record: Dict[str, Any] = {
            'device_id': str(device_id),
            'sensor_type': str(sensor_type),
            'value': scalar_value,
            'timestamp': timestamp,
            'topic': str(topic),
            'project_id': payload_dict.get('project_id') or topic_info.get('proyecto_id'),
            'unit_id': payload_dict.get('unit_id') or topic_info.get('unidad_id'),
            'quality': str(registro_data.get('calidad')),
        }

        for key, value in payload_dict.items():
            if key in sensor_record:
                continue
            if isinstance(value, (int, float, bool, str)):
                sensor_record[key] = value

        return sensor_record

    def _insert_registro(self, registro_data: Dict[str, Any], *, publish_control_event: bool = False) -> bool:
        """Inserta un registro en la base de datos."""
        try:
            sensor_record = self._build_sensor_record(registro_data)
            if sensor_record is None:
                self._inc_metric('database_errors')
                return False

            influx_handler = getattr(self.db_handler, 'influxdb_handler', None)
            if influx_handler:
                inserted = influx_handler.insert_influxdb(sensor_record)
            else:
                inserted = self.db_handler.insert_sensor_data(sensor_record)

            if inserted:
                if publish_control_event:
                    self.telemetry_publisher.publish_sensor_record(sensor_record)
                self._inc_metric('database_inserts')
                self.logger.info(
                    f"Registro persistido: {sensor_record.get('device_id')}.{sensor_record.get('sensor_type')}="
                    f"{sensor_record.get('value')}"
                )
                return True

            self._inc_metric('database_errors')
            return False

        except Exception as e:
            self.logger.error(f"Error insertando registro: {e}")
            self._inc_metric('database_errors')
            return False
    
    def _trigger_alarms(self, registro_data: Dict[str, Any], alarms: List[Dict[str, Any]]):
        """Dispara eventos de alarma"""
        try:
            for alarm in alarms:
                # Aquí se implementaría la creación de eventos de alarma
                self.logger.warning(f"ALARMA: {alarm['message']} - Severidad: {alarm['severity']}")
                
        except Exception as e:
            self.logger.error(f"Error disparando alarma: {e}")
    
    def add_message(self, message: MQTTMessage):
        """Agrega un mensaje a la cola de procesamiento"""
        try:
            self.message_queue.put_nowait(message)
            return True
        except Full:
            self.logger.warning("Cola de mensajes llena, mensaje descartado")
            # Aquí se podrían implementar estrategias de backpressure
            self._inc_metric('messages_dropped')
            return False
    
    def stop(self):
        """Detiene el procesador de mensajes"""
        self.stop_workers.set()
        
        # Esperar a que los workers terminen
        for worker in self.workers:
            worker.join(timeout=5.0)

        self.telemetry_publisher.close()
        
        self.logger.info("Procesador de mensajes detenido")


class MQTTIngestaService:
    """Servicio principal de ingesta MQTT"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = None
        self.mqtt_client = None
        self.db_handler = None
        self.message_processor = None
        self.topic_mapper = None
        self.data_validator = None
        
        # Estado del servicio
        self.running = False
        self.metrics = IngestaMetrics()
        
        # Señales de control
        self.stop_event = threading.Event()
        
        # Configurar logging
        self._setup_logging()
        
        # Configurar manejo de señales
        self._setup_signal_handlers()
    
    def _setup_logging(self):
        """Configura el logging estructurado"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('ingesta_service.log')
            ]
        )
    
    def _setup_signal_handlers(self):
        """Configura el manejo de señales del sistema"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Manejador de señales del sistema"""
        logger.info(f"Señal {signum} recibida, deteniendo servicio...")
        self.stop()

    def _ensure_runtime_demo_topics(self):
        """Asegura tópicos de suscripción compatibles con demo (5 y 6 segmentos)."""
        try:
            subscribe_topics = list((self.config.mqtt.topics or {}).get('subscribe') or [])
            required_topics = ["iot/+/+/+/+", "iot/+/+/+/+/+"]
            changed = False

            for topic in required_topics:
                if topic not in subscribe_topics:
                    subscribe_topics.append(topic)
                    changed = True

            if changed:
                self.config.mqtt.topics['subscribe'] = subscribe_topics
                logger.info(
                    f"📋 Tópicos MQTT actualizados para demo: {self.config.mqtt.topics['subscribe']}"
                )
        except Exception as exc:
            logger.warning(f"⚠️  No se pudieron ajustar tópicos MQTT de demo: {exc}")
    
    def initialize(self) -> bool:
        """Inicializa el servicio de ingesta"""
        try:
            logger.info("🚀 Inicializando servicio de ingesta MQTT...")
            
            # Cargar configuración
            self.config = load_config(self.config_path)
            logger.info("✅ Configuración cargada")
            self._ensure_runtime_demo_topics()
            
            # Crear manejador de base de datos
            self.db_handler = create_database_handler(
                postgresql_config=self.config.postgresql,
                influxdb_config=self.config.influxdb,
                storage_config=self.config.storage
            )
            logger.info("✅ Manejador de base de datos creado")
            
            # Crear mapeador de tópicos
            self.topic_mapper = TopicMapper(self.config.ingesta)
            logger.info("✅ Mapeador de tópicos creado")
            
            # Crear validador de datos
            self.data_validator = DataValidator(self.config.ingesta)
            logger.info("✅ Validador de datos creado")
            
            # Crear procesador de mensajes
            self.message_processor = MessageProcessor(
                self.config, 
                self.db_handler, 
                self.topic_mapper, 
                self.data_validator,
                self.metrics,
            )
            logger.info("✅ Procesador de mensajes creado")
            
            # Crear cliente MQTT
            self.mqtt_client = create_mqtt_client(self.config.mqtt)
            self.mqtt_client.set_message_processor(self._on_mqtt_message)
            logger.info("✅ Cliente MQTT creado")
            
            logger.info("🎯 Servicio de ingesta inicializado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando servicio: {e}")
            return False
    
    def _on_mqtt_message(self, message: MQTTMessage):
        """Callback para mensajes MQTT recibidos"""
        try:
            # Actualizar métricas
            self.metrics.messages_received += 1
            self.metrics.last_message_time = datetime.now(timezone.utc)
            
            # Agregar mensaje al procesador
            queued = self.message_processor.add_message(message)
            if not queued:
                self.metrics.messages_failed += 1
            
            logger.debug(f"📨 Mensaje recibido en {message.topic}")
            
        except Exception as e:
            logger.error(f"Error procesando mensaje MQTT: {e}")
            self.metrics.messages_failed += 1
    
    def start(self) -> bool:
        """Inicia el servicio de ingesta"""
        try:
            if not self.initialize():
                return False
            
            logger.info("🔌 Conectando al broker MQTT...")
            
            # Conectar al broker MQTT
            if not self.mqtt_client.connect():
                logger.error("❌ No se pudo conectar al broker MQTT")
                return False
            
            logger.info("✅ Conectado al broker MQTT")
            self.running = True
            
            # Loop principal del servicio
            self._main_loop()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando servicio: {e}")
            return False
    
    def _main_loop(self):
        """Loop principal del servicio"""
        logger.info("🔄 Servicio de ingesta ejecutándose...")
        
        try:
            while self.running and not self.stop_event.is_set():
                # Actualizar métricas
                self._update_metrics()
                
                # Verificar estado de conexión
                if not self.mqtt_client._connected:
                    logger.warning("⚠️  Conexión MQTT perdida, esperando reconexión...")
                
                # Esperar antes de la siguiente iteración
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Interrumpido por el usuario")
        except Exception as e:
            logger.error(f"❌ Error en loop principal: {e}")
        finally:
            self._cleanup()
    
    def _update_metrics(self):
        """Actualiza las métricas del servicio"""
        try:
            # Calcular uptime
            now = datetime.now(timezone.utc)
            self.metrics.uptime_seconds = int((now - self.metrics.start_time).total_seconds())
            
            # Log de métricas cada 60 segundos
            if self.metrics.uptime_seconds % 60 == 0:
                logger.info(f"📊 Métricas: Recibidos={self.metrics.messages_received}, "
                          f"Procesados={self.metrics.messages_processed}, "
                          f"Errores={self.metrics.messages_failed}, "
                          f"DB_OK={self.metrics.database_inserts}, "
                          f"DB_ERR={self.metrics.database_errors}, "
                          f"Uptime={self.metrics.uptime_seconds}s")
                
        except Exception as e:
            logger.error(f"Error actualizando métricas: {e}")
    
    def _cleanup(self):
        """Limpia recursos del servicio"""
        try:
            logger.info("🧹 Limpiando recursos del servicio...")
            
            # Detener procesador de mensajes
            if self.message_processor:
                self.message_processor.stop()
            
            # Desconectar cliente MQTT
            if self.mqtt_client:
                self.mqtt_client.disconnect()
            
            # Cerrar conexiones de base de datos
            if self.db_handler:
                self.db_handler.close()
            
            self.running = False
            logger.info("✅ Limpieza completada")
            
        except Exception as e:
            logger.error(f"Error en limpieza: {e}")
    
    def stop(self):
        """Detiene el servicio de ingesta"""
        logger.info("🛑 Deteniendo servicio de ingesta...")
        self.stop_event.set()
        self.running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del servicio"""
        return {
            'running': self.running,
            'mqtt_connected': self.mqtt_client._connected if self.mqtt_client else False,
            'metrics': {
                'messages_received': self.metrics.messages_received,
                'messages_processed': self.metrics.messages_processed,
                'messages_failed': self.metrics.messages_failed,
                'database_inserts': self.metrics.database_inserts,
                'database_errors': self.metrics.database_errors,
                'uptime_seconds': self.metrics.uptime_seconds,
                'last_message_time': self.metrics.last_message_time.isoformat() if self.metrics.last_message_time else None
            },
            'config': {
                'mqtt_broker': self.config.mqtt.broker['host'] if self.config else None,
                'topics_subscribed': self.config.mqtt.topics['subscribe'] if self.config else []
            }
        }


def run(config_path: Optional[str] = None) -> None:
    """Función principal para ejecutar el servicio de ingesta"""
    service = MQTTIngestaService(config_path)
    
    try:
        if service.start():
            logger.info("🎉 Servicio de ingesta ejecutándose exitosamente")
        else:
            logger.error("❌ El servicio de ingesta falló al iniciar")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
