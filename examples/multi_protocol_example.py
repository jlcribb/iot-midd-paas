#!/usr/bin/env python3
"""
Ejemplo de Uso Multi-Protocolo - IoT Middleware
===============================================

Este ejemplo demuestra cómo usar la nueva arquitectura modular para
recibir datos desde múltiples protocolos IoT y procesarlos de manera unificada.
"""

import json
import logging
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path

# Importar la nueva arquitectura modular
from src.iot_middleware.input import InputManager, InputManagerConfig
from src.iot_middleware.input.base_connector import UnifiedDataFormat


def setup_logging():
    """Configura el sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('multi_protocol_example.log')
        ]
    )


def data_callback(unified_data: UnifiedDataFormat):
    """
    Callback que recibe todos los datos unificados de todos los protocolos
    
    Args:
        unified_data: Datos en formato unificado desde cualquier protocolo
    """
    try:
        # Log de datos recibidos
        logging.info(f"📨 Datos recibidos de {unified_data.source_protocol}: "
                    f"{unified_data.device_id} -> {unified_data.measurements}")
        
        # Aquí puedes procesar los datos según tu lógica de negocio
        # Por ejemplo:
        # - Validar datos
        # - Transformar unidades
        # - Almacenar en base de datos
        # - Enviar a sistemas externos
        # - Disparar alarmas
        
        process_unified_data(unified_data)
        
    except Exception as e:
        logging.error(f"Error en callback de datos: {e}")


def process_unified_data(data: UnifiedDataFormat):
    """
    Procesa los datos unificados según el protocolo de origen
    
    Args:
        data: Datos unificados a procesar
    """
    try:
        protocol = data.source_protocol
        device_id = data.device_id
        measurements = data.measurements
        
        logging.info(f"🔄 Procesando datos de {protocol} para dispositivo {device_id}")
        
        # Procesamiento específico por protocolo
        if protocol == "mqtt":
            process_mqtt_data(data)
        elif protocol == "http":
            process_http_data(data)
        elif protocol == "ble":
            process_ble_data(data)
        elif protocol == "lora":
            process_lora_data(data)
        elif protocol == "midi":
            process_midi_data(data)
        elif protocol == "modbus":
            process_modbus_data(data)
        elif protocol == "zigbee":
            process_zigbee_data(data)
        else:
            logging.warning(f"Protocolo no reconocido: {protocol}")
            
        # Procesamiento común para todos los protocolos
        process_common_data(data)
        
    except Exception as e:
        logging.error(f"Error procesando datos unificados: {e}")


def process_mqtt_data(data: UnifiedDataFormat):
    """Procesa datos MQTT"""
    try:
        # Extraer información específica de MQTT
        topic_info = data.metadata.get('topic_info', {})
        project_id = topic_info.get('proyecto_id', 'default')
        unidad_id = topic_info.get('unidad_id', 'main')
        
        logging.info(f"📡 MQTT: Proyecto {project_id}, Unidad {unidad_id}")
        
        # Aquí puedes implementar lógica específica para MQTT
        # Por ejemplo, mapear tópicos a entidades del sistema
        
    except Exception as e:
        logging.error(f"Error procesando datos MQTT: {e}")


def process_http_data(data: UnifiedDataFormat):
    """Procesa datos HTTP/REST"""
    try:
        # Extraer información específica de HTTP
        method = data.metadata.get('method', 'POST')
        client_ip = data.metadata.get('client_ip', 'unknown')
        
        logging.info(f"🌐 HTTP: {method} desde {client_ip}")
        
        # Aquí puedes implementar lógica específica para HTTP
        # Por ejemplo, validar autenticación, rate limiting, etc.
        
    except Exception as e:
        logging.error(f"Error procesando datos HTTP: {e}")


def process_ble_data(data: UnifiedDataFormat):
    """Procesa datos BLE"""
    try:
        # Extraer información específica de BLE
        device_name = data.metadata.get('device_name', 'unknown')
        rssi = data.metadata.get('rssi', 0)
        
        logging.info(f"📱 BLE: {device_name} (RSSI: {rssi})")
        
        # Aquí puedes implementar lógica específica para BLE
        # Por ejemplo, filtrar por intensidad de señal, etc.
        
    except Exception as e:
        logging.error(f"Error procesando datos BLE: {e}")


def process_lora_data(data: UnifiedDataFormat):
    """Procesa datos LoRa"""
    try:
        # Extraer información específica de LoRa
        application_id = data.metadata.get('application_id', 'unknown')
        event_type = data.metadata.get('event_type', 'unknown')
        
        logging.info(f"📡 LoRa: Aplicación {application_id}, Evento {event_type}")
        
        # Aquí puedes implementar lógica específica para LoRa
        # Por ejemplo, decodificar payloads específicos, etc.
        
    except Exception as e:
        logging.error(f"Error procesando datos LoRa: {e}")


def process_midi_data(data: UnifiedDataFormat):
    """Procesa datos MIDI"""
    try:
        # Extraer información específica de MIDI
        channel = data.metadata.get('channel', 0)
        message_type = data.metadata.get('message_type', 'unknown')
        
        logging.info(f"🎵 MIDI: Canal {channel}, {message_type}")
        
        # Aquí puedes implementar lógica específica para MIDI
        # Por ejemplo, análisis musical, control de equipos, etc.
        
    except Exception as e:
        logging.error(f"Error procesando datos MIDI: {e}")


def process_modbus_data(data: UnifiedDataFormat):
    """Procesa datos Modbus"""
    try:
        # Extraer información específica de Modbus
        protocol = data.metadata.get('protocol', 'unknown')
        device_id = data.metadata.get('device_id', 0)
        
        logging.info(f"🏭 Modbus: {protocol}, Dispositivo {device_id}")
        
        # Aquí puedes implementar lógica específica para Modbus
        # Por ejemplo, escalado de valores, validación de rangos, etc.
        
    except Exception as e:
        logging.error(f"Error procesando datos Modbus: {e}")


def process_zigbee_data(data: UnifiedDataFormat):
    """Procesa datos ZigBee"""
    try:
        # Extraer información específica de ZigBee
        device_type = data.metadata.get('device_type', 'unknown')
        coordinator_type = data.metadata.get('coordinator_type', 'unknown')
        
        logging.info(f"🏠 ZigBee: {device_type} via {coordinator_type}")
        
        # Aquí puedes implementar lógica específica para ZigBee
        # Por ejemplo, control de domótica, etc.
        
    except Exception as e:
        logging.error(f"Error procesando datos ZigBee: {e}")


def process_common_data(data: UnifiedDataFormat):
    """Procesa datos comunes a todos los protocolos"""
    try:
        # Validación básica
        if not data.device_id or data.device_id == 'unknown':
            logging.warning("Dispositivo ID no válido")
            return
        
        if not data.measurements:
            logging.warning("No hay mediciones para procesar")
            return
        
        # Verificar calidad de datos
        if data.quality.value != 'valid':
            logging.warning(f"Calidad de datos baja: {data.quality.value}")
        
        # Aquí puedes implementar lógica común:
        # - Almacenamiento en base de datos
        # - Envío a sistemas de análisis
        # - Verificación de umbrales de alarma
        # - Generación de métricas
        
        logging.info(f"✅ Datos procesados exitosamente para {data.device_id}")
        
    except Exception as e:
        logging.error(f"Error procesando datos comunes: {e}")


def load_config(config_path: str) -> dict:
    """
    Carga la configuración desde un archivo YAML
    
    Args:
        config_path: Ruta al archivo de configuración
        
    Returns:
        Diccionario con la configuración
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        logging.info(f"✅ Configuración cargada desde {config_path}")
        return config
        
    except Exception as e:
        logging.error(f"❌ Error cargando configuración: {e}")
        raise


