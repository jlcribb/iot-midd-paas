#!/usr/bin/env python3
"""
Ejemplo de Uso del Procesador de Datos
IoT Middleware
======================================

Este script demuestra cómo usar el módulo de procesamiento y normalización
de datos para mensajes IoT.
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

def example_basic_processing():
    """Ejemplo básico de procesamiento de datos"""
    print("\n🔧 EJEMPLO 1: Procesamiento Básico de Datos")
    print("=" * 50)
    
    try:
        # Mensaje de ejemplo
        message = {
            "device_id": "sensor_001",
            "sensor_type": "temperature",
            "value": 75.2,
            "unit": "fahrenheit",
            "location": "sala_principal"
        }
        
        print(f"📨 Mensaje original: {json.dumps(message, indent=2)}")
        
        # Procesar mensaje usando la función de compatibilidad
        result = process_message(message)
        
        print(f"✅ Mensaje procesado:")
        print(f"   📊 Resultado: {json.dumps(result, indent=2, default=str)}")
        
        # Mostrar información clave
        print(f"\n📊 Información del procesamiento:")
        print(f"   🔧 Esquema usado: {result.get('metadata', {}).get('schema_used', 'Desconocido')}")
        print(f"   🌡️  Temperatura normalizada: {result.get('value')} {result.get('unit')}")
        print(f"   ⏰ Timestamp: {result.get('timestamp')}")
        print(f"   🔄 Normalizado: {result.get('normalized', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en procesamiento básico: {e}")
        return False

def example_advanced_processing():
    """Ejemplo avanzado con procesador personalizado"""
    print("\n🔧 EJEMPLO 2: Procesamiento Avanzado")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config = load_config()
        processor = create_data_processor(config.processing, config.normalizers)
        
        print("✅ Procesador de datos creado")
        
        # Mensajes de diferentes tipos
        messages = [
            {
                "name": "Datos de sensor de humedad",
                "payload": {
                    "device_id": "sensor_002",
                    "sensor_type": "humidity",
                    "value": 0.65,
                    "unit": "decimal",
                    "location": "cocina"
                }
            },
            {
                "name": "Estado del dispositivo",
                "payload": {
                    "device_id": "device_001",
                    "status": "online",
                    "battery": 85,
                    "uptime": 3600
                }
            }
        ]
        
        # Procesar cada mensaje
        for i, msg_data in enumerate(messages, 1):
            print(f"\n--- Mensaje {i}: {msg_data['name']} ---")
            print(f"📨 Payload: {json.dumps(msg_data['payload'], indent=2)}")
            
            # Procesar mensaje
            result = processor.process_message(msg_data['payload'])
            
            if "error" in result and result["error"]:
                print(f"❌ Error procesando mensaje: {result['error_message']}")
            else:
                print(f"✅ Mensaje procesado exitosamente")
                print(f"   📊 Esquema: {result.get('metadata', {}).get('schema_used', 'Desconocido')}")
                print(f"   ⏰ Timestamp: {result.get('timestamp', 'No disponible')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en procesamiento avanzado: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Ejemplos de Uso del Procesador de Datos")
    print("=" * 60)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    examples = [
        ("Procesamiento Básico", example_basic_processing),
        ("Procesamiento Avanzado", example_advanced_processing),
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
        print("\n💡 El procesador de datos está listo para usar en producción")
        return True
    else:
        print("⚠️  Algunos ejemplos fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
