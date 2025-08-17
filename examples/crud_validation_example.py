#!/usr/bin/env python3
"""
Ejemplo de Uso de Repositorios CRUD y Validación de Tipos
==========================================================

Este script demuestra el uso completo de la capa CRUD implementada,
incluyendo validación automática de tipos para registros_datos.
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any
import json

# Agregar el directorio src al path para importar módulos del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from iot_middleware.storage.db_handler import DatabaseHandler
    from iot_middleware.storage.repositories import (
        ClienteRepository,
        ProyectoRepository,
        CanalRepository,
        RegistroDatosRepository
    )
    from iot_middleware.config.config_loader import ConfigLoader
    from iot_middleware.models.enums import TipoDato, CalidadDato, EstadoProyecto
except ImportError as e:
    print(f"Error al importar módulos del proyecto: {e}")
    print("Asegúrate de estar ejecutando desde el directorio raíz del proyecto")
    sys.exit(1)


class CRUDValidationDemo:
    """Demostración de funcionalidades CRUD y validación"""
    
    def __init__(self, config_path: str):
        """Inicializar la demostración"""
        try:
            # Cargar configuración
            self.config = ConfigLoader(config_path).load_config()
            
            # Inicializar conexión a base de datos
            self.db = DatabaseHandler(self.config['postgresql'])
            
            # Inicializar repositorios
            self.cliente_repo = ClienteRepository(self.db)
            self.proyecto_repo = ProyectoRepository(self.db)
            self.canal_repo = CanalRepository(self.db)
            self.registro_repo = RegistroDatosRepository(self.db)
            
            print("✅ Repositorios inicializados correctamente")
            
        except Exception as e:
            print(f"❌ Error al inicializar: {e}")
            sys.exit(1)
    
    def demo_client_operations(self):
        """Demostrar operaciones CRUD para clientes"""
        print("\n" + "="*60)
        print("🏢 DEMOSTRACIÓN DE OPERACIONES CRUD PARA CLIENTES")
        print("="*60)
        
        # 1. Crear un nuevo cliente
        print("\n1️⃣ Creando nuevo cliente...")
        nuevo_cliente_data = {
            'nombre': 'Empresa Demo IoT',
            'sector': 'Tecnología',
            'industria': 'IoT y Automatización',
            'contacto_principal': {
                'nombre': 'Juan Pérez',
                'email': 'juan.perez@empresademo.com',
                'telefono': '+1234567890',
                'cargo': 'Director de Operaciones'
            },
            'contactos_adicionales': [
                {
                    'nombre': 'María García',
                    'email': 'maria.garcia@empresademo.com',
                    'telefono': '+1234567891',
                    'cargo': 'Ingeniera de Sistemas'
                }
            ],
            'direccion': {
                'calle': 'Av. Tecnología 123',
                'ciudad': 'Ciudad Demo',
                'estado': 'Estado Demo',
                'codigo_postal': '12345',
                'pais': 'Demo País'
            },
            'configuracion': {
                'timezone': 'America/Mexico_City',
                'idioma': 'es',
                'formato_fecha': 'DD/MM/YYYY'
            }
        }
        
        cliente_creado = self.cliente_repo.create(nuevo_cliente_data)
        if cliente_creado:
            print(f"✅ Cliente creado: {cliente_creado.nombre} (ID: {cliente_creado.id})")
            cliente_id = str(cliente_creado.id)
        else:
            print("❌ Error al crear cliente")
            return
        
        # 2. Obtener cliente por ID
        print("\n2️⃣ Obteniendo cliente por ID...")
        cliente_obtenido = self.cliente_repo.get_by_id(cliente_id)
        if cliente_obtenido:
            print(f"✅ Cliente obtenido: {cliente_obtenido.nombre}")
        else:
            print("❌ Error al obtener cliente")
        
        # 3. Buscar clientes por sector
        print("\n3️⃣ Buscando clientes por sector...")
        clientes_tecnologia = self.cliente_repo.get_by_sector('Tecnología')
        print(f"✅ Encontrados {len(clientes_tecnologia)} clientes en sector Tecnología")
        
        # 4. Obtener resumen del cliente
        print("\n4️⃣ Obteniendo resumen del cliente...")
        resumen_cliente = self.cliente_repo.get_client_summary(cliente_id)
        if resumen_cliente:
            print(f"✅ Resumen obtenido: {resumen_cliente['cliente']['nombre']}")
            print(f"   - Total proyectos: {resumen_cliente['estadisticas']['total_proyectos']}")
        else:
            print("❌ Error al obtener resumen")
        
        # 5. Actualizar cliente
        print("\n5️⃣ Actualizando cliente...")
        datos_actualizacion = {
            'industria': 'IoT, Automatización y Big Data',
            'configuracion': {
                'timezone': 'America/Mexico_City',
                'idioma': 'es',
                'formato_fecha': 'DD/MM/YYYY',
                'notificaciones': True
            }
        }
        
        cliente_actualizado = self.cliente_repo.update(cliente_id, datos_actualizacion)
        if cliente_actualizado:
            print(f"✅ Cliente actualizado: {cliente_actualizado.industria}")
        else:
            print("❌ Error al actualizar cliente")
        
        return cliente_id
    
    def demo_project_operations(self, cliente_id: str):
        """Demostrar operaciones CRUD para proyectos"""
        print("\n" + "="*60)
        print("📋 DEMOSTRACIÓN DE OPERACIONES CRUD PARA PROYECTOS")
        print("="*60)
        
        # 1. Crear un nuevo proyecto
        print("\n1️⃣ Creando nuevo proyecto...")
        nuevo_proyecto_data = {
            'cliente_id': cliente_id,
            'nombre': 'Sistema de Monitoreo IoT',
            'descripcion': 'Implementación de sistema de monitoreo en tiempo real para instalaciones industriales',
            'estado': 'planificado',
            'fecha_inicio': datetime.now().date(),
            'fecha_fin': (datetime.now() + timedelta(days=90)).date(),
            'presupuesto': 50000.00,
            'prioridad': 1,
            'configuracion': {
                'tipo_proyecto': 'IoT',
                'tecnologias': ['MQTT', 'PostgreSQL', 'Python'],
                'equipo': 5
            }
        }
        
        proyecto_creado = self.proyecto_repo.create(nuevo_proyecto_data)
        if proyecto_creado:
            print(f"✅ Proyecto creado: {proyecto_creado.nombre} (ID: {proyecto_creado.id})")
            proyecto_id = str(proyecto_creado.id)
        else:
            print("❌ Error al crear proyecto")
            return
        
        # 2. Obtener proyectos del cliente
        print("\n2️⃣ Obteniendo proyectos del cliente...")
        proyectos_cliente = self.proyecto_repo.get_by_cliente(cliente_id)
        print(f"✅ Encontrados {len(proyectos_cliente)} proyectos del cliente")
        
        # 3. Obtener proyectos activos
        print("\n3️⃣ Obteniendo proyectos activos...")
        proyectos_activos = self.proyecto_repo.get_active_projects()
        print(f"✅ Encontrados {len(proyectos_activos)} proyectos activos")
        
        # 4. Obtener detalles del proyecto
        print("\n4️⃣ Obteniendo detalles del proyecto...")
        detalles_proyecto = self.proyecto_repo.get_project_details(proyecto_id)
        if detalles_proyecto:
            print(f"✅ Detalles obtenidos: {detalles_proyecto['proyecto']['nombre']}")
            print(f"   - Cliente: {detalles_proyecto['cliente']['nombre']}")
            print(f"   - Presupuesto: ${detalles_proyecto['proyecto']['presupuesto']}")
        else:
            print("❌ Error al obtener detalles")
        
        # 5. Cambiar estado del proyecto
        print("\n5️⃣ Cambiando estado del proyecto...")
        estado_actualizado = self.proyecto_repo.update_project_status(proyecto_id, 'activo')
        if estado_actualizado:
            print("✅ Estado del proyecto actualizado a 'activo'")
        else:
            print("❌ Error al actualizar estado")
        
        return proyecto_id
    
    def demo_channel_validation(self, proyecto_id: str):
        """Demostrar validación de canales"""
        print("\n" + "="*60)
        print("🔌 DEMOSTRACIÓN DE VALIDACIÓN DE CANALES")
        print("="*60)
        
        # 1. Obtener canales del proyecto
        print("\n1️⃣ Obteniendo canales del proyecto...")
        canales_proyecto = self.canal_repo.get_channels_by_project(proyecto_id)
        print(f"✅ Encontrados {len(canales_proyecto)} canales en el proyecto")
        
        if not canales_proyecto:
            print("⚠️  No hay canales en el proyecto. Creando canales de ejemplo...")
            # Aquí se crearían canales de ejemplo si no existen
            return None
        
        # 2. Validar valores para diferentes tipos de canales
        print("\n2️⃣ Validando valores para diferentes tipos de canales...")
        
        for canal in canales_proyecto[:3]:  # Probar con los primeros 3 canales
            print(f"\n   Canal: {canal.nombre} (Tipo: {canal.tipo})")
            
            # Validar diferentes tipos de valores
            valores_prueba = self._get_test_values_for_type(canal.tipo)
            
            for valor in valores_prueba:
                resultado = self.canal_repo.validate_channel_value(str(canal.id), valor)
                if resultado['valid']:
                    print(f"     ✅ {valor} -> {resultado['valor_validado']} ({resultado['tipo_convertido']})")
                else:
                    print(f"     ❌ {valor}: {resultado['error']}")
        
        return canales_proyecto[0].id if canales_proyecto else None
    
    def demo_data_insertion_with_validation(self, canal_id: str):
        """Demostrar inserción de datos con validación automática"""
        print("\n" + "="*60)
        print("📊 DEMOSTRACIÓN DE INSERCIÓN CON VALIDACIÓN AUTOMÁTICA")
        print("="*60)
        
        if not canal_id:
            print("⚠️  No hay canal disponible para la demostración")
            return
        
        # 1. Obtener información del canal
        print(f"\n1️⃣ Obteniendo información del canal {canal_id}...")
        canal_info = self.canal_repo.get_channel_info_for_validation(canal_id)
        if not canal_info:
            print("❌ No se pudo obtener información del canal")
            return
        
        print(f"✅ Canal: {canal_info['nombre']} (Tipo: {canal_info['tipo']})")
        
        # 2. Insertar registros con diferentes tipos de valores
        print("\n2️⃣ Insertando registros con validación automática...")
        
        # Obtener valores de prueba según el tipo del canal
        valores_prueba = self._get_test_values_for_type(canal_info['tipo'])
        
        registros_creados = 0
        for i, valor in enumerate(valores_prueba):
            print(f"\n   Insertando valor {i+1}: {valor}")
            
            # Insertar con metadatos adicionales
            registro = self.registro_repo.insert_record(
                canal_id=canal_id,
                valor=valor,
                calidad=CalidadDato.OK,
                calidad_porcentaje=95,
                metadata={
                    'source': 'demo_script',
                    'test_case': f'valor_{i+1}',
                    'timestamp_demo': datetime.now().isoformat()
                },
                qos=1,
                ip='192.168.1.100',
                source='demo_device'
            )
            
            if registro:
                print(f"     ✅ Registro creado (ID: {registro.id})")
                registros_creados += 1
            else:
                print(f"     ❌ Error al crear registro")
        
        print(f"\n📊 Resumen: {registros_creados}/{len(valores_prueba)} registros creados exitosamente")
        
        # 3. Obtener estadísticas del canal
        print("\n3️⃣ Obteniendo estadísticas del canal...")
        estadisticas = self.registro_repo.get_statistics_by_canal(canal_id)
        if estadisticas:
            print(f"✅ Estadísticas obtenidas:")
            print(f"   - Total registros: {estadisticas['total_registros']}")
            print(f"   - Primer registro: {estadisticas['primer_registro']}")
            print(f"   - Último registro: {estadisticas['ultimo_registro']}")
        else:
            print("❌ Error al obtener estadísticas")
    
    def _get_test_values_for_type(self, tipo_dato: TipoDato) -> list:
        """Obtener valores de prueba según el tipo de dato"""
        if tipo_dato == TipoDato.INT:
            return [42, 100, -5, 0, 999999]
        elif tipo_dato == TipoDato.FLOAT:
            return [3.14, 42.0, -2.5, 0.0, 1000.75]
        elif tipo_dato == TipoDato.BOOL:
            return [True, False, 1, 0, "true", "false"]
        elif tipo_dato == TipoDato.STRING:
            return ["Hola Mundo", "Test String", "123", "", "Special chars: @#$%"]
        elif tipo_dato == TipoDato.JSON:
            return [
                {"key": "value", "number": 42},
                {"array": [1, 2, 3], "nested": {"data": "test"}},
                {"boolean": True, "null": None}
            ]
        else:
            return ["default_value"]
    
    def run_demo(self):
        """Ejecutar la demostración completa"""
        print("🚀 INICIANDO DEMOSTRACIÓN DE REPOSITORIOS CRUD Y VALIDACIÓN")
        print("="*80)
        
        try:
            # 1. Operaciones con clientes
            cliente_id = self.demo_client_operations()
            
            # 2. Operaciones con proyectos
            proyecto_id = self.demo_project_operations(cliente_id)
            
            # 3. Validación de canales
            canal_id = self.demo_channel_validation(proyecto_id)
            
            # 4. Inserción de datos con validación
            self.demo_data_insertion_with_validation(canal_id)
            
            print("\n" + "="*80)
            print("🎉 DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
            print("="*80)
            
        except Exception as e:
            print(f"\n❌ Error durante la demostración: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Función principal"""
    if len(sys.argv) != 2:
        print("Uso: python crud_validation_example.py <config_file>")
        print("Ejemplo: python crud_validation_example.py examples/config_partitioning.yaml")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    if not os.path.exists(config_path):
        print(f"❌ Archivo de configuración no encontrado: {config_path}")
        sys.exit(1)
    
    try:
        # Crear y ejecutar la demostración
        demo = CRUDValidationDemo(config_path)
        demo.run_demo()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demostración interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
