"""Partitioning System for IoT Middleware

Revision ID: 0002
Revises: 0001
Create Date: 2025-08-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Implementar sistema de particiones mensuales para registros_datos"""
    
    # 1. Crear función para crear particiones mensuales
    op.execute("""
        CREATE OR REPLACE FUNCTION iot_schema.fn_crear_particion_registros(fecha DATE)
        RETURNS TEXT
        LANGUAGE plpgsql
        AS $$
        DECLARE
            nombre_particion TEXT;
            nombre_tabla TEXT;
            fecha_inicio DATE;
            fecha_fin DATE;
            sql_crear TEXT;
            sql_indices TEXT;
            resultado TEXT;
        BEGIN
            -- Generar nombre de la partición (formato: YYYY_MM)
            nombre_particion := 'registros_datos_' || TO_CHAR(fecha, 'YYYY_MM');
            nombre_tabla := 'iot_schema.' || nombre_particion;
            
            -- Calcular rango de fechas para la partición
            fecha_inicio := DATE_TRUNC('month', fecha);
            fecha_fin := fecha_inicio + INTERVAL '1 month' - INTERVAL '1 day';
            
            -- Verificar si la partición ya existe
            IF EXISTS (
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE c.relname = nombre_particion 
                AND n.nspname = 'iot_schema'
            ) THEN
                RETURN 'La partición ' || nombre_particion || ' ya existe';
            END IF;
            
            -- Crear la partición
            sql_crear := 'CREATE TABLE ' || nombre_tabla || ' PARTITION OF iot_schema.registros_datos
                          FOR VALUES FROM (''' || fecha_inicio || ''') TO (''' || (fecha_fin + INTERVAL '1 day') || ''')';
            
            EXECUTE sql_crear;
            
            -- Crear índices en la partición (PostgreSQL los hereda automáticamente)
            -- Pero podemos crear índices específicos para optimización
            sql_indices := 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_' || nombre_particion || '_canal_ts 
                           ON ' || nombre_tabla || ' (canal_id, ts)';
            EXECUTE sql_indices;
            
            sql_indices := 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_' || nombre_particion || '_ts 
                           ON ' || nombre_tabla || ' (ts)';
            EXECUTE sql_indices;
            
            sql_indices := 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_' || nombre_particion || '_calidad 
                           ON ' || nombre_tabla || ' (calidad)';
            EXECUTE sql_indices;
            
            -- Registrar la creación en la tabla de control de particiones
            INSERT INTO iot_schema.control_particiones (nombre_particion, fecha_inicio, fecha_fin, creada_en, estado)
            VALUES (nombre_particion, fecha_inicio, fecha_fin, NOW(), 'activa')
            ON CONFLICT (nombre_particion) DO UPDATE SET
                fecha_inicio = EXCLUDED.fecha_inicio,
                fecha_fin = EXCLUDED.fecha_fin,
                actualizado_en = NOW(),
                estado = 'activa';
            
            resultado := 'Partición ' || nombre_particion || ' creada exitosamente para el rango ' || 
                        fecha_inicio || ' a ' || fecha_fin;
            
            RETURN resultado;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN 'Error al crear partición ' || nombre_particion || ': ' || SQLERRM;
        END;
        $$;
    """)
    
    # 2. Crear función para crear particiones automáticamente
    op.execute("""
        CREATE OR REPLACE FUNCTION iot_schema.fn_crear_particiones_automaticas()
        RETURNS TEXT
        LANGUAGE plpgsql
        AS $$
        DECLARE
            mes_actual DATE;
            mes_siguiente DATE;
            resultado TEXT;
            resultado_actual TEXT;
            resultado_siguiente TEXT;
        BEGIN
            -- Obtener mes actual y siguiente
            mes_actual := DATE_TRUNC('month', CURRENT_DATE);
            mes_siguiente := mes_actual + INTERVAL '1 month';
            
            -- Crear partición del mes actual
            resultado_actual := iot_schema.fn_crear_particion_registros(mes_actual);
            
            -- Crear partición del mes siguiente
            resultado_siguiente := iot_schema.fn_crear_particion_registros(mes_siguiente);
            
            resultado := 'Mes actual: ' || resultado_actual || ' | Mes siguiente: ' || resultado_siguiente;
            
            RETURN resultado;
        END;
        $$;
    """)
    
    # 3. Crear tabla de control de particiones
    op.create_table(
        'control_particiones',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('nombre_particion', sa.Text, nullable=False, unique=True),
        sa.Column('fecha_inicio', sa.Date, nullable=False),
        sa.Column('fecha_fin', sa.Date, nullable=False),
        sa.Column('estado', sa.String(20), nullable=False, server_default='activa'),
        sa.Column('registros_totales', sa.BigInteger, server_default='0'),
        sa.Column('tamaño_bytes', sa.BigInteger, server_default='0'),
        sa.Column('creada_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('actualizado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='iot_schema'
    )
    
    # 4. Crear trigger para validar inserción en particiones existentes
    op.execute("""
        CREATE OR REPLACE FUNCTION iot_schema.fn_validar_particion_registros()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        DECLARE
            nombre_particion TEXT;
            fecha_particion DATE;
            particion_existe BOOLEAN;
        BEGIN
            -- Obtener la fecha del registro a insertar
            fecha_particion := DATE_TRUNC('month', NEW.ts);
            nombre_particion := 'registros_datos_' || TO_CHAR(fecha_particion, 'YYYY_MM');
            
            -- Verificar si la partición existe
            SELECT EXISTS (
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE c.relname = nombre_particion 
                AND n.nspname = 'iot_schema'
            ) INTO particion_existe;
            
            -- Si la partición no existe, crearla automáticamente
            IF NOT particion_existe THEN
                PERFORM iot_schema.fn_crear_particion_registros(fecha_particion);
                RAISE NOTICE 'Partición % creada automáticamente para la fecha %', nombre_particion, fecha_particion;
            END IF;
            
            RETURN NEW;
        END;
        $$;
    """)
    
    # 5. Crear el trigger en la tabla registros_datos
    op.execute("""
        CREATE TRIGGER tr_validar_particion_registros
        BEFORE INSERT ON iot_schema.registros_datos
        FOR EACH ROW
        EXECUTE FUNCTION iot_schema.fn_validar_particion_registros();
    """)
    
    # 6. Crear función para limpiar particiones antiguas
    op.execute("""
        CREATE OR REPLACE FUNCTION iot_schema.fn_limpiar_particiones_antiguas(meses_retener INTEGER DEFAULT 12)
        RETURNS TEXT
        LANGUAGE plpgsql
        AS $$
        DECLARE
            fecha_limite DATE;
            particion_a_eliminar RECORD;
            resultado TEXT;
            total_eliminadas INTEGER := 0;
        BEGIN
            -- Calcular fecha límite (meses a retener)
            fecha_limite := DATE_TRUNC('month', CURRENT_DATE) - (meses_retener || ' months')::INTERVAL;
            
            -- Buscar particiones a eliminar
            FOR particion_a_eliminar IN
                SELECT nombre_particion, fecha_inicio
                FROM iot_schema.control_particiones
                WHERE fecha_inicio < fecha_limite
                AND estado = 'activa'
                ORDER BY fecha_inicio
            LOOP
                -- Marcar como inactiva en lugar de eliminar físicamente
                UPDATE iot_schema.control_particiones
                SET estado = 'archivada', actualizado_en = NOW()
                WHERE nombre_particion = particion_a_eliminar.nombre_particion;
                
                total_eliminadas := total_eliminadas + 1;
                resultado := resultado || 'Partición ' || particion_a_eliminar.nombre_particion || ' marcada como archivada' || E'\n';
            END LOOP;
            
            IF total_eliminadas = 0 THEN
                resultado := 'No se encontraron particiones para archivar';
            ELSE
                resultado := 'Total de particiones archivadas: ' || total_eliminadas || E'\n' || resultado;
            END IF;
            
            RETURN resultado;
        END;
        $$;
    """)
    
    # 7. Crear función para obtener estadísticas de particiones
    op.execute("""
        CREATE OR REPLACE FUNCTION iot_schema.fn_estadisticas_particiones()
        RETURNS TABLE (
            nombre_particion TEXT,
            fecha_inicio DATE,
            fecha_fin DATE,
            estado TEXT,
            registros_totales BIGINT,
            tamaño_mb NUMERIC,
            creada_en TIMESTAMP WITH TIME ZONE
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                cp.nombre_particion,
                cp.fecha_inicio,
                cp.fecha_fin,
                cp.estado,
                cp.registros_totales,
                ROUND(cp.tamaño_bytes / 1024.0 / 1024.0, 2) as tamaño_mb,
                cp.creada_en
            FROM iot_schema.control_particiones cp
            ORDER BY cp.fecha_inicio DESC;
        END;
        $$;
    """)
    
    # 8. Crear índices para la tabla de control
    op.create_index('idx_control_particiones_fecha', 'control_particiones', ['fecha_inicio'], schema='iot_schema')
    op.create_index('idx_control_particiones_estado', 'control_particiones', ['estado'], schema='iot_schema')
    op.create_index('idx_control_particiones_nombre', 'control_particiones', ['nombre_particion'], schema='iot_schema')
    
    # 9. Crear particiones iniciales para el mes actual y siguiente
    op.execute("SELECT iot_schema.fn_crear_particiones_automaticas()")
    
    # 10. Crear vista para monitoreo de particiones
    op.execute("""
        CREATE OR REPLACE VIEW iot_schema.v_monitoreo_particiones AS
        SELECT 
            cp.nombre_particion,
            cp.fecha_inicio,
            cp.fecha_fin,
            cp.estado,
            cp.registros_totales,
            ROUND(cp.tamaño_bytes / 1024.0 / 1024.0, 2) as tamaño_mb,
            cp.creada_en,
            cp.actualizado_en,
            CASE 
                WHEN cp.estado = 'activa' AND cp.fecha_fin < CURRENT_DATE THEN 'retrasada'
                WHEN cp.estado = 'activa' AND cp.fecha_inicio <= CURRENT_DATE AND cp.fecha_fin >= CURRENT_DATE THEN 'actual'
                WHEN cp.estado = 'activa' AND cp.fecha_inicio > CURRENT_DATE THEN 'futura'
                ELSE cp.estado
            END as estado_operativo
        FROM iot_schema.control_particiones cp
        ORDER BY cp.fecha_inicio DESC;
    """)
    
    # 11. Insertar configuración del sistema de particiones
    op.execute("""
        INSERT INTO iot_schema.config_middleware (clave, valor, descripcion, categoria, version)
        VALUES (
            'partitioning.auto_create', 
            '{"enabled": true, "months_ahead": 1, "retention_months": 12}',
            'Configuración del sistema de particiones automáticas',
            'database',
            1
        );
    """)


def downgrade() -> None:
    """Revertir el sistema de particiones"""
    
    # Eliminar vistas
    op.execute('DROP VIEW IF EXISTS iot_schema.v_monitoreo_particiones')
    
    # Eliminar funciones
    op.execute('DROP FUNCTION IF EXISTS iot_schema.fn_estadisticas_particiones()')
    op.execute('DROP FUNCTION IF EXISTS iot_schema.fn_limpiar_particiones_antiguas(INTEGER)')
    op.execute('DROP FUNCTION IF EXISTS iot_schema.fn_validar_particion_registros()')
    op.execute('DROP FUNCTION IF EXISTS iot_schema.fn_crear_particiones_automaticas()')
    op.execute('DROP FUNCTION IF EXISTS iot_schema.fn_crear_particion_registros(DATE)')
    
    # Eliminar trigger
    op.execute('DROP TRIGGER IF EXISTS tr_validar_particion_registros ON iot_schema.registros_datos')
    
    # Eliminar tabla de control
    op.drop_table('control_particiones', schema='iot_schema')
    
    # Eliminar configuración
    op.execute("DELETE FROM iot_schema.config_middleware WHERE clave = 'partitioning.auto_create'")
    
    # NOTA: Las particiones físicas creadas no se eliminan automáticamente
    # ya que podrían contener datos importantes. Se requiere limpieza manual.
