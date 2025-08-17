#!/usr/bin/env python3
"""
Ejemplo de uso del sistema de particiones mensuales

Este script demuestra cómo:
1. Crear particiones automáticamente
2. Insertar datos en diferentes meses
3. Monitorear el estado de las particiones
4. Gestionar el ciclo de vida de las particiones

Requisitos:
- Base de datos PostgreSQL con el esquema IoT Middleware
- Migración 0002 aplicada (sistema de particiones)
- Datos de prueba en las tablas clientes, proyectos, dispositivos, etc.
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from iot_middleware.storage.db_handler import DatabaseHandler
    from iot_middleware.config.config_loader import ConfigLoader
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    print("Asegúrate de estar ejecutando desde el directorio raíz del proyecto")
    sys.exit(1)


class PartitioningExample:
    """Ejemplo de uso del sistema de particiones"""
    
    def __init__(self, config_path: str = 'examples/config_with_postgresql.yaml'):
        """Inicializar el ejemplo"""
        try:
            self.config = ConfigLoader(config_path).load_config()
            self.db = DatabaseHandler(self.config['database'])
            print("✅ Conexión a base de datos establecida")
        except Exception as e:
            print(f"❌ Error al inicializar: {e}")
            sys.exit(1)
    
    def setup_test_data(self):
        """Configurar datos de prueba si no existen"""
        print("\n🔧 Configurando datos de prueba...")
        
        # Verificar si ya existen datos de prueba
        existing_data = self.db.execute_query(
            "SELECT COUNT(*) as count FROM iot_schema.clientes WHERE nombre = 'Cliente Demo Particiones'"
        )
        
        if existing_data and existing_data[0]['count'] > 0:
            print("ℹ️  Los datos de prueba ya existen")
            return
        
        # Crear cliente de prueba
        cliente_id = self.db.execute_query("""
            INSERT INTO iot_schema.clientes (nombre, sector, industria, contacto_principal)
            VALUES (
                'Cliente Demo Particiones',
                'Industrial',
                'Manufactura',
                '{"nombre": "Ana García", "email": "ana.garcia@demo.com", "telefono": "+1234567890"}'
            ) RETURNING id
        """)[0]['id']
        
        # Crear proyecto de prueba
        proyecto_id = self.db.execute_query("""
            INSERT INTO iot_schema.proyectos (cliente_id, nombre, descripcion, estado)
            VALUES (%s, 'Proyecto Demo Particiones', 'Proyecto para demostrar el sistema de particiones', 'activo')
            RETURNING id
        """, (cliente_id,))[0]['id']
        
        # Crear dispositivo de prueba
        dispositivo_id = self.db.execute_query("""
            INSERT INTO iot_schema.dispositivos (tipo, fabricante, modelo, identificador_unico, protocolo)
            VALUES ('Sensor', 'Demo Corp', 'DS-001', 'DEMO_SENSOR_001', 'MQTT')
            RETURNING id
        """)[0]['id']
        
        # Asociar dispositivo al proyecto
        self.db.execute_query("""
            INSERT INTO iot_schema.dispositivos_proyecto (proyecto_id, dispositivo_id, nombre_personalizado)
            VALUES (%s, %s, 'Sensor Demo Principal')
        """, (proyecto_id, dispositivo_id))
        
        # Crear canal de prueba
        self.canal_id = self.db.execute_query("""
            INSERT INTO iot_schema.canales (dispositivo_id, nombre, tipo, unidad_medida)
            VALUES (%s, 'temperatura', 'float', '°C')
            RETURNING id
        """, (dispositivo_id,))[0]['id']
        
        print("✅ Datos de prueba creados")
    
    def create_partitions(self):
        """Crear particiones para el mes actual y siguiente"""
        print("\n📅 Creando particiones mensuales...")
        
        try:
            # Llamar a la función de creación automática
            result = self.db.execute_query(
                "SELECT iot_schema.fn_crear_particiones_automaticas() as resultado"
            )
            
            if result:
                print(f"✅ {result[0]['resultado']}")
            else:
                print("❌ Error al crear particiones")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def insert_test_data(self, months_back: int = 3):
        """Insertar datos de prueba en diferentes meses"""
        print(f"\n📊 Insertando datos de prueba en los últimos {months_back} meses...")
        
        # Generar fechas para los últimos meses
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        current_date = start_date
        total_inserted = 0
        
        while current_date <= end_date:
            # Crear partición para este mes si no existe
            month_start = current_date.replace(day=1)
            partition_name = f"registros_datos_{month_start.strftime('%Y_%m')}"
            
            # Verificar si la partición existe
            partition_exists = self.db.execute_query("""
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE c.relname = %s AND n.nspname = 'iot_schema'
            """, (partition_name,))
            
            if not partition_exists:
                print(f"  📅 Creando partición para {month_start.strftime('%Y-%m')}...")
                self.db.execute_query(
                    "SELECT iot_schema.fn_crear_particion_registros(%s)",
                    (month_start,)
                )
            
            # Insertar datos para este mes (10 registros por día)
            days_in_month = (month_start.replace(month=month_start.month + 1) - month_start).days
            
            for day in range(days_in_month):
                current_day = month_start + timedelta(days=day)
                
                # Insertar 10 registros por día
                for hour in range(0, 24, 2):  # Cada 2 horas
                    timestamp = current_day + timedelta(hours=hour, minutes=random.randint(0, 59))
                    
                    # Generar valor de temperatura realista
                    base_temp = 20.0  # Temperatura base
                    variation = random.uniform(-5, 5)  # Variación ±5°C
                    temperature = base_temp + variation
                    
                    # Insertar registro
                    self.db.execute_query("""
                        INSERT INTO iot_schema.registros_datos (canal_id, ts, valor_num, calidad, metadata)
                        VALUES (%s, %s, %s, 'OK', %s)
                    """, (
                        self.canal_id,
                        timestamp,
                        round(temperature, 2),
                        json.dumps({
                            'fuente': 'demo_partitioning',
                            'tipo_sensor': 'temperatura',
                            'ubicacion': 'laboratorio'
                        })
                    ))
                    
                    total_inserted += 1
            
            # Avanzar al siguiente mes
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        print(f"✅ Total de registros insertados: {total_inserted:,}")
    
    def demonstrate_partitioning(self):
        """Demostrar el funcionamiento del particionado"""
        print("\n🔍 Demostrando funcionamiento del particionado...")
        
        # 1. Mostrar todas las particiones
        print("\n📋 Particiones existentes:")
        partitions = self.db.execute_query("""
            SELECT 
                nombre_particion,
                fecha_inicio,
                fecha_fin,
                estado,
                registros_totales
            FROM iot_schema.control_particiones
            ORDER BY fecha_inicio
        """)
        
        for partition in partitions:
            print(f"  • {partition['nombre_particion']}: "
                  f"{partition['fecha_inicio']} a {partition['fecha_fin']} "
                  f"({partition['estado']}) - {partition['registros_totales']} registros")
        
        # 2. Demostrar consultas en particiones específicas
        print("\n🔍 Consultas en particiones específicas:")
        
        # Consulta en el mes actual
        current_month = datetime.now().strftime('%Y_%m')
        current_partition = f"registros_datos_{current_month}"
        
        current_data = self.db.execute_query(f"""
            SELECT 
                COUNT(*) as total_registros,
                MIN(ts) as primer_registro,
                MAX(ts) as ultimo_registro,
                AVG(valor_num) as temperatura_promedio
            FROM iot_schema.{current_partition}
            WHERE canal_id = %s
        """, (self.canal_id,))
        
        if current_data:
            data = current_data[0]
            print(f"  📊 Mes actual ({current_month}):")
            print(f"    - Total registros: {data['total_registros']}")
            print(f"    - Rango temporal: {data['primer_registro']} a {data['ultimo_registro']}")
            print(f"    - Temperatura promedio: {data['temperatura_promedio']:.2f}°C")
        
        # 3. Demostrar consulta en tabla principal (se distribuye automáticamente)
        print("\n🌐 Consulta en tabla principal (distribución automática):")
        
        total_data = self.db.execute_query("""
            SELECT 
                COUNT(*) as total_registros,
                MIN(ts) as primer_registro,
                MAX(ts) as ultimo_registro,
                AVG(valor_num) as temperatura_promedio
            FROM iot_schema.registros_datos
            WHERE canal_id = %s
        """, (self.canal_id,))
        
        if total_data:
            data = total_data[0]
            print(f"  📊 Total general:")
            print(f"    - Total registros: {data['total_registros']}")
            print(f"    - Rango temporal: {data['primer_registro']} a {data['ultimo_registro']}")
            print(f"    - Temperatura promedio: {data['temperatura_promedio']:.2f}°C")
    
    def show_performance_benefits(self):
        """Mostrar beneficios de rendimiento del particionado"""
        print("\n⚡ Beneficios de rendimiento del particionado:")
        
        # Comparar tiempos de consulta con y sin particionado
        import time
        
        # Consulta en tabla principal (con particionado)
        start_time = time.time()
        self.db.execute_query("""
            SELECT COUNT(*) FROM iot_schema.registros_datos 
            WHERE ts >= %s AND ts < %s
        """, (
            datetime.now() - timedelta(days=30),
            datetime.now()
        ))
        partitioned_time = time.time() - start_time
        
        # Consulta en partición específica
        current_month = datetime.now().strftime('%Y_%m')
        start_time = time.time()
        self.db.execute_query(f"""
            SELECT COUNT(*) FROM iot_schema.registros_datos_{current_month}
            WHERE ts >= %s AND ts < %s
        """, (
            datetime.now() - timedelta(days=30),
            datetime.now()
        ))
        specific_partition_time = time.time() - start_time
        
        print(f"  📊 Tiempo consulta tabla principal: {partitioned_time:.4f}s")
        print(f"  📊 Tiempo consulta partición específica: {specific_partition_time:.4f}s")
        
        if specific_partition_time < partitioned_time:
            improvement = ((partitioned_time - specific_partition_time) / partitioned_time) * 100
            print(f"  🚀 Mejora de rendimiento: {improvement:.1f}%")
    
    def cleanup_demo_data(self):
        """Limpiar datos de demostración"""
        print("\n🧹 Limpiando datos de demostración...")
        
        try:
            # Eliminar registros de datos de prueba
            deleted_records = self.db.execute_query("""
                DELETE FROM iot_schema.registros_datos 
                WHERE metadata->>'fuente' = 'demo_partitioning'
                RETURNING COUNT(*) as deleted_count
            """)
            
            if deleted_records:
                print(f"✅ {deleted_records[0]['deleted_count']} registros de prueba eliminados")
            
            # Eliminar canal de prueba
            self.db.execute_query("DELETE FROM iot_schema.canales WHERE id = %s", (self.canal_id,))
            
            # Eliminar dispositivo de prueba
            self.db.execute_query("""
                DELETE FROM iot_schema.dispositivos 
                WHERE identificador_unico = 'DEMO_SENSOR_001'
            """)
            
            # Eliminar proyecto de prueba
            self.db.execute_query("""
                DELETE FROM iot_schema.proyectos 
                WHERE nombre = 'Proyecto Demo Particiones'
            """)
            
            # Eliminar cliente de prueba
            self.db.execute_query("""
                DELETE FROM iot_schema.clientes 
                WHERE nombre = 'Cliente Demo Particiones'
            """)
            
            print("✅ Datos de demostración limpiados")
            
        except Exception as e:
            print(f"⚠️  Error al limpiar datos: {e}")
    
    def run_demo(self):
        """Ejecutar demostración completa"""
        print("🚀 INICIANDO DEMOSTRACIÓN DEL SISTEMA DE PARTICIONES")
        print("=" * 60)
        
        try:
            # 1. Configurar datos de prueba
            self.setup_test_data()
            
            # 2. Crear particiones
            self.create_partitions()
            
            # 3. Insertar datos de prueba
            self.insert_test_data(months_back=3)
            
            # 4. Demostrar funcionamiento
            self.demonstrate_partitioning()
            
            # 5. Mostrar beneficios de rendimiento
            self.show_performance_benefits()
            
            print("\n🎉 DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
            print("=" * 60)
            
            # Preguntar si limpiar datos
            response = input("\n¿Deseas limpiar los datos de demostración? (s/N): ").strip().lower()
            if response in ['s', 'si', 'sí', 'y', 'yes']:
                self.cleanup_demo_data()
            else:
                print("ℹ️  Los datos de demostración se mantienen para inspección manual")
            
        except Exception as e:
            print(f"❌ Error durante la demostración: {e}")
        finally:
            self.db.close()


def main():
    """Función principal"""
    import json
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = 'examples/config_with_postgresql.yaml'
    
    # Verificar que existe el archivo de configuración
    if not os.path.exists(config_path):
        print(f"❌ Archivo de configuración no encontrado: {config_path}")
        print("Uso: python partitioning_example.py [ruta_config.yaml]")
        sys.exit(1)
    
    # Ejecutar demostración
    demo = PartitioningExample(config_path)
    demo.run_demo()


if __name__ == '__main__':
    main()
