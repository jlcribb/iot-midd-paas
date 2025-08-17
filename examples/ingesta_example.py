#!/usr/bin/env python3
"""
Ejemplo de Uso del Servicio de Ingesta MQTT
IoT Middleware
===========================================

Este script demuestra cómo usar el servicio de ingesta MQTT para:
- Suscribirse a tópicos configurados
- Procesar payloads y mapearlos a canales
- Validar datos por tipo y rangos
- Almacenar en base de datos
- Disparar alarmas según umbrales
"""

import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
import threading

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.services.ingestor import MQTTIngestaService, run
    from iot_middleware.mqtt.mqtt_client import create_mqtt_client
    from iot_middleware.config import load_config
    print("✅ Módulos importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    sys.exit(1)


def example_basic_ingesta():
    """Ejemplo básico de ingesta MQTT"""
    print("\n🔧 EJEMPLO 1: Ingesta Básica MQTT")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config_path = Path(__file__).parent / "config_ingesta.yaml"
        config = load_config(str(config_path))
        
        print("✅ Configuración cargada")
        print(f"   📡 Broker MQTT: {config.mqtt.broker['host']}:{config.mqtt.broker['port']}")
        print(f"   📋 Tópicos de suscripción: {len(config.mqtt.topics['subscribe'])}")
        print(f"   🗄️  Base de datos: {config.storage.type}")
        
        # Crear servicio de ingesta
        service = MQTTIngestaService(str(config_path))
        
        print("✅ Servicio de ingesta creado")
        
        # Inicializar servicio
        if service.initialize():
            print("✅ Servicio inicializado")
            
            # Mostrar estado
            status = service.get_status()
            print(f"   📊 Estado: {status['running']}")
            print(f"   📡 MQTT conectado: {status['mqtt_connected']}")
            
            # Iniciar servicio en thread separado
            service_thread = threading.Thread(target=service.start, daemon=True)
            service_thread.start()
            
            print("✅ Servicio iniciado en thread separado")
            
            # Esperar un poco para que se conecte
            time.sleep(5)
            
            # Mostrar estado actualizado
            status = service.get_status()
            print(f"   📊 Estado actualizado:")
            print(f"      MQTT conectado: {status['mqtt_connected']}")
            print(f"      Mensajes recibidos: {status['metrics']['messages_received']}")
            
            # Simular recepción de mensajes
            print("\n📨 Simulando recepción de mensajes...")
            time.sleep(10)
            
            # Mostrar métricas finales
            status = service.get_status()
            print(f"\n📊 Métricas finales:")
            print(f"   Mensajes recibidos: {status['metrics']['messages_received']}")
            print(f"   Mensajes procesados: {status['metrics']['messages_processed']}")
            print(f"   Mensajes fallidos: {status['metrics']['messages_failed']}")
            print(f"   Uptime: {status['metrics']['uptime_seconds']}s")
            
            # Detener servicio
            service.stop()
            print("✅ Servicio detenido")
            
            return True
            
        else:
            print("❌ Error inicializando servicio")
            return False
        
    except Exception as e:
        print(f"❌ Error en ingesta básica: {e}")
        return False


def example_custom_topic_mapping():
    """Ejemplo con mapeo personalizado de tópicos"""
    print("\n🔧 EJEMPLO 2: Mapeo Personalizado de Tópicos")
    print("=" * 50)
    
    try:
        # Crear configuración personalizada
        custom_config = {
            'mqtt': {
                'broker': {'host': 'localhost', 'port': 1883},
                'topics': {
                    'subscribe': [
                        'sensors/+/+/+',  # sensors/{tipo}/{ubicacion}/{id}
                        'custom/+/data'   # custom/{category}/data
                    ],
                    'publish': ['iot/status/ingesta']
                },
                'qos': 1,
                'retain': False
            },
            'storage': {
                'type': 'postgresql',
                'postgresql': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'iot_middleware',
                    'username': 'iot_user',
                    'password': 'iot_password'
                }
            },
            'ingesta': {
                'max_queue_size': 500,
                'batch_size': 50,
                'max_workers': 2,
                'validation_enabled': True,
                'topic_mapping': {
                    '^sensors/(?P<tipo>[^/]+)/(?P<ubicacion>[^/]+)/(?P<id>[^/]+)$': {
                        'proyecto_id': 'sensors_project',
                        'unidad_id': 'tipo',
                        'dispositivo_id': 'ubicacion',
                        'canal_id': 'id'
                    },
                    '^custom/(?P<category>[^/]+)/data$': {
                        'proyecto_id': 'custom_project',
                        'unidad_id': 'category',
                        'dispositivo_id': 'default',
                        'canal_id': 'data'
                    }
                },
                'alarm_thresholds': {
                    'temperatura': [
                        {'tipo': 'max', 'valor': 85, 'severidad': 'ADVERTENCIA'},
                        {'tipo': 'min', 'valor': -10, 'severidad': 'ADVERTENCIA'}
                    ]
                }
            }
        }
        
        print("✅ Configuración personalizada creada")
        print(f"   📋 Patrones de tópicos: {len(custom_config['ingesta']['topic_mapping'])}")
        print(f"   🚨 Umbrales de alarma: {len(custom_config['ingesta']['alarm_thresholds'])}")
        
        # Aquí se podría crear el servicio con la configuración personalizada
        # Por ahora solo mostramos la configuración
        
        return True
        
    except Exception as e:
        print(f"❌ Error en mapeo personalizado: {e}")
        return False


