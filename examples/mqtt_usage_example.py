#!/usr/bin/env python3
"""
Ejemplo de Uso del Cliente MQTT
IoT Middleware
================================

Este script demuestra cómo usar el cliente MQTT en diferentes
escenarios prácticos.
"""

import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.mqtt import (
        IoTMQTTClient, 
        MQTTMessage, 
        create_mqtt_client
    )
    from iot_middleware.config import load_config
    print("✅ Módulos importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    sys.exit(1)

class IoTDeviceSimulator:
    """Simulador de dispositivo IoT que publica datos"""
    
    def __init__(self, device_id: str, mqtt_client: IoTMQTTClient):
        self.device_id = device_id
        self.mqtt_client = mqtt_client
        self.running = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def start(self):
        """Iniciar simulación del dispositivo"""
        self.running = True
        self.logger.info(f"🚀 Iniciando simulación del dispositivo {self.device_id}")
        
        # Publicar estado online
        self._publish_status("online")
        
        # Iniciar publicación de datos
        self._publish_data_loop()
    
    def stop(self):
        """Detener simulación del dispositivo"""
        self.running = False
        self.logger.info(f"🛑 Deteniendo simulación del dispositivo {self.device_id}")
        
        # Publicar estado offline
        self._publish_status("offline")
    
    def _publish_status(self, status: str):
        """Publicar estado del dispositivo"""
        message = {
            "device_id": self.device_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "type": "status"
        }
        
        topic = f"iot/{self.device_id}/status"
        if self.mqtt_client.publish(topic, message):
            self.logger.info(f"📤 Estado publicado: {status}")
        else:
            self.logger.error(f"❌ Error al publicar estado: {status}")
    
    def _publish_data_loop(self):
        """Loop de publicación de datos del sensor"""
        import random
        
        while self.running:
            try:
                # Simular datos de temperatura
                temperature = round(random.uniform(18.0, 32.0), 1)
                humidity = round(random.uniform(40.0, 80.0), 1)
                pressure = round(random.uniform(1000.0, 1020.0), 1)
                
                # Publicar datos de temperatura
                temp_message = {
                    "device_id": self.device_id,
                    "sensor_type": "temperature",
                    "value": temperature,
                    "unit": "celsius",
                    "timestamp": datetime.now().isoformat(),
                    "type": "sensor_data"
                }
                
                temp_topic = f"iot/{self.device_id}/data"
                if self.mqtt_client.publish(temp_topic, temp_message):
                    self.logger.debug(f"🌡️  Temperatura publicada: {temperature}°C")
                
                # Publicar datos de humedad
                hum_message = {
                    "device_id": self.device_id,
                    "sensor_type": "humidity",
                    "value": humidity,
                    "unit": "percentage",
                    "timestamp": datetime.now().isoformat(),
                    "type": "sensor_data"
                }
                
                if self.mqtt_client.publish(temp_topic, hum_message):
                    self.logger.debug(f"💧 Humedad publicada: {humidity}%")
                
                # Publicar datos de presión
                press_message = {
                    "device_id": self.device_id,
                    "sensor_type": "pressure",
                    "value": pressure,
                    "unit": "hPa",
                    "timestamp": datetime.now().isoformat(),
                    "type": "sensor_data"
                }
                
                if self.mqtt_client.publish(temp_topic, press_message):
                    self.logger.debug(f"🌪️  Presión publicada: {pressure} hPa")
                
                # Esperar antes de la siguiente publicación
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"❌ Error en loop de datos: {e}")
                time.sleep(5)


