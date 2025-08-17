#!/usr/bin/env python3
"""
Demostración Rápida - IoT Middleware
====================================

Script de demostración rápida para probar la funcionalidad básica
del sistema multi-protocolo.
"""

import sys
import os
import time
from datetime import datetime

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from iot_middleware.demo import DemoManager, DemoConfig


def demo_rapida_mqtt_http():
    """Demostración rápida con MQTT y HTTP"""
    print("🚀 DEMOSTRACIÓN RÁPIDA - MQTT + HTTP")
    print("=" * 50)
    
    config = DemoConfig(
        name="Demo Rápida MQTT+HTTP",
        duration_minutes=3,
        enable_protocols=["mqtt", "http"],
        data_interval=1.0,
        data_count_per_protocol=20,
        enable_pipeline=True,
        enable_postgresql=False,  # Sin BD para demo rápida
        enable_influxdb=False,
        output_directory="demo_rapida_output",
        generate_reports=True,
        real_time_monitoring=True
    )
    
    ejecutar_demo_rapida(config)


def demo_rapida_todos_protocolos():
    """Demostración rápida con todos los protocolos"""
    print("🚀 DEMOSTRACIÓN RÁPIDA - TODOS LOS PROTOCOLOS")
    print("=" * 50)
    
    config = DemoConfig(
        name="Demo Rápida Todos Protocolos",
        duration_minutes=5,
        enable_protocols=["mqtt", "http", "ble", "lora", "midi", "modbus", "zigbee"],
        data_interval=0.5,  # Más rápido para demo
        data_count_per_protocol=15,
        enable_pipeline=True,
        enable_postgresql=False,
        enable_influxdb=False,
        output_directory="demo_rapida_output",
        generate_reports=True,
        real_time_monitoring=True
    )
    
    ejecutar_demo_rapida(config)


def demo_rapida_solo_simulacion():
    """Demostración rápida solo con simulación (sin pipeline)"""
    print("🚀 DEMOSTRACIÓN RÁPIDA - SOLO SIMULACIÓN")
    print("=" * 50)
    
    config = DemoConfig(
        name="Demo Rápida Solo Simulación",
        duration_minutes=2,
        enable_protocols=["mqtt", "http", "ble"],
        data_interval=0.8,
        data_count_per_protocol=25,
        enable_pipeline=False,  # Sin pipeline
        enable_postgresql=False,
        enable_influxdb=False,
        output_directory="demo_rapida_output",
        generate_reports=True,
        real_time_monitoring=True
    )
    
    ejecutar_demo_rapida(config)


def ejecutar_demo_rapida(config: DemoConfig):
    """Ejecutar demostración rápida"""
    print(f"Configuración:")
    print(f"  Protocolos: {', '.join(config.enabled_protocols)}")
    print(f"  Duración: {config.duration_minutes} minutos")
    print(f"  Intervalo: {config.data_interval} segundos")
    print(f"  Datos por protocolo: {config.data_count_per_protocol}")
    print(f"  Pipeline: {'Sí' if config.enable_pipeline else 'No'}")
    print(f"  Salida: {config.output_directory}")
    print()
    
    try:
        # Crear gestor de demostración
        demo_manager = DemoManager(config)
        
        # Inicializar
        print("📋 Inicializando...")
        if not demo_manager.initialize():
            print("❌ Error inicializando")
            return
        print("✅ Inicializado correctamente")
        
        # Iniciar
        print("🚀 Iniciando...")
        if not demo_manager.start():
            print("❌ Error iniciando")
            return
        print("✅ Iniciado correctamente")
        
        # Monitoreo en tiempo real
        print(f"\n⏱️  Ejecutando por {config.duration_minutes} minutos...")
        print("📊 Monitoreo en tiempo real:")
        
        start_time = time.time()
        last_status_time = start_time
        
        while demo_manager.running:
            time.sleep(2)  # Actualizar cada 2 segundos
            
            # Mostrar estado cada 30 segundos
            current_time = time.time()
            if current_time - last_status_time >= 30:
                mostrar_estado_rapido(demo_manager)
                last_status_time = current_time
                
                # Verificar si ha terminado
                elapsed = current_time - start_time
                if elapsed >= config.duration_minutes * 60:
                    break
        
        # Detener
        print("\n🛑 Deteniendo...")
        demo_manager.stop()
        print("✅ Detenido correctamente")
        
        # Estado final
        mostrar_estado_rapido(demo_manager)
        
        # Mostrar archivos generados
        if config.generate_reports:
            print(f"\n📁 Informes generados en: {config.output_directory}")
            try:
                from iot_middleware.demo.report_generator import ReportGenerator
                report_gen = ReportGenerator(config.output_directory)
                report_files = report_gen.get_report_files()
                
                if report_files:
                    print("📄 Archivos generados:")
                    for report_type, filepath in report_files.items():
                        filename = os.path.basename(filepath)
                        print(f"  📊 {report_type}: {filename}")
                else:
                    print("❌ No se encontraron archivos de informe")
                    
            except Exception as e:
                print(f"⚠️  Error obteniendo archivos: {e}")
        
        print("\n🎉 Demostración completada exitosamente!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Detenido por usuario")
        if 'demo_manager' in locals():
            demo_manager.stop()
    except Exception as e:
        print(f"\n❌ Error en demostración: {e}")


def mostrar_estado_rapido(demo_manager: DemoManager):
    """Mostrar estado de forma rápida y concisa"""
    try:
        summary = demo_manager.get_summary()
        status = demo_manager.get_status()
        
        elapsed_minutes = status.get('elapsed_minutes', 0)
        
        print(f"\n⏱️  [{elapsed_minutes:.1f}min] "
              f"📊 {summary['total_data_generated']} generados, "
              f"{summary['total_data_processed']} procesados, "
              f"⚡ {summary['processing_rate']:.1f} msg/s")
        
        # Estado de protocolos
        protocol_status = []
        for protocol, protocol_info in status.get('protocols', {}).items():
            if protocol_info.get('running'):
                data_gen = protocol_info.get('data_generated', 0)
                data_total = protocol_info.get('data_count', 0)
                protocol_status.append(f"{protocol.upper()}:{data_gen}/{data_total}")
        
        if protocol_status:
            print(f"🔌 Protocolos: {', '.join(protocol_status)}")
            
    except Exception as e:
        print(f"⚠️  Error mostrando estado: {e}")


def main():
    """Función principal"""
    print("🎯 DEMOSTRACIÓN RÁPIDA - IoT MIDDLEWARE")
    print("=" * 50)
    print("Seleccione el tipo de demostración:")
    print("1. MQTT + HTTP (3 min)")
    print("2. Todos los protocolos (5 min)")
    print("3. Solo simulación (2 min)")
    print("4. Salir")
    
    while True:
        try:
            opcion = input("\nOpción [1-4]: ").strip()
            
            if opcion == "1":
                demo_rapida_mqtt_http()
                break
            elif opcion == "2":
                demo_rapida_todos_protocolos()
                break
            elif opcion == "3":
                demo_rapida_solo_simulacion()
                break
            elif opcion == "4":
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida. Por favor seleccione 1-4.")
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
