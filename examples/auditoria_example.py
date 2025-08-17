#!/usr/bin/env python3
"""
Ejemplo de Uso del Sistema de Auditoría
IoT Middleware
=======================================

Este script demuestra cómo usar el sistema de auditoría para:
- Registrar cambios en entidades del sistema
- Usar decoradores para auditoría automática
- Generar reportes de auditoría
- Integrar con FastAPI
"""

import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.utils.auditoria import (
        AuditoriaService, 
        ContextoAuditoria, 
        AccionAuditoria, 
        EntidadAuditable,
        auditar_cambios,
        contexto_auditoria,
        create_auditoria_service
    )
    from iot_middleware.storage.db_handler import create_database_handler
    from iot_middleware.config import load_config
    print("✅ Módulos importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    sys.exit(1)


class ServicioConAuditoria:
    """Ejemplo de servicio que usa auditoría automática"""
    
    def __init__(self, auditoria_service: AuditoriaService):
        self.auditoria_service = auditoria_service
    
    @auditar_cambios(EntidadAuditable.CONFIG_MIDDLEWARE, AccionAuditoria.CREAR)
    def crear_configuracion(self, id: str, config_data: Dict[str, Any]) -> bool:
        """Crea una nueva configuración"""
        print(f"🔧 Creando configuración: {id}")
        
        # Simular operación de base de datos
        time.sleep(0.1)
        
        # La auditoría se ejecuta automáticamente
        return True
    
    @auditar_cambios(EntidadAuditable.CONFIG_MIDDLEWARE, AccionAuditoria.ACTUALIZAR)
    def actualizar_configuracion(self, id: str, config_data: Dict[str, Any]) -> bool:
        """Actualiza una configuración existente"""
        print(f"🔧 Actualizando configuración: {id}")
        
        # Simular operación de base de datos
        time.sleep(0.1)
        
        # La auditoría se ejecuta automáticamente
        return True
    
    @auditar_cambios(EntidadAuditable.CANAL, AccionAuditoria.CONFIGURAR)
    def configurar_canal(self, id: str, config_data: Dict[str, Any]) -> bool:
        """Configura un canal"""
        print(f"📡 Configurando canal: {id}")
        
        # Simular operación de base de datos
        time.sleep(0.1)
        
        # La auditoría se ejecuta automáticamente
        return True


def example_basic_auditoria():
    """Ejemplo básico de auditoría"""
    print("\n🔧 EJEMPLO 1: Auditoría Básica")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config_path = Path(__file__).parent / "config_ingesta.yaml"
        config = load_config(str(config_path))
        
        # Crear manejador de base de datos
        db_handler = create_database_handler(config.storage)
        
        # Crear servicio de auditoría
        auditoria_service = create_auditoria_service(db_handler)
        
        print("✅ Servicio de auditoría creado")
        
        # Establecer contexto de auditoría
        contexto = ContextoAuditoria(
            usuario_id="usuario_ejemplo_001",
            ip_origen="192.168.1.100",
            user_agent="Python/3.9 Example",
            endpoint="/api/ejemplo",
            metodo_http="POST"
        )
        
        auditoria_service.set_contexto(contexto)
        
        # Registrar algunos cambios de ejemplo
        print("\n📝 Registrando cambios de ejemplo...")
        
        # Auditoría de configuración
        success = auditoria_service.auditar_config_middleware(
            config_id="config_temp_001",
            accion=AccionAuditoria.CREAR,
            antes={},
            despues={
                'clave': 'temperatura_maxima',
                'valor': 85.0,
                'descripcion': 'Temperatura máxima permitida',
                'categoria': 'sensores'
            }
        )
        
        if success:
            print("✅ Auditoría de configuración registrada")
        else:
            print("❌ Error en auditoría de configuración")
        
        # Auditoría de canal
        success = auditoria_service.auditar_canal(
            canal_id="canal_temp_001",
            accion=AccionAuditoria.CONFIGURAR,
            antes={
                'umbral_alto': 80.0,
                'umbral_bajo': 0.0
            },
            despues={
                'umbral_alto': 85.0,
                'umbral_bajo': -5.0
            }
        )
        
        if success:
            print("✅ Auditoría de canal registrada")
        else:
            print("❌ Error en auditoría de canal")
        
        # Auditoría de evento de alarma
        success = auditoria_service.auditar_evento_alarma(
            evento_id="alarma_temp_001",
            accion=AccionAuditoria.RECONOCER,
            antes={
                'estado': 'activa',
                'reconocida_por': None,
                'reconocida_en': None
            },
            despues={
                'estado': 'reconocida',
                'reconocida_por': 'usuario_ejemplo_001',
                'reconocida_en': datetime.now(timezone.utc).isoformat()
            }
        )
        
        if success:
            print("✅ Auditoría de evento de alarma registrada")
        else:
            print("❌ Error en auditoría de evento de alarma")
        
        # Limpiar contexto
        auditoria_service.clear_contexto()
        
        return True
        
    except Exception as e:
        print(f"❌ Error en auditoría básica: {e}")
        return False


def example_context_manager():
    """Ejemplo usando context manager"""
    print("\n🔧 EJEMPLO 2: Context Manager de Auditoría")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config_path = Path(__file__).parent / "config_ingesta.yaml"
        config = load_config(str(config_path))
        
        # Crear manejador de base de datos
        db_handler = create_database_handler(config.storage)
        
        # Crear servicio de auditoría
        auditoria_service = create_auditoria_service(db_handler)
        
        print("✅ Servicio de auditoría creado")
        
        # Usar context manager para auditoría
        with contexto_auditoria(
            auditoria_service=auditoria_service,
            usuario_id="usuario_admin_001",
            ip_origen="10.0.0.50",
            user_agent="AdminTool/1.0",
            endpoint="/admin/configuracion",
            metodo_http="PUT"
        ) as audit_service:
            
            print("🔒 Contexto de auditoría establecido")
            
            # Registrar cambios dentro del contexto
            success = audit_service.auditar_dispositivo(
                dispositivo_id="device_001",
                accion=AccionAuditoria.ACTIVAR,
                antes={'estado': 'inactivo'},
                despues={'estado': 'activo'}
            )
            
            if success:
                print("✅ Auditoría de dispositivo registrada")
            else:
                print("❌ Error en auditoría de dispositivo")
            
            # Registrar más cambios
            success = audit_service.auditar_proyecto(
                proyecto_id="proyecto_001",
                accion=AccionAuditoria.CONFIGURAR,
                antes={'configuracion': {'version': '1.0'}},
                despues={'configuracion': {'version': '2.0'}}
            )
            
            if success:
                print("✅ Auditoría de proyecto registrada")
            else:
                print("❌ Error en auditoría de proyecto")
        
        print("🔓 Contexto de auditoría liberado automáticamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en context manager: {e}")
        return False


def example_decorators():
    """Ejemplo usando decoradores de auditoría"""
    print("\n🔧 EJEMPLO 3: Decoradores de Auditoría")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config_path = Path(__file__).parent / "config_ingesta.yaml"
        config = load_config(str(config_path))
        
        # Crear manejador de base de datos
        db_handler = create_database_handler(config.storage)
        
        # Crear servicio de auditoría
        auditoria_service = create_auditoria_service(db_handler)
        
        # Crear servicio que usa decoradores
        servicio = ServicioConAuditoria(auditoria_service)
        
        print("✅ Servicio con decoradores creado")
        
        # Establecer contexto de auditoría
        contexto = ContextoAuditoria(
            usuario_id="usuario_sistema_001",
            ip_origen="127.0.0.1",
            user_agent="SystemService/1.0",
            endpoint="/system/config",
            metodo_http="POST"
        )
        
        auditoria_service.set_contexto(contexto)
        
        # Ejecutar operaciones (la auditoría es automática)
        print("\n📝 Ejecutando operaciones con auditoría automática...")
        
        # Crear configuración
        success = servicio.crear_configuracion(
            id="config_sistema_001",
            config_data={'timeout': 30, 'retries': 3}
        )
        
        if success:
            print("✅ Configuración creada con auditoría automática")
        else:
            print("❌ Error creando configuración")
        
        # Actualizar configuración
        success = servicio.actualizar_configuracion(
            id="config_sistema_001",
            config_data={'timeout': 60, 'retries': 5}
        )
        
        if success:
            print("✅ Configuración actualizada con auditoría automática")
        else:
            print("❌ Error actualizando configuración")
        
        # Configurar canal
        success = servicio.configurar_canal(
            id="canal_sistema_001",
            config_data={'frecuencia': 1000, 'buffer_size': 1024}
        )
        
        if success:
            print("✅ Canal configurado con auditoría automática")
        else:
            print("❌ Error configurando canal")
        
        # Limpiar contexto
        auditoria_service.clear_contexto()
        
        return True
        
    except Exception as e:
        print(f"❌ Error en decoradores: {e}")
        return False


def example_consultas_auditoria():
    """Ejemplo de consultas de auditoría"""
    print("\n🔧 EJEMPLO 4: Consultas de Auditoría")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config_path = Path(__file__).parent / "config_ingesta.yaml"
        config = load_config(str(config_path))
        
        # Crear manejador de base de datos
        db_handler = create_database_handler(config.storage)
        
        # Crear servicio de auditoría
        auditoria_service = create_auditoria_service(db_handler)
        
        print("✅ Servicio de auditoría creado")
        
        # Consultar registros de auditoría
        print("\n📊 Consultando registros de auditoría...")
        
        # Obtener todos los registros recientes
        registros = auditoria_service.obtener_auditoria(limite=10)
        
        print(f"📋 Total de registros encontrados: {len(registros)}")
        
        if registros:
            print("\n📝 Últimos registros:")
            for i, registro in enumerate(registros[:5], 1):
                print(f"   {i}. {registro['entidad']} - {registro['accion']} - {registro['timestamp']}")
        
        # Filtrar por entidad específica
        print("\n🔍 Filtrando por entidad 'config_middleware':")
        registros_config = auditoria_service.obtener_auditoria(
            entidad='config_middleware',
            limite=5
        )
        
        print(f"   Configuraciones encontradas: {len(registros_config)}")
        
        # Filtrar por acción
        print("\n🔍 Filtrando por acción 'CREAR':")
        registros_crear = auditoria_service.obtener_auditoria(
            accion='CREAR',
            limite=5
        )
        
        print(f"   Operaciones de creación: {len(registros_crear)}")
        
        # Filtrar por fecha
        fecha_desde = datetime.now(timezone.utc) - timedelta(hours=1)
        fecha_hasta = datetime.now(timezone.utc)
        
        print(f"\n🔍 Filtrando por período: {fecha_desde.strftime('%H:%M')} - {fecha_hasta.strftime('%H:%M')}")
        registros_periodo = auditoria_service.obtener_auditoria(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limite=10
        )
        
        print(f"   Registros en el período: {len(registros_periodo)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en consultas: {e}")
        return False


def example_reportes():
    """Ejemplo de generación de reportes"""
    print("\n🔧 EJEMPLO 5: Generación de Reportes")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config_path = Path(__file__).parent / "config_ingesta.yaml"
        config = load_config(str(config_path))
        
        # Crear manejador de base de datos
        db_handler = create_database_handler(config.storage)
        
        # Crear servicio de auditoría
        auditoria_service = create_auditoria_service(db_handler)
        
        print("✅ Servicio de auditoría creado")
        
        # Generar reporte del último día
        fecha_hasta = datetime.now(timezone.utc)
        fecha_desde = fecha_hasta - timedelta(days=1)
        
        print(f"\n📊 Generando reporte del período: {fecha_desde.strftime('%Y-%m-%d %H:%M')} - {fecha_hasta.strftime('%Y-%m-%d %H:%M')}")
        
        # Reporte en JSON
        reporte_json = auditoria_service.generar_reporte_auditoria(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            formato='json'
        )
        
        if isinstance(reporte_json, dict):
            print("✅ Reporte JSON generado:")
            print(f"   Total de registros: {reporte_json.get('estadisticas', {}).get('total_registros', 0)}")
            print(f"   Usuarios únicos: {reporte_json.get('estadisticas', {}).get('usuarios_unicos', 0)}")
            
            # Mostrar estadísticas por entidad
            entidades = reporte_json.get('estadisticas', {}).get('entidades', {})
            if entidades:
                print("   Registros por entidad:")
                for entidad, count in entidades.items():
                    print(f"     - {entidad}: {count}")
        else:
            print(f"❌ Error generando reporte JSON: {reporte_json}")
        
        # Reporte en CSV
        print("\n📊 Generando reporte CSV...")
        reporte_csv = auditoria_service.generar_reporte_auditoria(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            formato='csv'
        )
        
        if isinstance(reporte_csv, str) and reporte_csv.startswith('ID,Usuario'):
            print("✅ Reporte CSV generado")
            # Mostrar primeras líneas
            lineas = reporte_csv.split('\n')[:5]
            print("   Primeras líneas:")
            for linea in lineas:
                print(f"     {linea}")
        else:
            print(f"❌ Error generando reporte CSV: {reporte_csv}")
        
        # Reporte en HTML
        print("\n📊 Generando reporte HTML...")
        reporte_html = auditoria_service.generar_reporte_auditoria(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            formato='html'
        )
        
        if isinstance(reporte_html, str) and '<html>' in reporte_html:
            print("✅ Reporte HTML generado")
            print(f"   Tamaño del reporte: {len(reporte_html)} caracteres")
        else:
            print(f"❌ Error generando reporte HTML: {reporte_html}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en reportes: {e}")
        return False


def example_sanitizacion():
    """Ejemplo de sanitización de datos sensibles"""
    print("\n🔧 EJEMPLO 6: Sanitización de Datos Sensibles")
    print("=" * 50)
    
    try:
        # Cargar configuración
        config_path = Path(__file__).parent / "config_ingesta.yaml"
        config = load_config(str(config_path))
        
        # Crear manejador de base de datos
        db_handler = create_database_handler(config.storage)
        
        # Crear servicio de auditoría
        auditoria_service = create_auditoria_service(db_handler)
        
        print("✅ Servicio de auditoría creado")
        
        # Establecer contexto de auditoría
        contexto = ContextoAuditoria(
            usuario_id="usuario_test_001",
            ip_origen="192.168.1.200",
            user_agent="TestTool/1.0"
        )
        
        auditoria_service.set_contexto(contexto)
        
        # Datos con información sensible
        datos_sensibles = {
            'username': 'admin',
            'password': 'super_secret_password_123',
            'api_key': 'sk-1234567890abcdef',
            'private_key': '-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...',
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
            'configuracion': {
                'database_url': 'postgresql://user:pass@localhost:5432/db',
                'redis_password': 'redis_secret_456',
                'smtp_password': 'email_password_789'
            },
            'datos_normales': {
                'nombre': 'Sistema IoT',
                'version': '1.0.0',
                'activo': True
            }
        }
        
        print("🔒 Registrando datos con información sensible...")
        
        # Registrar cambio (los datos sensibles se sanitizarán automáticamente)
        success = auditoria_service.auditar_config_middleware(
            config_id="config_seguridad_001",
            accion=AccionAuditoria.CREAR,
            antes={},
            despues=datos_sensibles
        )
        
        if success:
            print("✅ Auditoría con sanitización registrada")
            
            # Verificar que los datos sensibles fueron sanitizados
            print("\n🔍 Verificando sanitización...")
            
            # Consultar el registro reciente
            registros = auditoria_service.obtener_auditoria(
                entidad='config_middleware',
                limite=1
            )
            
            if registros:
                registro = registros[0]
                cambios = registro['cambios']
                
                print("   Datos sanitizados:")
                print(f"     - password: {cambios['despues'].get('password', 'NO_ENCONTRADO')}")
                print(f"     - api_key: {cambios['despues'].get('api_key', 'NO_ENCONTRADO')}")
                print(f"     - private_key: {cambios['despues'].get('private_key', 'NO_ENCONTRADO')}")
                print(f"     - token: {cambios['despues'].get('token', 'NO_ENCONTRADO')}")
                print(f"     - database_url: {cambios['despues'].get('configuracion', {}).get('database_url', 'NO_ENCONTRADO')}")
                
                # Verificar que los datos normales no fueron sanitizados
                print("\n   Datos normales (no sanitizados):")
                print(f"     - nombre: {cambios['despues'].get('datos_normales', {}).get('nombre', 'NO_ENCONTRADO')}")
                print(f"     - version: {cambios['despues'].get('datos_normales', {}).get('version', 'NO_ENCONTRADO')}")
                print(f"     - activo: {cambios['despues'].get('datos_normales', {}).get('activo', 'NO_ENCONTRADO')}")
        else:
            print("❌ Error en auditoría con sanitización")
        
        # Limpiar contexto
        auditoria_service.clear_contexto()
        
        return True
        
    except Exception as e:
        print(f"❌ Error en sanitización: {e}")
        return False


def main():
    """Función principal"""
    print("🚀 Ejemplos de Uso del Sistema de Auditoría")
    print("=" * 60)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    examples = [
        ("Auditoría Básica", example_basic_auditoria),
        ("Context Manager", example_context_manager),
        ("Decoradores", example_decorators),
        ("Consultas", example_consultas_auditoria),
        ("Reportes", example_reportes),
        ("Sanitización", example_sanitizacion),
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
        print("\n💡 El sistema de auditoría está listo para usar en producción")
        print("\n🔧 Funcionalidades implementadas:")
        print("   ✅ Auditoría automática de cambios")
        print("   ✅ Registro de contexto (usuario, IP, etc.)")
        print("   ✅ Sanitización de datos sensibles")
        print("   ✅ Generación de reportes (JSON, CSV, HTML)")
        print("   ✅ Decoradores para auditoría automática")
        print("   ✅ Context managers para auditoría")
        print("   ✅ Middleware para FastAPI")
        return True
    else:
        print("⚠️  Algunos ejemplos fallaron")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