class IoTDataProcessor:
    """Procesador de datos IoT recibidos por MQTT"""
    
    def __init__(self):
        self.processed_messages = 0
        self.device_data: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def process_message(self, message: MQTTMessage):
        """Procesar mensaje MQTT recibido"""
        try:
            self.processed_messages += 1
            
            # Extraer información del mensaje
            device_id = message.payload.get('device_id')
            message_type = message.payload.get('type')
            timestamp = message.payload.get('timestamp')
            
            if not device_id:
                self.logger.warning("⚠️  Mensaje sin device_id")
                return
            
            # Inicializar datos del dispositivo si no existen
            if device_id not in self.device_data:
                self.device_data[device_id] = {
                    'last_seen': None,
                    'status': 'unknown',
                    'sensors': {},
                    'message_count': 0
                }
            
            # Actualizar información del dispositivo
            self.device_data[device_id]['last_seen'] = timestamp
            self.device_data[device_id]['message_count'] += 1
            
            # Procesar según el tipo de mensaje
            if message_type == 'status':
                self._process_status_message(device_id, message.payload)
            elif message_type == 'sensor_data':
                self._process_sensor_data(device_id, message.payload)
            else:
                self.logger.debug(f"📨 Mensaje de tipo desconocido: {message_type}")
            
            # Mostrar resumen cada 10 mensajes
            if self.processed_messages % 10 == 0:
                self._show_summary()
                
        except Exception as e:
            self.logger.error(f"❌ Error al procesar mensaje: {e}")
    
    def _process_status_message(self, device_id: str, payload: Dict[str, Any]):
        """Procesar mensaje de estado"""
        status = payload.get('status', 'unknown')
        self.device_data[device_id]['status'] = status
        
        self.logger.info(f"📊 Estado del dispositivo {device_id}: {status}")
    
    def _process_sensor_data(self, device_id: str, payload: Dict[str, Any]):
        """Procesar datos del sensor"""
        sensor_type = payload.get('sensor_type')
        value = payload.get('value')
        unit = payload.get('unit')
        
        if sensor_type and value is not None:
            # Actualizar datos del sensor
            if 'sensors' not in self.device_data[device_id]:
                self.device_data[device_id]['sensors'] = {}
            
            self.device_data[device_id]['sensors'][sensor_type] = {
                'value': value,
                'unit': unit,
                'last_update': payload.get('timestamp')
            }
            
            self.logger.debug(f"📊 Datos del sensor {sensor_type}: {value} {unit}")
    
    def _show_summary(self):
        """Mostrar resumen de datos procesados"""
        print("\n" + "="*50)
        print("📊 RESUMEN DE DATOS PROCESADOS")
        print("="*50)
        print(f"📨 Total de mensajes procesados: {self.processed_messages}")
        print(f"📱 Dispositivos activos: {len(self.device_data)}")
        
        for device_id, data in self.device_data.items():
            print(f"\n📱 Dispositivo: {device_id}")
            print(f"   📊 Estado: {data['status']}")
            print(f"   📨 Mensajes: {data['message_count']}")
            print(f"   ⏰ Última actividad: {data['last_seen']}")
            
            if data['sensors']:
                print(f"   🔍 Sensores:")
                for sensor_type, sensor_data in data['sensors'].items():
                    print(f"      {sensor_type}: {sensor_data['value']} {sensor_data['unit']}")
        
        print("="*50)


def example_basic_usage():
    """Ejemplo básico de uso del cliente MQTT"""
    print("\n🔧 EJEMPLO 1: Uso Básico del Cliente MQTT")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config = load_config()
        mqtt_config = config.mqtt
        
        # Crear cliente MQTT
        client = create_mqtt_client(mqtt_config, "basic_example_client")
        print("✅ Cliente MQTT creado")
        
        # Conectar al broker
        if client.connect():
            print("✅ Conectado al broker MQTT")
            
            # Publicar mensaje simple
            test_message = {
                "message": "Hola desde IoT Middleware",
                "timestamp": datetime.now().isoformat(),
                "example": True
            }
            
            if client.publish("iot/example/hello", test_message):
                print("✅ Mensaje de prueba publicado")
            else:
                print("❌ Error al publicar mensaje")
            
            # Desconectar
            client.disconnect()
            print("✅ Desconectado del broker")
            return True
        else:
            print("❌ No se pudo conectar al broker")
            return False
            
    except Exception as e:
        print(f"❌ Error en uso básico: {e}")
        return False


def example_device_simulation():
    """Ejemplo de simulación de dispositivos IoT"""
    print("\n🔧 EJEMPLO 2: Simulación de Dispositivos IoT")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config = load_config()
        mqtt_config = config.mqtt
        
        # Crear cliente MQTT
        client = create_mqtt_client(mqtt_config, "simulation_client")
        print("✅ Cliente MQTT creado para simulación")
        
        # Conectar al broker
        if not client.connect():
            print("❌ No se pudo conectar al broker")
            return False
        
        print("✅ Conectado al broker MQTT")
        
        # Crear simuladores de dispositivos
        devices = [
            IoTDeviceSimulator("sensor_001", client),
            IoTDeviceSimulator("sensor_002", client),
            IoTDeviceSimulator("sensor_003", client)
        ]
        
        print(f"🚀 Iniciando {len(devices)} dispositivos simulados...")
        
        # Iniciar dispositivos
        for device in devices:
            device.start()
        
        # Ejecutar simulación por 30 segundos
        print("⏰ Ejecutando simulación por 30 segundos...")
        time.sleep(30)
        
        # Detener dispositivos
        print("🛑 Deteniendo dispositivos...")
        for device in devices:
            device.stop()
        
        # Desconectar cliente
        client.disconnect()
        print("✅ Simulación completada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en simulación: {e}")
        return False


