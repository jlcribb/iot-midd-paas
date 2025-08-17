#!/usr/bin/env python3
"""
Script de Prueba para el Módulo de Configuración
IoT Middleware
"""

import sys
import os
import logging
from pathlib import Path

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.config import (
        ConfigLoader, 
        load_config, 
        validate_config_file,
        IoTMiddlewareConfig
    )
    print("✅ Módulo de configuración importado exitosamente")
except ImportError as e:
    print(f"❌ Error al importar el módulo: {e}")
    sys.exit(1)

def test_config_loader():
    """Probar el cargador de configuración"""
    print("\n🧪 Probando ConfigLoader...")
    
    # Crear instancia del cargador
    loader = ConfigLoader()
    print("✅ ConfigLoader creado")
    
    # Buscar archivo de configuración
    try:
        config_path = loader.find_config_file()
        print(f"✅ Archivo de configuración encontrado: {config_path}")
    except FileNotFoundError as e:
        print(f"❌ No se encontró archivo de configuración: {e}")
        return False
    
    # Cargar configuración
    try:
        config = loader.load_config()
        print("✅ Configuración cargada y validada")
        return True
    except Exception as e:
        print(f"❌ Error al cargar configuración: {e}")
        return False

def test_direct_load():
    """Probar carga directa de configuración"""
    print("\n🧪 Probando carga directa...")
    
    try:
        config = load_config()
        print("✅ Configuración cargada directamente")
        return True
    except Exception as e:
        print(f"❌ Error en carga directa: {e}")
        return False

def test_config_validation():
    """Probar validación de configuración"""
    print("\n🧪 Probando validación...")
    
    try:
        # Buscar archivo de configuración
        config_paths = [
            "examples/config_test.yaml",
            "examples/config_simple.yaml",
            "examples/config_with_postgresql.yaml",
            "../examples/config_test.yaml",
            "../examples/config_simple.yaml",
            "../examples/config_with_postgresql.yaml"
        ]
        
        config_path = None
        for path in config_paths:
            if os.path.exists(path):
                config_path = path
                break
        
        if not config_path:
            print("❌ No se encontró archivo de configuración para validar")
            return False
        
        # Validar archivo
        is_valid = validate_config_file(config_path)
        if is_valid:
            print(f"✅ Archivo de configuración válido: {config_path}")
            return True
        else:
            print(f"❌ Archivo de configuración inválido: {config_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error en validación: {e}")
        return False

def test_config_access():
    """Probar acceso a la configuración"""
    print("\n🧪 Probando acceso a configuración...")
    
    try:
        config = load_config()
        
        # Acceder a configuraciones específicas
        print(f"📡 MQTT Broker: {config.mqtt.broker['host']}:{config.mqtt.broker['port']}")
        print(f"🗄️  InfluxDB: {config.influxdb.url}")
        print(f"🐘 PostgreSQL: {config.postgresql.host}:{config.postgresql.port}")
        print(f"🌐 API: {config.api.host}:{config.api.port}")
        print(f"📝 Logging Level: {config.logging.level}")
        
        # Verificar tópicos MQTT
        print(f"📨 Tópicos de suscripción: {config.mqtt.topics['subscribe']}")
        print(f"📤 Tópicos de publicación: {config.mqtt.topics['publish']}")
        
        # Verificar configuración de almacenamiento
        print(f"💾 Almacenamiento de series temporales: {config.storage.timeseries['provider']}")
        print(f"🗃️  Almacenamiento relacional: {config.storage.relational['provider']}")
        
        print("✅ Acceso a configuración exitoso")
        return True
        
    except Exception as e:
        print(f"❌ Error al acceder a configuración: {e}")
        return False

def test_config_loader_methods():
    """Probar métodos del ConfigLoader"""
    print("\n🧪 Probando métodos del ConfigLoader...")
    
    try:
        loader = ConfigLoader()
        config = loader.load_config()
        
        # Probar métodos getters
        mqtt_config = loader.get_mqtt_config()
        influxdb_config = loader.get_influxdb_config()
        postgresql_config = loader.get_postgresql_config()
        api_config = loader.get_api_config()
        
        print(f"✅ MQTT Config obtenida: {mqtt_config.broker['host']}")
        print(f"✅ InfluxDB Config obtenida: {influxdb_config.url}")
        print(f"✅ PostgreSQL Config obtenida: {postgresql_config.host}")
        print(f"✅ API Config obtenida: {api_config.host}")
        
        # Probar validación
        is_valid = loader.validate_config()
        if is_valid:
            print("✅ Validación de configuración exitosa")
        else:
            print("❌ Validación de configuración falló")
            return False
        
        print("✅ Métodos del ConfigLoader funcionando correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en métodos del ConfigLoader: {e}")
        return False

def test_error_handling():
    """Probar manejo de errores"""
    print("\n🧪 Probando manejo de errores...")
    
    # Probar con archivo inexistente
    try:
        loader = ConfigLoader("archivo_inexistente.yaml")
        loader.load_config()
        print("❌ Debería haber fallado con archivo inexistente")
        return False
    except FileNotFoundError:
        print("✅ Error de archivo no encontrado manejado correctamente")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
    
    # Probar acceso sin cargar configuración
    try:
        loader = ConfigLoader()
        loader.get_config()
        print("❌ Debería haber fallado sin configuración cargada")
        return False
    except RuntimeError:
        print("✅ Error de configuración no cargada manejado correctamente")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
    
    print("✅ Manejo de errores funcionando correctamente")
    return True

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando Pruebas del Módulo de Configuración")
    print("=" * 60)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        ("ConfigLoader", test_config_loader),
        ("Carga Directa", test_direct_load),
        ("Validación", test_config_validation),
        ("Acceso a Configuración", test_config_access),
        ("Métodos del ConfigLoader", test_config_loader_methods),
        ("Manejo de Errores", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Error inesperado en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
