#!/usr/bin/env python3
"""
Demostración Completa - IoT Middleware
======================================

Este script demuestra el flujo completo de datos desde la simulación
hasta la persistencia, incluyendo todos los protocolos implementados.
"""

import sys
import os
import time
import json
import argparse
from datetime import datetime

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from iot_middleware.demo import DemoManager, DemoConfig


def crear_configuracion_demo(args) -> DemoConfig:
    """Crear configuración de demostración basada en argumentos"""
    return DemoConfig(
        name=args.name,
        duration_minutes=args.duration,
        enable_protocols=args.protocols.split(',') if args.protocols else None,
        data_interval=args.interval,
        data_count_per_protocol=args.count,
        enable_pipeline=args.pipeline,
        enable_postgresql=args.postgresql,
        enable_influxdb=args.influxdb,
        output_directory=args.output,
        generate_reports=args.reports,
        real_time_monitoring=args.monitoring
    )


def mostrar_menu_interactivo():
    """Mostrar menú interactivo para configuración"""
    print("\n" + "="*60)
    print("CONFIGURACIÓN INTERACTIVA - DEMOSTRACIÓN IoT MIDDLEWARE")
    print("="*60)
    
    # Nombre de la demostración
    name = input("Nombre de la demostración [IoT Middleware Demo]: ").strip()
    if not name:
        name = "IoT Middleware Demo"
    
    # Duración
    while True:
        try:
            duration = input("Duración en minutos [10]: ").strip()
            duration = int(duration) if duration else 10
            if duration > 0:
                break
            print("La duración debe ser mayor a 0")
        except ValueError:
            print("Por favor ingrese un número válido")
    
    # Protocolos
    print("\nProtocolos disponibles:")
    protocols = ["mqtt", "http", "ble", "lora", "midi", "modbus", "zigbee"]
    for i, protocol in enumerate(protocols, 1):
        print(f"  {i}. {protocol.upper()}")
    
    while True:
        try:
            protocol_input = input("\nSeleccione protocolos (números separados por coma) [todos]: ").strip()
            if not protocol_input:
                selected_protocols = protocols
                break
            
            selected_indices = [int(x.strip()) - 1 for x in protocol_input.split(',')]
            if all(0 <= i < len(protocols) for i in selected_indices):
                selected_protocols = [protocols[i] for i in selected_indices]
                break
            print("Por favor seleccione números válidos")
        except ValueError:
            print("Por favor ingrese números válidos")
    
    # Intervalo de datos
    while True:
        try:
            interval = input("Intervalo entre datos en segundos [2.0]: ").strip()
            interval = float(interval) if interval else 2.0
            if interval > 0:
                break
            print("El intervalo debe ser mayor a 0")
        except ValueError:
            print("Por favor ingrese un número válido")
    
    # Cantidad de datos por protocolo
    while True:
        try:
            count = input("Cantidad de datos por protocolo [50]: ").strip()
            count = int(count) if count else 50
            if count > 0:
                break
            print("La cantidad debe ser mayor a 0")
        except ValueError:
            print("Por favor ingrese un número válido")
    
    # Pipeline
    pipeline = input("¿Habilitar pipeline de datos? [s/n]: ").strip().lower()
    pipeline = pipeline != 'n'
    
    # PostgreSQL
    postgresql = input("¿Habilitar PostgreSQL? [s/n]: ").strip().lower()
    postgresql = postgresql != 'n'
    
    # InfluxDB
    influxdb = input("¿Habilitar InfluxDB? [s/n]: ").strip().lower()
    influxdb = influxdb != 'n'
    
    # Directorio de salida
    output = input("Directorio de salida [demo_outputs]: ").strip()
    if not output:
        output = "demo_outputs"
    
    # Informes
    reports = input("¿Generar informes? [s/n]: ").strip().lower()
    reports = reports != 'n'
    
    # Monitoreo en tiempo real
    monitoring = input("¿Habilitar monitoreo en tiempo real? [s/n]: ").strip().lower()
    monitoring = monitoring != 'n'
    
    return DemoConfig(
        name=name,
        duration_minutes=duration,
        enable_protocols=selected_protocols,
        data_interval=interval,
        data_count_per_protocol=count,
        enable_pipeline=pipeline,
        enable_postgresql=postgresql,
        enable_influxdb=influxdb,
        output_directory=output,
        generate_reports=reports,
        real_time_monitoring=monitoring
    )


