#!/usr/bin/env python3
"""
Script Principal - IoT Middleware
=================================

Este script principal inicia todos los servicios del IoT Middleware:
- Cliente MQTT para ingesta de datos
- API REST para consulta de datos
- Servicios de auditoría y procesamiento

Los servicios se ejecutan en paralelo usando threading para máxima eficiencia.
"""

import os
import sys
import time
import signal
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from iot_middleware.config import load_config
    from iot_middleware.services.ingestor import MQTTIngestaService, run as run_ingestor
    from iot_middleware.api.api import initialize_api, app
    from iot_middleware.mqtt.mqtt_client import create_mqtt_client
    from iot_middleware.storage.db_handler import create_database_handler
    from iot_middleware.utils.auditoria import create_auditoria_service
    print("✅ Módulos importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    print("💡 Asegúrate de que todas las dependencias estén instaladas")
    sys.exit(1)


class IoTMiddlewareManager:
    """Gestor principal del IoT Middleware"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = None
        self.ingestor_service = None
        self.api_app = None
        self.mqtt_client = None
        self.db_handler = None
        self.auditoria_service = None
        
        # Estado de los servicios
        self.services_status = {
            'config': False,
            'database': False,
            'mqtt': False,
            'ingestor': False,
            'api': False,
            'auditoria': False
        }
        
        # Threads de los servicios
        self.service_threads = {}
        
        # Flags de control
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Configurar logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Configurar manejo de señales
        self.setup_signal_handlers()
    
    def setup_logging(self):
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('iot_middleware.log')
            ]
        )
        
        # Configurar nivel de logging para módulos específicos
        logging.getLogger('iot_middleware').setLevel(logging.INFO)
        logging.getLogger('fastapi').setLevel(logging.WARNING)
        logging.getLogger('uvicorn').setLevel(logging.WARNING)
    
    def setup_signal_handlers(self):
        """Configura los manejadores de señales del sistema"""
        def signal_handler(signum, frame):
            self.logger.info(f"🛑 Señal recibida: {signum}")
            self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def load_configuration(self) -> bool:
        """Carga la configuración del sistema"""
        try:
            self.logger.info(f"📋 Cargando configuración desde: {self.config_path}")
            
            if not os.path.exists(self.config_path):
                self.logger.error(f"❌ Archivo de configuración no encontrado: {self.config_path}")
                return False
            
            self.config = load_config(self.config_path)
            self.logger.info("✅ Configuración cargada exitosamente")
            
            # Mostrar información de configuración
            self.log_config_info()
            
            self.services_status['config'] = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error cargando configuración: {e}")
            return False
    
    def log_config_info(self):
        """Muestra información de la configuración cargada"""
        if not self.config:
            return
        
        self.logger.info("📊 Información de Configuración:")
        
        # Configuración MQTT
        if hasattr(self.config, 'mqtt') and self.config.mqtt:
            mqtt_config = self.config.mqtt
            self.logger.info(f"   📡 MQTT Broker: {mqtt_config.broker.host}:{mqtt_config.broker.port}")
            self.logger.info(f"   🔐 Usuario: {mqtt_config.broker.username}")
            self.logger.info(f"   📝 Tópicos a suscribir: {len(mqtt_config.topics.subscribe)}")
        
        # Configuración de almacenamiento
        if hasattr(self.config, 'storage') and self.config.storage:
            storage_config = self.config.storage
            self.logger.info(f"   🗄️  Tipo de almacenamiento: {storage_config.type}")
            if hasattr(storage_config, 'postgresql') and storage_config.postgresql:
                pg_config = storage_config.postgresql
                self.logger.info(f"   🐘 PostgreSQL: {pg_config.host}:{pg_config.port}/{pg_config.database}")
        
        # Configuración de ingesta
        if hasattr(self.config, 'ingesta') and self.config.ingesta:
            ingesta_config = self.config.ingesta
            self.logger.info(f"   🔄 Tamaño de cola: {ingesta_config.get('max_queue_size', 'N/A')}")
            self.logger.info(f"   📦 Tamaño de lote: {ingesta_config.get('batch_size', 'N/A')}")
    
    def initialize_database(self) -> bool:
        """Inicializa la conexión a la base de datos"""
        try:
            self.logger.info("🗄️  Inicializando conexión a base de datos...")
            
            self.db_handler = create_database_handler(self.config.storage)
            
            # Verificar conexión
            with self.db_handler.get_session() as session:
                session.execute("SELECT 1")
            
            self.logger.info("✅ Base de datos inicializada exitosamente")
            self.services_status['database'] = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando base de datos: {e}")
            return False
    
    def initialize_auditoria(self) -> bool:
        """Inicializa el servicio de auditoría"""
        try:
            self.logger.info("🔍 Inicializando servicio de auditoría...")
            
            self.auditoria_service = create_auditoria_service(self.db_handler)
            
            self.logger.info("✅ Servicio de auditoría inicializado exitosamente")
            self.services_status['auditoria'] = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando auditoría: {e}")
            return False
    
    def initialize_mqtt_client(self) -> bool:
        """Inicializa el cliente MQTT"""
        try:
            self.logger.info("📡 Inicializando cliente MQTT...")
            
            self.mqtt_client = create_mqtt_client(self.config.mqtt)
            
            # Conectar al broker
            if self.mqtt_client.connect():
                self.logger.info("✅ Cliente MQTT conectado exitosamente")
                self.services_status['mqtt'] = True
                return True
            else:
                self.logger.error("❌ No se pudo conectar al broker MQTT")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error inicializando cliente MQTT: {e}")
            return False
    
    def initialize_ingestor_service(self) -> bool:
        """Inicializa el servicio de ingesta"""
        try:
            self.logger.info("🔄 Inicializando servicio de ingesta...")
            
            self.ingestor_service = MQTTIngestaService(self.config_path)
            
            if self.ingestor_service.initialize():
                self.logger.info("✅ Servicio de ingesta inicializado exitosamente")
                self.services_status['ingestor'] = True
                return True
            else:
                self.logger.error("❌ No se pudo inicializar el servicio de ingesta")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error inicializando servicio de ingesta: {e}")
            return False
    
    def initialize_api(self) -> bool:
        """Inicializa la API REST"""
        try:
            self.logger.info("🌐 Inicializando API REST...")
            
            # Inicializar la API con la configuración
            initialize_api(self.config_path)
            
            self.logger.info("✅ API REST inicializada exitosamente")
            self.services_status['api'] = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando API REST: {e}")
            return False
    
    def start_ingestor_service(self):
        """Inicia el servicio de ingesta en un thread separado"""
        try:
            self.logger.info("🚀 Iniciando servicio de ingesta...")
            
            def ingestor_worker():
                try:
                    self.ingestor_service.start()
                except Exception as e:
                    self.logger.error(f"❌ Error en servicio de ingesta: {e}")
                    self.services_status['ingestor'] = False
            
            # Crear y iniciar thread
            ingestor_thread = threading.Thread(
                target=ingestor_worker,
                name="IngestorService",
                daemon=True
            )
            ingestor_thread.start()
            
            self.service_threads['ingestor'] = ingestor_thread
            self.logger.info("✅ Servicio de ingesta iniciado en thread separado")
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando servicio de ingesta: {e}")
    
    def start_api_server(self):
        """Inicia el servidor de la API REST en un thread separado"""
        try:
            self.logger.info("🚀 Iniciando servidor de API REST...")
            
            import uvicorn
            
            def api_worker():
                try:
                    uvicorn.run(
                        app,
                        host="0.0.0.0",
                        port=8000,
                        log_level="info",
                        access_log=False
                    )
                except Exception as e:
                    self.logger.error(f"❌ Error en servidor de API: {e}")
                    self.services_status['api'] = False
            
            # Crear y iniciar thread
            api_thread = threading.Thread(
                target=api_worker,
                name="APIServer",
                daemon=True
            )
            api_thread.start()
            
            self.service_threads['api'] = api_thread
            self.logger.info("✅ Servidor de API REST iniciado en thread separado")
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando servidor de API: {e}")
    
    def monitor_services(self):
        """Monitorea el estado de los servicios"""
        try:
            self.logger.info("📊 Monitoreando servicios...")
            
            while self.running and not self.shutdown_event.is_set():
                # Verificar estado de threads
                for service_name, thread in self.service_threads.items():
                    if not thread.is_alive():
                        self.logger.warning(f"⚠️  Thread del servicio {service_name} no está activo")
                        self.services_status[service_name] = False
                    else:
                        self.services_status[service_name] = True
                
                # Mostrar estado
                self.print_status()
                
                # Esperar antes de la siguiente verificación
                time.sleep(10)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Monitoreo interrumpido por el usuario")
        except Exception as e:
            self.logger.error(f"❌ Error en monitoreo: {e}")
    
    def print_status(self):
        """Imprime el estado actual de los servicios"""
        print("\n" + "=" * 60)
        print("📊 ESTADO DE SERVICIOS - IoT Middleware")
        print("=" * 60)
        print(f"🕐 Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print()
        
        # Estado de servicios
        for service, status in self.services_status.items():
            icon = "✅" if status else "❌"
            status_text = "ACTIVO" if status else "INACTIVO"
            print(f"{icon} {service.upper()}: {status_text}")
        
        print()
        
        # Estado de threads
        print("🧵 THREADS DE SERVICIOS:")
        for service_name, thread in self.service_threads.items():
            if thread.is_alive():
                print(f"   ✅ {service_name}: ACTIVO (ID: {thread.ident})")
            else:
                print(f"   ❌ {service_name}: INACTIVO")
        
        print()
        
        # Información de conexiones
        if self.services_status['mqtt']:
            print("📡 MQTT:")
            print(f"   Broker: {self.config.mqtt.broker.host}:{self.config.mqtt.broker.port}")
            print(f"   Estado: CONECTADO")
            print(f"   Tópicos suscritos: {len(self.config.mqtt.topics.subscribe)}")
        
        if self.services_status['api']:
            print("🌐 API REST:")
            print(f"   URL: http://localhost:8000")
            print(f"   Documentación: http://localhost:8000/docs")
            print(f"   Estado: ACTIVA")
        
        print("=" * 60)
    
    def initialize_all_services(self) -> bool:
        """Inicializa todos los servicios del sistema"""
        try:
            self.logger.info("🚀 Inicializando todos los servicios...")
            
            # 1. Cargar configuración
            if not self.load_configuration():
                return False
            
            # 2. Inicializar base de datos
            if not self.initialize_database():
                return False
            
            # 3. Inicializar auditoría
            if not self.initialize_auditoria():
                return False
            
            # 4. Inicializar cliente MQTT
            if not self.initialize_mqtt_client():
                return False
            
            # 5. Inicializar servicio de ingesta
            if not self.initialize_ingestor_service():
                return False
            
            # 6. Inicializar API REST
            if not self.initialize_api():
                return False
            
            self.logger.info("🎉 Todos los servicios inicializados exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando servicios: {e}")
            return False
    
    def start_all_services(self):
        """Inicia todos los servicios en threads separados"""
        try:
            self.logger.info("🚀 Iniciando todos los servicios...")
            
            # Iniciar servicio de ingesta
            self.start_ingestor_service()
            
            # Iniciar servidor de API
            self.start_api_server()
            
            # Esperar un momento para que los servicios se inicien
            time.sleep(2)
            
            self.logger.info("🎉 Todos los servicios iniciados")
            
        except Exception as e:
            self.logger.error(f"❌ Error iniciando servicios: {e}")
    
    def run(self):
        """Ejecuta el sistema completo"""
        try:
            self.logger.info("🚀 Iniciando IoT Middleware...")
            
            # Inicializar servicios
            if not self.initialize_all_services():
                self.logger.error("❌ Falló la inicialización de servicios")
                return False
            
            # Iniciar servicios
            self.start_all_services()
            
            # Marcar como ejecutándose
            self.running = True
            
            # Mostrar estado inicial
            self.print_status()
            
            # Iniciar monitoreo en thread separado
            monitor_thread = threading.Thread(
                target=self.monitor_services,
                name="ServiceMonitor",
                daemon=True
            )
            monitor_thread.start()
            
            self.logger.info("🎉 IoT Middleware ejecutándose correctamente")
            self.logger.info("💡 Presiona Ctrl+C para detener")
            
            # Esperar señal de parada
            try:
                while self.running and not self.shutdown_event.is_set():
                    time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("🛑 Señal de interrupción recibida")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error ejecutando sistema: {e}")
            return False
    
    def shutdown(self):
        """Detiene todos los servicios de forma ordenada"""
        try:
            self.logger.info("🛑 Deteniendo IoT Middleware...")
            
            # Marcar para parada
            self.running = False
            self.shutdown_event.set()
            
            # Detener servicio de ingesta
            if self.ingestor_service:
                try:
                    self.ingestor_service.stop()
                    self.logger.info("✅ Servicio de ingesta detenido")
                except Exception as e:
                    self.logger.error(f"❌ Error deteniendo ingesta: {e}")
            
            # Detener cliente MQTT
            if self.mqtt_client:
                try:
                    self.mqtt_client.disconnect()
                    self.logger.info("✅ Cliente MQTT desconectado")
                except Exception as e:
                    self.logger.error(f"❌ Error desconectando MQTT: {e}")
            
            # Cerrar conexiones de base de datos
            if self.db_handler:
                try:
                    self.db_handler.close()
                    self.logger.info("✅ Conexiones de base de datos cerradas")
                except Exception as e:
                    self.logger.error(f"❌ Error cerrando BD: {e}")
            
            # Esperar que los threads terminen
            for service_name, thread in self.service_threads.items():
                if thread.is_alive():
                    self.logger.info(f"⏳ Esperando que termine thread: {service_name}")
                    thread.join(timeout=5)
                    if thread.is_alive():
                        self.logger.warning(f"⚠️  Thread {service_name} no terminó en tiempo")
            
            self.logger.info("🎉 IoT Middleware detenido correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error durante parada: {e}")


def main():
    """Función principal"""
    print("🚀 IoT Middleware - Sistema Principal")
    print("=" * 50)
    
    # Verificar archivo de configuración
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        print(f"❌ Archivo de configuración no encontrado: {config_path}")
        print("💡 Asegúrate de que config.yaml esté en el directorio actual")
        return False
    
    # Crear y ejecutar el gestor
    manager = IoTMiddlewareManager(config_path)
    
    try:
        success = manager.run()
        return success
    except KeyboardInterrupt:
        print("\n🛑 Interrumpido por el usuario")
        return True
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
    finally:
        manager.shutdown()


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Programa interrumpido")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)
