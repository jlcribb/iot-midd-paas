"""Convert Table to Partitioned - IoT Middleware

Revision ID: 0003
Revises: 0002
Create Date: 2025-08-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convertir tabla registros_datos a particionada por tiempo"""
    
    # 1. Crear nueva tabla particionada
    op.execute("""
        CREATE TABLE iot_schema.registros_datos_partitioned (
            id INTEGER NOT NULL,
            canal_id UUID NOT NULL,
            ts TIMESTAMP WITH TIME ZONE NOT NULL,
            valor_num DOUBLE PRECISION,
            valor_int INTEGER,
            valor_bool BOOLEAN,
            valor_text TEXT,
            valor_json JSONB,
            calidad TEXT DEFAULT 'OK',
            calidad_porcentaje INTEGER DEFAULT 100,
            metadata JSONB DEFAULT '{}',
            procesado BOOLEAN DEFAULT false,
            validado BOOLEAN DEFAULT false,
            CONSTRAINT pk_registros_datos_partitioned PRIMARY KEY (id, ts)
        ) PARTITION BY RANGE (ts);
    """)
    
    # 2. Crear particiones iniciales
    op.execute("""
        CREATE TABLE iot_schema.registros_datos_2025_08 PARTITION OF iot_schema.registros_datos_partitioned
        FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');
    """)
    
    op.execute("""
        CREATE TABLE iot_schema.registros_datos_2025_09 PARTITION OF iot_schema.registros_datos_partitioned
        FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
    """)
    
    # 3. Crear índices básicos en las particiones
    op.execute("CREATE INDEX idx_reg_datos_2025_08_canal_ts ON iot_schema.registros_datos_2025_08 (canal_id, ts)")
    op.execute("CREATE INDEX idx_reg_datos_2025_08_ts ON iot_schema.registros_datos_2025_08 (ts)")
    op.execute("CREATE INDEX idx_reg_datos_2025_08_calidad ON iot_schema.registros_datos_2025_08 (calidad)")
    
    op.execute("CREATE INDEX idx_reg_datos_2025_09_canal_ts ON iot_schema.registros_datos_2025_09 (canal_id, ts)")
    op.execute("CREATE INDEX idx_reg_datos_2025_09_ts ON iot_schema.registros_datos_2025_09 (ts)")
    op.execute("CREATE INDEX idx_reg_datos_2025_09_calidad ON iot_schema.registros_datos_2025_09 (calidad)")
    
    # 4. Copiar datos existentes (si los hay)
    op.execute("""
        INSERT INTO iot_schema.registros_datos_partitioned 
        SELECT * FROM iot_schema.registros_datos;
    """)
    
    # 5. Eliminar tabla antigua y renombrar la nueva
    op.execute("DROP TABLE iot_schema.registros_datos")
    op.execute("ALTER TABLE iot_schema.registros_datos_partitioned RENAME TO registros_datos")
    
    # 6. Registrar las particiones en la tabla de control
    op.execute("""
        INSERT INTO iot_schema.control_particiones (nombre_particion, fecha_inicio, fecha_fin, estado)
        VALUES 
            ('registros_datos_2025_08', '2025-08-01', '2025-08-31', 'activa'),
            ('registros_datos_2025_09', '2025-09-01', '2025-09-30', 'activa');
    """)
    
    # 7. Crear trigger para validar particiones
    op.execute("""
        CREATE TRIGGER tr_validar_particion_registros
        BEFORE INSERT ON iot_schema.registros_datos
        FOR EACH ROW
        EXECUTE FUNCTION iot_schema.fn_validar_particion_registros();
    """)


def downgrade() -> None:
    """Revertir la conversión a particionado"""
    
    # 1. Eliminar trigger
    op.execute('DROP TRIGGER IF EXISTS tr_validar_particion_registros ON iot_schema.registros_datos')
    
    # 2. Crear tabla normal
    op.execute("""
        CREATE TABLE iot_schema.registros_datos_normal (
            id INTEGER NOT NULL,
            canal_id UUID NOT NULL,
            ts TIMESTAMP WITH TIME ZONE NOT NULL,
            valor_num DOUBLE PRECISION,
            valor_int INTEGER,
            valor_bool BOOLEAN,
            valor_text TEXT,
            valor_json JSONB,
            calidad TEXT DEFAULT 'OK',
            calidad_porcentaje INTEGER DEFAULT 100,
            metadata JSONB DEFAULT '{}',
            procesado BOOLEAN DEFAULT false,
            validado BOOLEAN DEFAULT false,
            CONSTRAINT pk_registros_datos_normal PRIMARY KEY (id, ts)
        );
    """)
    
    # 3. Copiar datos de todas las particiones
    op.execute("""
        INSERT INTO iot_schema.registros_datos_normal 
        SELECT * FROM iot_schema.registros_datos;
    """)
    
    # 4. Eliminar tabla particionada y renombrar la normal
    op.execute("DROP TABLE iot_schema.registros_datos")
    op.execute("ALTER TABLE iot_schema.registros_datos_normal RENAME TO registros_datos")
    
    # 5. Crear índices en la tabla normal
    op.execute("""
        CREATE INDEX idx_reg_datos_canal_ts ON iot_schema.registros_datos (canal_id, ts);
        CREATE INDEX idx_reg_datos_ts ON iot_schema.registros_datos (ts);
        CREATE INDEX idx_reg_datos_calidad ON iot_schema.registros_datos (calidad);
        CREATE INDEX idx_reg_datos_procesado ON iot_schema.registros_datos (procesado);
        CREATE INDEX idx_reg_datos_validado ON iot_schema.registros_datos (validado);
        CREATE INDEX idx_reg_datos_metadata ON iot_schema.registros_datos (metadata) USING GIN;
    """)
    
    # 6. Limpiar tabla de control
    op.execute("DELETE FROM iot_schema.control_particiones WHERE nombre_particion LIKE 'registros_datos_%'")
