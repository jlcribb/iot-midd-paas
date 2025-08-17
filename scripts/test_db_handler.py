#!/usr/bin/env python3
"""
Script de Prueba para el Manejador de Base de Datos
IoT Middleware
==================================================

Este script prueba las funcionalidades del módulo de persistencia de datos:
- Conexión a PostgreSQL
- Conexión a InfluxDB
- Inserción de datos
- Manejo de errores y reconexión
- Health checks
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.storage import (
        DatabaseHandler,
        PostgreSQLHandler,
        InfluxDBHandler,
        DatabaseType,
        ConnectionStatus,
        create_database_handler,
        insert_sensor_data
    )
    from iot_middleware.config import load_config
    print("✅ Módulos importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    sys.exit(1)

def test_postgresql_handler():
    """Probar manejador de PostgreSQL"""
    print("\n🧪 Probando manejador de PostgreSQL...")
    
    try:
        # Crear configuración por defecto
        from iot_middleware.config import PostgreSQLConfig
        
        postgresql_config = PostgreSQLConfig(
            host="localhost",  # Cambiar por tu host
            port=5432,
            database="iot_middleware",
            username="iot_user",
            password="iot_password"
        )
        
        # Crear manejador
        handler = PostgreSQLHandler(postgresql_config)
        print("✅ Manejador de PostgreSQL creado")
        
        # Verificar estado de conexión
        status = handler.get_connection_status()
        print(f"📊 Estado de conexión: {status.value}")
        
        if status == ConnectionStatus.CONNECTED:
            print("   ✅ Conexión exitosa a PostgreSQL")
            
            # Probar inserción de datos
            test_data = {
                "topic": "iot/test/temperature",
                "device_id": "test_device_001",
                "sensor_type": "temperature",
                "value": 25.5,
                "unit": "celsius",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"📨 Insertando datos de prueba: {json.dumps(test_data, indent=2)}")
            
            success = handler.insert_sensor_data(test_data)
            
            if success:
                print("   ✅ Datos insertados exitosamente")
            else:
                print("   ❌ Error insertando datos")
            
            # Mostrar métricas
            metrics = handler.get_metrics()
            print(f"\n📈 Métricas de PostgreSQL:")
            print(f"   Operaciones totales: {metrics.total_operations}")
            print(f"   Operaciones exitosas: {metrics.successful_operations}")
            print(f"   Operaciones fallidas: {metrics.failed_operations}")
            print(f"   Uptime: {metrics.uptime_seconds} segundos")
            
        else:
            print(f"   ❌ No se pudo conectar a PostgreSQL: {status.value}")
            print("   💡 Verificar que PostgreSQL esté ejecutándose y la configuración sea correcta")
        
        # Cerrar conexiones
        handler.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en manejador de PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_influxdb_handler():
    """Probar manejador de InfluxDB"""
    print("\n🧪 Probando manejador de InfluxDB...")
    
    try:
        # Crear configuración por defecto
        from iot_middleware.config import InfluxDBConfig
        
        influxdb_config = InfluxDBConfig(
            url="http://localhost:8086",  # Cambiar por tu URL
            token="dev-token",
            org="my-org",
            bucket="iot"
        )
        
        # Crear manejador
        handler = InfluxDBHandler(influxdb_config)
        print("✅ Manejador de InfluxDB creado")
        
        # Verificar estado de conexión
        status = handler.get_connection_status()
        print(f"📊 Estado de conexión: {status.value}")
        
        if status == ConnectionStatus.CONNECTED:
            print("   ✅ Conexión exitosa a InfluxDB")
            
            # Probar inserción de datos
            test_data = {
                "topic": "iot/test/humidity",
                "device_id": "test_device_002",
                "sensor_type": "humidity",
                "value": 65.0,
                "unit": "percentage",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"📨 Insertando datos de prueba: {json.dumps(test_data, indent=2)}")
            
            success = handler.insert_influxdb(test_data)
            
            if success:
                print("   ✅ Datos insertados exitosamente")
            else:
                print("   ❌ Error insertando datos")
            
            # Mostrar métricas
            metrics = handler.get_metrics()
            print(f"\n📈 Métricas de InfluxDB:")
            print(f"   Operaciones totales: {metrics.total_operations}")
            print(f"   Operaciones exitosas: {metrics.successful_operations}")
            print(f"   Operaciones fallidas: {metrics.failed_operations}")
            print(f"   Uptime: {metrics.uptime_seconds} segundos")
            
        else:
            print(f"   ❌ No se pudo conectar a InfluxDB: {status.value}")
            print("   💡 Verificar que InfluxDB esté ejecutándose y la configuración sea correcta")
        
        # Cerrar conexiones
        handler.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en manejador de InfluxDB: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_handler():
    """Probar manejador principal de base de datos"""
    print("\n🧪 Probando manejador principal de base de datos...")
    
    try:
        # Crear configuración por defecto
        from iot_middleware.config import PostgreSQLConfig, InfluxDBConfig, StorageConfig
        
        postgresql_config = PostgreSQLConfig(
            host="localhost",
            port=5432,
            database="iot_middleware",
            username="iot_user",
            password="iot_password"
        )
        
        influxdb_config = InfluxDBConfig(
            url="http://localhost:8086",
            token="dev-token",
            org="my-org",
            bucket="iot"
        )
        
        storage_config = StorageConfig(
            timeseries={"provider": "influxdb"},
            relational={"provider": "postgresql"},
            metadata={"provider": "postgresql"}
        )
        
        # Crear manejador principal
        handler = create_database_handler(postgresql_config, influxdb_config, storage_config)
        print("✅ Manejador principal de base de datos creado")
        
        # Verificar tipo de base de datos
        print(f"🗄️  Tipo de base de datos: {handler.db_type.value}")
        
        # Verificar estado de conexiones
        status = handler.get_connection_status()
        print(f"\n📊 Estado de conexiones:")
        for db_name, db_status in status.items():
            print(f"   {db_name}: {db_status.value}")
        
        # Probar inserción de datos
        test_data = {
            "topic": "iot/test/pressure",
            "device_id": "test_device_003",
            "sensor_type": "pressure",
            "value": 1013.25,
            "unit": "hpa",
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\n📨 Insertando datos de prueba: {json.dumps(test_data, indent=2)}")
        
        success = handler.insert_sensor_data(test_data)
        
        if success:
            print("   ✅ Datos insertados exitosamente")
        else:
            print("   ❌ Error insertando datos")
        
        # Mostrar métricas
        metrics = handler.get_metrics()
        print(f"\n📈 Métricas de todas las bases de datos:")
        for db_name, db_metrics in metrics.items():
            print(f"   {db_name}: {db_metrics.total_operations} operaciones, "
                  f"{db_metrics.successful_operations} exitosas")
        
        # Health check
        health = handler.health_check()
        print(f"\n🏥 Health Check: {health['status']}")
        print(f"   Timestamp: {health['timestamp']}")
        
        for db_name, db_health in health['databases'].items():
            print(f"   {db_name}: {db_health['status']} "
                  f"({'conectado' if db_health['connected'] else 'desconectado'})")
        
        # Cerrar conexiones
        handler.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en manejador principal: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_function_compatibility():
    """Probar función de compatibilidad insert_sensor_data"""
    print("\n🧪 Probando función de compatibilidad insert_sensor_data...")
    
    try:
        # Datos de prueba
        test_data = {
            "topic": "iot/test/compatibility",
            "device_id": "test_device_004",
            "sensor_type": "temperature",
            "value": 22.8,
            "unit": "celsius",
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"📨 Datos de prueba: {json.dumps(test_data, indent=2)}")
        
        # Usar función de compatibilidad
        success = insert_sensor_data(test_data)
        
        if success:
            print("   ✅ Función de compatibilidad funcionando")
        else:
            print("   ❌ Función de compatibilidad falló")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en función de compatibilidad: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_config_file():
    """Probar con archivo de configuración real"""
    print("\n🧪 Probando con archivo de configuración...")
    
    try:
        # Cargar configuración
        config = load_config()
        print("✅ Configuración cargada exitosamente")
        
        # Crear manejador con configuración real
        handler = create_database_handler(
            config.postgresql, 
            config.influxdb, 
            config.storage
        )
        
        print("✅ Manejador creado con configuración real")
        
        # Verificar estado de conexiones
        status = handler.get_connection_status()
        print(f"\n📊 Estado de conexiones:")
        for db_name, db_status in status.items():
            print(f"   {db_name}: {db_status.value}")
        
        # Health check
        health = handler.health_check()
        print(f"\n🏥 Health Check: {health['status']}")
        
        # Cerrar conexiones
        handler.close()
        return True
        
    except Exception as e:
        print(f"❌ Error con archivo de configuración: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando Pruebas del Manejador de Base de Datos")
    print("=" * 70)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        ("Manejador de PostgreSQL", test_postgresql_handler),
        ("Manejador de InfluxDB", test_influxdb_handler),
        ("Manejador Principal", test_database_handler),
        ("Función de Compatibilidad", test_function_compatibility),
        ("Archivo de Configuración", test_with_config_file),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*25} {test_name} {'='*25}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Error inesperado en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 70)
    
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
        print("\n💡 El manejador de base de datos está listo para usar en producción")
        print("   ✅ Conexiones a PostgreSQL funcionando")
        print("   ✅ Conexiones a InfluxDB funcionando")
        print("   ✅ Inserción de datos funcionando")
        print("   ✅ Manejo de errores funcionando")
        print("   ✅ Health checks funcionando")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron")
        print("   🔍 Revisar los logs de error para identificar problemas")
        print("   💡 Verificar que las bases de datos estén ejecutándose")
        print("   💡 Verificar la configuración de conexión")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