def mostrar_estado_demo(demo_manager: DemoManager):
    """Mostrar estado actual de la demostración"""
    try:
        status = demo_manager.get_status()
        summary = demo_manager.get_summary()
        
        print("\n" + "="*60)
        print("ESTADO ACTUAL DE LA DEMOSTRACIÓN")
        print("="*60)
        print(f"Nombre: {status['name']}")
        print(f"Estado: {'Ejecutándose' if status['running'] else 'Detenida'}")
        print(f"Tiempo transcurrido: {status['elapsed_minutes']:.1f} minutos")
        print(f"Datos generados: {status['total_data_generated']}")
        print(f"Datos procesados: {status['total_data_processed']}")
        
        if status['pipeline']:
            pipeline_status = status['pipeline']
            print(f"\nPipeline:")
            print(f"  Estado: {'Activo' if pipeline_status['running'] else 'Inactivo'}")
            print(f"  PostgreSQL: {'Conectado' if pipeline_status['postgresql_connected'] else 'Desconectado'}")
            print(f"  InfluxDB: {'Conectado' if pipeline_status['influxdb_connected'] else 'Desconectado'}")
            
            if pipeline_status['metrics']:
                metrics = pipeline_status['metrics']
                print(f"  Rate: {metrics['processing_rate']:.2f} msg/s")
                print(f"  Cola: {metrics['queue_size']}")
        
        print(f"\nProtocolos:")
        for protocol, protocol_status in status['protocols'].items():
            print(f"  {protocol.upper()}: {'Activo' if protocol_status['running'] else 'Inactivo'}")
            print(f"    Datos: {protocol_status['data_generated']}/{protocol_status['data_count']}")
            
    except Exception as e:
        print(f"Error obteniendo estado: {e}")


def mostrar_metricas_tiempo_real(demo_manager: DemoManager):
    """Mostrar métricas en tiempo real"""
    try:
        summary = demo_manager.get_summary()
        
        print("\n" + "="*60)
        print("MÉTRICAS EN TIEMPO REAL")
        print("="*60)
        print(f"Estado: {summary['status']}")
        print(f"Duración configurada: {summary['duration_minutes']} minutos")
        print(f"Protocolos habilitados: {summary['enabled_protocols']}")
        print(f"Datos generados: {summary['total_data_generated']}")
        print(f"Datos procesados: {summary['total_data_processed']}")
        print(f"Rate de procesamiento: {summary['processing_rate']:.2f} msg/s")
        print(f"Errores: {summary['error_count']}")
        print(f"Advertencias: {summary['warning_count']}")
        
    except Exception as e:
        print(f"Error obteniendo métricas: {e}")


def ejecutar_demo_interactiva():
    """Ejecutar demostración en modo interactivo"""
    print("\n" + "="*60)
    print("DEMOSTRACIÓN INTERACTIVA - IoT MIDDLEWARE")
    print("="*60)
    
    # Configuración interactiva
    config = mostrar_menu_interactivo()
    
    # Mostrar resumen de configuración
    print("\n" + "="*60)
    print("RESUMEN DE CONFIGURACIÓN")
    print("="*60)
    print(f"Nombre: {config.name}")
    print(f"Duración: {config.duration_minutes} minutos")
    print(f"Protocolos: {', '.join(config.enabled_protocols)}")
    print(f"Intervalo: {config.data_interval} segundos")
    print(f"Datos por protocolo: {config.data_count_per_protocol}")
    print(f"Pipeline: {'Habilitado' if config.enable_pipeline else 'Deshabilitado'}")
    print(f"PostgreSQL: {'Habilitado' if config.enable_postgresql else 'Deshabilitado'}")
    print(f"InfluxDB: {'Habilitado' if config.enable_influxdb else 'Deshabilitado'}")
    print(f"Directorio salida: {config.output_directory}")
    print(f"Informes: {'Habilitados' if config.generate_reports else 'Deshabilitados'}")
    print(f"Monitoreo: {'Habilitado' if config.real_time_monitoring else 'Deshabilitado'}")
    
    # Confirmar inicio
    confirm = input("\n¿Iniciar demostración? [s/n]: ").strip().lower()
    if confirm != 's':
        print("Demostración cancelada")
        return
    
    # Crear y ejecutar demostración
    ejecutar_demo(config)


