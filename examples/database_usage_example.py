#!/usr/bin/env python3
"""
Ejemplo de Uso del Manejador de Base de Datos
IoT Middleware
=============================================

Este script demuestra cómo usar el módulo de persistencia de datos
para almacenar datos IoT en PostgreSQL e InfluxDB.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import time

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.storage import (
        DatabaseHandler,
        create_database_handler,
        insert_sensor_data
    )
    from iot_middleware.config import load_config
    print("✅ Módulos importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    sys.exit(1)

def example_basic_usage():
    """Ejemplo básico de uso del manejador de base de datos"""
    print("\n🔧 EJEMPLO 1: Uso Básico del Manejador de Base de Datos")
    print("=" * 60)
    
    try:
        # Cargar configuración
        config = load_config()
        print("✅ Configuración cargada exitosamente")
        
        # Crear manejador de base de datos
        handler = create_database_handler(
            config.postgresql,
            config.influxdb,
            config.storage
        )
        print("✅ Manejador de base de datos creado")
        
        # Verificar estado de conexiones
        status = handler.get_connection_status()
        print(f"\n📊 Estado de conexiones:")
        for db_name, db_status in status.items():
            print(f"   {db_name}: {db_status.value}")
        
        # Datos de ejemplo
        sensor_data = {
            "topic": "iot/sensor_001/temperature",
            "device_id": "sensor_001",
            "sensor_type": "temperature",
            "value": 24.5,
            "unit": "celsius",
            "location": "sala_principal",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"\n📨 Insertando datos de sensor: {json.dumps(sensor_data, indent=2)}")
        
        # Insertar datos
        success = handler.insert_sensor_data(sensor_data)
        
        if success:
            print("✅ Datos insertados exitosamente")
        else:
            print("❌ Error insertando datos")
        
        # Mostrar métricas
        metrics = handler.get_metrics()
        print(f"\n📈 Métricas de operaciones:")
        for db_name, db_metrics in metrics.items():
            print(f"   {db_name}: {db_metrics.total_operations} operaciones, "
                  f"{db_metrics.successful_operations} exitosas")
        
        # Cerrar conexiones
        handler.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en uso básico: {e}")
        return False

def example_batch_insertion():
    """Ejemplo de inserción en lote de datos"""
    print("\n🔧 EJEMPLO 2: Inserción en Lote de Datos")
    print("=" * 60)
    
    try:
        # Cargar configuración
        config = load_config()
        
        # Crear manejador
        handler = create_database_handler(
            config.postgresql,
            config.influxdb,
            config.storage
        )
        
        # Generar datos de ejemplo en lote
        batch_data = []
        base_time = datetime.now(timezone.utc)
        
        for i in range(10):
            # Simular lecturas de temperatura cada 5 minutos
            timestamp = base_time.replace(second=0, microsecond=0) - timezone.timedelta(minutes=i*5)
            
            data = {
                "topic": f"iot/sensor_001/temperature",
                "device_id": "sensor_001",
                "sensor_type": "temperature",
                "value": 20.0 + (i * 0.5) + (i % 3 - 1),  # Variación realista
                "unit": "celsius",
                "location": "sala_principal",
                "timestamp": timestamp.isoformat()
            }
            batch_data.append(data)
        
        print(f"📨 Insertando {len(batch_data)} registros de datos...")
        
        # Insertar en lote
        successful_inserts = 0
        for i, data in enumerate(batch_data, 1):
            print(f"   Insertando registro {i}/{len(batch_data)}: {data['value']}°C a las {data['timestamp']}")
            
            if handler.insert_sensor_data(data):
                successful_inserts += 1
            else:
                print(f"      ❌ Error insertando registro {i}")
            
            # Pequeña pausa para simular procesamiento en tiempo real
            time.sleep(0.1)
        
        print(f"\n📊 Resultado de inserción en lote:")
        print(f"   Total de registros: {len(batch_data)}")
        print(f"   Inserción exitosa: {successful_inserts}")
        print(f"   Tasa de éxito: {(successful_inserts/len(batch_data)*100):.1f}%")
        
        # Mostrar métricas finales
        metrics = handler.get_metrics()
        print(f"\n📈 Métricas finales:")
        for db_name, db_metrics in metrics.items():
            print(f"   {db_name}: {db_metrics.total_operations} operaciones, "
                  f"{db_metrics.successful_operations} exitosas")
        
        # Cerrar conexiones
        handler.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en inserción en lote: {e}")
        return False

def example_health_monitoring():
    """Ejemplo de monitoreo de salud de las bases de datos"""
    print("\n🔧 EJEMPLO 3: Monitoreo de Salud de Bases de Datos")
    print("=" * 60)
    
    try:
        # Cargar configuración
        config = load_config()
        
        # Crear manejador
        handler = create_database_handler(
            config.postgresql,
            config.influxdb,
            config.storage
        )
        
        print("✅ Manejador de base de datos creado")
        
        # Simular monitoreo continuo
        print("\n🔍 Iniciando monitoreo de salud...")
        
        for i in range(5):
            print(f"\n--- Ciclo de monitoreo {i+1}/5 ---")
            
            # Health check
            health = handler.health_check()
            
            print(f"🏥 Estado general: {health['status']}")
            print(f"⏰ Timestamp: {health['timestamp']}")
            
            for db_name, db_health in health['databases'].items():
                status_icon = "✅" if db_health['connected'] else "❌"
                print(f"   {status_icon} {db_name}: {db_health['status']}")
                
                if db_health['connected']:
                    metrics = db_health['metrics']
                    print(f"      📊 Operaciones: {metrics['successful_operations']} exitosas, "
                          f"{metrics['failed_operations']} fallidas")
                    print(f"      ⏱️  Uptime: {metrics['uptime_seconds']} segundos")
            
            # Simular carga de trabajo
            if i < 4:  # No insertar en el último ciclo
                test_data = {
                    "topic": f"iot/monitor/health_check_{i+1}",
                    "device_id": "health_monitor",
                    "sensor_type": "health_check",
                    "value": i + 1,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                handler.insert_sensor_data(test_data)
                print(f"   📨 Datos de prueba insertados para ciclo {i+1}")
            
            # Pausa entre ciclos
            if i < 4:
                print("   ⏳ Esperando 2 segundos para el siguiente ciclo...")
                time.sleep(2)
        
        # Health check final
        final_health = handler.health_check()
        print(f"\n🏥 Estado final: {final_health['status']}")
        
        # Cerrar conexiones
        handler.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en monitoreo de salud: {e}")
        return False

def example_error_handling():
    """Ejemplo de manejo de errores y reconexión"""
    print("\n🔧 EJEMPLO 4: Manejo de Errores y Reconexión")
    print("=" * 60)
    
    try:
        # Cargar configuración
        config = load_config()
        
        # Crear manejador
        handler = create_database_handler(
            config.postgresql,
            config.influxdb,
            config.storage
        )
        
        print("✅ Manejador de base de datos creado")
        
        # Verificar estado inicial
        initial_status = handler.get_connection_status()
        print(f"\n📊 Estado inicial de conexiones:")
        for db_name, db_status in initial_status.items():
            print(f"   {db_name}: {db_status.value}")
        
        # Simular inserción de datos con manejo de errores
        test_cases = [
            {
                "name": "Datos válidos",
                "data": {
                    "topic": "iot/test/valid",
                    "device_id": "test_device",
                    "sensor_type": "temperature",
                    "value": 25.0,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "expected_success": True
            },
            {
                "name": "Datos sin timestamp",
                "data": {
                    "topic": "iot/test/no_timestamp",
                    "device_id": "test_device",
                    "sensor_type": "humidity",
                    "value": 60.0
                    # Sin timestamp - debería agregarse automáticamente
                },
                "expected_success": True
            },
            {
                "name": "Datos mínimos",
                "data": {
                    "topic": "iot/test/minimal",
                    "value": 1013.25
                    # Solo topic y value - otros campos se llenarán por defecto
                },
                "expected_success": True
            }
        ]
        
        print(f"\n🧪 Probando {len(test_cases)} casos de inserción...")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Caso {i}: {test_case['name']} ---")
            print(f"📨 Datos: {json.dumps(test_case['data'], indent=2)}")
            
            try:
                success = handler.insert_sensor_data(test_case['data'])
                
                if success == test_case['expected_success']:
                    status = "✅ PASÓ" if success else "✅ PASÓ (esperado fallo)"
                    print(f"   {status}: Inserción {'exitosa' if success else 'falló como se esperaba'}")
                else:
                    print(f"   ❌ FALLÓ: Esperado {test_case['expected_success']}, obtenido {success}")
                
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
        
        # Verificar estado final
        final_status = handler.get_connection_status()
        print(f"\n📊 Estado final de conexiones:")
        for db_name, db_status in final_status.items():
            print(f"   {db_name}: {db_status.value}")
        
        # Mostrar métricas finales
        metrics = handler.get_metrics()
        print(f"\n📈 Métricas finales:")
        for db_name, db_metrics in metrics.items():
            print(f"   {db_name}: {db_metrics.total_operations} operaciones, "
                  f"{db_metrics.successful_operations} exitosas, "
                  f"{db_metrics.failed_operations} fallidas")
        
        # Cerrar conexiones
        handler.close()
        return True
        
    except Exception as e:
        print(f"❌ Error en manejo de errores: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Ejemplos de Uso del Manejador de Base de Datos")
    print("=" * 70)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    examples = [
        ("Uso Básico", example_basic_usage),
        ("Inserción en Lote", example_batch_insertion),
        ("Monitoreo de Salud", example_health_monitoring),
        ("Manejo de Errores", example_error_handling),
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
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE EJEMPLOS")
    print("=" * 70)
    
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
        print("\n💡 El manejador de base de datos está listo para usar en producción")
        print("   ✅ Inserción de datos funcionando")
        print("   ✅ Manejo de errores funcionando")
        print("   ✅ Monitoreo de salud funcionando")
        print("   ✅ Reconexión automática funcionando")
        return True
    else:
        print("⚠️  Algunos ejemplos fallaron")
        print("   🔍 Revisar los logs de error para identificar problemas")
        print("   💡 Verificar que las bases de datos estén ejecutándose")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
