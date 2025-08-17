#!/usr/bin/env python3
"""
Ejemplo Offline del Cliente MQTT
IoT Middleware
================================

Este script demuestra las funcionalidades del cliente MQTT
sin necesidad de conexión real al broker.
"""

import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.mqtt import (
        IoTMQTTClient, 
        MQTTMessage, 
        create_mqtt_client
    )
    from iot_middleware.config import load_config
    print("✅ Módulos importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    sys.exit(1)

def example_client_creation():
    """Ejemplo de creación del cliente MQTT"""
    print("\n🔧 EJEMPLO 1: Creación del Cliente MQTT")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config = load_config()
        mqtt_config = config.mqtt
        
        # Crear cliente MQTT
        client = create_mqtt_client(mqtt_config, "offline_example_client")
        print("✅ Cliente MQTT creado exitosamente")
        
        # Mostrar configuración
        print(f"📡 Broker configurado: {client.config.broker['host']}:{client.config.broker['port']}")
        print(f"📋 Tópicos de suscripción: {client.config.topics['subscribe']}")
        print(f"📤 Tópicos de publicación: {client.config.topics['publish']}")
        print(f"🔧 QoS por defecto: {client.config.qos}")
        print(f"💾 Retain por defecto: {client.config.retain}")
        
        # Mostrar estado inicial
        status = client.get_connection_status()
        print(f"📊 Estado inicial: {status['connected']}")
        
        return True, client
        
    except Exception as e:
        print(f"❌ Error al crear cliente: {e}")
        return False, None

def example_message_processing():
    """Ejemplo de procesamiento de mensajes"""
    print("\n🔧 EJEMPLO 2: Procesamiento de Mensajes")
    print("=" * 50)
    
    try:
        # Crear mensajes de prueba
        test_messages = [
            MQTTMessage(
                topic="iot/sensor_001/data",
                payload={
                    "device_id": "sensor_001",
                    "sensor_type": "temperature",
                    "value": 24.5,
                    "unit": "celsius",
                    "timestamp": datetime.now().isoformat()
                },
                qos=1,
                retain=False
            ),
            MQTTMessage(
                topic="iot/sensor_002/status",
                payload={
                    "device_id": "sensor_002",
                    "status": "online",
                    "battery": 85,
                    "timestamp": datetime.now().isoformat()
                },
                qos=1,
                retain=False
            ),
            MQTTMessage(
                topic="iot/gateway/alerts",
                payload={
                    "alert_type": "high_temperature",
                    "device_id": "sensor_003",
                    "value": 35.2,
                    "threshold": 30.0,
                    "severity": "warning",
                    "timestamp": datetime.now().isoformat()
                },
                qos=2,
                retain=True
            )
        ]
        
        # Procesar cada mensaje
        for i, message in enumerate(test_messages, 1):
            print(f"\n📨 Procesando mensaje {i}:")
            print(f"   📍 Tópico: {message.topic}")
            print(f"   📊 Payload: {json.dumps(message.payload, indent=2)}")
            print(f"   🔧 QoS: {message.qos}")
            print(f"   💾 Retain: {message.retain}")
            print(f"   ⏰ Timestamp: {message.timestamp}")
            
            # Simular procesamiento
            time.sleep(0.5)
        
        print("\n✅ Todos los mensajes procesados exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en procesamiento: {e}")
        return False

def example_custom_processor():
    """Ejemplo de procesador personalizado"""
    print("\n🔧 EJEMPLO 3: Procesador Personalizado")
    print("=" * 50)
    
    try:
        # Crear cliente
        config = load_config()
        client = create_mqtt_client(config.mqtt, "processor_example")
        
        # Contador de mensajes procesados
        message_count = 0
        device_stats = {}
        
        def custom_processor(message):
            nonlocal message_count
            message_count += 1
            
            print(f"\n🔧 Mensaje #{message_count} procesado:")
            print(f"   📍 Tópico: {message.topic}")
            
            # Extraer device_id si está disponible
            device_id = message.payload.get('device_id', 'unknown')
            
            # Actualizar estadísticas del dispositivo
            if device_id not in device_stats:
                device_stats[device_id] = {
                    'message_count': 0,
                    'last_seen': None,
                    'topics': set()
                }
            
            device_stats[device_id]['message_count'] += 1
            device_stats[device_id]['last_seen'] = message.timestamp
            device_stats[device_id]['topics'].add(message.topic)
            
            # Mostrar estadísticas actualizadas
            print(f"   📱 Dispositivo: {device_id}")
            print(f"   📊 Total mensajes del dispositivo: {device_stats[device_id]['message_count']}")
            print(f"   📋 Tópicos del dispositivo: {list(device_stats[device_id]['topics'])}")
            
            # Simular procesamiento específico por tipo de mensaje
            if 'data' in message.topic:
                print("   🔍 Procesando datos del sensor...")
                if 'value' in message.payload:
                    print(f"      📊 Valor: {message.payload['value']} {message.payload.get('unit', '')}")
            elif 'status' in message.topic:
                print("   📊 Procesando estado del dispositivo...")
                if 'status' in message.payload:
                    print(f"      🟢 Estado: {message.payload['status']}")
            elif 'alerts' in message.topic:
                print("   🚨 Procesando alerta...")
                if 'severity' in message.payload:
                    print(f"      ⚠️  Severidad: {message.payload['severity']}")
        
        # Configurar procesador
        client.set_message_processor(custom_processor)
        print("✅ Procesador personalizado configurado")
        
        # Simular recepción de mensajes
        test_messages = [
            {
                "topic": "iot/sensor_001/data",
                "payload": {
                    "device_id": "sensor_001",
                    "sensor_type": "temperature",
                    "value": 24.5,
                    "unit": "celsius",
                    "timestamp": datetime.now().isoformat()
                }
            },
            {
                "topic": "iot/sensor_001/status",
                "payload": {
                    "device_id": "sensor_001",
                    "status": "online",
                    "battery": 90,
                    "timestamp": datetime.now().isoformat()
                }
            },
            {
                "topic": "iot/sensor_002/data",
                "payload": {
                    "device_id": "sensor_002",
                    "sensor_type": "humidity",
                    "value": 65.2,
                    "unit": "percentage",
                    "timestamp": datetime.now().isoformat()
                }
            },
            {
                "topic": "iot/gateway/alerts",
                "payload": {
                    "device_id": "sensor_001",
                    "alert_type": "low_battery",
                    "severity": "warning",
                    "value": 15,
                    "threshold": 20,
                    "timestamp": datetime.now().isoformat()
                }
            }
        ]
        
        print("\n📨 Simulando recepción de mensajes...")
        for i, msg_data in enumerate(test_messages, 1):
            print(f"\n--- Mensaje {i} ---")
            
            # Crear mensaje MQTT
            message = MQTTMessage(
                topic=msg_data["topic"],
                payload=msg_data["payload"],
                qos=1,
                retain=False
            )
            
            # Procesar mensaje
            custom_processor(message)
            
            time.sleep(1)
        
        # Mostrar resumen final
        print("\n" + "="*50)
        print("📊 RESUMEN FINAL")
        print("="*50)
        print(f"📨 Total de mensajes procesados: {message_count}")
        print(f"📱 Dispositivos activos: {len(device_stats)}")
        
        for device_id, stats in device_stats.items():
            print(f"\n📱 Dispositivo: {device_id}")
            print(f"   📨 Mensajes: {stats['message_count']}")
            print(f"   ⏰ Última actividad: {stats['last_seen']}")
            print(f"   📋 Tópicos: {list(stats['topics'])}")
        
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error en procesador personalizado: {e}")
        return False

def example_configuration_analysis():
    """Ejemplo de análisis de configuración"""
    print("\n🔧 EJEMPLO 4: Análisis de Configuración")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config = load_config()
        mqtt_config = config.mqtt
        
        print("🔍 Analizando configuración MQTT...")
        
        # Analizar broker
        broker = mqtt_config.broker
        print(f"\n📡 Configuración del Broker:")
        print(f"   🏠 Host: {broker['host']}")
        print(f"   🚪 Puerto: {broker['port']}")
        print(f"   ⏱️  Keepalive: {broker.get('keepalive', 'No configurado')}")
        print(f"   👤 Username: {broker.get('username', 'No configurado')}")
        print(f"   🔐 Password: {'Configurado' if broker.get('password') else 'No configurado'}")
        print(f"   🔒 TLS: {'Habilitado' if broker.get('tls_enabled') else 'Deshabilitado'}")
        
        # Analizar tópicos
        topics = mqtt_config.topics
        print(f"\n📋 Configuración de Tópicos:")
        print(f"   📥 Suscripción ({len(topics['subscribe'])} tópicos):")
        for topic in topics['subscribe']:
            print(f"      📋 {topic}")
        
        print(f"   📤 Publicación ({len(topics['publish'])} tópicos):")
        for topic in topics['publish']:
            print(f"      📤 {topic}")
        
        # Analizar QoS y retención
        print(f"\n⚙️  Configuración de Calidad:")
        print(f"   🔧 QoS por defecto: {mqtt_config.qos}")
        print(f"   💾 Retención por defecto: {mqtt_config.retain}")
        
        # Análisis de seguridad
        print(f"\n🔐 Análisis de Seguridad:")
        if broker.get('username') and broker.get('password'):
            print("   ✅ Autenticación configurada")
        else:
            print("   ⚠️  Autenticación no configurada")
        
        if broker.get('tls_enabled'):
            print("   ✅ TLS/SSL habilitado")
            if broker.get('ca_certs'):
                print("   ✅ Certificado CA configurado")
            if broker.get('certfile') and broker.get('keyfile'):
                print("   ✅ Certificado cliente configurado")
        else:
            print("   ⚠️  TLS/SSL no habilitado (conexión no cifrada)")
        
        # Recomendaciones
        print(f"\n💡 Recomendaciones:")
        if not broker.get('username'):
            print("   🔐 Considerar configurar autenticación para producción")
        if not broker.get('tls_enabled'):
            print("   🔒 Considerar habilitar TLS para conexiones seguras")
        if mqtt_config.qos == 0:
            print("   ⚠️  QoS 0 puede resultar en pérdida de mensajes")
        elif mqtt_config.qos == 2:
            print("   ✅ QoS 2 garantiza entrega exactamente una vez")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en análisis de configuración: {e}")
        return False

def example_error_handling():
    """Ejemplo de manejo de errores"""
    print("\n🔧 EJEMPLO 5: Manejo de Errores")
    print("=" * 50)
    
    try:
        # Crear cliente
        config = load_config()
        client = create_mqtt_client(config.mqtt, "error_example")
        
        print("🔍 Probando diferentes escenarios de error...")
        
        # 1. Intentar publicar sin conexión
        print("\n1️⃣  Intentando publicar sin conexión...")
        try:
            result = client.publish("iot/test/error", {"test": "data"})
            if not result:
                print("   ✅ Error manejado correctamente: No se puede publicar sin conexión")
            else:
                print("   ❌ Error no manejado correctamente")
        except Exception as e:
            print(f"   ✅ Excepción capturada: {e}")
        
        # 2. Intentar suscribirse sin conexión
        print("\n2️⃣  Intentando suscribirse sin conexión...")
        try:
            result = client.subscribe("iot/test/error")
            if not result:
                print("   ✅ Error manejado correctamente: No se puede suscribir sin conexión")
            else:
                print("   ❌ Error no manejado correctamente")
        except Exception as e:
            print(f"   ✅ Excepción capturada: {e}")
        
        # 3. Verificar estado de conexión
        print("\n3️⃣  Verificando estado de conexión...")
        status = client.get_connection_status()
        print(f"   📊 Estado: {status['connected']}")
        print(f"   🆔 Client ID: {status['client_id']}")
        print(f"   🏠 Broker: {status['broker_host']}:{status['broker_port']}")
        
        # 4. Simular manejo de mensajes malformados
        print("\n4️⃣  Simulando manejo de mensajes malformados...")
        
        def procesador_con_errores(mensaje):
            try:
                # Simular error en procesamiento
                if 'error' in mensaje.topic:
                    raise ValueError("Mensaje de error simulado")
                
                print(f"   ✅ Mensaje procesado: {mensaje.topic}")
                
            except Exception as e:
                print(f"   ❌ Error procesando mensaje: {e}")
                # Continuar procesando otros mensajes
                return
        
        # Configurar procesador
        client.set_message_processor(procesador_con_errores)
        
        # Procesar mensajes (algunos con error)
        mensajes_prueba = [
            MQTTMessage("iot/test/normal", {"data": "normal"}, 1, False),
            MQTTMessage("iot/test/error", {"data": "error"}, 1, False),
            MQTTMessage("iot/test/another", {"data": "another"}, 1, False)
        ]
        
        for mensaje in mensajes_prueba:
            procesador_con_errores(mensaje)
        
        print("\n✅ Manejo de errores demostrado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en manejo de errores: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Ejemplos Offline del Cliente MQTT")
    print("=" * 60)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    examples = [
        ("Creación del Cliente", example_client_creation),
        ("Procesamiento de Mensajes", example_message_processing),
        ("Procesador Personalizado", example_custom_processor),
        ("Análisis de Configuración", example_configuration_analysis),
        ("Manejo de Errores", example_error_handling)
    ]
    
    results = []
    
    for example_name, example_func in examples:
        print(f"\n{'='*20} {example_name} {'='*20}")
        try:
            if example_name == "Creación del Cliente":
                success, client = example_func()
                results.append((example_name, success))
            else:
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
        print("\n💡 El módulo MQTT está listo para usar en producción")
        print("   🔌 Para pruebas con broker real, ejecuta los contenedores")
        return True
    else:
        print("⚠️  Algunos ejemplos fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
