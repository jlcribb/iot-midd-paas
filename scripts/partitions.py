#!/usr/bin/env python3
"""
Script utilitario para gestionar particiones mensuales de registros_datos

Este script proporciona funcionalidades para:
- Crear particiones del mes actual y siguiente
- Listar todas las particiones existentes
- Obtener estadísticas de particiones
- Limpiar particiones antiguas
- Monitorear el estado del sistema de particiones

Uso:
    python partitions.py [comando] [opciones]

Comandos disponibles:
    create          - Crear particiones del mes actual y siguiente
    list            - Listar todas las particiones
    stats           - Mostrar estadísticas detalladas
    cleanup         - Limpiar particiones antiguas
    monitor         - Monitorear estado del sistema
    health          - Verificar salud del sistema de particiones
"""

import argparse
import sys
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import json

# Agregar el directorio src al path para importar módulos del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from iot_middleware.storage.db_handler import DatabaseHandler
    from iot_middleware.config.config_loader import ConfigLoader
except ImportError as e:
    print(f"Error al importar módulos del proyecto: {e}")
    print("Asegúrate de estar ejecutando desde el directorio raíz del proyecto")
    sys.exit(1)


class PartitionManager:
    """Gestor de particiones mensuales para la tabla registros_datos"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Inicializar el gestor de particiones"""
        try:
            # Cargar configuración
            if config_path:
                self.config = ConfigLoader(config_path).load_config()
            else:
                # Buscar archivo de configuración por defecto
                default_configs = [
                    'examples/config.yaml',
                    'examples/config_with_postgresql.yaml',
                    'config.yaml'
                ]
                
                config_found = False
                for config_file in default_configs:
                    if os.path.exists(config_file):
                        self.config = ConfigLoader(config_file).load_config()
                        config_found = True
                        break
                
                if not config_found:
                    raise FileNotFoundError("No se encontró archivo de configuración")
            
            # Inicializar conexión a base de datos
            if 'postgresql' in self.config:
                self.db = DatabaseHandler(self.config['postgresql'])
            elif 'database' in self.config:
                self.db = DatabaseHandler(self.config['database'])
            else:
                raise ValueError("Configuración de base de datos no encontrada")
            
        except Exception as e:
            print(f"Error al inicializar PartitionManager: {e}")
            sys.exit(1)
    
    def create_partitions(self, months_ahead: int = 1) -> Dict[str, str]:
        """Crear particiones para el mes actual y meses futuros"""
        try:
            print(f"Creando particiones para los próximos {months_ahead + 1} meses...")
            
            # Llamar a la función SQL para crear particiones automáticamente
            result = self.db.execute_query(
                "SELECT iot_schema.fn_crear_particiones_automaticas() as resultado"
            )
            
            if result and len(result) > 0:
                resultado = result[0]['resultado']
                print(f"✅ {resultado}")
                return {"status": "success", "message": resultado}
            else:
                return {"status": "error", "message": "No se pudo crear las particiones"}
                
        except Exception as e:
            error_msg = f"Error al crear particiones: {e}"
            print(f"❌ {error_msg}")
            return {"status": "error", "message": error_msg}
    
    def list_partitions(self) -> Dict[str, any]:
        """Listar todas las particiones existentes"""
        try:
            print("📋 Listando particiones existentes...")
            
            query = """
                SELECT 
                    nombre_particion,
                    fecha_inicio,
                    fecha_fin,
                    estado,
                    registros_totales,
                    ROUND(tamaño_bytes / 1024.0 / 1024.0, 2) as tamaño_mb,
                    creada_en
                FROM iot_schema.control_particiones
                ORDER BY fecha_inicio DESC
            """
            
            result = self.db.execute_query(query)
            
            if not result:
                print("ℹ️  No se encontraron particiones")
                return {"status": "success", "partitions": []}
            
            print(f"\n📊 Total de particiones: {len(result)}")
            print("-" * 80)
            print(f"{'Partición':<25} {'Inicio':<12} {'Fin':<12} {'Estado':<10} {'Registros':<10} {'Tamaño (MB)':<12}")
            print("-" * 80)
            
            for partition in result:
                print(f"{partition['nombre_particion']:<25} "
                      f"{partition['fecha_inicio']:<12} "
                      f"{partition['fecha_fin']:<12} "
                      f"{partition['estado']:<10} "
                      f"{partition['registros_totales']:<10} "
                      f"{partition['tamaño_mb']:<12}")
            
            return {"status": "success", "partitions": result}
            
        except Exception as e:
            error_msg = f"Error al listar particiones: {e}"
            print(f"❌ {error_msg}")
            return {"status": "error", "message": error_msg}
    
    def get_statistics(self) -> Dict[str, any]:
        """Obtener estadísticas detalladas de las particiones"""
        try:
            print("📈 Obteniendo estadísticas de particiones...")
            
            # Estadísticas generales
            stats_query = """
                SELECT 
                    COUNT(*) as total_particiones,
                    COUNT(CASE WHEN estado = 'activa' THEN 1 END) as particiones_activas,
                    COUNT(CASE WHEN estado = 'archivada' THEN 1 END) as particiones_archivadas,
                    SUM(registros_totales) as total_registros,
                    SUM(tamaño_bytes) as total_tamaño_bytes
                FROM iot_schema.control_particiones
            """
            
            stats_result = self.db.execute_query(stats_query)
            
            if not stats_result:
                print("ℹ️  No se pudieron obtener estadísticas")
                return {"status": "error", "message": "No se pudieron obtener estadísticas"}
            
            stats = stats_result[0]
            
            # Estadísticas por mes
            monthly_stats_query = """
                SELECT 
                    TO_CHAR(fecha_inicio, 'YYYY-MM') as mes,
                    COUNT(*) as particiones,
                    SUM(registros_totales) as registros,
                    SUM(tamaño_bytes) as tamaño_bytes
                FROM iot_schema.control_particiones
                GROUP BY TO_CHAR(fecha_inicio, 'YYYY-MM')
                ORDER BY mes DESC
                LIMIT 12
            """
            
            monthly_stats = self.db.execute_query(monthly_stats_query)
            
            # Mostrar estadísticas
            print(f"\n📊 ESTADÍSTICAS GENERALES")
            print("-" * 50)
            print(f"Total de particiones: {stats['total_particiones']}")
            print(f"Particiones activas: {stats['particiones_activas']}")
            print(f"Particiones archivadas: {stats['particiones_archivadas']}")
            print(f"Total de registros: {stats['total_registros']:,}")
            print(f"Tamaño total: {stats['total_tamaño_bytes'] / 1024 / 1024:.2f} MB")
            
            if monthly_stats:
                print(f"\n📅 ESTADÍSTICAS POR MES (últimos 12 meses)")
                print("-" * 60)
                print(f"{'Mes':<10} {'Particiones':<12} {'Registros':<12} {'Tamaño (MB)':<12}")
                print("-" * 60)
                
                for month_stat in monthly_stats:
                    print(f"{month_stat['mes']:<10} "
                          f"{month_stat['particiones']:<12} "
                          f"{month_stat['registros']:<12} "
                          f"{month_stat['tamaño_bytes'] / 1024 / 1024:<12.2f}")
            
            return {
                "status": "success", 
                "general_stats": stats,
                "monthly_stats": monthly_stats
            }
            
        except Exception as e:
            error_msg = f"Error al obtener estadísticas: {e}"
            print(f"❌ {error_msg}")
            return {"status": "error", "message": error_msg}
    
    def cleanup_old_partitions(self, retention_months: int = 12) -> Dict[str, str]:
        """Limpiar particiones antiguas"""
        try:
            print(f"🧹 Limpiando particiones más antiguas de {retention_months} meses...")
            
            result = self.db.execute_query(
                "SELECT iot_schema.fn_limpiar_particiones_antiguas(%s) as resultado",
                (retention_months,)
            )
            
            if result and len(result) > 0:
                resultado = result[0]['resultado']
                print(f"✅ {resultado}")
                return {"status": "success", "message": resultado}
            else:
                return {"status": "error", "message": "No se pudo limpiar las particiones"}
                
        except Exception as e:
            error_msg = f"Error al limpiar particiones: {e}"
            print(f"❌ {error_msg}")
            return {"status": "error", "message": error_msg}
    
    def monitor_system(self) -> Dict[str, any]:
        """Monitorear el estado del sistema de particiones"""
        try:
            print("🔍 Monitoreando sistema de particiones...")
            
            # Usar la vista de monitoreo
            monitor_query = """
                SELECT * FROM iot_schema.v_monitoreo_particiones
                ORDER BY fecha_inicio DESC
            """
            
            result = self.db.execute_query(monitor_query)
            
            if not result:
                print("ℹ️  No se encontraron particiones para monitorear")
                return {"status": "success", "monitoring": []}
            
            # Agrupar por estado operativo
            status_counts = {}
            for partition in result:
                status = partition['estado_operativo']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"\n📊 ESTADO DEL SISTEMA DE PARTICIONES")
            print("-" * 60)
            print(f"Total de particiones: {len(result)}")
            
            for status, count in status_counts.items():
                icon = "🟢" if status == "actual" else "🟡" if status == "futura" else "🔴"
                print(f"{icon} {status.capitalize()}: {count}")
            
            # Mostrar particiones con problemas
            problematic = [p for p in result if p['estado_operativo'] == 'retrasada']
            if problematic:
                print(f"\n⚠️  PARTICIONES CON PROBLEMAS:")
                print("-" * 40)
                for partition in problematic:
                    print(f"  • {partition['nombre_particion']} (fecha fin: {partition['fecha_fin']})")
            
            return {"status": "success", "monitoring": result, "status_counts": status_counts}
            
        except Exception as e:
            error_msg = f"Error al monitorear sistema: {e}"
            print(f"❌ {error_msg}")
            return {"status": "error", "message": error_msg}
    
    def health_check(self) -> Dict[str, any]:
        """Verificar la salud del sistema de particiones"""
        try:
            print("🏥 Verificando salud del sistema de particiones...")
            
            health_status = {
                "database_connection": False,
                "partitioning_functions": False,
                "control_table": False,
                "current_partitions": False,
                "auto_creation": False
            }
            
            # 1. Verificar conexión a base de datos
            try:
                test_query = self.db.execute_query("SELECT 1 as test")
                if test_query:
                    health_status["database_connection"] = True
                    print("✅ Conexión a base de datos: OK")
                else:
                    print("❌ Conexión a base de datos: FALLÓ")
            except Exception as e:
                print(f"❌ Conexión a base de datos: ERROR - {e}")
            
            # 2. Verificar funciones de particionado
            try:
                functions_query = """
                    SELECT routine_name 
                    FROM information_schema.routines 
                    WHERE routine_schema = 'iot_schema' 
                    AND routine_name LIKE 'fn_%particion%'
                """
                functions = self.db.execute_query(functions_query)
                if functions and len(functions) >= 3:  # Debería tener al menos 3 funciones
                    health_status["partitioning_functions"] = True
                    print("✅ Funciones de particionado: OK")
                else:
                    print("❌ Funciones de particionado: FALLÓ")
            except Exception as e:
                print(f"❌ Funciones de particionado: ERROR - {e}")
            
            # 3. Verificar tabla de control
            try:
                control_query = "SELECT COUNT(*) as count FROM iot_schema.control_particiones"
                control_result = self.db.execute_query(control_query)
                if control_result:
                    health_status["control_table"] = True
                    print("✅ Tabla de control: OK")
                else:
                    print("❌ Tabla de control: FALLÓ")
            except Exception as e:
                print(f"❌ Tabla de control: ERROR - {e}")
            
            # 4. Verificar particiones actuales
            try:
                partitions_query = "SELECT COUNT(*) as count FROM iot_schema.control_particiones WHERE estado = 'activa'"
                partitions_result = self.db.execute_query(partitions_query)
                if partitions_result and partitions_result[0]['count'] > 0:
                    health_status["current_partitions"] = True
                    print("✅ Particiones actuales: OK")
                else:
                    print("❌ Particiones actuales: FALLÓ")
            except Exception as e:
                print(f"❌ Particiones actuales: ERROR - {e}")
            
            # 5. Verificar creación automática
            try:
                config_query = "SELECT valor FROM iot_schema.config_middleware WHERE clave = 'partitioning.auto_create'"
                config_result = self.db.execute_query(config_query)
                if config_result and config_result[0]['valor'].get('enabled', False):
                    health_status["auto_creation"] = True
                    print("✅ Creación automática: OK")
                else:
                    print("❌ Creación automática: FALLÓ")
            except Exception as e:
                print(f"❌ Creación automática: ERROR - {e}")
            
            # Resumen de salud
            total_checks = len(health_status)
            passed_checks = sum(health_status.values())
            health_percentage = (passed_checks / total_checks) * 100
            
            print(f"\n📊 RESUMEN DE SALUD")
            print("-" * 30)
            print(f"Checks pasados: {passed_checks}/{total_checks}")
            print(f"Porcentaje de salud: {health_percentage:.1f}%")
            
            if health_percentage >= 80:
                print("🏆 Sistema en buen estado")
            elif health_percentage >= 60:
                print("⚠️  Sistema con problemas menores")
            else:
                print("🚨 Sistema con problemas críticos")
            
            return {
                "status": "success",
                "health_status": health_status,
                "health_percentage": health_percentage
            }
            
        except Exception as e:
            error_msg = f"Error en health check: {e}"
            print(f"❌ {error_msg}")
            return {"status": "error", "message": error_msg}
    
    def close(self):
        """Cerrar conexiones"""
        if hasattr(self, 'db'):
            self.db.close()


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description="Gestor de particiones mensuales para IoT Middleware",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'command',
        choices=['create', 'list', 'stats', 'cleanup', 'monitor', 'health'],
        help='Comando a ejecutar'
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Ruta al archivo de configuración'
    )
    
    parser.add_argument(
        '--months-ahead', '-m',
        type=int,
        default=1,
        help='Número de meses futuros para crear particiones (default: 1)'
    )
    
    parser.add_argument(
        '--retention-months', '-r',
        type=int,
        default=12,
        help='Meses de retención para limpieza (default: 12)'
    )
    
    args = parser.parse_args()
    
    # Crear instancia del gestor
    try:
        manager = PartitionManager(args.config)
    except Exception as e:
        print(f"❌ Error al inicializar: {e}")
        sys.exit(1)
    
    try:
        # Ejecutar comando
        if args.command == 'create':
            result = manager.create_partitions(args.months_ahead)
        elif args.command == 'list':
            result = manager.list_partitions()
        elif args.command == 'stats':
            result = manager.get_statistics()
        elif args.command == 'cleanup':
            result = manager.cleanup_old_partitions(args.retention_months)
        elif args.command == 'monitor':
            result = manager.monitor_system()
        elif args.command == 'health':
            result = manager.health_check()
        else:
            print(f"❌ Comando no reconocido: {args.command}")
            sys.exit(1)
        
        # Verificar resultado
        if result.get('status') == 'error':
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)
    finally:
        manager.close()


if __name__ == '__main__':
    main()
