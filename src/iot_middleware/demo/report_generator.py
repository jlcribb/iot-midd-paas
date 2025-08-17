"""
Generador de Informes - IoT Middleware
======================================

Este módulo genera informes detallados de la demostración en formato JSON y PDF,
incluyendo métricas, análisis de datos y visualizaciones.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np

# Configurar matplotlib para no mostrar ventanas
plt.switch_backend('Agg')


class ReportGenerator:
    """Generador de informes de demostración"""
    
    def __init__(self, output_directory: str):
        self.output_directory = output_directory
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Crear directorio de informes
        self.reports_dir = os.path.join(output_directory, "reports")
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Crear directorio de gráficos
        self.charts_dir = os.path.join(output_directory, "charts")
        os.makedirs(self.charts_dir, exist_ok=True)
        
    def generate_demo_report(self, report_data: Dict[str, Any]) -> str:
        """Generar informe completo de la demostración"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Generar informe JSON
            json_report_path = self._generate_json_report(report_data, timestamp)
            
            # Generar informe PDF
            pdf_report_path = self._generate_pdf_report(report_data, timestamp)
            
            # Generar gráficos
            self._generate_charts(report_data, timestamp)
            
            self.logger.info(f"Informe generado: {json_report_path}, {pdf_report_path}")
            return json_report_path
            
        except Exception as e:
            self.logger.error(f"Error generando informe: {e}")
            return ""
            
    def _generate_json_report(self, report_data: Dict[str, Any], timestamp: str) -> str:
        """Generar informe en formato JSON"""
        try:
            # Agregar metadatos del informe
            report_data["report_metadata"] = {
                "generated_at": datetime.now().isoformat(),
                "report_type": "iot_middleware_demo",
                "version": "1.0"
            }
            
            # Generar nombre del archivo
            filename = f"demo_report_{timestamp}.json"
            filepath = os.path.join(self.reports_dir, filename)
            
            # Escribir archivo JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
                
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error generando informe JSON: {e}")
            return ""
            
    def _generate_pdf_report(self, report_data: Dict[str, Any], timestamp: str) -> str:
        """Generar informe en formato PDF"""
        try:
            # Por ahora, solo creamos un archivo de texto que simule PDF
            # En una implementación real, usarías una librería como reportlab o fpdf
            
            filename = f"demo_report_{timestamp}.txt"
            filepath = os.path.join(self.reports_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self._format_text_report(report_data))
                
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error generando informe PDF: {e}")
            return ""
            
    def _format_text_report(self, report_data: Dict[str, Any]) -> str:
        """Formatear informe como texto plano"""
        lines = []
        
        # Encabezado
        lines.append("=" * 80)
        lines.append("INFORME DE DEMOSTRACIÓN - IoT MIDDLEWARE")
        lines.append("=" * 80)
        lines.append("")
        
        # Configuración de la demostración
        lines.append("CONFIGURACIÓN DE LA DEMOSTRACIÓN")
        lines.append("-" * 40)
        config = report_data.get("demo_config", {})
        lines.append(f"Nombre: {config.get('name', 'N/A')}")
        lines.append(f"Duración: {config.get('duration_minutes', 0)} minutos")
        lines.append(f"Protocolos habilitados: {', '.join(config.get('enabled_protocols', []))}")
        lines.append(f"Intervalo de datos: {config.get('data_interval', 0)} segundos")
        lines.append(f"Datos por protocolo: {config.get('data_count_per_protocol', 0)}")
        lines.append("")
        
        # Métricas generales
        lines.append("MÉTRICAS GENERALES")
        lines.append("-" * 40)
        metrics = report_data.get("demo_metrics", {})
        lines.append(f"Total de datos generados: {metrics.get('total_data_generated', 0)}")
        lines.append(f"Total de datos procesados: {metrics.get('total_data_processed', 0)}")
        lines.append(f"Total de datos persistidos: {metrics.get('total_data_persisted', 0)}")
        lines.append(f"Errores: {len(metrics.get('errors', []))}")
        lines.append(f"Advertencias: {len(metrics.get('warnings', []))}")
        lines.append("")
        
        # Métricas por protocolo
        lines.append("MÉTRICAS POR PROTOCOLO")
        lines.append("-" * 40)
        protocol_metrics = report_data.get("protocol_metrics", {})
        for protocol, metrics in protocol_metrics.items():
            lines.append(f"{protocol.upper()}:")
            lines.append(f"  Datos generados: {metrics.get('data_generated', 0)}")
            lines.append(f"  Datos procesados: {metrics.get('data_processed', 0)}")
            lines.append(f"  Dispositivos únicos: {metrics.get('device_count', 0)}")
            lines.append(f"  Último dato: {metrics.get('last_data_time', 'N/A')}")
            lines.append("")
            
        # Métricas del pipeline
        lines.append("MÉTRICAS DEL PIPELINE")
        lines.append("-" * 40)
        pipeline_metrics = report_data.get("pipeline_metrics")
        if pipeline_metrics:
            lines.append(f"Rate de procesamiento: {pipeline_metrics.get('processing_rate', 0):.2f} msg/s")
            lines.append(f"Operaciones PostgreSQL: {pipeline_metrics.get('postgresql_operations', 0)}")
            lines.append(f"Operaciones InfluxDB: {pipeline_metrics.get('influxdb_operations', 0)}")
            lines.append(f"Tamaño de cola: {pipeline_metrics.get('queue_size', 0)}")
        else:
            lines.append("Pipeline no disponible")
        lines.append("")
        
        # Errores y advertencias
        if metrics.get('errors'):
            lines.append("ERRORES ENCONTRADOS")
            lines.append("-" * 40)
            for error in metrics.get('errors', []):
                lines.append(f"• {error}")
            lines.append("")
            
        if metrics.get('warnings'):
            lines.append("ADVERTENCIAS")
            lines.append("-" * 40)
            for warning in metrics.get('warnings', []):
                lines.append(f"• {warning}")
            lines.append("")
            
        # Resumen ejecutivo
        lines.append("RESUMEN EJECUTIVO")
        lines.append("-" * 40)
        total_protocols = len(config.get('enabled_protocols', []))
        total_data = metrics.get('total_data_generated', 0)
        total_processed = metrics.get('total_data_processed', 0)
        
        if total_data > 0:
            success_rate = (total_processed / total_data) * 100
        else:
            success_rate = 0
            
        lines.append(f"La demostración procesó exitosamente {total_processed} de {total_data} datos")
        lines.append(f"generados por {total_protocols} protocolos diferentes.")
        lines.append(f"Tasa de éxito: {success_rate:.1f}%")
        lines.append("")
        
        # Pie de página
        lines.append("=" * 80)
        lines.append(f"Informe generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        
        return "\n".join(lines)
        
    def _generate_charts(self, report_data: Dict[str, Any], timestamp: str):
        """Generar gráficos de la demostración"""
        try:
            # Gráfico de datos por protocolo
            self._generate_protocol_chart(report_data, timestamp)
            
            # Gráfico de tasa de procesamiento
            self._generate_processing_chart(report_data, timestamp)
            
            # Gráfico de dispositivos por protocolo
            self._generate_devices_chart(report_data, timestamp)
            
        except Exception as e:
            self.logger.error(f"Error generando gráficos: {e}")
            
    def _generate_protocol_chart(self, report_data: Dict[str, Any], timestamp: str):
        """Generar gráfico de datos por protocolo"""
        try:
            protocol_metrics = report_data.get("protocol_metrics", {})
            
            if not protocol_metrics:
                return
                
            protocols = list(protocol_metrics.keys())
            data_generated = [protocol_metrics[p].get("data_generated", 0) for p in protocols]
            data_processed = [protocol_metrics[p].get("data_processed", 0) for p in protocols]
            
            # Crear gráfico
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Gráfico de barras para datos generados
            bars1 = ax1.bar(protocols, data_generated, color='skyblue', alpha=0.7)
            ax1.set_title('Datos Generados por Protocolo', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Cantidad de Datos')
            ax1.tick_params(axis='x', rotation=45)
            
            # Agregar valores en las barras
            for bar, value in zip(bars1, data_generated):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{value}', ha='center', va='bottom')
            
            # Gráfico de barras para datos procesados
            bars2 = ax2.bar(protocols, data_processed, color='lightgreen', alpha=0.7)
            ax2.set_title('Datos Procesados por Protocolo', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Cantidad de Datos')
            ax2.tick_params(axis='x', rotation=45)
            
            # Agregar valores en las barras
            for bar, value in zip(bars2, data_processed):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{value}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Guardar gráfico
            filename = f"protocol_data_chart_{timestamp}.png"
            filepath = os.path.join(self.charts_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Error generando gráfico de protocolos: {e}")
            
    def _generate_processing_chart(self, report_data: Dict[str, Any], timestamp: str):
        """Generar gráfico de tasa de procesamiento"""
        try:
            pipeline_metrics = report_data.get("pipeline_metrics")
            
            if not pipeline_metrics:
                return
                
            # Crear gráfico de métricas del pipeline
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # Métricas principales
            metrics = [
                pipeline_metrics.get("total_messages", 0),
                pipeline_metrics.get("processed_messages", 0),
                pipeline_metrics.get("failed_messages", 0),
                pipeline_metrics.get("queue_size", 0)
            ]
            
            labels = ["Total", "Procesados", "Fallidos", "En Cola"]
            colors = ["lightblue", "lightgreen", "lightcoral", "lightyellow"]
            
            ax1.pie(metrics, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.set_title('Distribución de Mensajes', fontsize=12, fontweight='bold')
            
            # Rate de procesamiento
            processing_rate = pipeline_metrics.get("processing_rate", 0)
            ax2.bar(['Rate'], [processing_rate], color='orange', alpha=0.7)
            ax2.set_title('Tasa de Procesamiento', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Mensajes por Segundo')
            ax2.text(0, processing_rate + 0.01, f'{processing_rate:.2f}', 
                    ha='center', va='bottom', fontweight='bold')
            
            # Operaciones de base de datos
            db_ops = [
                pipeline_metrics.get("postgresql_operations", 0),
                pipeline_metrics.get("influxdb_operations", 0)
            ]
            db_labels = ["PostgreSQL", "InfluxDB"]
            bars = ax3.bar(db_labels, db_ops, color=['blue', 'green'], alpha=0.7)
            ax3.set_title('Operaciones de Base de Datos', fontsize=12, fontweight='bold')
            ax3.set_ylabel('Operaciones')
            
            # Agregar valores en las barras
            for bar, value in zip(bars, db_ops):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{value}', ha='center', va='bottom')
            
            # Tasa de error
            error_rate = pipeline_metrics.get("error_rate", 0)
            ax4.bar(['Error Rate'], [error_rate], color='red', alpha=0.7)
            ax4.set_title('Tasa de Error', fontsize=12, fontweight='bold')
            ax4.set_ylabel('Porcentaje (%)')
            ax4.text(0, error_rate + 0.01, f'{error_rate:.1f}%', 
                    ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            
            # Guardar gráfico
            filename = f"processing_metrics_chart_{timestamp}.png"
            filepath = os.path.join(self.charts_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Error generando gráfico de procesamiento: {e}")
            
    def _generate_devices_chart(self, report_data: Dict[str, Any], timestamp: str):
        """Generar gráfico de dispositivos por protocolo"""
        try:
            protocol_metrics = report_data.get("protocol_metrics", {})
            
            if not protocol_metrics:
                return
                
            protocols = list(protocol_metrics.keys())
            device_counts = [len(protocol_metrics[p].get("devices", [])) for p in protocols]
            
            # Crear gráfico
            fig, ax = plt.subplots(figsize=(12, 6))
            
            bars = ax.bar(protocols, device_counts, color='lightsteelblue', alpha=0.8)
            ax.set_title('Dispositivos Únicos por Protocolo', fontsize=16, fontweight='bold')
            ax.set_xlabel('Protocolo')
            ax.set_ylabel('Número de Dispositivos')
            ax.tick_params(axis='x', rotation=45)
            
            # Agregar valores en las barras
            for bar, value in zip(bars, device_counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{value}', ha='center', va='bottom', fontweight='bold')
            
            # Agregar línea de promedio
            avg_devices = np.mean(device_counts)
            ax.axhline(y=avg_devices, color='red', linestyle='--', alpha=0.7, 
                      label=f'Promedio: {avg_devices:.1f}')
            ax.legend()
            
            plt.tight_layout()
            
            # Guardar gráfico
            filename = f"devices_chart_{timestamp}.png"
            filepath = os.path.join(self.charts_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Error generando gráfico de dispositivos: {e}")
            
    def generate_summary_report(self, demo_manager) -> str:
        """Generar informe resumido en tiempo real"""
        try:
            summary = demo_manager.get_summary()
            status = demo_manager.get_status()
            
            # Crear resumen ejecutivo
            summary_data = {
                "summary": summary,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "report_type": "summary"
            }
            
            # Guardar como JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_report_{timestamp}.json"
            filepath = os.path.join(self.reports_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False, default=str)
                
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error generando informe resumido: {e}")
            return ""
            
    def get_report_files(self) -> Dict[str, str]:
        """Obtener lista de archivos de informe generados"""
        try:
            reports = {}
            
            # Informes JSON
            json_files = [f for f in os.listdir(self.reports_dir) if f.endswith('.json')]
            for file in json_files:
                reports[f"json_{file}"] = os.path.join(self.reports_dir, file)
                
            # Informes de texto (simulando PDF)
            txt_files = [f for f in os.listdir(self.reports_dir) if f.endswith('.txt')]
            for file in txt_files:
                reports[f"text_{file}"] = os.path.join(self.reports_dir, file)
                
            # Gráficos
            chart_files = [f for f in os.listdir(self.charts_dir) if f.endswith('.png')]
            for file in chart_files:
                reports[f"chart_{file}"] = os.path.join(self.charts_dir, file)
                
            return reports
            
        except Exception as e:
            self.logger.error(f"Error obteniendo archivos de informe: {e}")
            return {}
