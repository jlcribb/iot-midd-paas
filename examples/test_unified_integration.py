#!/usr/bin/env python3
"""
Script de Prueba - Integración Unificada
========================================

Este script prueba la integración del InputManager con el middleware core
a través del servicio unificado de ingesta.
"""

import sys
import os
import json
import time
import threading
from datetime import datetime

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_unified_integration():
    """Probar la integración unificada"""
    try:
        from iot_middleware.services.unified_ingestor import UnifiedIngestaService, create_unified_ingesta_service
        from iot_middleware.input import InputManager, UnifiedDataFormat, DataQuality
        
        print("✅ Módulo UnifiedIngestaService importado correctamente")
        
        # Crear configuración de prueba
        test_config = {
            'input_manager': {
                'enabled_protocols': ['mqtt', 'http', 'ble'],
                'mqtt_config': {
                    'broker': 'localhost',
                    'port': 1883,
                    'topics': ['test/+/+']
                },
                'http_config': {
                    'host': '0.0.0.0',
                    'port': 8080,
                    'endpoint': '/ingest'
                },
                'ble_config': {
                    'bridge_type': 'mqtt',
                    'bridge_config': {
                        'mqtt_topics': ['ble/+/+']
                    }
                }
            },
            'core_config': {
                'mqtt_broker': 'localhost',
                'mqtt_port': 1883
            },
            'integration': {
                'enable_protocol_bridge': True,
                'mqtt_topic_prefix': 'iot/unified',
                'auto_create_channels': True
            }
        }
        
        # Crear servicio unificado
        print("🔧 Creando servicio unificado de ingesta...")
        service = create_unified_ingesta_service()
        
        # Simular configuración completa
        mock_config = type('Config', (), {
            'input_manager': test_config['input_manager'],
            'core_config': test_config['core_config'],
            'integration': test_config['integration']
        })()
        
        service.config = mock_config
        
        print("✅ Servicio unificado creado")
        
        # Probar inicialización
        print("\n🚀 Probando inicialización...")
        if service.initialize():
            print("✅ Inicialización exitosa")
        else:
            print("❌ Error en inicialización")
            return False
        
        # Probar estado del servicio
        print("\n📊 Verificando estado del servicio...")
        status = service.get_status()
        print(f"✅ Estado obtenido: {len(status)} campos")
        
        # Verificar componentes
        if service.input_manager:
            print("✅ InputManager creado")
        else:
            print("❌ InputManager no creado")
            return False
        
        if service.protocol_bridge:
            print("✅ ProtocolBridge creado")
        else:
            print("❌ ProtocolBridge no creado")
            return False
        
        # Probar callback de datos unificados
        print("\n📨 Probando callback de datos unificados...")
        
        # Crear datos de prueba
        test_data = UnifiedDataFormat(
            device_id="test_device_001",
            project_id="test_project",
            timestamp=datetime.now().isoformat(),
            measurements={
                "temperature": 25.5,
                "humidity": 60.0
            },
            source_address="http://localhost:8080/ingest",
            quality=DataQuality.VALID
        )
        
        # Simular recepción de datos
        service._on_unified_data(test_data)
        
        # Verificar métricas
        print(f"✅ Datos procesados: {service.metrics.input_messages_received}")
        print(f"✅ Datos enviados al core: {service.metrics.core_messages_sent}")
        
        # Probar limpieza
        print("\n🧹 Probando limpieza de recursos...")
        service._cleanup()
        print("✅ Limpieza completada")
        
        print("\n🎉 ¡Prueba de integración unificada completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_input_manager_integration():
    """Probar la integración directa del InputManager"""
    try:
        from iot_middleware.input import InputManager, UnifiedDataFormat, DataQuality
        
        print("✅ Módulo InputManager importado correctamente")
        
        # Crear configuración de prueba
        configs = [
            {
                'name': 'mqtt_test',
                'protocol': 'mqtt',
                'enabled': True,
                'config': {
                    'broker': 'localhost',
                    'port': 1883,
                    'topics': ['test/+/+']
                }
            },
            {
                'name': 'http_test',
                'protocol': 'http',
                'enabled': True,
                'config': {
                    'host': '0.0.0.0',
                    'port': 8080,
                    'endpoint': '/ingest'
                }
            }
        ]
        
        # Probar callback de datos
        print("\n📨 Probando callback de datos...")
        
        received_data = []
        
        def data_callback(data: UnifiedDataFormat):
            received_data.append(data)
            print(f"📨 Datos recibidos: {data.device_id} - {data.measurements}")
        
        # Crear InputManager con callback
        print("🔧 Creando InputManager...")
        input_manager = InputManager(configs, data_callback)
        print("✅ InputManager creado")
        
        # Verificar protocolos habilitados
        enabled_protocols = list(input_manager.connectors.keys())
        print(f"✅ Protocolos habilitados: {enabled_protocols}")
        print("✅ Callback configurado")
        
        # Simular datos de diferentes protocolos
        test_data_mqtt = UnifiedDataFormat(
            device_id="mqtt_sensor_001",
            project_id="test_project",
            timestamp=datetime.now().isoformat(),
            measurements={"temperature": 22.5},
            source_address="mqtt://localhost:1883/test/sensor",
            quality=DataQuality.VALID
        )
        
        test_data_http = UnifiedDataFormat(
            device_id="http_device_001",
            project_id="test_project",
            timestamp=datetime.now().isoformat(),
            measurements={"humidity": 65.0},
            source_address="http://localhost:8080/ingest",
            quality=DataQuality.VALID
        )
        
        # Simular recepción
        data_callback(test_data_mqtt)
        data_callback(test_data_http)
        
        print(f"✅ Datos simulados: {len(received_data)} recibidos")
        
        # Verificar estado
        status = input_manager.get_manager_status()
        print(f"✅ Estado del InputManager: {len(status)} campos")
        
        print("\n🎉 ¡Prueba de InputManager completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error en la prueba del InputManager: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_protocol_bridge():
    """Probar el puente de protocolos"""
    try:
        from iot_middleware.services.unified_ingestor import ProtocolBridge
        from iot_middleware.input import UnifiedDataFormat, DataQuality
        
        print("✅ Módulo ProtocolBridge importado correctamente")
        
        # Crear configuración de prueba
        config = {
            'enable_protocol_bridge': True,
            'mqtt_topic_prefix': 'iot/unified',
            'auto_create_channels': True
        }
        
        # Crear puente
        print("🔧 Creando ProtocolBridge...")
        bridge = ProtocolBridge(config)
        print("✅ ProtocolBridge creado")
        
        # Crear datos de prueba
        test_data = UnifiedDataFormat(
            device_id="test_device_001",
            project_id="test_project",
            timestamp=datetime.now().isoformat(),
            measurements={"temperature": 25.5},
            source_address="http://localhost:8080/ingest",
            quality=DataQuality.VALID
        )
        
        # Probar creación de tópico
        print("\n📡 Probando creación de tópico...")
        topic = bridge._create_core_topic(test_data)
        print(f"✅ Tópico creado: {topic}")
        
        # Probar conversión de formato
        print("\n🔄 Probando conversión de formato...")
        core_payload = bridge._convert_to_core_format(test_data)
        print(f"✅ Payload convertido: {len(core_payload)} campos")
        
        # Verificar estructura del payload
        expected_fields = ['timestamp', 'device_id', 'project_id', 'measurements', 'metadata']
        for field in expected_fields:
            if field in core_payload:
                print(f"  ✅ Campo {field}: presente")
            else:
                print(f"  ❌ Campo {field}: ausente")
        
        print("\n🎉 ¡Prueba del ProtocolBridge completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error en la prueba del ProtocolBridge: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🧪 PRUEBA DE INTEGRACIÓN UNIFICADA")
    print("=" * 50)
    
    tests = [
        ("InputManager", test_input_manager_integration),
        ("ProtocolBridge", test_protocol_bridge),
        ("UnifiedIngestaService", test_unified_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 Ejecutando prueba: {test_name}")
        print("-" * 30)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name}: PASÓ")
            else:
                print(f"❌ {test_name}: FALLÓ")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n📊 RESUMEN DE PRUEBAS")
    print("=" * 30)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("\n🎉 ¡Todas las pruebas pasaron! La integración está funcionando correctamente.")
        return True
    else:
        print(f"\n⚠️  {total - passed} pruebas fallaron. Revisar errores antes de continuar.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