def create_input_manager(config: dict) -> InputManager:
    """
    Crea el gestor de entrada con la configuración proporcionada
    
    Args:
        config: Configuración del sistema
        
    Returns:
        Instancia del gestor de entrada
    """
    try:
        # Extraer configuración del gestor
        manager_config = config.get('input_manager', {})
        input_manager_config = InputManagerConfig(**manager_config)
        
        # Extraer configuración de conectores
        connectors_config = config.get('connectors', [])
        
        # Crear gestor de entrada
        input_manager = InputManager(
            configs=connectors_config,
            data_callback=data_callback,
            manager_config=input_manager_config
        )
        
        logging.info(f"✅ Gestor de entrada creado con {len(connectors_config)} conectores")
        return input_manager
        
    except Exception as e:
        logging.error(f"❌ Error creando gestor de entrada: {e}")
        raise


def main():
    """Función principal del ejemplo"""
    try:
        # Configurar logging
        setup_logging()
        logging.info("🚀 Iniciando ejemplo multi-protocolo")
        
        # Cargar configuración
        config_path = "examples/config_multi_protocol.yaml"
        if not Path(config_path).exists():
            logging.error(f"❌ Archivo de configuración no encontrado: {config_path}")
            return
        
        config = load_config(config_path)
        
        # Crear gestor de entrada
        input_manager = create_input_manager(config)
        
        # Iniciar el gestor
        if input_manager.start():
            logging.info("✅ Gestor de entrada iniciado exitosamente")
            
            try:
                # Loop principal
                while True:
                    # Obtener estado del gestor
                    status = input_manager.get_manager_status()
                    
                    # Mostrar métricas cada 30 segundos
                    if status['uptime_seconds'] % 30 == 0:
                        logging.info(f"📊 Estado del gestor: "
                                   f"Conectores activos={status['active_connectors']}, "
                                   f"Mensajes totales={status['total_messages']}, "
                                   f"Uptime={status['uptime_seconds']}s")
                    
                    # Verificar conectores individuales
                    connectors_status = input_manager.get_all_connectors_status()
                    for name, connector_status in connectors_status.items():
                        if connector_status['status'] == 'error':
                            logging.warning(f"⚠️  Conector {name} en estado de error")
                    
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logging.info("🛑 Interrumpido por el usuario")
            except Exception as e:
                logging.error(f"❌ Error en loop principal: {e}")
            finally:
                # Detener el gestor
                input_manager.stop()
                logging.info("✅ Gestor de entrada detenido")
        else:
            logging.error("❌ No se pudo iniciar el gestor de entrada")
            
    except Exception as e:
        logging.error(f"❌ Error en función principal: {e}")
        raise