def example_message_processing():
    """Ejemplo de procesamiento de mensajes"""
    print("\n🔧 EJEMPLO 3: Procesamiento de Mensajes")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config = load_config()
        mqtt_config = config.mqtt
        
        # Crear cliente MQTT
        client = create_mqtt_client(mqtt_config, "processor_client")
        print("✅ Cliente MQTT creado para procesamiento")
        
        # Crear procesador de datos
        processor = IoTDataProcessor()
        print("✅ Procesador de datos creado")
        
        # Configurar procesador en el cliente
        client.set_message_processor(processor.process_message)
        print("✅ Procesador configurado en el cliente")
        
        # Conectar al broker
        if not client.connect():
            print("❌ No se pudo conectar al broker")
            return False
        
        print("✅ Conectado al broker MQTT")
        
        # Publicar algunos mensajes de prueba para procesar
        test_messages = [
            {
                "device_id": "test_device_001",
                "type": "status",
                "status": "online",
                "timestamp": datetime.now().isoformat()
            },
            {
                "device_id": "test_device_001",
                "type": "sensor_data",
                "sensor_type": "temperature",
                "value": 24.5,
                "unit": "celsius",
                "timestamp": datetime.now().isoformat()
            },
            {
                "device_id": "test_device_002",
                "type": "status",
                "status": "online",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        print("📤 Publicando mensajes de prueba...")
        for i, message in enumerate(test_messages, 1):
            topic = f"iot/test/device{i:03d}/data"
            if client.publish(topic, message):
                print(f"✅ Mensaje {i} publicado")
            else:
                print(f"❌ Error al publicar mensaje {i}")
            
            time.sleep(1)
        
        # Esperar a que se procesen los mensajes
        print("⏳ Esperando procesamiento de mensajes...")
        time.sleep(5)
        
        # Mostrar resumen final
        processor._show_summary()
        
        # Desconectar cliente
        client.disconnect()
        print("✅ Procesamiento completado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en procesamiento: {e}")
        return False


def example_advanced_features():
    """Ejemplo de características avanzadas"""
    print("\n🔧 EJEMPLO 4: Características Avanzadas")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config = load_config()
        mqtt_config = config.mqtt
        
        # Crear cliente MQTT
        client = create_mqtt_client(mqtt_config, "advanced_client")
        print("✅ Cliente MQTT creado para características avanzadas")
        
        # Conectar al broker
        if not client.connect():
            print("❌ No se pudo conectar al broker")
            return False
        
        print("✅ Conectado al broker MQTT")
        
        # Suscribirse a tópicos adicionales
        additional_topics = [
            "iot/+/+/alerts",
            "iot/+/+/commands"
        ]
        
        for topic in additional_topics:
            if client.subscribe(topic):
                print(f"📋 Suscrito a tópico adicional: {topic}")
            else:
                print(f"❌ Error al suscribirse a: {topic}")
        
        # Publicar mensajes con diferentes QoS
        messages_qos = [
            ("iot/test/qos0/data", {"qos": 0, "message": "QoS 0 - At most once"}, 0),
            ("iot/test/qos1/data", {"qos": 1, "message": "QoS 1 - At least once"}, 1),
            ("iot/test/qos2/data", {"qos": 2, "message": "QoS 2 - Exactly once"}, 2)
        ]
        
        print("📤 Publicando mensajes con diferentes QoS...")
        for topic, payload, qos in messages_qos:
            if client.publish(topic, payload, qos=qos):
                print(f"✅ Mensaje QoS {qos} publicado en {topic}")
            else:
                print(f"❌ Error al publicar mensaje QoS {qos}")
            
            time.sleep(1)
        
        # Publicar mensaje retenido
        retained_message = {
            "type": "system_info",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "retained": True
        }
        
        if client.publish("iot/system/info", retained_message, retain=True):
            print("✅ Mensaje retenido publicado")
        else:
            print("❌ Error al publicar mensaje retenido")
        
        # Mostrar estado de conexión
        status = client.get_connection_status()
        print(f"\n📊 Estado de conexión:")
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        # Desconectar cliente
        client.disconnect()
        print("✅ Características avanzadas demostradas")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en características avanzadas: {e}")
        return False


def main():
    """Función principal"""
    print("🚀 Ejemplos de Uso del Cliente MQTT")
    print("=" * 60)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    examples = [
        ("Uso Básico", example_basic_usage),
        ("Simulación de Dispositivos", example_device_simulation),
        ("Procesamiento de Mensajes", example_message_processing),
        ("Características Avanzadas", example_advanced_features)
    ]
    
    results = []
    
    for example_name, example_func in examples:
        print(f"\n{'='*20} {example_name} {'='*20}")
        try:
            success = example_func()
            results.append((example_name, success))
        except Exception as e:
            print(f"❌ Error inesperado en {example_name}: {e}")
            results.append((example_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE EJEMPLOS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for example_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{example_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} ejemplos funcionaron")
    
    if passed == total:
        print("🎉 ¡Todos los ejemplos funcionaron exitosamente!")
        print("\n💡 El cliente MQTT está listo para usar en producción")
        return True
    else:
        print("⚠️  Algunos ejemplos fallaron")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
