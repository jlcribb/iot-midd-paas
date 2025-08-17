#!/usr/bin/env python3
"""
Ejemplo de Uso del Módulo de Configuración
IoT Middleware
==========================================

Este script demuestra cómo usar el módulo de configuración
en diferentes escenarios prácticos.
"""

import sys
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

def example_basic_usage():
    """Ejemplo básico de uso"""
    print("\n🔧 EJEMPLO 1: Uso Básico")
    print("=" * 40)
    
    try:
        # Cargar configuración automáticamente
        config = load_config()
        print("✅ Configuración cargada automáticamente")
        
        # Acceder a configuraciones específicas
        print(f"📡 MQTT Broker: {config.mqtt.broker['host']}:{config.mqtt.broker['port']}")
        print(f"🗄️  InfluxDB: {config.influxdb.url}")
        print(f"🐘 PostgreSQL: {config.postgresql.host}:{config.postgresql.port}")
        print(f"🌐 API: {config.api.host}:{config.api.port}")
        
        return True
    except Exception as e:
        print(f"❌ Error en uso básico: {e}")
        return False

def example_config_loader():
    """Ejemplo usando ConfigLoader"""
    print("\n🔧 EJEMPLO 2: ConfigLoader Avanzado")
    print("=" * 40)
    
    try:
        # Crear instancia del cargador
        loader = ConfigLoader()
        print("✅ ConfigLoader creado")
        
        # Buscar archivo de configuración
        config_path = loader.find_config_file()
        print(f"📁 Archivo encontrado: {config_path}")
        
        # Cargar configuración
        config = loader.load_config()
        print("✅ Configuración cargada")
        
        # Usar métodos getters
        mqtt_config = loader.get_mqtt_config()
        influxdb_config = loader.get_influxdb_config()
        postgresql_config = loader.get_postgresql_config()
        
        print(f"📡 Configuración MQTT: {mqtt_config.broker['host']}")
        print(f"🗄️  Configuración InfluxDB: {influxdb_config.url}")
        print(f"🐘 Configuración PostgreSQL: {postgresql_config.host}")
        
        return True
    except Exception as e:
        print(f"❌ Error en ConfigLoader: {e}")
        return False

def example_validation():
    """Ejemplo de validación de archivos"""
    print("\n🔧 EJEMPLO 3: Validación de Archivos")
    print("=" * 40)
    
    try:
        # Lista de archivos a validar
        config_files = [
            "examples/config_test.yaml",
            "examples/config_simple.yaml",
            "examples/config_with_postgresql.yaml"
        ]
        
        for config_file in config_files:
            if Path(config_file).exists():
                is_valid = validate_config_file(config_file)
                status = "✅ VÁLIDO" if is_valid else "❌ INVÁLIDO"
                print(f"{status}: {config_file}")
            else:
                print(f"⚠️  NO ENCONTRADO: {config_file}")
        
        return True
    except Exception as e:
        print(f"❌ Error en validación: {e}")
        return False

def example_error_handling():
    """Ejemplo de manejo de errores"""
    print("\n🔧 EJEMPLO 4: Manejo de Errores")
    print("=" * 40)
    
    try:
        # Probar con archivo inexistente
        try:
            config = load_config("archivo_inexistente.yaml")
            print("❌ Debería haber fallado")
            return False
        except FileNotFoundError:
            print("✅ Error de archivo no encontrado manejado correctamente")
        
        # Probar con archivo inválido (crear uno temporal)
        invalid_config = """
mqtt:
  broker:
    host: "localhost"
    # Falta el puerto - esto debería fallar
"""
        
        with open("temp_invalid.yaml", "w") as f:
            f.write(invalid_config)
        
        try:
            config = load_config("temp_invalid.yaml")
            print("❌ Debería haber fallado con configuración inválida")
            return False
        except Exception as e:
            print("✅ Error de validación manejado correctamente")
        
        # Limpiar archivo temporal
        Path("temp_invalid.yaml").unlink()
        
        return True
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def example_config_reload():
    """Ejemplo de recarga de configuración"""
    print("\n🔧 EJEMPLO 5: Recarga de Configuración")
    print("=" * 40)
    
    try:
        # Crear cargador con archivo específico
        loader = ConfigLoader("examples/config_test.yaml")
        config = loader.load_config()
        print("✅ Configuración inicial cargada")
        
        # Simular recarga
        config_reloaded = loader.reload_config()
        print("✅ Configuración recargada")
        
        # Verificar que es la misma
        if config.mqtt.broker['host'] == config_reloaded.mqtt.broker['host']:
            print("✅ Configuración recargada correctamente")
        else:
            print("❌ Error en la recarga")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error en recarga: {e}")
        return False

def example_custom_validation():
    """Ejemplo de validación personalizada"""
    print("\n🔧 EJEMPLO 6: Validación Personalizada")
    print("=" * 40)
    
    try:
        config = load_config()
        
        # Validaciones personalizadas
        print("🔍 Ejecutando validaciones personalizadas...")
        
        # Validar que el puerto MQTT esté en rango seguro
        mqtt_port = config.mqtt.broker['port']
        if 1024 <= mqtt_port <= 65535:
            print(f"✅ Puerto MQTT {mqtt_port} está en rango seguro")
        else:
            print(f"⚠️  Puerto MQTT {mqtt_port} está fuera del rango recomendado")
        
        # Validar que InfluxDB use HTTPS en producción
        influxdb_url = config.influxdb.url
        if influxdb_url.startswith("https://"):
            print("✅ InfluxDB usa HTTPS (seguro para producción)")
        else:
            print("⚠️  InfluxDB usa HTTP (solo para desarrollo)")
        
        # Validar configuración de logging
        log_level = config.logging.level
        if log_level in ["INFO", "WARNING", "ERROR"]:
            print(f"✅ Nivel de logging {log_level} es apropiado para producción")
        else:
            print(f"⚠️  Nivel de logging {log_level} puede ser muy verboso para producción")
        
        return True
    except Exception as e:
        print(f"❌ Error en validación personalizada: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Ejemplos de Uso del Módulo de Configuración")
    print("=" * 60)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    examples = [
        ("Uso Básico", example_basic_usage),
        ("ConfigLoader Avanzado", example_config_loader),
        ("Validación de Archivos", example_validation),
        ("Manejo de Errores", example_error_handling),
        ("Recarga de Configuración", example_config_reload),
        ("Validación Personalizada", example_custom_validation)
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
        print("\n💡 El módulo de configuración está listo para usar en producción")
        return True
    else:
        print("⚠️  Algunos ejemplos fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
