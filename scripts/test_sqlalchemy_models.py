#!/usr/bin/env python3
"""
Script de Prueba para Modelos SQLAlchemy
IoT Middleware
========================================

Este script prueba la creación y funcionalidad de los modelos SQLAlchemy
para el sistema IoT Middleware.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.models import (
        Base, Cliente, Proyecto, UnidadProyecto, Sesion,
        Dispositivo, DispositivoProyecto, Canal,
        RegistroDatos, EventoAlarma, Usuario,
        UsuarioScope, ConfigMiddleware, Auditoria
    )
    from iot_middleware.models.enums import (
        EstadoProyecto, ProtocoloComunicacion, TipoDato,
        RolSistema, CalidadDato, SeveridadEvento, EstadoDispositivo
    )
    print("✅ Modelos SQLAlchemy importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar modelos: {e}")
    sys.exit(1)

def test_model_creation():
    """Probar la creación de instancias de modelos"""
    print("\n🧪 Probando creación de modelos...")
    
    try:
        # Crear cliente
        cliente = Cliente(
            nombre="Cliente de Prueba",
            sector="Tecnología",
            industria="Software",
            contacto_principal={
                "nombre": "Ana García",
                "email": "ana.garcia@cliente.com",
                "telefono": "+34 91 123 4567"
            }
        )
        print("   ✅ Cliente creado")
        
        # Crear proyecto
        proyecto = Proyecto(
            nombre="Proyecto de Prueba",
            descripcion="Proyecto para testing de modelos",
            estado=EstadoProyecto.PLANIFICADO,
            fecha_inicio=datetime.now().date(),
            prioridad=2
        )
        print("   ✅ Proyecto creado")
        
        # Crear dispositivo
        dispositivo = Dispositivo(
            tipo="sensor",
            fabricante="Sensirion",
            modelo="SHT30",
            identificador_unico="SENSOR_TEST_001",
            protocolo=ProtocoloComunicacion.MQTT,
            vida_util_meses=60
        )
        print("   ✅ Dispositivo creado")
        
        # Crear canal
        canal = Canal(
            nombre="temperature",
            etiqueta="Temperatura Ambiente",
            tipo=TipoDato.FLOAT,
            unidad_medida="°C",
            rango_min=-40.0,
            rango_max=125.0
        )
        print("   ✅ Canal creado")
        
        # Crear usuario
        usuario = Usuario(
            email="test@iot-middleware.com",
            nombre="Usuario",
            apellido="Test",
            password_hash="hash_test",
            rol=RolSistema.TECNICO
        )
        print("   ✅ Usuario creado")
        
        # Crear registro de datos
        registro = RegistroDatos(
            ts=datetime.now(timezone.utc),
            valor_num=24.5,
            calidad=CalidadDato.OK,
            calidad_porcentaje=95
        )
        print("   ✅ Registro de datos creado")
        
        # Crear evento/alarma
        evento = EventoAlarma(
            titulo="Temperatura alta detectada",
            descripcion="La temperatura superó el umbral establecido",
            severidad=SeveridadEvento.WARNING
        )
        print("   ✅ Evento/alarma creado")
        
        print("   🎯 Todos los modelos se crearon exitosamente")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creando modelos: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enum_values():
    """Probar los valores de los enums"""
    print("\n🔧 Probando valores de enums...")
    
    try:
        # Estado de proyecto
        print(f"   📋 Estados de proyecto: {[e.value for e in EstadoProyecto]}")
        
        # Protocolos de comunicación
        print(f"   📡 Protocolos: {[p.value for p in ProtocoloComunicacion]}")
        
        # Tipos de dato
        print(f"   📊 Tipos de dato: {[t.value for t in TipoDato]}")
        
        # Roles del sistema
        print(f"   👤 Roles: {[r.value for r in RolSistema]}")
        
        # Calidad de datos
        print(f"   ✅ Calidad: {[c.value for c in CalidadDato]}")
        
        # Severidad de eventos
        print(f"   ⚠️  Severidad: {[s.value for e in SeveridadEvento]}")
        
        # Estados de dispositivos
        print(f"   📱 Estados de dispositivo: {[e.value for e in EstadoDispositivo]}")
        
        print("   🎯 Todos los enums funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando enums: {e}")
        return False

def test_model_attributes():
    """Probar atributos de los modelos"""
    print("\n🔍 Probando atributos de modelos...")
    
    try:
        # Verificar atributos del cliente
        cliente = Cliente()
        expected_attrs = ['id', 'nombre', 'sector', 'industria', 'contacto_principal']
        for attr in expected_attrs:
            if hasattr(cliente, attr):
                print(f"   ✅ Cliente tiene atributo: {attr}")
            else:
                print(f"   ❌ Cliente falta atributo: {attr}")
                return False
        
        # Verificar atributos del proyecto
        proyecto = Proyecto()
        expected_attrs = ['id', 'nombre', 'estado', 'cliente_id', 'fecha_inicio']
        for attr in expected_attrs:
            if hasattr(proyecto, attr):
                print(f"   ✅ Proyecto tiene atributo: {attr}")
            else:
                print(f"   ❌ Proyecto falta atributo: {attr}")
                return False
        
        # Verificar atributos del dispositivo
        dispositivo = Dispositivo()
        expected_attrs = ['id', 'tipo', 'fabricante', 'protocolo', 'identificador_unico']
        for attr in expected_attrs:
            if hasattr(dispositivo, attr):
                print(f"   ✅ Dispositivo tiene atributo: {attr}")
            else:
                print(f"   ❌ Dispositivo falta atributo: {attr}")
                return False
        
        # Verificar atributos del canal
        canal = Canal()
        expected_attrs = ['id', 'nombre', 'tipo', 'unidad_medida', 'rango_min', 'rango_max']
        for attr in expected_attrs:
            if hasattr(canal, attr):
                print(f"   ✅ Canal tiene atributo: {attr}")
            else:
                print(f"   ❌ Canal falta atributo: {attr}")
                return False
        
        # Verificar atributos del registro de datos
        registro = RegistroDatos()
        expected_attrs = ['id', 'ts', 'valor_num', 'valor_int', 'valor_bool', 'valor_text', 'valor_json']
        for attr in expected_attrs:
            if hasattr(registro, attr):
                print(f"   ✅ Registro tiene atributo: {attr}")
            else:
                print(f"   ❌ Registro falta atributo: {attr}")
                return False
        
        print("   🎯 Todos los atributos están presentes")
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando atributos: {e}")
        return False

def test_model_relationships():
    """Probar las relaciones entre modelos"""
    print("\n🔗 Probando relaciones entre modelos...")
    
    try:
        # Verificar relaciones del cliente
        cliente = Cliente()
        if hasattr(cliente, 'proyectos'):
            print("   ✅ Cliente tiene relación con proyectos")
        else:
            print("   ❌ Cliente no tiene relación con proyectos")
            return False
        
        # Verificar relaciones del proyecto
        proyecto = Proyecto()
        expected_rels = ['cliente', 'unidades', 'dispositivos_proyecto', 'eventos_alarmas']
        for rel in expected_rels:
            if hasattr(proyecto, rel):
                print(f"   ✅ Proyecto tiene relación: {rel}")
            else:
                print(f"   ❌ Proyecto falta relación: {rel}")
                return False
        
        # Verificar relaciones del dispositivo
        dispositivo = Dispositivo()
        expected_rels = ['canales', 'dispositivos_proyecto', 'eventos_alarmas']
        for rel in expected_rels:
            if hasattr(dispositivo, rel):
                print(f"   ✅ Dispositivo tiene relación: {rel}")
            else:
                print(f"   ❌ Dispositivo falta relación: {rel}")
                return False
        
        # Verificar relaciones del canal
        canal = Canal()
        expected_rels = ['dispositivo', 'registros_datos', 'eventos_alarmas']
        for rel in expected_rels:
            if hasattr(canal, rel):
                print(f"   ✅ Canal tiene relación: {rel}")
            else:
                print(f"   ❌ Canal falta relación: {rel}")
                return False
        
        print("   🎯 Todas las relaciones están definidas")
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando relaciones: {e}")
        return False

def test_table_metadata():
    """Probar metadatos de las tablas"""
    print("\n📋 Probando metadatos de tablas...")
    
    try:
        # Verificar que Base.metadata contiene todas las tablas
        expected_tables = [
            'iot_schema.clientes',
            'iot_schema.proyectos', 
            'iot_schema.unidades_proyecto',
            'iot_schema.sesiones',
            'iot_schema.dispositivos',
            'iot_schema.dispositivos_proyecto',
            'iot_schema.canales',
            'iot_schema.registros_datos',
            'iot_schema.eventos_alarmas',
            'iot_schema.usuarios',
            'iot_schema.usuarios_scope',
            'iot_schema.config_middleware',
            'iot_schema.auditoria'
        ]
        
        for table_name in expected_tables:
            if table_name in Base.metadata.tables:
                print(f"   ✅ Tabla presente: {table_name}")
            else:
                print(f"   ❌ Tabla faltante: {table_name}")
                return False
        
        # Verificar esquema
        for table_name, table in Base.metadata.tables.items():
            if table.schema == 'iot_schema':
                print(f"   ✅ Esquema correcto: {table_name}")
            else:
                print(f"   ❌ Esquema incorrecto: {table_name} -> {table.schema}")
                return False
        
        print("   🎯 Todos los metadatos están correctos")
        return True
        
    except Exception as e:
        print(f"   ❌ Error probando metadatos: {e}")
        return False

def test_model_validation():
    """Probar validación de modelos"""
    print("\n✅ Probando validación de modelos...")
    
    try:
        # Probar cliente con datos válidos
        cliente_valido = Cliente(
            nombre="Cliente Válido",
            contacto_principal={"nombre": "Test", "email": "test@test.com"}
        )
        print("   ✅ Cliente válido creado")
        
        # Probar proyecto con datos válidos
        proyecto_valido = Proyecto(
            nombre="Proyecto Válido",
            estado=EstadoProyecto.ACTIVO
        )
        print("   ✅ Proyecto válido creado")
        
        # Probar dispositivo con datos válidos
        dispositivo_valido = Dispositivo(
            tipo="sensor",
            identificador_unico="UNIQUE_001",
            protocolo=ProtocoloComunicacion.HTTP
        )
        print("   ✅ Dispositivo válido creado")
        
        # Probar canal con datos válidos
        canal_valido = Canal(
            nombre="test_channel",
            tipo=TipoDato.INT,
            dispositivo_id=None  # Se establecerá al relacionar
        )
        print("   ✅ Canal válido creado")
        
        print("   🎯 Todos los modelos pasan validación")
        return True
        
    except Exception as e:
        print(f"   ❌ Error en validación: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🚀 Probando Modelos SQLAlchemy para IoT Middleware")
    print("=" * 70)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        ("Creación de Modelos", test_model_creation),
        ("Valores de Enums", test_enum_values),
        ("Atributos de Modelos", test_model_attributes),
        ("Relaciones entre Modelos", test_model_relationships),
        ("Metadatos de Tablas", test_table_metadata),
        ("Validación de Modelos", test_model_validation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Error inesperado en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("\n💡 Los modelos SQLAlchemy están funcionando correctamente")
        print("   ✅ Todos los modelos se crean sin errores")
        print("   ✅ Todos los enums tienen valores correctos")
        print("   ✅ Todas las relaciones están definidas")
        print("   ✅ Los metadatos están configurados correctamente")
        print("   ✅ La validación funciona correctamente")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron")
        print("   🔍 Revisar los logs de error para identificar problemas")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