def demo_simple_usage():
    """
    Demuestra un uso simple de la arquitectura modular
    """
    try:
        logging.info("🎯 Demostración de uso simple")
        
        # Configuración básica para un conector MQTT
        mqtt_config = {
            'name': 'demo_mqtt',
            'protocol': 'mqtt',
            'enabled': True,
            'broker_host': 'localhost',
            'broker_port': 1883,
            'topics_subscribe': ['demo/+/data'],
            'topics_publish': [],
            'qos': 1,
            'retain': False
        }
        
        # Configuración básica para un conector HTTP
        http_config = {
            'name': 'demo_http',
            'protocol': 'http',
            'enabled': True,
            'host': '0.0.0.0',
            'port': 8080,
            'endpoint': '/demo/ingest',
            'auth_enabled': False,
            'cors_enabled': True
        }
        
        # Crear gestor con configuración simple
        input_manager = InputManager(
            configs=[mqtt_config, http_config],
            data_callback=data_callback
        )
        
        # Iniciar
        if input_manager.start():
            logging.info("✅ Demo iniciado exitosamente")
            
            # Ejecutar por 10 segundos
            time.sleep(10)
            
            # Detener
            input_manager.stop()
            logging.info("✅ Demo detenido")
        else:
            logging.error("❌ No se pudo iniciar el demo")
            
    except Exception as e:
        logging.error(f"❌ Error en demo: {e}")


if __name__ == "__main__":
    # Ejecutar demo simple si se ejecuta directamente
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_simple_usage()
    else:
        main()
