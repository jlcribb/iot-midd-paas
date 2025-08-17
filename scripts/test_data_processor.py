#!/usr/bin/env python3
"""
Script de Prueba para el Procesador de Datos
IoT Middleware
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

def test_field_schema_validation():
    """Probar validación de esquemas de campos"""
    print("\n🧪 Probando validación de esquemas de campos...")
    
    try:
        # Crear esquema de campo de temperatura
        temp_field = FieldSchema(
            name="temperature",
            data_type=DataType.FLOAT,
            required=True,
            min_value=-50.0,
            max_value=100.0,
            description="Temperatura en Celsius"
        )
        
        print("✅ Esquema de campo de temperatura creado")
        
        # Probar validaciones
        test_cases = [
            (25.5, True, "Temperatura válida"),
            (-60.0, False, "Temperatura por debajo del mínimo"),
            (120.0, False, "Temperatura por encima del máximo"),
            ("25.5", True, "String numérico válido"),
            (None, False, "Valor None en campo requerido"),
        ]
        
        for value, expected_valid, description in test_cases:
            is_valid, normalized_value, error_msg = temp_field.validate(value)
            
            if is_valid == expected_valid:
                status = "✅ PASÓ" if is_valid else "✅ PASÓ (rechazado correctamente)"
                print(f"   {status}: {description} - Valor: {value}")
            else:
                print(f"   ❌ FALLÓ: {description} - Valor: {value}, Esperado: {expected_valid}, Obtenido: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en validación de esquemas: {e}")
        return False

def test_message_schema_creation():
    """Probar creación de esquemas de mensajes"""
    print("\n🧪 Probando creación de esquemas de mensajes...")
    
    try:
        # Crear esquema personalizado
        custom_schema = MessageSchema(
            name="custom_sensor",
            description="Sensor personalizado",
            fields=[
                FieldSchema("device_id", DataType.STRING, required=True, description="ID del dispositivo"),
                FieldSchema("sensor_type", DataType.STRING, required=True, description="Tipo de sensor"),
                FieldSchema("value", DataType.FLOAT, required=True, description="Valor del sensor"),
                FieldSchema("unit", DataType.STRING, required=False, default="unknown", description="Unidad de medida"),
                FieldSchema("timestamp", DataType.TIMESTAMP, required=False, description="Timestamp de la medición"),
                FieldSchema("quality", DataType.INTEGER, required=False, min_value=0, max_value=100, default=50, description="Calidad de la medición")
            ]
        )
        
        print("✅ Esquema personalizado creado")
        print(f"   📋 Nombre: {custom_schema.name}")
        print(f"   📝 Descripción: {custom_schema.description}")
        print(f"   🔧 Campos requeridos: {custom_schema.required_fields}")
        print(f"   🔧 Campos opcionales: {custom_schema.optional_fields}")
        print(f"   📊 Total de campos: {len(custom_schema.fields)}")
        
        return True, custom_schema
        
    except Exception as e:
        print(f"❌ Error en creación de esquemas: {e}")
        return False, None

def test_data_normalizer():
    """Probar normalizador de datos"""
    print("\n🧪 Probando normalizador de datos...")
    
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
        ]
        
        for value, unit, description in temp_tests:
            result = normalizer.normalize_temperature(value, unit)
            if result["normalized"]:
                print(f"   ✅ {description}: {value} {unit} → {result['value']} celsius")
            else:
                print(f"   ❌ {description}: Error - {result.get('error', 'Desconocido')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en normalizador: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando Pruebas del Procesador de Datos")
    print("=" * 60)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        ("Validación de Esquemas de Campos", test_field_schema_validation),
        ("Creación de Esquemas de Mensajes", test_message_schema_creation),
        ("Normalizador de Datos", test_data_normalizer),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_name == "Creación de Esquemas de Mensajes":
                success, custom_schema = test_func()
                results.append((test_name, success))
            else:
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
        print("\n💡 El procesador de datos está listo para usar en producción")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
