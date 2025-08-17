#!/usr/bin/env python3
"""
Script de Prueba para Publicador MQTT
IoT Middleware
=====================================

Este script simula el envío de mensajes MQTT desde dispositivos IoT
para probar el servicio de ingesta.
"""

import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime
import threading

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.mqtt.mqtt_client import create_mqtt_client
    from iot_middleware.config import load_config
    print("✅ Módulos importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    sys.exit(1)


class MQTTPublisherTest:
    """Clase para probar la publicación de mensajes MQTT"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None
        self.mqtt_client = None
        self.running = False
        self.published_count = 0
        
        # Configurar logging
        import logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def initialize(self) -> bool:
        """Inicializa el publicador de prueba"""
        try:
            # Cargar configuración
            self.config = load_config(self.config_path)
            self.logger.info("✅ Configuración cargada")
            
            # Crear cliente MQTT
            self.mqtt_client = create_mqtt_client(self.config.mqtt)
            self.logger.info("✅ Cliente MQTT creado")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando: {e}")
            return False
    
    def connect(self) -> bool:
        """Conecta al broker MQTT"""
        try:
            if self.mqtt_client.connect():
                self.logger.info("✅ Conectado al broker MQTT")
                return True
            else:
                self.logger.error("❌ No se pudo conectar al broker MQTT")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error conectando: {e}")
            return False
    
    def publish_sensor_data(self, topic: str, data: dict, qos: int = 1):
        """Publica datos de sensor en un tópico"""
        try:
            if self.mqtt_client.publish(topic, data, qos=qos):
                self.published_count += 1
                self.logger.debug(f"📤 Publicado en {topic}: {data}")
                return True
            else:
                self.logger.error(f"❌ Error publicando en {topic}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Excepción publicando en {topic}: {e}")
            return False
    
    def generate_temperature_data(self, device_id: str, location: str) -> dict:
        """Genera datos de temperatura simulados"""
        # Simular temperatura con variación realista
        base_temp = 22.0  # temperatura base en Celsius
        variation = random.uniform(-5, 5)  # variación de ±5°C
        temperature = base_temp + variation
        
        # Agregar ruido aleatorio
        noise = random.uniform(-0.5, 0.5)
        temperature += noise
        
        return {
            "device_id": device_id,
            "sensor_type": "temperature",
            "value": round(temperature, 2),
            "unit": "celsius",
            "location": location,
            "timestamp": datetime.now().isoformat(),
            "battery": random.randint(80, 100),
            "signal_strength": random.randint(-60, -30)
        }
    
    def generate_humidity_data(self, device_id: str, location: str) -> dict:
        """Genera datos de humedad simulados"""
        # Simular humedad con variación realista
        base_humidity = 45.0  # humedad base en porcentaje
        variation = random.uniform(-15, 15)  # variación de ±15%
        humidity = base_humidity + variation
        
        # Asegurar que esté en rango válido
        humidity = max(0, min(100, humidity))
        
        return {
            "device_id": device_id,
            "sensor_type": "humidity",
            "value": round(humidity, 1),
            "unit": "percent",
            "location": location,
            "timestamp": datetime.now().isoformat(),
            "battery": random.randint(75, 95),
            "signal_strength": random.randint(-65, -35)
        }
    
    def generate_pressure_data(self, device_id: str, location: str) -> dict:
        """Genera datos de presión atmosférica simulados"""
        # Simular presión atmosférica (normalmente alrededor de 1013.25 hPa)
        base_pressure = 1013.25
        variation = random.uniform(-20, 20)  # variación de ±20 hPa
        pressure = base_pressure + variation
        
        return {
            "device_id": device_id,
            "sensor_type": "pressure",
            "value": round(pressure, 2),
            "unit": "hpa",
            "location": location,
            "timestamp": datetime.now().isoformat(),
            "battery": random.randint(70, 90),
            "signal_strength": random.randint(-70, -40)
        }
    
    def generate_device_status(self, device_id: str) -> dict:
        """Genera estado del dispositivo"""
        statuses = ["online", "offline", "maintenance", "error"]
        status = random.choice(statuses)
        
        return {
            "device_id": device_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "uptime": random.randint(0, 86400),  # 0-24 horas en segundos
            "battery": random.randint(0, 100),
            "signal_strength": random.randint(-80, -20),
            "last_maintenance": (datetime.now() - random.randint(0, 30)).isoformat(),
            "errors": random.randint(0, 5) if status == "error" else 0
        }
    
    def run_temperature_simulation(self, duration: int = 60):
        """Ejecuta simulación de sensores de temperatura"""
        self.logger.info(f"🌡️  Iniciando simulación de temperatura por {duration} segundos")
        
        start_time = time.time()
        devices = [
            ("sensor_temp_001", "sala_principal"),
            ("sensor_temp_002", "cocina"),
            ("sensor_temp_003", "dormitorio"),
            ("sensor_temp_004", "exterior")
        ]
        
        while time.time() - start_time < duration and self.running:
            for device_id, location in devices:
                # Generar datos
                data = self.generate_temperature_data(device_id, location)
                
                # Publicar en tópico estructurado
                topic = f"iot/proyecto_001/unidad_001/{device_id}/canal_temperatura"
                self.publish_sensor_data(topic, data)
                
                # Publicar en tópico alternativo
                topic_alt = f"sensors/temperature/{location}/{device_id}"
                self.publish_sensor_data(topic_alt, data)
            
            # Esperar antes del siguiente ciclo
            time.sleep(5)
        
        self.logger.info("🌡️  Simulación de temperatura completada")
    
    def run_humidity_simulation(self, duration: int = 60):
        """Ejecuta simulación de sensores de humedad"""
        self.logger.info(f"💧 Iniciando simulación de humedad por {duration} segundos")
        
        start_time = time.time()
        devices = [
            ("sensor_hum_001", "sala_principal"),
            ("sensor_hum_002", "cocina"),
            ("sensor_hum_003", "bano")
        ]
        
        while time.time() - start_time < duration and self.running:
            for device_id, location in devices:
                # Generar datos
                data = self.generate_humidity_data(device_id, location)
                
                # Publicar en tópico estructurado
                topic = f"iot/proyecto_001/unidad_001/{device_id}/canal_humedad"
                self.publish_sensor_data(topic, data)
                
                # Publicar en tópico alternativo
                topic_alt = f"sensors/humidity/{location}/{device_id}"
                self.publish_sensor_data(topic_alt, data)
            
            # Esperar antes del siguiente ciclo
            time.sleep(8)
        
        self.logger.info("💧 Simulación de humedad completada")
    
    def run_pressure_simulation(self, duration: int = 60):
        """Ejecuta simulación de sensores de presión"""
        self.logger.info(f"🌪️  Iniciando simulación de presión por {duration} segundos")
        
        start_time = time.time()
        devices = [
            ("sensor_pres_001", "exterior"),
            ("sensor_pres_002", "interior")
        ]
        
        while time.time() - start_time < duration and self.running:
            for device_id, location in devices:
                # Generar datos
                data = self.generate_pressure_data(device_id, location)
                
                # Publicar en tópico estructurado
                topic = f"iot/proyecto_001/unidad_001/{device_id}/canal_presion"
                self.publish_sensor_data(topic, data)
                
                # Publicar en tópico alternativo
                topic_alt = f"sensors/pressure/{location}/{device_id}"
                self.publish_sensor_data(topic_alt, data)
            
            # Esperar antes del siguiente ciclo
            time.sleep(10)
        
        self.logger.info("🌪️  Simulación de presión completada")
    
    def run_device_status_simulation(self, duration: int = 60):
        """Ejecuta simulación de estado de dispositivos"""
        self.logger.info(f"📱 Iniciando simulación de estado de dispositivos por {duration} segundos")
        
        start_time = time.time()
        devices = [
            "device_001",
            "device_002",
            "device_003",
            "gateway_001"
        ]
        
        while time.time() - start_time < duration and self.running:
            for device_id in devices:
                # Generar estado
                data = self.generate_device_status(device_id)
                
                # Publicar en tópico de estado
                topic = f"devices/{device_id}/status"
                self.publish_sensor_data(topic, data)
                
                # Publicar en tópico alternativo
                topic_alt = f"iot/status/{device_id}"
                self.publish_sensor_data(topic_alt, data)
            
            # Esperar antes del siguiente ciclo
            time.sleep(15)
        
        self.logger.info("📱 Simulación de estado de dispositivos completada")
    
    def run_custom_data_simulation(self, duration: int = 60):
        """Ejecuta simulación de datos personalizados"""
        self.logger.info(f"🔧 Iniciando simulación de datos personalizados por {duration} segundos")
        
        start_time = time.time()
        categories = ["production", "quality", "maintenance", "security"]
        
        while time.time() - start_time < duration and self.running:
            for category in categories:
                # Generar datos personalizados
                data = {
                    "category": category,
                    "value": random.randint(1, 100),
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "source": "custom_system",
                        "version": "1.0",
                        "priority": random.choice(["low", "medium", "high"])
                    }
                }
                
                # Publicar en tópico personalizado
                topic = f"custom/{category}/data"
                self.publish_sensor_data(topic, data)
            
            # Esperar antes del siguiente ciclo
            time.sleep(12)
        
        self.logger.info("🔧 Simulación de datos personalizados completada")
    
    def run_comprehensive_simulation(self, duration: int = 120):
        """Ejecuta simulación completa de todos los tipos de datos"""
        self.logger.info(f"🚀 Iniciando simulación completa por {duration} segundos")
        
        # Ejecutar todas las simulaciones en threads separados
        threads = []
        
        # Simulación de temperatura (cada 5 segundos)
        temp_thread = threading.Thread(
            target=self.run_temperature_simulation,
            args=(duration,),
            daemon=True
        )
        threads.append(temp_thread)
        
        # Simulación de humedad (cada 8 segundos)
        hum_thread = threading.Thread(
            target=self.run_humidity_simulation,
            args=(duration,),
            daemon=True
        )
        threads.append(hum_thread)
        
        # Simulación de presión (cada 10 segundos)
        pres_thread = threading.Thread(
            target=self.run_pressure_simulation,
            args=(duration,),
            daemon=True
        )
        threads.append(pres_thread)
        
        # Simulación de estado de dispositivos (cada 15 segundos)
        status_thread = threading.Thread(
            target=self.run_device_status_simulation,
            args=(duration,),
            daemon=True
        )
        threads.append(status_thread)
        
        # Simulación de datos personalizados (cada 12 segundos)
        custom_thread = threading.Thread(
            target=self.run_custom_data_simulation,
            args=(duration,),
            daemon=True
        )
        threads.append(custom_thread)
        
        # Iniciar todos los threads
        for thread in threads:
            thread.start()
        
        # Esperar a que termine la simulación
        time.sleep(duration)
        
        self.logger.info("🚀 Simulación completa finalizada")
    
    def start(self, simulation_type: str = "comprehensive", duration: int = 120):
        """Inicia la simulación especificada"""
        try:
            if not self.initialize():
                return False
            
            if not self.connect():
                return False
            
            self.running = True
            self.logger.info(f"🎯 Iniciando simulación: {simulation_type}")
            
            if simulation_type == "temperature":
                self.run_temperature_simulation(duration)
            elif simulation_type == "humidity":
                self.run_humidity_simulation(duration)
            elif simulation_type == "pressure":
                self.run_pressure_simulation(duration)
            elif simulation_type == "status":
                self.run_device_status_simulation(duration)
            elif simulation_type == "custom":
                self.run_custom_data_simulation(duration)
            elif simulation_type == "comprehensive":
                self.run_comprehensive_simulation(duration)
            else:
                self.logger.error(f"❌ Tipo de simulación no válido: {simulation_type}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error en simulación: {e}")
            return False
        finally:
            self.stop()
    
    def stop(self):
        """Detiene la simulación"""
        self.running = False
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        
        self.logger.info(f"📊 Simulación finalizada. Total de mensajes publicados: {self.published_count}")


def main():
    """Función principal"""
    print("🚀 Simulador de Publicador MQTT - IoT Middleware")
    print("=" * 60)
    
    # Verificar argumentos de línea de comandos
    if len(sys.argv) < 2:
        print("Uso: python mqtt_publisher_test.py <tipo_simulacion> [duracion_segundos]")
        print("\nTipos de simulación disponibles:")
        print("  temperature  - Solo sensores de temperatura")
        print("  humidity     - Solo sensores de humedad")
        print("  pressure     - Solo sensores de presión")
        print("  status       - Solo estado de dispositivos")
        print("  custom       - Solo datos personalizados")
        print("  comprehensive - Todas las simulaciones (por defecto)")
        print("\nEjemplos:")
        print("  python mqtt_publisher_test.py temperature 60")
        print("  python mqtt_publisher_test.py comprehensive 300")
        sys.exit(1)
    
    simulation_type = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    
    # Validar tipo de simulación
    valid_types = ["temperature", "humidity", "pressure", "status", "custom", "comprehensive"]
    if simulation_type not in valid_types:
        print(f"❌ Tipo de simulación no válido: {simulation_type}")
        print(f"Tipos válidos: {', '.join(valid_types)}")
        sys.exit(1)
    
    print(f"🎯 Tipo de simulación: {simulation_type}")
    print(f"⏱️  Duración: {duration} segundos")
    
    # Ruta de configuración
    config_path = Path(__file__).parent / "config_ingesta.yaml"
    
    if not config_path.exists():
        print(f"❌ Archivo de configuración no encontrado: {config_path}")
        print("Asegúrate de que config_ingesta.yaml esté en el directorio examples/")
        sys.exit(1)
    
    print(f"📁 Archivo de configuración: {config_path}")
    
    # Crear y ejecutar simulador
    try:
        publisher = MQTTPublisherTest(str(config_path))
        
        print("\n🚀 Iniciando simulación...")
        print("💡 Presiona Ctrl+C para detener la simulación")
        
        success = publisher.start(simulation_type, duration)
        
        if success:
            print("✅ Simulación completada exitosamente")
        else:
            print("❌ La simulación falló")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Simulación interrumpida por el usuario")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
