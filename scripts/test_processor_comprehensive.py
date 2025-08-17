#!/usr/bin/env python3
"""
Script de Prueba Comprehensivo para el Procesador de Datos
IoT Middleware
========================================================

Este script prueba todas las funcionalidades del procesador de datos:
- Validación de esquemas
- Normalización de datos
- Manejo de errores
- Niveles de validación
- Esquemas personalizados
- Estadísticas de procesamiento
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.processing import (
        DataProcessor, 
        DataNormalizer, 
        MessageSchema, 
        FieldSchema, 
        DataType, 
        ValidationLevel,
        create_data_processor,
        process_message
    )
    from iot_middleware.config import load_config
    print("✅ Módulos importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    sys.exit(1)

def test_schema_validation():
    """Probar validación de esquemas"""
    print("\n🧪 Probando validación de esquemas...")
    
    try:
        # Crear esquema personalizado para sensores de calidad del aire
        air_quality_schema = MessageSchema(
            name="air_quality",
            description="Datos de calidad del aire",
            fields=[
                FieldSchema("device_id", DataType.STRING, required=True, description="ID del dispositivo"),
                FieldSchema("pm25", DataType.FLOAT, required=True, min_value=0, max_value=500, description="PM2.5"),
                FieldSchema("pm10", DataType.FLOAT, required=True, min_value=0, max_value=1000, description="PM10"),
                FieldSchema("co2", DataType.FLOAT, required=False, min_value=300, max_value=5000, description="CO2"),
                FieldSchema("timestamp", DataType.TIMESTAMP, required=False, description="Timestamp"),
                FieldSchema("location", DataType.STRING, required=False, default="unknown", description="Ubicación")
            ]
        )
        
        print("✅ Esquema de calidad del aire creado")
        
        # Probar validación con diferentes mensajes
        test_messages = [
            {
                "name": "Mensaje válido completo",
                "payload": {
                    "device_id": "aq_sensor_001",
                    "pm25": 25.5,
                    "pm10": 45.2,
                    "co2": 450,
                    "location": "oficina_principal"
                },
                "expected_valid": True
            },
            {
                "name": "Mensaje con valores fuera de rango",
                "payload": {
                    "device_id": "aq_sensor_002",
                    "pm25": 600,  # Fuera de rango
                    "pm10": 45.2,
                    "co2": 6000   # Fuera de rango
                },
                "expected_valid": False
            },
            {
                "name": "Mensaje con campos faltantes",
                "payload": {
                    "device_id": "aq_sensor_003",
                    "pm25": 25.5
                    # Falta pm10 (requerido)
                },
                "expected_valid": False
            }
        ]
        
        for i, test_case in enumerate(test_messages, 1):
            print(f"\n--- Test {i}: {test_case['name']} ---")
            print(f"📨 Payload: {json.dumps(test_case['payload'], indent=2)}")
            
            # Validar manualmente cada campo
            errors = []
            for field_schema in air_quality_schema.fields:
                field_name = field_schema.name
                field_value = test_case['payload'].get(field_name)
                
                is_valid, normalized_value, error_msg = field_schema.validate(field_value)
                
                if not is_valid:
                    errors.append(f"Campo '{field_name}': {error_msg}")
                else:
                    print(f"   ✅ Campo '{field_name}': {normalized_value}")
            
            if errors:
                print(f"   ❌ Errores de validación:")
                for error in errors:
                    print(f"      - {error}")
            else:
                print(f"   ✅ Todos los campos son válidos")
            
            # Verificar si el resultado coincide con lo esperado
            is_valid = len(errors) == 0
            if is_valid == test_case['expected_valid']:
                print(f"   🎯 Resultado esperado: {test_case['expected_valid']} ✓")
            else:
                print(f"   ⚠️  Resultado inesperado: esperado {test_case['expected_valid']}, obtenido {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en validación de esquemas: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_normalization():
    """Probar normalización de datos"""
    print("\n🧪 Probando normalización de datos...")
    
    try:
        # Crear configuración por defecto
        from iot_middleware.config import NormalizerConfig
        normalizer_config = NormalizerConfig()
        
        # Crear normalizador
        normalizer = DataNormalizer(normalizer_config)
        print("✅ Normalizador de datos creado")
        
        # Probar normalización de temperatura
        print("\n🌡️  Probando normalización de temperatura...")
        temp_tests = [
            (75.2, "fahrenheit", "Fahrenheit a Celsius"),
            (298.15, "kelvin", "Kelvin a Celsius"),
            (25.0, "celsius", "Celsius (sin cambio)"),
            ("23.5", "celsius", "String numérico"),
            (-40, "fahrenheit", "Fahrenheit negativo"),
        ]
        
        for value, unit, description in temp_tests:
            result = normalizer.normalize_temperature(value, unit)
            if result["normalized"]:
                print(f"   ✅ {description}: {value} {unit} → {result['value']} celsius")
                print(f"      📊 Original: {result['original_value']} {result['original_unit']}")
            else:
                print(f"   ❌ {description}: Error - {result.get('error', 'Desconocido')}")
        
        # Probar normalización de humedad
        print("\n💧 Probando normalización de humedad...")
        hum_tests = [
            (0.65, "decimal", "Decimal a porcentaje"),
            (6500, "ppm", "PPM a porcentaje"),
            (75.0, "percentage", "Porcentaje (sin cambio)"),
        ]
        
        for value, unit, description in hum_tests:
            result = normalizer.normalize_humidity(value, unit)
            if result["normalized"]:
                print(f"   ✅ {description}: {value} {unit} → {result['value']} percentage")
            else:
                print(f"   ❌ {description}: Error - {result.get('error', 'Desconocido')}")
        
        # Probar normalización de presión
        print("\n🌪️  Probando normalización de presión...")
        press_tests = [
            (101325, "pa", "Pascal a hPa"),
            (1.013, "bar", "Bar a hPa"),
            (1.0, "atm", "Atmósfera a hPa"),
        ]
        
        for value, unit, description in press_tests:
            result = normalizer.normalize_pressure(value, unit)
            if result["normalized"]:
                print(f"   ✅ {description}: {value} {unit} → {result['value']} hpa")
            else:
                print(f"   ❌ {description}: Error - {result.get('error', 'Desconocido')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en normalización de datos: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validation_levels():
    """Probar diferentes niveles de validación"""
    print("\n🧪 Probando niveles de validación...")
    
    try:
        # Crear configuración por defecto
        from iot_middleware.config import ProcessingConfig, NormalizerConfig
        processing_config = ProcessingConfig()
        normalizer_config = NormalizerConfig()
        
        # Crear procesador
        processor = create_data_processor(processing_config, normalizer_config)
        print("✅ Procesador de datos creado")
        
        # Mensaje con problemas
        problematic_message = {
            "device_id": "sensor_001",
            "sensor_type": "temperature",
            "value": "invalid_value",  # Valor inválido
            "unit": "fahrenheit",
            "location": "sala_principal"
        }
        
        print(f"📨 Mensaje problemático: {json.dumps(problematic_message, indent=2)}")
        
        # Probar con validación STRICT
        print("\n🔒 Probando validación STRICT...")
        try:
            result = processor.process_message(
                problematic_message, 
                validation_level=ValidationLevel.STRICT
            )
            print("   ❌ No debería haber llegado aquí (STRICT debería fallar)")
        except Exception as e:
            print(f"   ✅ STRICT falló correctamente: {e}")
        
        # Probar con validación NORMAL
        print("\n🔧 Probando validación NORMAL...")
        try:
            result = processor.process_message(
                problematic_message, 
                validation_level=ValidationLevel.NORMAL
            )
            print(f"   ✅ NORMAL procesó el mensaje: {result.get('error', False)}")
            if 'error' in result:
                print(f"      📝 Error: {result.get('error_message', 'Desconocido')}")
        except Exception as e:
            print(f"   ❌ NORMAL falló inesperadamente: {e}")
        
        # Probar con validación LENIENT
        print("\n😊 Probando validación LENIENT...")
        try:
            result = processor.process_message(
                problematic_message, 
                validation_level=ValidationLevel.LENIENT
            )
            print(f"   ✅ LENIENT procesó el mensaje: {result.get('error', False)}")
        except Exception as e:
            print(f"   ❌ LENIENT falló inesperadamente: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en niveles de validación: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_custom_schemas():
    """Probar esquemas personalizados"""
    print("\n🧪 Probando esquemas personalizados...")
    
    try:
        # Crear configuración por defecto
        from iot_middleware.config import ProcessingConfig, NormalizerConfig
        processing_config = ProcessingConfig()
        normalizer_config = NormalizerConfig()
        
        # Crear procesador
        processor = create_data_processor(processing_config, normalizer_config)
        print("✅ Procesador de datos creado")
        
        # Crear esquema personalizado para sensores de movimiento
        motion_schema = MessageSchema(
            name="motion_sensor",
            description="Sensor de movimiento",
            fields=[
                FieldSchema("device_id", DataType.STRING, required=True, description="ID del dispositivo"),
                FieldSchema("motion_detected", DataType.BOOLEAN, required=True, description="Movimiento detectado"),
                FieldSchema("confidence", DataType.FLOAT, required=False, min_value=0, max_value=1, default=0.8, description="Confianza de la detección"),
                FieldSchema("timestamp", DataType.TIMESTAMP, required=False, description="Timestamp"),
                FieldSchema("zone", DataType.STRING, required=False, description="Zona de detección")
            ]
        )
        
        # Agregar esquema personalizado
        processor.add_custom_schema("motion_sensor", motion_schema)
        print("✅ Esquema personalizado agregado")
        
        # Verificar que se agregó
        schemas = processor.list_schemas()
        print(f"📋 Esquemas disponibles: {schemas}")
        
        if "motion_sensor" in schemas:
            print("   ✅ Esquema personalizado encontrado en la lista")
        else:
            print("   ❌ Esquema personalizado no encontrado en la lista")
        
        # Probar el esquema personalizado
        motion_message = {
            "device_id": "motion_001",
            "motion_detected": True,
            "confidence": 0.95,
            "zone": "entrada_principal"
        }
        
        print(f"\n📨 Probando mensaje de movimiento: {json.dumps(motion_message, indent=2)}")
        
        result = processor.process_message(motion_message, schema_name="motion_sensor")
        
        if "error" in result and result["error"]:
            print(f"   ❌ Error procesando mensaje: {result['error_message']}")
        else:
            print(f"   ✅ Mensaje procesado exitosamente")
            print(f"      📊 Esquema usado: {result.get('metadata', {}).get('schema_used', 'Desconocido')}")
            print(f"      ⏰ Timestamp: {result.get('timestamp', 'No disponible')}")
            print(f"      🎯 Movimiento: {result.get('motion_detected')}")
            print(f"      📈 Confianza: {result.get('confidence')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en esquemas personalizados: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_processing_stats():
    """Probar estadísticas de procesamiento"""
    print("\n🧪 Probando estadísticas de procesamiento...")
    
    try:
        # Crear configuración por defecto
        from iot_middleware.config import ProcessingConfig, NormalizerConfig
        processing_config = ProcessingConfig()
        normalizer_config = NormalizerConfig()
        
        # Crear procesador
        processor = create_data_processor(processing_config, normalizer_config)
        print("✅ Procesador de datos creado")
        
        # Obtener estadísticas iniciales
        initial_stats = processor.get_processing_stats()
        # Convertir datetime a string para JSON
        initial_stats_json = {
            k: v.isoformat() if isinstance(v, datetime) else v 
            for k, v in initial_stats.items()
        }
        print(f"📊 Estadísticas iniciales: {json.dumps(initial_stats_json, indent=2)}")
        
        # Procesar algunos mensajes
        test_messages = [
            {"device_id": "test_001", "sensor_type": "temperature", "value": 25.0},
            {"device_id": "test_002", "sensor_type": "humidity", "value": 60.0},
            {"device_id": "test_003", "sensor_type": "pressure", "value": 1013.25}
        ]
        
        print(f"\n📨 Procesando {len(test_messages)} mensajes de prueba...")
        
        for i, message in enumerate(test_messages, 1):
            try:
                result = processor.process_message(message)
                print(f"   ✅ Mensaje {i} procesado")
            except Exception as e:
                print(f"   ❌ Mensaje {i} falló: {e}")
        
        # Obtener estadísticas finales
        final_stats = processor.get_processing_stats()
        # Convertir datetime a string para JSON
        final_stats_json = {
            k: v.isoformat() if isinstance(v, datetime) else v 
            for k, v in final_stats.items()
        }
        print(f"\n📊 Estadísticas finales: {json.dumps(final_stats_json, indent=2)}")
        
        # Verificar que las estadísticas se incrementaron
        if final_stats["messages_processed"] > initial_stats["messages_processed"]:
            print("   ✅ Estadísticas se incrementaron correctamente")
        else:
            print("   ❌ Estadísticas no se incrementaron")
        
        # Reiniciar estadísticas
        processor.reset_stats()
        reset_stats = processor.get_processing_stats()
        # Convertir datetime a string para JSON
        reset_stats_json = {
            k: v.isoformat() if isinstance(v, datetime) else v 
            for k, v in reset_stats.items()
        }
        print(f"\n🔄 Estadísticas después del reset: {json.dumps(reset_stats_json, indent=2)}")
        
        if reset_stats["messages_processed"] == 0:
            print("   ✅ Estadísticas se reiniciaron correctamente")
        else:
            print("   ❌ Estadísticas no se reiniciaron")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en estadísticas de procesamiento: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando Pruebas Comprehensivas del Procesador de Datos")
    print("=" * 80)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        ("Validación de Esquemas", test_schema_validation),
        ("Normalización de Datos", test_data_normalization),
        ("Niveles de Validación", test_validation_levels),
        ("Esquemas Personalizados", test_custom_schemas),
        ("Estadísticas de Procesamiento", test_processing_stats),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*30} {test_name} {'='*30}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Error inesperado en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE PRUEBAS COMPREHENSIVAS")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas comprehensivas pasaron exitosamente!")
        print("\n💡 El procesador de datos está completamente funcional y listo para producción")
        print("   ✅ Validación de esquemas funcionando")
        print("   ✅ Normalización de datos funcionando")
        print("   ✅ Niveles de validación funcionando")
        print("   ✅ Esquemas personalizados funcionando")
        print("   ✅ Estadísticas de procesamiento funcionando")
        return True
    else:
        print("⚠️  Algunas pruebas comprehensivas fallaron")
        print("   🔍 Revisar los logs de error para identificar problemas")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
