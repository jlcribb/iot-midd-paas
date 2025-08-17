#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión a PostgreSQL
IoT Middleware
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import yaml
from datetime import datetime

def load_config(config_path):
    """Cargar configuración desde archivo YAML"""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"❌ Archivo de configuración no encontrado: {config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"❌ Error al parsear YAML: {e}")
        return None

def test_postgresql_connection(config):
    """Probar conexión a PostgreSQL"""
    pg_config = config.get('postgresql', {})
    
    print("🔍 Configuración de PostgreSQL:")
    print(f"   Host: {pg_config.get('host', 'N/A')}")
    print(f"   Puerto: {pg_config.get('port', 'N/A')}")
    print(f"   Base de datos: {pg_config.get('database', 'N/A')}")
    print(f"   Usuario: {pg_config.get('username', 'N/A')}")
    print(f"   Esquema: {pg_config.get('schema', 'N/A')}")
    print()
    
    # Parámetros de conexión
    connection_params = {
        'host': pg_config.get('host'),
        'port': pg_config.get('port'),
        'database': pg_config.get('database'),
        'user': pg_config.get('username'),
        'password': pg_config.get('password')
    }
    
    try:
        print("🔌 Intentando conectar a PostgreSQL...")
        conn = psycopg2.connect(**connection_params)
        
        print("✅ Conexión exitosa a PostgreSQL!")
        
        # Crear cursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verificar versión
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"📊 Versión de PostgreSQL: {version['version']}")
            
            # Verificar esquema
            schema = pg_config.get('schema', 'iot_schema')
            cur.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.schemata 
                    WHERE schema_name = %s
                );
            """, (schema,))
            
            if cur.fetchone()['exists']:
                print(f"✅ Esquema '{schema}' existe")
                
                # Listar tablas
                cur.execute(f"""
                    SELECT table_name, table_type 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    ORDER BY table_name;
                """, (schema,))
                
                tables = cur.fetchall()
                print(f"📋 Tablas en el esquema '{schema}':")
                for table in tables:
                    print(f"   - {table['table_name']} ({table['table_type']})")
                
                # Verificar tabla de dispositivos
                cur.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM {schema}.devices;
                """)
                device_count = cur.fetchone()['count']
                print(f"📱 Dispositivos registrados: {device_count}")
                
                # Verificar tabla de sensores
                cur.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM {schema}.sensors;
                """)
                sensor_count = cur.fetchone()['count']
                print(f"📡 Sensores registrados: {sensor_count}")
                
                # Verificar tabla de configuraciones
                cur.execute(f"""
                    SELECT key, value, description 
                    FROM {schema}.configurations 
                    ORDER BY key;
                """)
                configs = cur.fetchall()
                print(f"⚙️  Configuraciones del sistema: {len(configs)}")
                for config_item in configs:
                    print(f"   - {config_item['key']}: {config_item['value']}")
                
            else:
                print(f"❌ El esquema '{schema}' no existe")
                
        conn.close()
        print("🔌 Conexión cerrada correctamente")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except psycopg2.Error as e:
        print(f"❌ Error de PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_sqlalchemy_connection(config):
    """Probar conexión usando SQLAlchemy"""
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError
        
        pg_config = config.get('postgresql', {})
        
        # Construir URL de conexión
        connection_url = f"postgresql://{pg_config.get('username')}:{pg_config.get('password')}@{pg_config.get('host')}:{pg_config.get('port')}/{pg_config.get('database')}"
        
        print("\n🔍 Probando conexión con SQLAlchemy...")
        
        # Crear engine
        engine = create_engine(connection_url, echo=False)
        
        # Probar conexión
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database(), current_user, version();"))
            row = result.fetchone()
            
            print("✅ Conexión SQLAlchemy exitosa!")
            print(f"   Base de datos actual: {row[0]}")
            print(f"   Usuario actual: {row[1]}")
            print(f"   Versión: {row[2]}")
            
        engine.dispose()
        return True
        
    except ImportError:
        print("⚠️  SQLAlchemy no está instalado")
        return False
    except SQLAlchemyError as e:
        print(f"❌ Error de SQLAlchemy: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado con SQLAlchemy: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Prueba de Conexión a PostgreSQL - IoT Middleware")
    print("=" * 60)
    
    # Buscar archivo de configuración
    config_paths = [
        "examples/config_with_postgresql.yaml",
        "examples/config.yaml",
        "../examples/config_with_postgresql.yaml",
        "../examples/config.yaml"
    ]
    
    config = None
    for path in config_paths:
        if os.path.exists(path):
            print(f"📁 Cargando configuración desde: {path}")
            config = load_config(path)
            if config:
                break
    
    if not config:
        print("❌ No se pudo cargar la configuración")
        print("💡 Asegúrate de que el archivo de configuración existe")
        return False
    
    print()
    
    # Probar conexión directa
    pg_success = test_postgresql_connection(config)
    
    # Probar conexión con SQLAlchemy
    sqlalchemy_success = test_sqlalchemy_connection(config)
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS:")
    print(f"   PostgreSQL (psycopg2): {'✅ EXITOSO' if pg_success else '❌ FALLO'}")
    print(f"   SQLAlchemy: {'✅ EXITOSO' if sqlalchemy_success else '❌ FALLO'}")
    
    if pg_success and sqlalchemy_success:
        print("\n🎉 ¡Todas las pruebas fueron exitosas!")
        print("   PostgreSQL está configurado correctamente para el IoT Middleware")
        return True
    else:
        print("\n⚠️  Algunas pruebas fallaron")
        print("   Revisa la configuración y asegúrate de que PostgreSQL esté ejecutándose")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