def ejecutar_demo(config: DemoConfig):
    """Ejecutar demostración con configuración específica"""
    print(f"\nIniciando demostración: {config.name}")
    
    try:
        # Crear gestor de demostración
        demo_manager = DemoManager(config)
        
        # Inicializar
        if not demo_manager.initialize():
            print("Error inicializando demostración")
            return
        
        # Iniciar
        if not demo_manager.start():
            print("Error iniciando demostración")
            return
        
        print(f"Demostración iniciada. Duración: {config.duration_minutes} minutos")
        print("Presiona Ctrl+C para detener manualmente")
        
        # Bucle principal de monitoreo
        start_time = time.time()
        while demo_manager.running:
            try:
                time.sleep(10)  # Actualizar cada 10 segundos
                
                # Mostrar estado cada minuto
                elapsed = time.time() - start_time
                if elapsed >= 60:
                    mostrar_estado_demo(demo_manager)
                    start_time = time.time()
                    
            except KeyboardInterrupt:
                print("\nDeteniendo demostración...")
                demo_manager.stop()
                break
        
        # Mostrar estado final
        mostrar_estado_demo(demo_manager)
        
        # Mostrar archivos generados
        if config.generate_reports:
            print(f"\nInformes generados en: {config.output_directory}")
            try:
                from iot_middleware.demo.report_generator import ReportGenerator
                report_gen = ReportGenerator(config.output_directory)
                report_files = report_gen.get_report_files()
                
                if report_files:
                    print("\nArchivos generados:")
                    for report_type, filepath in report_files.items():
                        print(f"  {report_type}: {os.path.basename(filepath)}")
                else:
                    print("No se encontraron archivos de informe")
                    
            except Exception as e:
                print(f"Error obteniendo archivos de informe: {e}")
        
        print("\nDemostración completada")
        
    except Exception as e:
        print(f"Error en demostración: {e}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Demostración completa del IoT Middleware",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Demostración interactiva
  python demo_completa.py

  # Demostración rápida con MQTT y HTTP
  python demo_completa.py --protocols mqtt,http --duration 5 --count 20

  # Demostración completa de todos los protocolos
  python demo_completa.py --protocols mqtt,http,ble,lora,midi,modbus,zigbee --duration 15

  # Demostración sin pipeline (solo simulación)
  python demo_completa.py --no-pipeline --duration 10
        """
    )
    
    parser.add_argument('--name', default='IoT Middleware Demo',
                       help='Nombre de la demostración')
    parser.add_argument('--duration', type=int, default=10,
                       help='Duración en minutos (0 = sin límite)')
    parser.add_argument('--protocols', 
                       help='Protocolos a habilitar (separados por coma)')
    parser.add_argument('--interval', type=float, default=2.0,
                       help='Intervalo entre datos en segundos')
    parser.add_argument('--count', type=int, default=50,
                       help='Cantidad de datos por protocolo')
    parser.add_argument('--output', default='demo_outputs',
                       help='Directorio de salida')
    parser.add_argument('--no-pipeline', action='store_true',
                       help='Deshabilitar pipeline de datos')
    parser.add_argument('--no-postgresql', action='store_true',
                       help='Deshabilitar PostgreSQL')
    parser.add_argument('--no-influxdb', action='store_true',
                       help='Deshabilitar InfluxDB')
    parser.add_argument('--no-reports', action='store_true',
                       help='Deshabilitar generación de informes')
    parser.add_argument('--no-monitoring', action='store_true',
                       help='Deshabilitar monitoreo en tiempo real')
    
    args = parser.parse_args()
    
    # Crear configuración
    config = DemoConfig(
        name=args.name,
        duration_minutes=args.duration,
        enable_protocols=args.protocols.split(',') if args.protocols else None,
        data_interval=args.interval,
        data_count_per_protocol=args.count,
        enable_pipeline=not args.no_pipeline,
        enable_postgresql=not args.no_postgresql,
        enable_influxdb=not args.no_influxdb,
        output_directory=args.output,
        generate_reports=not args.no_reports,
        real_time_monitoring=not args.no_monitoring
    )
    
    # Si no se especificaron argumentos, usar modo interactivo
    if len(sys.argv) == 1:
        ejecutar_demo_interactiva()
    else:
        ejecutar_demo(config)


if __name__ == "__main__":
    main()