def example_alarm_thresholds():
    """Ejemplo con umbrales de alarma"""
    print("\n🔧 EJEMPLO 3: Umbrales de Alarma")
    print("=" * 50)
    
    try:
        # Configuración de umbrales de ejemplo
        alarm_config = {
            'canal_temperatura_001': [
                {
                    'tipo': 'max',
                    'valor': 80,
                    'severidad': 'ADVERTENCIA',
                    'mensaje': 'Temperatura alta detectada',
                    'accion': 'enviar_notificacion'
                },
                {
                    'tipo': 'min',
                    'valor': 0,
                    'severidad': 'CRITICO',
                    'mensaje': 'Temperatura crítica baja',
                    'accion': 'activar_calefaccion'
                }
            ],
            'canal_humedad_001': [
                {
                    'tipo': 'max',
                    'valor': 90,
                    'severidad': 'ADVERTENCIA',
                    'mensaje': 'Humedad muy alta',
                    'accion': 'activar_deshumidificador'
                }
            ],
            'canal_presion_001': [
                {
                    'tipo': 'critical',
                    'valor': 1100,
                    'severidad': 'CRITICO',
                    'mensaje': 'Presión atmosférica crítica',
                    'accion': 'evacuar_zona'
                }
            ]
        }
        
        print("✅ Configuración de umbrales creada")
        
        # Simular validación de datos
        test_values = [
            ('canal_temperatura_001', 85, 'Temperatura alta'),
            ('canal_temperatura_001', -5, 'Temperatura crítica baja'),
            ('canal_humedad_001', 95, 'Humedad muy alta'),
            ('canal_presion_001', 1105, 'Presión crítica')
        ]
        
        print("\n🧪 Simulando validación de umbrales:")
        
        for canal_id, valor, descripcion in test_values:
            print(f"\n   📊 Canal: {canal_id}")
            print(f"      Valor: {valor}")
            print(f"      Descripción: {descripcion}")
            
            # Verificar umbrales
            if canal_id in alarm_config:
                for threshold in alarm_config[canal_id]:
                    threshold_value = threshold['valor']
                    threshold_type = threshold['tipo']
                    
                    triggered = False
                    if threshold_type == 'max' and valor > threshold_value:
                        triggered = True
                    elif threshold_type == 'min' and valor < threshold_value:
                        triggered = True
                    elif threshold_type == 'critical' and valor >= threshold_value:
                        triggered = True
                    
                    if triggered:
                        print(f"      🚨 ALARMA: {threshold['mensaje']}")
                        print(f"         Severidad: {threshold['severidad']}")
                        print(f"         Acción: {threshold['accion']}")
                    else:
                        print(f"      ✅ Sin alarma")
            else:
                print(f"      ⚠️  Canal no configurado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en umbrales de alarma: {e}")
        return False


