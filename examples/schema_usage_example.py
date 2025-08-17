#!/usr/bin/env python3
"""
Ejemplo de Uso de la Nueva Estructura de Datos
IoT Middleware
==============================================

Este script demuestra cómo usar la nueva estructura de datos PostgreSQL
implementada para el sistema IoT Middleware, incluyendo todas las entidades
y funcionalidades avanzadas.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
import uuid

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.storage import create_database_handler
    from iot_middleware.config import load_config
    print("✅ Módulos importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    sys.exit(1)

def example_client_management(handler):
    """Ejemplo de gestión de clientes"""
    print("\n🔧 EJEMPLO 1: Gestión de Clientes")
    print("=" * 60)
    
    try:
        with handler.postgresql_handler.get_session() as session:
            from sqlalchemy import text
            
            # Crear nuevo cliente
            print("📋 Creando nuevo cliente...")
            nuevo_cliente = {
                "nombre": "Industrias Tecnológicas S.A.",
                "sector": "Tecnología",
                "industria": "Software y Servicios",
                "contacto_principal": {
                    "nombre": "Ana Martínez",
                    "email": "ana.martinez@indutech.com",
                    "telefono": "+34 91 123 4567",
                    "cargo": "Directora de Operaciones"
                },
                "contactos_adicionales": [
                    {
                        "nombre": "Carlos Ruiz",
                        "email": "carlos.ruiz@indutech.com",
                        "telefono": "+34 91 123 4568",
                        "cargo": "Gerente de IT",
                        "tipo": "técnico"
                    }
                ],
                "direccion": {
                    "calle": "Calle de la Innovación 123",
                    "ciudad": "Madrid",
                    "estado": "Madrid",
                    "pais": "España",
                    "codigo_postal": "28001"
                }
            }
            
            result = session.execute(text("""
                INSERT INTO iot_schema.clientes (
                    nombre, sector, industria, contacto_principal, 
                    contactos_adicionales, direccion
                ) VALUES (
                    :nombre, :sector, :industria, :contacto_principal,
                    :contactos_adicionales, :direccion
                ) RETURNING id, nombre
            """), nuevo_cliente)
            
            cliente_creado = result.fetchone()
            print(f"   ✅ Cliente creado: {cliente_creado['nombre']} (ID: {cliente_creado['id']})")
            
            # Listar todos los clientes
            print("\n📋 Listando todos los clientes...")
            result = session.execute(text("""
                SELECT id, nombre, sector, industria, 
                       contacto_principal->>'nombre' as contacto_nombre,
                       contacto_principal->>'email' as contacto_email
                FROM iot_schema.clientes 
                WHERE activo = true
                ORDER BY nombre
            """))
            
            clientes = result.fetchall()
            for cliente in clientes:
                print(f"   🏢 {cliente['nombre']} - {cliente['sector']}")
                print(f"      Contacto: {cliente['contacto_nombre']} ({cliente['contacto_email']})")
            
            return True
            
    except Exception as e:
        print(f"❌ Error en gestión de clientes: {e}")
        return False

def example_project_creation(handler):
    """Ejemplo de creación de proyectos"""
    print("\n🔧 EJEMPLO 2: Creación de Proyectos")
    print("=" * 60)
    
    try:
        with handler.postgresql_handler.get_session() as session:
            from sqlalchemy import text
            
            # Obtener cliente existente
            result = session.execute(text("""
                SELECT id, nombre FROM iot_schema.clientes 
                WHERE nombre = 'Industrias Tecnológicas S.A.'
                LIMIT 1
            """))
            
            cliente = result.fetchone()
            if not cliente:
                print("   ❌ Cliente no encontrado")
                return False
            
            # Crear proyecto
            print("📋 Creando nuevo proyecto...")
            nuevo_proyecto = {
                "cliente_id": cliente['id'],
                "nombre": "Monitoreo Inteligente de Edificios",
                "descripcion": "Sistema IoT para monitoreo de temperatura, humedad y consumo energético en edificios corporativos",
                "estado": "planificado",
                "fecha_inicio": datetime.now().date(),
                "fecha_fin": (datetime.now() + timedelta(days=365)).date(),
                "presupuesto": 50000.00,
                "prioridad": 3
            }
            
            result = session.execute(text("""
                INSERT INTO iot_schema.proyectos (
                    cliente_id, nombre, descripcion, estado, 
                    fecha_inicio, fecha_fin, presupuesto, prioridad
                ) VALUES (
                    :cliente_id, :nombre, :descripcion, :estado,
                    :fecha_inicio, :fecha_fin, :presupuesto, :prioridad
                ) RETURNING id, nombre, estado
            """), nuevo_proyecto)
            
            proyecto_creado = result.fetchone()
            print(f"   ✅ Proyecto creado: {proyecto_creado['nombre']} - {proyecto_creado['estado']}")
            
            # Crear unidades del proyecto
            unidades = [
                {
                    "nombre": "Edificio Principal",
                    "descripcion": "Edificio corporativo principal de 20 pisos",
                    "ubicacion": "Centro de Madrid",
                    "responsable": "Ing. Laura Fernández",
                    "lat": 40.4168,
                    "lon": -3.7038
                },
                {
                    "nombre": "Centro de Datos",
                    "descripcion": "Centro de procesamiento de datos",
                    "ubicacion": "Parque Tecnológico de Madrid",
                    "responsable": "Ing. Miguel Ángel López",
                    "lat": 40.4168,
                    "lon": -3.7038
                }
            ]
            
            print("🏢 Creando unidades del proyecto...")
            for unidad in unidades:
                unidad['proyecto_id'] = proyecto_creado['id']
                
                result = session.execute(text("""
                    INSERT INTO iot_schema.unidades_proyecto (
                        proyecto_id, nombre, descripcion, ubicacion, 
                        responsable, lat, lon
                    ) VALUES (
                        :proyecto_id, :nombre, :descripcion, :ubicacion,
                        :responsable, :lat, :lon
                    ) RETURNING id, nombre
                """), unidad)
                
                unidad_creada = result.fetchone()
                print(f"   ✅ Unidad creada: {unidad_creada['nombre']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error en creación de proyectos: {e}")
        return False

def example_device_management(handler):
    """Ejemplo de gestión de dispositivos"""
    print("\n🔧 EJEMPLO 3: Gestión de Dispositivos")
    print("=" * 60)
    
    try:
        with handler.postgresql_handler.get_session() as session:
            from sqlalchemy import text
            
            # Crear dispositivos en el catálogo
            dispositivos = [
                {
                    "tipo": "sensor",
                    "fabricante": "Sensirion",
                    "modelo": "SHT30",
                    "identificador_unico": "SENSOR_TEMP_HUM_001",
                    "protocolo": "MQTT",
                    "vida_util_meses": 60,
                    "especificaciones_tecnicas": {
                        "temperatura": {"rango": [-40, 125], "precision": "±0.2°C"},
                        "humedad": {"rango": [0, 100], "precision": "±2%RH"},
                        "voltaje": "2.4V - 5.5V",
                        "consumo": "2.4µA"
                    }
                },
                {
                    "tipo": "gateway",
                    "fabricante": "Raspberry Pi",
                    "modelo": "4 Model B",
                    "identificador_unico": "GATEWAY_001",
                    "protocolo": "MQTT",
                    "vida_util_meses": 48,
                    "especificaciones_tecnicas": {
                        "procesador": "Broadcom BCM2711",
                        "ram": "4GB LPDDR4",
                        "almacenamiento": "32GB microSD",
                        "conectividad": ["WiFi 802.11ac", "Bluetooth 5.0", "Ethernet"]
                    }
                }
            ]
            
            print("📱 Creando dispositivos en el catálogo...")
            dispositivos_creados = []
            
            for dispositivo in dispositivos:
                result = session.execute(text("""
                    INSERT INTO iot_schema.dispositivos (
                        tipo, fabricante, modelo, identificador_unico,
                        protocolo, vida_util_meses, especificaciones_tecnicas
                    ) VALUES (
                        :tipo, :fabricante, :modelo, :identificador_unico,
                        :protocolo, :vida_util_meses, :especificaciones_tecnicas
                    ) RETURNING id, tipo, modelo, identificador_unico
                """), dispositivo)
                
                dispositivo_creado = result.fetchone()
                dispositivos_creados.append(dispositivo_creado)
                print(f"   ✅ Dispositivo creado: {dispositivo_creado['tipo']} {dispositivo_creado['modelo']}")
            
            # Obtener proyecto existente
            result = session.execute(text("""
                SELECT id, nombre FROM iot_schema.proyectos 
                WHERE nombre = 'Monitoreo Inteligente de Edificios'
                LIMIT 1
            """))
            
            proyecto = result.fetchone()
            if not proyecto:
                print("   ❌ Proyecto no encontrado")
                return False
            
            # Obtener unidad existente
            result = session.execute(text("""
                SELECT id, nombre FROM iot_schema.unidades_proyecto 
                WHERE nombre = 'Edificio Principal'
                LIMIT 1
            """))
            
            unidad = result.fetchone()
            if not unidad:
                print("   ❌ Unidad no encontrada")
                return False
            
            # Asignar dispositivos al proyecto
            print("🔗 Asignando dispositivos al proyecto...")
            for dispositivo in dispositivos_creados:
                asignacion = {
                    "proyecto_id": proyecto['id'],
                    "dispositivo_id": dispositivo['id'],
                    "unidad_id": unidad['id'],
                    "nombre_personalizado": f"{dispositivo['tipo'].title()} {dispositivo['modelo']} - {unidad['nombre']}",
                    "descripcion": f"Dispositivo instalado en {unidad['nombre']}",
                    "ubicacion_fisica": "Piso 5, Sala de Servidores",
                    "responsable": "Ing. Laura Fernández",
                    "responsable_email": "laura.fernandez@indutech.com"
                }
                
                result = session.execute(text("""
                    INSERT INTO iot_schema.dispositivos_proyecto (
                        proyecto_id, dispositivo_id, unidad_id, nombre_personalizado,
                        descripcion, ubicacion_fisica, responsable, responsable_email
                    ) VALUES (
                        :proyecto_id, :dispositivo_id, :unidad_id, :nombre_personalizado,
                        :descripcion, :ubicacion_fisica, :responsable, :responsable_email
                    ) RETURNING id, nombre_personalizado
                """), asignacion)
                
                asignacion_creada = result.fetchone()
                print(f"   ✅ Dispositivo asignado: {asignacion_creada['nombre_personalizado']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error en gestión de dispositivos: {e}")
        return False

def example_channel_creation(handler):
    """Ejemplo de creación de canales/sensores"""
    print("\n🔧 EJEMPLO 4: Creación de Canales/Sensores")
    print("=" * 60)
    
    try:
        with handler.postgresql_handler.get_session() as session:
            from sqlalchemy import text
            
            # Obtener dispositivo existente
            result = session.execute(text("""
                SELECT id, tipo, modelo FROM iot_schema.dispositivos 
                WHERE identificador_unico = 'SENSOR_TEMP_HUM_001'
                LIMIT 1
            """))
            
            dispositivo = result.fetchone()
            if not dispositivo:
                print("   ❌ Dispositivo no encontrado")
                return False
            
            # Crear canales para el sensor
            canales = [
                {
                    "nombre": "temperature",
                    "etiqueta": "Temperatura Ambiente",
                    "descripcion": "Sensor de temperatura ambiente del SHT30",
                    "unidad_medida": "°C",
                    "tipo": "float",
                    "rango_min": -40.0,
                    "rango_max": 125.0,
                    "precision_valor": 1,
                    "frecuencia_muestreo": 60,
                    "umbral_alto": 30.0,
                    "umbral_bajo": 15.0,
                    "metadatos": {
                        "topic": "iot/sensor_001/temperature",
                        "qos": 1,
                        "retain": False
                    }
                },
                {
                    "nombre": "humidity",
                    "etiqueta": "Humedad Relativa",
                    "descripcion": "Sensor de humedad relativa del SHT30",
                    "unidad_medida": "%RH",
                    "tipo": "float",
                    "rango_min": 0.0,
                    "rango_max": 100.0,
                    "precision_valor": 1,
                    "frecuencia_muestreo": 60,
                    "umbral_alto": 80.0,
                    "umbral_bajo": 20.0,
                    "metadatos": {
                        "topic": "iot/sensor_001/humidity",
                        "qos": 1,
                        "retain": False
                    }
                }
            ]
            
            print("📡 Creando canales para el sensor...")
            for canal in canales:
                canal['dispositivo_id'] = dispositivo['id']
                
                result = session.execute(text("""
                    INSERT INTO iot_schema.canales (
                        dispositivo_id, nombre, etiqueta, descripcion,
                        unidad_medida, tipo, rango_min, rango_max,
                        precision_valor, frecuencia_muestreo, umbral_alto, umbral_bajo,
                        metadatos
                    ) VALUES (
                        :dispositivo_id, :nombre, :etiqueta, :descripcion,
                        :unidad_medida, :tipo, :rango_min, :rango_max,
                        :precision_valor, :frecuencia_muestreo, :umbral_alto, :umbral_bajo,
                        :metadatos
                    ) RETURNING id, nombre, etiqueta, unidad_medida
                """), canal)
                
                canal_creado = result.fetchone()
                print(f"   ✅ Canal creado: {canal_creado['etiqueta']} ({canal_creado['unidad_medida']})")
            
            return True
            
    except Exception as e:
        print(f"❌ Error en creación de canales: {e}")
        return False

def example_data_insertion(handler):
    """Ejemplo de inserción de datos en la nueva estructura"""
    print("\n🔧 EJEMPLO 5: Inserción de Datos")
    print("=" * 60)
    
    try:
        with handler.postgresql_handler.get_session() as session:
            from sqlalchemy import text
            
            # Obtener canal de temperatura
            result = session.execute(text("""
                SELECT c.id, c.nombre, c.etiqueta, c.unidad_medida,
                       d.identificador_unico, dp.nombre_personalizado
                FROM iot_schema.canales c
                JOIN iot_schema.dispositivos d ON c.dispositivo_id = d.id
                JOIN iot_schema.dispositivos_proyecto dp ON d.id = dp.dispositivo_id
                WHERE c.nombre = 'temperature'
                LIMIT 1
            """))
            
            canal = result.fetchone()
            if not canal:
                print("   ❌ Canal no encontrado")
                return False
            
            print(f"📊 Insertando datos en canal: {canal['etiqueta']}")
            print(f"   Dispositivo: {canal['nombre_personalizado']}")
            print(f"   Unidad: {canal['unidad_medida']}")
            
            # Generar datos de ejemplo (últimas 24 horas)
            base_time = datetime.now(timezone.utc)
            datos_ejemplo = []
            
            for i in range(24):
                # Simular lecturas cada hora con variación realista
                timestamp = base_time - timedelta(hours=i)
                temperatura = 22.0 + (i % 6 - 3) + (i % 3 - 1) * 0.5  # Variación entre 18-26°C
                
                datos_ejemplo.append({
                    "canal_id": canal['id'],
                    "ts": timestamp,
                    "valor_num": round(temperatura, 1),
                    "calidad": "OK",
                    "calidad_porcentaje": 95,
                    "metadata": {
                        "qos": 1,
                        "device_status": "online",
                        "rssi": -45,
                        "battery": 85
                    },
                    "procesado": True,
                    "validado": True
                })
            
            # Insertar datos
            print(f"   📨 Insertando {len(datos_ejemplo)} registros...")
            
            for i, dato in enumerate(datos_ejemplo, 1):
                result = session.execute(text("""
                    INSERT INTO iot_schema.registros_datos (
                        canal_id, ts, valor_num, calidad, calidad_porcentaje,
                        metadata, procesado, validado
                    ) VALUES (
                        :canal_id, :ts, :valor_num, :calidad, :calidad_porcentaje,
                        :metadata, :procesado, :validado
                    ) RETURNING id, ts, valor_num
                """), dato)
                
                if i % 6 == 0:  # Mostrar progreso cada 6 registros
                    registro = result.fetchone()
                    print(f"      ✅ Registro {i}: {registro['valor_num']}°C a las {registro['ts'].strftime('%H:%M')}")
            
            print(f"   🎯 Total de registros insertados: {len(datos_ejemplo)}")
            
            # Verificar inserción
            result = session.execute(text("""
                SELECT COUNT(*) as total,
                       MIN(ts) as primer_registro,
                       MAX(ts) as ultimo_registro,
                       AVG(valor_num) as temperatura_promedio
                FROM iot_schema.registros_datos
                WHERE canal_id = :canal_id
            """), {"canal_id": canal['id']})
            
            estadisticas = result.fetchone()
            print(f"\n📈 Estadísticas del canal:")
            print(f"   Total de registros: {estadisticas['total']}")
            print(f"   Rango temporal: {estadisticas['primer_registro'].strftime('%Y-%m-%d %H:%M')} - {estadisticas['ultimo_registro'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   Temperatura promedio: {estadisticas['temperatura_promedio']:.1f}°C")
            
            return True
            
    except Exception as e:
        print(f"❌ Error en inserción de datos: {e}")
        return False

def example_queries_and_views(handler):
    """Ejemplo de consultas y vistas"""
    print("\n🔧 EJEMPLO 6: Consultas y Vistas")
    print("=" * 60)
    
    try:
        with handler.postgresql_handler.get_session() as session:
            from sqlalchemy import text
            
            # Consultar vista de resumen de proyectos
            print("📋 Resumen de proyectos:")
            result = session.execute(text("""
                SELECT nombre, estado, cliente_nombre, total_unidades, total_dispositivos, total_canales
                FROM iot_schema.v_resumen_proyectos
                ORDER BY nombre
            """))
            
            proyectos = result.fetchall()
            for proyecto in proyectos:
                print(f"   🏢 {proyecto['nombre']} ({proyecto['estado']})")
                print(f"      Cliente: {proyecto['cliente_nombre']}")
                print(f"      Unidades: {proyecto['total_unidades']}, Dispositivos: {proyecto['total_dispositivos']}, Canales: {proyecto['total_canales']}")
            
            # Consultar vista de resumen de dispositivos
            print("\n📱 Resumen de dispositivos:")
            result = session.execute(text("""
                SELECT nombre_personalizado, tipo, fabricante, modelo, protocolo, proyecto_nombre, unidad_nombre
                FROM iot_schema.v_resumen_dispositivos
                ORDER BY proyecto_nombre, unidad_nombre
            """))
            
            dispositivos = result.fetchall()
            for dispositivo in dispositivos:
                print(f"   📱 {dispositivo['nombre_personalizado']}")
                print(f"      Tipo: {dispositivo['tipo']}, Fabricante: {dispositivo['fabricante']}")
                print(f"      Protocolo: {dispositivo['protocolo']}, Proyecto: {dispositivo['proyecto_nombre']}")
                print(f"      Unidad: {dispositivo['unidad_nombre']}")
            
            # Consulta personalizada: datos de temperatura de las últimas 6 horas
            print("\n🌡️ Datos de temperatura (últimas 6 horas):")
            result = session.execute(text("""
                SELECT 
                    rd.ts,
                    rd.valor_num,
                    rd.calidad,
                    rd.calidad_porcentaje,
                    c.etiqueta,
                    c.unidad_medida,
                    d.identificador_unico,
                    dp.nombre_personalizado
                FROM iot_schema.registros_datos rd
                JOIN iot_schema.canales c ON rd.canal_id = c.id
                JOIN iot_schema.dispositivos d ON c.dispositivo_id = d.id
                JOIN iot_schema.dispositivos_proyecto dp ON d.id = dp.dispositivo_id
                WHERE c.nombre = 'temperature'
                  AND rd.ts >= NOW() - INTERVAL '6 hours'
                ORDER BY rd.ts DESC
                LIMIT 10
            """))
            
            datos_temperatura = result.fetchall()
            for dato in datos_temperatura:
                print(f"   📊 {dato['ts'].strftime('%H:%M')}: {dato['valor_num']}{dato['unidad_medida']} "
                      f"({dato['calidad']}, {dato['calidad_porcentaje']}%)")
                print(f"      Dispositivo: {dato['nombre_personalizado']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error en consultas y vistas: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Ejemplos de Uso de la Nueva Estructura de Datos")
    print("=" * 70)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Cargar configuración
        config = load_config()
        
        # Crear manejador de base de datos
        handler = create_database_handler(
            config.postgresql,
            config.influxdb,
            config.storage
        )
        
        # Verificar conexión
        status = handler.get_connection_status()
        if not status.get('postgresql') or status['postgresql'].value != 'connected':
            print("❌ No se pudo conectar a PostgreSQL")
            print("💡 Ejecutar primero: python3 scripts/apply_schema.py")
            return False
        
        examples = [
            ("Gestión de Clientes", example_client_management),
            ("Creación de Proyectos", example_project_creation),
            ("Gestión de Dispositivos", example_device_management),
            ("Creación de Canales", example_channel_creation),
            ("Inserción de Datos", example_data_insertion),
            ("Consultas y Vistas", example_queries_and_views),
        ]
        
        results = []
        
        for example_name, example_func in examples:
            print(f"\n{'='*20} {example_name} {'='*20}")
            try:
                success = example_func(handler)
                results.append((example_name, success))
            except Exception as e:
                print(f"❌ Error inesperado en {example_name}: {e}")
                results.append((example_name, False))
        
        # Resumen de resultados
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE EJEMPLOS")
        print("=" * 70)
        
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
            print("\n💡 La nueva estructura de datos está funcionando correctamente")
            print("   ✅ Gestión de clientes y proyectos")
            print("   ✅ Gestión de dispositivos y canales")
            print("   ✅ Inserción y consulta de datos")
            print("   ✅ Vistas y consultas optimizadas")
            return True
        else:
            print("⚠️  Algunos ejemplos fallaron")
            print("   🔍 Revisar los logs de error para identificar problemas")
            return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cerrar conexiones
        if 'handler' in locals():
            handler.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
