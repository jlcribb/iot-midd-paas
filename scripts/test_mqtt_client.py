#!/usr/bin/env python3
"""
Script de Prueba para el Cliente MQTT
IoT Middleware
"""

import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.mqtt import (
        IoTMQTTClient, 
        MQTTMessage, 
        create_mqtt_client,
        process_message
    )
    from iot_middleware.config import load_config
    print("✅ Módulos importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    sys.exit(1)

def test_mqtt_client_creation():
    """Probar creación del cliente MQTT"""
    print("\n🧪 Probando creación del cliente MQTT...")
    
    try:
        # Cargar configuración
        config = load_config()
        mqtt_config = config.mqtt
        
        # Crear cliente
        client = create_mqtt_client(mqtt_config, "test_client")
        print("✅ Cliente MQTT creado exitosamente")
        
        # Verificar configuración
        print(f"📡 Broker: {client.config.broker['host']}:{client.config.broker['port']}")
        print(f"📋 Tópicos de suscripción: {client.config.topics['subscribe']}")
        print(f"📤 Tópicos de publicación: {client.config.topics['publish']}")
        print(f"🔧 QoS: {client.config.qos}")
        print(f"💾 Retain: {client.config.retain}")
        
        return True, client
        
    except Exception as e:
        print(f"❌ Error al crear cliente MQTT: {e}")
        return False, None

def test_mqtt_connection(client):
    """Probar conexión MQTT"""
    print("\n🧪 Probando conexión MQTT...")
    
    try:
        # Intentar conectar
        if client.connect():
            print("✅ Conexión MQTT exitosa")
            
            # Esperar un momento para que se establezca la conexión
            time.sleep(2)
            
            # Verificar estado de conexión
            status = client.get_connection_status()
            print(f"📊 Estado de conexión: {status}")
            
            return True
        else:
            print("❌ Falló la conexión MQTT")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la conexión: {e}")
        return False

def test_mqtt_subscription(client):
    """Probar suscripción a tópicos"""
    print("\n🧪 Probando suscripción a tópicos...")
    
    try:
        # Verificar tópicos suscritos
        status = client.get_connection_status()
        subscribed_topics = status['subscribed_topics']
        
        if subscribed_topics:
            print(f"✅ Suscrito a {len(subscribed_topics)} tópicos:")
            for topic in subscribed_topics:
                print(f"   📋 {topic}")
        else:
            print("⚠️  No hay tópicos suscritos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar suscripciones: {e}")
        return False

def test_mqtt_publishing(client):
    """Probar publicación de mensajes"""
    print("\n🧪 Probando publicación de mensajes...")
    
    try:
        # Mensaje de prueba
        test_message = {
            "device_id": "test_device_001",
            "sensor_type": "temperature",
            "value": 23.5,
            "unit": "celsius",
            "timestamp": datetime.now().isoformat(),
            "test": True
        }
        
        # Publicar en tópico de prueba
        test_topic = "iot/test/+/data"
        if client.publish(test_topic, test_message):
            print(f"✅ Mensaje publicado exitosamente en {test_topic}")
            print(f"   📤 Payload: {test_message}")
        else:
            print(f"❌ Error al publicar mensaje en {test_topic}")
            return False
        
        # Publicar en tópico de estado
        status_message = {
            "device_id": "test_device_001",
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "test": True
        }
        
        status_topic = "iot/test/+/status"
        if client.publish(status_topic, status_message):
            print(f"✅ Mensaje de estado publicado en {status_topic}")
            print(f"   📤 Payload: {status_message}")
        else:
            print(f"❌ Error al publicar mensaje de estado en {status_topic}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la publicación: {e}")
        return False

def test_message_processor():
    """Probar procesador de mensajes"""
    print("\n🧪 Probando procesador de mensajes...")
    
    try:
        # Crear mensaje de prueba
        test_message = MQTTMessage(
            topic="iot/test/device001/data",
            payload={
                "device_id": "device001",
                "sensor_type": "humidity",
                "value": 65.2,
                "unit": "percentage"
            },
            qos=1,
            retain=False
        )
        
        # Procesar mensaje
        print("📨 Procesando mensaje de prueba...")
        process_message(test_message)
        
        print("✅ Procesador de mensajes funcionando correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en procesador de mensajes: {e}")
        return False

def test_custom_message_processor(client):
    """Probar procesador de mensajes personalizado"""
    print("\n🧪 Probando procesador de mensajes personalizado...")
    
    try:
        # Contador de mensajes
        message_count = 0
        
        def custom_processor(message):
            nonlocal message_count
            message_count += 1
            print(f"🔧 Mensaje #{message_count} procesado por procesador personalizado:")
            print(f"   📨 Tópico: {message.topic}")
            print(f"   📊 Payload: {message.payload}")
            print(f"   ⏰ Timestamp: {message.timestamp}")
        
        # Configurar procesador personalizado
        client.set_message_processor(custom_processor)
        print("✅ Procesador personalizado configurado")
        
        # Publicar mensaje de prueba
        test_message = {
            "device_id": "custom_test_device",
            "sensor_type": "pressure",
            "value": 1013.25,
            "unit": "hPa",
            "timestamp": datetime.now().isoformat(),
            "custom_test": True
        }
        
        if client.publish("iot/custom/+/data", test_message):
            print("✅ Mensaje de prueba publicado para procesador personalizado")
            
            # Esperar un momento para que se procese
            time.sleep(1)
            
            if message_count > 0:
                print(f"✅ Procesador personalizado procesó {message_count} mensaje(s)")
                return True
            else:
                print("❌ El procesador personalizado no recibió mensajes")
                return False
        else:
            print("❌ Error al publicar mensaje de prueba")
            return False
        
    except Exception as e:
        print(f"❌ Error en procesador personalizado: {e}")
        return False

def test_mqtt_disconnection(client):
    """Probar desconexión MQTT"""
    print("\n🧪 Probando desconexión MQTT...")
    
    try:
        # Desconectar
        client.disconnect()
        print("✅ Desconexión MQTT exitosa")
        
        # Verificar estado
        status = client.get_connection_status()
        if not status['connected']:
            print("✅ Estado de conexión actualizado correctamente")
            return True
        else:
            print("❌ Estado de conexión no se actualizó")
            return False
        
    except Exception as e:
        print(f"❌ Error durante la desconexión: {e}")
        return False

def test_context_manager():
    """Probar context manager del cliente MQTT"""
    print("\n🧪 Probando context manager...")
    
    try:
        # Cargar configuración
        config = load_config()
        mqtt_config = config.mqtt
        
        # Usar context manager
        with create_mqtt_client(mqtt_config, "context_test_client") as client:
            print("✅ Context manager iniciado correctamente")
            
            # Verificar que el cliente está disponible
            if client.config:
                print("✅ Cliente disponible dentro del context manager")
                
                # Intentar conectar
                if client.connect():
                    print("✅ Conexión exitosa dentro del context manager")
                    
                    # Verificar estado
                    status = client.get_connection_status()
                    print(f"📊 Estado: {status['connected']}")
                    
                    # El context manager se encargará de desconectar automáticamente
                    return True
                else:
                    print("❌ Falló la conexión dentro del context manager")
                    return False
            else:
                print("❌ Cliente no disponible dentro del context manager")
                return False
        
    except Exception as e:
        print(f"❌ Error en context manager: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando Pruebas del Cliente MQTT")
    print("=" * 60)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    tests = [
        ("Creación del Cliente", test_mqtt_client_creation),
        ("Procesador de Mensajes", test_message_processor),
        ("Context Manager", test_context_manager)
    ]
    
    # Pruebas que requieren conexión activa
    connection_tests = [
        ("Conexión MQTT", test_mqtt_connection),
        ("Suscripción a Tópicos", test_mqtt_subscription),
        ("Publicación de Mensajes", test_mqtt_publishing),
        ("Procesador Personalizado", test_custom_message_processor),
        ("Desconexión MQTT", test_mqtt_disconnection)
    ]
    
    results = []
    
    # Ejecutar pruebas básicas
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_name == "Creación del Cliente":
                success, client = test_func()
                if success and client:
                    # Ejecutar pruebas de conexión
                    for conn_test_name, conn_test_func in connection_tests:
                        print(f"\n{'='*20} {conn_test_name} {'='*20}")
                        try:
                            conn_success = conn_test_func(client)
                            results.append((conn_test_name, conn_success))
                        except Exception as e:
                            print(f"❌ Error inesperado en {conn_test_name}: {e}")
                            results.append((conn_test_name, False))
                    
                    # Limpiar cliente
                    try:
                        client.disconnect()
                    except:
                        pass
                    
                    results.append((test_name, success))
                else:
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
        print("\n💡 El cliente MQTT está listo para usar en producción")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