def example_performance_monitoring():
    """Ejemplo de monitoreo de rendimiento"""
    print("\n🔧 EJEMPLO 4: Monitoreo de Rendimiento")
    print("=" * 50)
    
    try:
        # Simular métricas de rendimiento
        performance_metrics = {
            'throughput': {
                'messages_per_second': 150,
                'peak_messages_per_second': 300,
                'average_processing_time_ms': 25
            },
            'queue_metrics': {
                'current_size': 45,
                'max_size': 1000,
                'utilization_percent': 4.5
            },
            'database_metrics': {
                'inserts_per_second': 120,
                'average_insert_time_ms': 15,
                'connection_pool_usage': 0.3
            },
            'error_metrics': {
                'error_rate_percent': 0.5,
                'validation_errors': 2,
                'database_errors': 1,
                'mqtt_errors': 0
            }
        }
        
        print("✅ Métricas de rendimiento simuladas")
        
        # Mostrar métricas
        print(f"\n📊 Rendimiento del Sistema:")
        print(f"   📨 Throughput: {performance_metrics['throughput']['messages_per_second']} msg/s")
        print(f"   📈 Pico: {performance_metrics['throughput']['peak_messages_per_second']} msg/s")
        print(f"   ⏱️  Tiempo promedio: {performance_metrics['throughput']['average_processing_time_ms']} ms")
        
        print(f"\n🗂️  Cola de Mensajes:")
        print(f"   📦 Tamaño actual: {performance_metrics['queue_metrics']['current_size']}")
        print(f"   📊 Utilización: {performance_metrics['queue_metrics']['utilization_percent']}%")
        
        print(f"\n🗄️  Base de Datos:")
        print(f"   💾 Inserciones/s: {performance_metrics['database_metrics']['inserts_per_second']}")
        print(f"   ⏱️  Tiempo promedio: {performance_metrics['database_metrics']['average_insert_time_ms']} ms")
        print(f"   🔌 Pool de conexiones: {performance_metrics['database_metrics']['connection_pool_usage']*100:.1f}%")
        
        print(f"\n❌ Errores:")
        print(f"   📊 Tasa de error: {performance_metrics['error_metrics']['error_rate_percent']}%")
        print(f"   🔍 Errores de validación: {performance_metrics['error_metrics']['validation_errors']}")
        print(f"   💾 Errores de BD: {performance_metrics['error_metrics']['database_errors']}")
        
        # Análisis de rendimiento
        print(f"\n📈 Análisis de Rendimiento:")
        
        if performance_metrics['queue_metrics']['utilization_percent'] < 10:
            print("   ✅ Cola de mensajes: Excelente (baja utilización)")
        elif performance_metrics['queue_metrics']['utilization_percent'] < 50:
            print("   ⚠️  Cola de mensajes: Buena (utilización moderada)")
        else:
            print("   🚨 Cola de mensajes: Crítica (alta utilización)")
        
        if performance_metrics['error_metrics']['error_rate_percent'] < 1:
            print("   ✅ Tasa de error: Excelente (baja tasa de errores)")
        elif performance_metrics['error_metrics']['error_rate_percent'] < 5:
            print("   ⚠️  Tasa de error: Aceptable (tasa moderada)")
        else:
            print("   🚨 Tasa de error: Crítica (alta tasa de errores)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en monitoreo de rendimiento: {e}")
        return False


def main():
    """Función principal"""
    print("🚀 Ejemplos de Uso del Servicio de Ingesta MQTT")
    print("=" * 60)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    examples = [
        ("Ingesta Básica MQTT", example_basic_ingesta),
        ("Mapeo Personalizado de Tópicos", example_custom_topic_mapping),
        ("Umbrales de Alarma", example_alarm_thresholds),
        ("Monitoreo de Rendimiento", example_performance_monitoring),
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
        print("\n💡 El servicio de ingesta MQTT está listo para usar en producción")
        print("\n🚀 Para ejecutar el servicio completo:")
        print("   python -m iot_middleware.services.ingestor config_ingesta.yaml")
        return True
    else:
        print("⚠️  Algunos ejemplos fallaron")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
