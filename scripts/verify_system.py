#!/usr/bin/env python3
"""
Script de Verificación del Sistema - IoT Middleware
====================================================

Este script verifica que todos los componentes del sistema estén
correctamente configurados y funcionando.
"""

import os
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class SystemVerifier:
    """Verificador del sistema IoT Middleware"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success = []
        
    def check_file_exists(self, path: str, description: str) -> bool:
        """Verifica que un archivo exista"""
        if os.path.exists(path):
            self.success.append(f"✅ {description}: {path}")
            return True
        else:
            self.errors.append(f"❌ {description} no encontrado: {path}")
            return False
    
    def check_directory_exists(self, path: str, description: str) -> bool:
        """Verifica que un directorio exista"""
        if os.path.isdir(path):
            self.success.append(f"✅ {description}: {path}")
            return True
        else:
            self.errors.append(f"❌ {description} no encontrado: {path}")
            return False
    
    def check_imports(self):
        """Verifica que todos los módulos puedan importarse"""
        print("\n📦 Verificando importaciones de módulos...")
        
        modules_to_check = [
            ("iot_middleware.config", "load_config", "Config"),
            ("iot_middleware.mqtt.mqtt_client", "create_mqtt_client", "MQTT Client"),
            ("iot_middleware.storage.db_handler", "create_database_handler", "Database Handler"),
            ("iot_middleware.services.ingestor", "MQTTIngestaService", "Ingestor Service"),
            ("iot_middleware.utils.auditoria", "create_auditoria_service", "Auditoría Service"),
        ]
        
        # Verificar API por separado para manejar mejor los errores de dependencias
        print("\n🌐 Verificando módulo API...")
        try:
            module = __import__("iot_middleware.api.api", fromlist=["initialize_api"])
            if hasattr(module, "initialize_api"):
                self.success.append("✅ API: OK")
            else:
                self.warnings.append("⚠️  API: Atributo 'initialize_api' no encontrado")
        except ImportError as e:
            error_str = str(e)
            if "jwt" in error_str.lower():
                self.warnings.append("⚠️  API: PyJWT no instalado (instalar con: pip install PyJWT)")
            elif "passlib" in error_str.lower():
                self.warnings.append("⚠️  API: passlib no instalado (instalar con: pip install 'passlib[bcrypt]')")
            else:
                self.errors.append(f"❌ API: {e}")
        except Exception as e:
            error_str = str(e)
            if "jwt" in error_str.lower():
                self.warnings.append("⚠️  API: PyJWT no instalado (instalar con: pip install PyJWT)")
            elif "passlib" in error_str.lower():
                self.warnings.append("⚠️  API: passlib no instalado (instalar con: pip install 'passlib[bcrypt]')")
            else:
                self.errors.append(f"❌ API: {e}")
        
        for module_name, attribute_name, description in modules_to_check:
            try:
                module = __import__(module_name, fromlist=[attribute_name])
                if hasattr(module, attribute_name):
                    self.success.append(f"✅ {description}: OK")
                else:
                    self.warnings.append(f"⚠️  {description}: Atributo '{attribute_name}' no encontrado")
            except ImportError as e:
                error_str = str(e)
                # Intentar verificar si es un problema de dependencias opcionales
                if "pika" in error_str or "aio-pika" in error_str:
                    self.warnings.append(f"⚠️  {description}: Dependencia RabbitMQ no instalada (opcional)")
                elif "email-validator" in error_str or "email" in error_str.lower():
                    self.warnings.append(f"⚠️  {description}: email-validator no instalado (instalar con: pip install email-validator)")
                else:
                    self.errors.append(f"❌ {description}: {e}")
            except Exception as e:
                error_str = str(e)
                # Tratar errores de email-validator como warnings
                if "email-validator" in error_str or ("email" in error_str.lower() and "validator" in error_str.lower()):
                    self.warnings.append(f"⚠️  {description}: email-validator no instalado (instalar con: pip install email-validator)")
                else:
                    self.errors.append(f"❌ {description}: {e}")
    
    def check_rabbitmq_imports(self):
        """Verifica imports de RabbitMQ (opcional)"""
        print("\n🐰 Verificando módulos de RabbitMQ...")
        try:
            from iot_middleware.messaging import RabbitMQClient, create_rabbitmq_client
            self.success.append("✅ RabbitMQ Client: OK")
        except ImportError as e:
            if "pika" in str(e):
                self.warnings.append("⚠️  RabbitMQ: Dependencias no instaladas (monitoreo limitado)")
            else:
                self.errors.append(f"❌ RabbitMQ: {e}")
        except Exception as e:
            self.warnings.append(f"⚠️  RabbitMQ: {e}")
    
    def check_config_file(self):
        """Verifica que el archivo de configuración sea válido"""
        print("\n⚙️  Verificando archivo de configuración...")
        
        config_path = Path(__file__).parent.parent / "config.yaml"
        if not config_path.exists():
            self.errors.append(f"❌ Config.yaml no encontrado: {config_path}")
            return
        
        try:
            from iot_middleware.config import load_config
            config = load_config(str(config_path))
            self.success.append("✅ Config.yaml: Válido y cargado correctamente")
            
            # Verificar secciones críticas
            required_sections = ['mqtt', 'storage', 'api']
            for section in required_sections:
                if hasattr(config, section):
                    self.success.append(f"✅ Sección '{section}': Presente")
                else:
                    self.errors.append(f"❌ Sección '{section}': Faltante")
            
            # Verificar RabbitMQ (opcional)
            if hasattr(config, 'rabbitmq'):
                self.success.append("✅ Sección 'rabbitmq': Presente")
            else:
                self.warnings.append("⚠️  Sección 'rabbitmq': No presente (monitoreo no disponible)")
                
        except Exception as e:
            self.errors.append(f"❌ Error cargando config.yaml: {e}")
    
    def check_directory_structure(self):
        """Verifica la estructura de directorios"""
        print("\n📁 Verificando estructura de directorios...")
        
        base_path = Path(__file__).parent.parent
        
        directories_to_check = [
            ("src/iot_middleware", "Código fuente principal"),
            ("src/iot_middleware/config", "Configuración"),
            ("src/iot_middleware/mqtt", "Cliente MQTT"),
            ("src/iot_middleware/storage", "Almacenamiento"),
            ("src/iot_middleware/api", "API REST"),
            ("src/iot_middleware/services", "Servicios"),
            ("tests", "Tests"),
            ("infra/containers", "Infraestructura local"),
            ("apps/admin-fastapi", "Admin FastAPI transicional"),
            ("apps/monitoring-dashboard", "Dashboard experimental"),
            ("containers", "Compatibilidad containers"),
        ]
        
        for dir_path, description in directories_to_check:
            self.check_directory_exists(str(base_path / dir_path), description)
    
    def check_required_files(self):
        """Verifica archivos requeridos"""
        print("\n📄 Verificando archivos requeridos...")
        
        base_path = Path(__file__).parent.parent
        
        files_to_check = [
            ("main.py", "Entrypoint transicional/manual"),
            ("requirements.txt", "Dependencias"),
            ("config.yaml", "Configuración"),
            ("src/iot_middleware/__init__.py", "Paquete principal"),
        ]
        
        for file_path, description in files_to_check:
            self.check_file_exists(str(base_path / file_path), description)
    
    def check_dependencies_file(self):
        """Verifica que requirements.txt exista y tenga dependencias críticas"""
        print("\n📋 Verificando archivo de dependencias...")
        
        req_file = Path(__file__).parent.parent / "requirements.txt"
        if not req_file.exists():
            self.errors.append("❌ requirements.txt no encontrado")
            return
        
        required_deps = [
            "fastapi",
            "paho-mqtt",
            "sqlalchemy",
            "psycopg2-binary",
            "pydantic",
            "PyYAML",
        ]
        
        content = req_file.read_text()
        for dep in required_deps:
            if dep in content:
                self.success.append(f"✅ Dependencia '{dep}': Presente")
            else:
                self.warnings.append(f"⚠️  Dependencia '{dep}': No encontrada en requirements.txt")
    
    def verify_all(self):
        """Ejecuta todas las verificaciones"""
        print("🔍 Verificación del Sistema IoT Middleware")
        print("=" * 60)
        
        self.check_directory_structure()
        self.check_required_files()
        self.check_dependencies_file()
        self.check_config_file()
        self.check_imports()
        self.check_rabbitmq_imports()
        
        # Resumen
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE VERIFICACIÓN")
        print("=" * 60)
        
        if self.success:
            print(f"\n✅ Exitosos ({len(self.success)}):")
            for msg in self.success:
                print(f"   {msg}")
        
        if self.warnings:
            print(f"\n⚠️  Advertencias ({len(self.warnings)}):")
            for msg in self.warnings:
                print(f"   {msg}")
        
        if self.errors:
            print(f"\n❌ Errores ({len(self.errors)}):")
            for msg in self.errors:
                print(f"   {msg}")
        
        print("\n" + "=" * 60)
        
        if self.errors:
            print(f"❌ Sistema NO funcional - {len(self.errors)} error(es) encontrado(s)")
            return False
        elif self.warnings:
            print(f"⚠️  Sistema funcional con advertencias - {len(self.warnings)} advertencia(s)")
            return True
        else:
            print(f"✅ Sistema funcional - Todas las verificaciones pasaron")
            return True


def main():
    """Función principal"""
    verifier = SystemVerifier()
    success = verifier.verify_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
