#!/usr/bin/env python3
"""
Ejemplo de Uso del Script Principal - IoT Middleware
====================================================

Este script demuestra cómo usar el script principal main.py
y cómo configurar el sistema para diferentes escenarios.
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from typing import Optional, Dict, Any

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.config import load_config
    print("✅ Módulos importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    sys.exit(1)


class MainScriptTester:
    """Clase para probar el script principal"""
    
    def __init__(self):
        self.main_process = None
        self.config_path = "config.yaml"
        self.log_file = "iot_middleware.log"
    
    def check_prerequisites(self) -> bool:
        """Verifica los prerrequisitos del sistema"""
        print("🔍 Verificando prerrequisitos...")
        
        # Verificar archivo de configuración
        if not os.path.exists(self.config_path):
            print(f"❌ Archivo de configuración no encontrado: {self.config_path}")
            print("💡 Asegúrate de que config.yaml esté en el directorio raíz")
            return False
        
        # Verificar directorio src
        src_dir = Path("src")
        if not src_dir.exists():
            print("❌ Directorio src no encontrado")
            print("💡 Asegúrate de estar en el directorio raíz del proyecto")
            return False
        
        # Verificar dependencias básicas
        try:
            import fastapi
            import uvicorn
            import paho.mqtt.client
            import sqlalchemy
            print("✅ Dependencias básicas verificadas")
        except ImportError as e:
            print(f"❌ Dependencia faltante: {e}")
            print("💡 Instala las dependencias con: pip install -r requirements.txt")
            return False
        
        print("✅ Prerrequisitos verificados")
        return True
    
    def validate_configuration(self) -> bool:
        """Valida la configuración del archivo config.yaml"""
        print("📋 Validando configuración...")
        
        try:
            config = load_config(self.config_path)
            print("✅ Configuración cargada exitosamente")
            
            # Mostrar información básica de configuración
            print("\n📊 Información de Configuración:")
            
            if hasattr(config, 'mqtt') and config.mqtt:
                mqtt_config = config.mqtt
                print(f"   📡 MQTT Broker: {mqtt_config.broker.host}:{mqtt_config.broker.port}")
                print(f"   📝 Tópicos a suscribir: {len(mqtt_config.topics.subscribe)}")
            
            if hasattr(config, 'storage') and config.storage:
                storage_config = config.storage
                print(f"   🗄️  Tipo de almacenamiento: {storage_config.type}")
                if hasattr(storage_config, 'postgresql') and storage_config.postgresql:
                    pg_config = storage_config.postgresql
                    print(f"   🐘 PostgreSQL: {pg_config.host}:{pg_config.port}/{pg_config.database}")
            
            if hasattr(config, 'api') and config.api:
                api_config = config.api
                print(f"   🌐 API REST: {api_config.host}:{api_config.port}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error validando configuración: {e}")
            return False
    
    def start_main_script(self) -> bool:
        """Inicia el script principal en un proceso separado"""
        print("🚀 Iniciando script principal...")
        
        try:
            # Iniciar el script principal
            self.main_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            print(f"✅ Script principal iniciado (PID: {self.main_process.pid})")
            
            # Esperar un momento para que se inicialice
            time.sleep(3)
            
            # Verificar si el proceso sigue ejecutándose
            if self.main_process.poll() is None:
                print("✅ Script principal ejecutándose correctamente")
                return True
            else:
                print("❌ Script principal terminó prematuramente")
                return False
                
        except Exception as e:
            print(f"❌ Error iniciando script principal: {e}")
            return False
    
    def monitor_main_script(self, duration: int = 30):
        """Monitorea el script principal durante un tiempo determinado"""
        print(f"📊 Monitoreando script principal durante {duration} segundos...")
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                # Verificar estado del proceso
                if self.main_process.poll() is not None:
                    print("❌ Script principal terminó inesperadamente")
                    break
                
                # Leer salida si está disponible
                try:
                    stdout_line = self.main_process.stdout.readline()
                    if stdout_line:
                        print(f"📝 [MAIN] {stdout_line.strip()}")
                except:
                    pass
                
                # Leer errores si están disponibles
                try:
                    stderr_line = self.main_process.stderr.readline()
                    if stderr_line:
                        print(f"⚠️  [ERROR] {stderr_line.strip()}")
                except:
                    pass
                
                time.sleep(1)
            
            print("✅ Monitoreo completado")
            
        except KeyboardInterrupt:
            print("\n🛑 Monitoreo interrumpido por el usuario")
    
    def stop_main_script(self):
        """Detiene el script principal"""
        print("🛑 Deteniendo script principal...")
        
        if self.main_process:
            try:
                # Enviar señal SIGTERM
                self.main_process.terminate()
                
                # Esperar que termine
                try:
                    self.main_process.wait(timeout=10)
                    print("✅ Script principal detenido correctamente")
                except subprocess.TimeoutExpired:
                    print("⚠️  Script principal no terminó en tiempo, forzando parada...")
                    self.main_process.kill()
                    self.main_process.wait()
                    print("✅ Script principal forzado a parar")
                
            except Exception as e:
                print(f"❌ Error deteniendo script principal: {e}")
    
    def check_logs(self):
        """Verifica los logs generados"""
        print("📋 Verificando logs...")
        
        if os.path.exists(self.log_file):
            print(f"✅ Archivo de log encontrado: {self.log_file}")
            
            # Mostrar últimas líneas del log
            try:
                with open(self.log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"\n📝 Últimas 5 líneas del log:")
                        for line in lines[-5:]:
                            print(f"   {line.strip()}")
                    else:
                        print("   Log vacío")
            except Exception as e:
                print(f"❌ Error leyendo log: {e}")
        else:
            print(f"⚠️  Archivo de log no encontrado: {self.log_file}")
    
    def test_api_endpoints(self):
        """Prueba los endpoints de la API REST"""
        print("🌐 Probando endpoints de la API...")
        
        import requests
        
        base_url = "http://localhost:8000"
        
        # Lista de endpoints a probar
        endpoints = [
            ("/", "Información de la API"),
            ("/health", "Estado de salud"),
            ("/topics", "Tópicos disponibles"),
            ("/data", "Datos de sensores"),
            ("/stats", "Estadísticas")
        ]
        
        for endpoint, description in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ {endpoint}: {description} - OK")
                else:
                    print(f"   ⚠️  {endpoint}: {description} - Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"   ❌ {endpoint}: {description} - Error: {e}")
    
    def run_full_test(self):
        """Ejecuta una prueba completa del sistema"""
        print("🧪 EJECUTANDO PRUEBA COMPLETA DEL SISTEMA")
        print("=" * 60)
        
        try:
            # 1. Verificar prerrequisitos
            if not self.check_prerequisites():
                return False
            
            # 2. Validar configuración
            if not self.validate_configuration():
                return False
            
            # 3. Iniciar script principal
            if not self.start_main_script():
                return False
            
            # 4. Monitorear ejecución
            self.monitor_main_script(duration=20)
            
            # 5. Probar API (si está disponible)
            try:
                self.test_api_endpoints()
            except Exception as e:
                print(f"⚠️  No se pudieron probar los endpoints: {e}")
            
            # 6. Verificar logs
            self.check_logs()
            
            return True
            
        except Exception as e:
            print(f"❌ Error en prueba completa: {e}")
            return False
        finally:
            # 7. Detener script principal
            self.stop_main_script()


def example_basic_usage():
    """Ejemplo de uso básico del script principal"""
    print("\n🔧 EJEMPLO 1: Uso Básico del Script Principal")
    print("=" * 50)
    
    print("💡 Para usar el script principal:")
    print("   1. Asegúrate de tener config.yaml configurado")
    print("   2. Ejecuta: python main.py")
    print("   3. El sistema iniciará automáticamente:")
    print("      - Cliente MQTT")
    print("      - API REST en puerto 8000")
    print("      - Servicios de auditoría")
    print("      - Monitoreo continuo")
    
    print("\n📋 Comandos útiles:")
    print("   # Iniciar sistema completo")
    print("   python main.py")
    print("   ")
    print("   # Ver logs en tiempo real")
    print("   tail -f iot_middleware.log")
    print("   ")
    print("   # Probar API REST")
    print("   curl http://localhost:8000/health")
    print("   curl http://localhost:8000/data?limit=10")


def example_configuration_tips():
    """Ejemplo de configuración del sistema"""
    print("\n🔧 EJEMPLO 2: Configuración del Sistema")
    print("=" * 50)
    
    print("📋 Archivo config.yaml:")
    print("   - Configuración MQTT (broker, tópicos)")
    print("   - Configuración de base de datos")
    print("   - Configuración de la API REST")
    print("   - Configuración de auditoría")
    print("   - Configuración de logging")
    
    print("\n🔧 Configuración MQTT:")
    print("   mqtt:")
    print("     broker:")
    print("       host: 'localhost'")
    print("       port: 1883")
    print("       username: 'iot_user'")
    print("       password: 'iot_password'")
    
    print("\n🗄️  Configuración PostgreSQL:")
    print("   storage:")
    print("     type: 'postgresql'")
    print("     postgresql:")
    print("       host: 'localhost'")
    print("       port: 5432")
    print("       database: 'iot_middleware'")
    
    print("\n🌐 Configuración API REST:")
    print("   api:")
    print("     host: '0.0.0.0'")
    print("     port: 8000")
    print("     cors:")
    print("       enabled: true")


def example_troubleshooting():
    """Ejemplo de solución de problemas"""
    print("\n🔧 EJEMPLO 3: Solución de Problemas")
    print("=" * 50)
    
    print("❌ Problema: Error de conexión a base de datos")
    print("💡 Solución:")
    print("   1. Verifica que PostgreSQL esté ejecutándose")
    print("   2. Verifica credenciales en config.yaml")
    print("   3. Verifica que la base de datos exista")
    print("   4. Ejecuta: psql -h localhost -U iot_user -d iot_middleware")
    
    print("\n❌ Problema: Error de conexión MQTT")
    print("💡 Solución:")
    print("   1. Verifica que Mosquitto esté ejecutándose")
    print("   2. Verifica credenciales en config.yaml")
    print("   3. Verifica firewall y puertos")
    print("   4. Ejecuta: mosquitto_sub -h localhost -t 'test'")
    
    print("\n❌ Problema: API no responde")
    print("💡 Solución:")
    print("   1. Verifica que el puerto 8000 esté libre")
    print("   2. Verifica logs en iot_middleware.log")
    print("   3. Verifica que la base de datos esté disponible")
    print("   4. Ejecuta: curl http://localhost:8000/health")


def example_monitoring():
    """Ejemplo de monitoreo del sistema"""
    print("\n🔧 EJEMPLO 4: Monitoreo del Sistema")
    print("=" * 50)
    
    print("📊 Monitoreo en Tiempo Real:")
    print("   El script principal muestra automáticamente:")
    print("   - Estado de todos los servicios")
    print("   - Estado de threads")
    print("   - Información de conexiones MQTT")
    print("   - Estado de la API REST")
    
    print("\n📋 Logs del Sistema:")
    print("   - iot_middleware.log: Log principal del sistema")
    print("   - Consola: Estado en tiempo real")
    print("   - Base de datos: Registros de auditoría")
    
    print("\n🔍 Endpoints de Monitoreo:")
    print("   - GET /health: Estado de salud del sistema")
    print("   - GET /stats: Estadísticas de datos")
    print("   - GET /topics: Tópicos disponibles")
    
    print("\n📈 Métricas Disponibles:")
    print("   - Mensajes MQTT recibidos/procesados")
    print("   - Consultas a la API")
    print("   - Estado de la base de datos")
    print("   - Uso de memoria y CPU")


def main():
    """Función principal"""
    print("🚀 Ejemplos de Uso del Script Principal - IoT Middleware")
    print("=" * 70)
    
    # Ejecutar ejemplos
    examples = [
        ("Uso Básico", example_basic_usage),
        ("Configuración", example_configuration_tips),
        ("Solución de Problemas", example_troubleshooting),
        ("Monitoreo", example_monitoring),
    ]
    
    for example_name, example_func in examples:
        print(f"\n{'='*20} {example_name} {'='*20}")
        try:
            example_func()
        except Exception as e:
            print(f"❌ Error en ejemplo {example_name}: {e}")
    
    # Ejecutar prueba completa si se solicita
    print("\n" + "=" * 70)
    print("🧪 PRUEBA COMPLETA DEL SISTEMA")
    print("=" * 70)
    
    response = input("¿Deseas ejecutar una prueba completa del sistema? (s/n): ").lower().strip()
    
    if response in ['s', 'si', 'sí', 'y', 'yes']:
        print("\n🚀 Iniciando prueba completa...")
        
        tester = MainScriptTester()
        success = tester.run_full_test()
        
        if success:
            print("\n🎉 ¡Prueba completada exitosamente!")
            print("💡 El sistema está funcionando correctamente")
        else:
            print("\n⚠️  La prueba encontró algunos problemas")
            print("💡 Revisa los errores y la configuración")
    else:
        print("\n💡 Para probar el sistema completo, ejecuta:")
        print("   python main.py")
    
    print("\n🎯 Resumen de Funcionalidades:")
    print("   ✅ Script principal que inicia todos los servicios")
    print("   ✅ Cliente MQTT y API REST en paralelo")
    print("   ✅ Monitoreo continuo del estado del sistema")
    print("   ✅ Logging estructurado y auditoría")
    print("   ✅ Manejo ordenado de parada y señales")
    print("   ✅ Configuración flexible via config.yaml")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Programa interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)
