#!/usr/bin/env python3
"""
Script de Prueba - Generador de Informes
========================================

Este script prueba la funcionalidad del generador de informes
de forma independiente.
"""

import sys
import os
import json
from datetime import datetime

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_report_generator():
    """Probar el generador de informes"""
    try:
        from iot_middleware.demo import ReportGenerator
        
        print("✅ Módulo ReportGenerator importado correctamente")
        
        # Crear directorio de prueba
        test_dir = "test_reports_output"
        os.makedirs(test_dir, exist_ok=True)
        
        # Crear instancia del generador
        report_gen = ReportGenerator(test_dir)
        print(f"✅ ReportGenerator creado en: {test_dir}")
        
        # Datos de prueba
        test_data = {
            "demo_config": {
                "name": "Test Demo",
                "duration_minutes": 5,
                "enabled_protocols": ["mqtt", "http", "ble"],
                "data_interval": 2.0,
                "data_count_per_protocol": 30
            },
            "demo_metrics": {
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_data_generated": 90,
                "total_data_processed": 88,
                "total_data_persisted": 88,
                "errors": ["Error de conexión temporal"],
                "warnings": ["Datos fuera de rango"]
            },
            "protocol_metrics": {
                "mqtt": {
                    "data_generated": 30,
                    "data_processed": 29,
                    "last_data_time": datetime.now().isoformat(),
                    "device_count": 15,
                    "devices": ["mqtt_device_001", "mqtt_device_002"]
                },
                "http": {
                    "data_generated": 30,
                    "data_processed": 30,
                    "last_data_time": datetime.now().isoformat(),
                    "device_count": 12,
                    "devices": ["http_device_001", "http_device_002"]
                },
                "ble": {
                    "data_generated": 30,
                    "data_processed": 29,
                    "last_data_time": datetime.now().isoformat(),
                    "device_count": 18,
                    "devices": ["ble_device_001", "ble_device_002"]
                }
            },
            "pipeline_metrics": {
                "total_messages": 90,
                "processed_messages": 88,
                "failed_messages": 2,
                "postgresql_operations": 88,
                "influxdb_operations": 88,
                "processing_rate": 1.5,
                "error_rate": 2.2,
                "queue_size": 0
            }
        }
        
        # Generar informe
        print("📊 Generando informe de prueba...")
        report_path = report_gen.generate_demo_report(test_data)
        
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
        json_files = [f for f in os.listdir(os.path.join(test_dir, "reports")) if f.endswith('.json')]
        
        if json_files:
            json_file = os.path.join(test_dir, "reports", json_files[0])
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
        chart_files = [f for f in os.listdir(os.path.join(test_dir, "charts")) if f.endswith('.png')]
        
        if chart_files:
            print(f"✅ Gráficos generados: {len(chart_files)} archivos")
            for chart in chart_files:
                print(f"  📈 {chart}")
        else:
            print("❌ No se generaron gráficos")
            return False
        
        print("\n🎉 ¡Prueba del generador de informes completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🧪 PRUEBA DEL GENERADOR DE INFORMES")
    print("=" * 50)
    
    success = test_report_generator()
    
    if success:
        print("\n✅ Todas las pruebas pasaron correctamente")
        print("📁 Los informes se generaron en: test_reports_output/")
    else:
        print("\n❌ Algunas pruebas fallaron")
        sys.exit(1)

if __name__ == "__main__":
    main()
