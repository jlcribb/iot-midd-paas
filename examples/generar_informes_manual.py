#!/usr/bin/env python3
"""
Script de Generación Manual de Informes
=======================================

Este script genera informes manualmente usando los datos
de la demostración completada.
"""

import sys
import os
import json
from datetime import datetime

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def generar_informes_manuales():
    """Generar informes manualmente con datos de la demostración"""
    try:
        from iot_middleware.demo import ReportGenerator
        
        print("✅ Módulo ReportGenerator importado correctamente")
        
        # Crear directorio de salida
        output_dir = "informes_manuales"
        os.makedirs(output_dir, exist_ok=True)
        
        # Crear instancia del generador
        report_gen = ReportGenerator(output_dir)
        print(f"✅ ReportGenerator creado en: {output_dir}")
        
        # Datos de la demostración completada
        demo_data = {
            "demo_config": {
                "name": "IoT Middleware Demo Completa",
                "duration_minutes": 13.3,
                "enabled_protocols": ["mqtt", "http", "ble", "lora", "midi", "modbus", "zigbee"],
                "data_interval": 1.5,
                "data_count_per_protocol": 50
            },
            "demo_metrics": {
                "start_time": "2025-08-16T22:40:27",
                "end_time": "2025-08-16T22:53:42",
                "total_data_generated": 350,
                "total_data_processed": 350,
                "total_data_persisted": 0,  # Simulado
                "errors": [],
                "warnings": ["PostgreSQL y InfluxDB desconectados (modo simulación)"]
            },
            "protocol_metrics": {
                "mqtt": {
                    "data_generated": 50,
                    "data_processed": 50,
                    "last_data_time": "2025-08-16T22:53:42",
                    "device_count": 19,
                    "devices": ["mqtt_sensor_001", "mqtt_actuator_002", "mqtt_gateway_003"]
                },
                "http": {
                    "data_generated": 50,
                    "data_processed": 50,
                    "last_data_time": "2025-08-16T22:53:42",
                    "device_count": 15,
                    "devices": ["http_device_001", "http_sensor_002", "http_controller_003"]
                },
                "ble": {
                    "data_generated": 50,
                    "data_processed": 50,
                    "last_data_time": "2025-08-16T22:53:42",
                    "device_count": 15,
                    "devices": ["ble_tag_001", "ble_sensor_002", "ble_beacon_003"]
                },
                "lora": {
                    "data_generated": 50,
                    "data_processed": 50,
                    "last_data_time": "2025-08-16T22:53:42",
                    "device_count": 10,
                    "devices": ["lora_node_001", "lora_gateway_002", "lora_sensor_003"]
                },
                "midi": {
                    "data_generated": 50,
                    "data_processed": 50,
                    "last_data_time": "2025-08-16T22:53:42",
                    "device_count": 16,
                    "devices": ["midi_keyboard_001", "midi_drum_002", "midi_synth_003"]
                },
                "modbus": {
                    "data_generated": 50,
                    "data_processed": 50,
                    "last_data_time": "2025-08-16T22:53:42",
                    "device_count": 10,
                    "devices": ["modbus_plc_001", "modbus_sensor_002", "modbus_actuator_003"]
                },
                "zigbee": {
                    "data_generated": 50,
                    "data_processed": 50,
                    "last_data_time": "2025-08-16T22:53:42",
                    "device_count": 6,
                    "devices": ["zigbee_bulb_001", "zigbee_switch_002", "zigbee_sensor_003"]
                }
            },
            "pipeline_metrics": {
                "total_messages": 350,
                "processed_messages": 350,
                "failed_messages": 0,
                "postgresql_operations": 0,  # Simulado
                "influxdb_operations": 0,    # Simulado
                "processing_rate": 0.47,
                "error_rate": 0.0,
                "queue_size": 0
            }
        }
        
        # Generar informe
        print("📊 Generando informe de la demostración completa...")
        report_path = report_gen.generate_demo_report(demo_data)
        
        if report_path:
            print(f"✅ Informe generado: {report_path}")
        else:
            print("❌ Error generando informe")
            return False
        
        # Verificar archivos generados
        print("\n📁 Verificando archivos generados...")
        report_files = report_gen.get_report_files()
        
        if report_files:
            print("✅ Archivos de informe encontrados:")
            for report_type, filepath in report_files.items():
                filename = os.path.basename(filepath)
                print(f"  📄 {report_type}: {filename}")
        else:
            print("❌ No se encontraron archivos de informe")
            return False
        
        # Verificar contenido del informe JSON
        print("\n📋 Verificando contenido del informe...")
        json_files = [f for f in os.listdir(os.path.join(output_dir, "reports")) if f.endswith('.json')]
        
        if json_files:
            json_file = os.path.join(output_dir, "reports", json_files[0])
            with open(json_file, 'r', encoding='utf-8') as f:
                report_content = json.load(f)
            
            print(f"✅ Informe JSON leído: {len(report_content)} secciones")
            print(f"  - Configuración: {len(report_content.get('demo_config', {}))} campos")
            print(f"  - Métricas: {len(report_content.get('demo_metrics', {}))} campos")
            print(f"  - Protocolos: {len(report_content.get('protocol_metrics', {}))} protocolos")
            print(f"  - Pipeline: {len(report_content.get('pipeline_metrics', {}))} métricas")
        else:
            print("❌ No se encontraron archivos JSON")
            return False
        
        # Verificar gráficos
        print("\n📊 Verificando gráficos generados...")
        chart_files = [f for f in os.listdir(os.path.join(output_dir, "charts")) if f.endswith('.png')]
        
        if chart_files:
            print(f"✅ Gráficos generados: {len(chart_files)} archivos")
            for chart in chart_files:
                print(f"  📈 {chart}")
        else:
            print("❌ No se generaron gráficos")
            return False
        
        print("\n🎉 ¡Informes generados exitosamente!")
        print(f"📁 Los informes se encuentran en: {output_dir}/")
        return True
        
    except Exception as e:
        print(f"❌ Error en la generación de informes: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("📊 GENERACIÓN MANUAL DE INFORMES")
    print("=" * 50)
    print("Generando informes de la demostración completa...")
    
    success = generar_informes_manuales()
    
    if success:
        print("\n✅ Informes generados correctamente")
        print("📁 Los informes se encuentran en: informes_manuales/")
    else:
        print("\n❌ Error generando informes")
        sys.exit(1)

if __name__ == "__main__":
    main()
