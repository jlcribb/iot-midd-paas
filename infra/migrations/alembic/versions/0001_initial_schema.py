"""Initial Schema Creation - IoT Middleware

Revision ID: 0001
Revises: 
Create Date: 2025-08-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crear esquema inicial completo"""
    
    # Crear esquema principal
    op.execute('CREATE SCHEMA IF NOT EXISTS iot_schema')
    
    # Activar extensiones útiles
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')
    op.execute('CREATE EXTENSION IF NOT EXISTS citext')
    
    # Crear tipos ENUM nativos de PostgreSQL
    op.execute("""
        DO $$
        BEGIN
          -- Estado de proyectos
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_proyecto') THEN
            CREATE TYPE iot_schema.estado_proyecto AS ENUM (
              'planificado', 'activo', 'pausado', 'cerrado', 'cancelado'
            );
          END IF;

          -- Protocolos de comunicación
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'protocolo_comunicacion') THEN
            CREATE TYPE iot_schema.protocolo_comunicacion AS ENUM (
              'MQTT', 'BLE', 'HTTP', 'RF', 'LoRa', 'Modbus', 'OPC_UA', 'Otro'
            );
          END IF;

          -- Tipos de datos para canales
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_dato') THEN
            CREATE TYPE iot_schema.tipo_dato AS ENUM (
              'int', 'float', 'bool', 'string', 'json', 'binary', 'timestamp'
            );
          END IF;

          -- Roles del sistema
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rol_sistema') THEN
            CREATE TYPE iot_schema.rol_sistema AS ENUM (
              'admin', 'tecnico', 'cliente', 'lectura', 'supervisor'
            );
          END IF;

          -- Calidad de datos (estándar OPC UA)
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'calidad_dato') THEN
            CREATE TYPE iot_schema.calidad_dato AS ENUM (
              'OK', 'GOOD', 'UNCERTAIN', 'BAD', 'SUSPECTO', 'MALO'
            );
          END IF;

          -- Severidad de eventos/alarmas
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'severidad_evento') THEN
            CREATE TYPE iot_schema.severidad_evento AS ENUM (
              'info', 'warning', 'error', 'critical', 'fatal'
            );
          END IF;

          -- Estados de dispositivos
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_dispositivo') THEN
            CREATE TYPE iot_schema.estado_dispositivo AS ENUM (
              'activo', 'inactivo', 'mantenimiento', 'error', 'desconectado'
            );
          END IF;
        END$$;
    """)
    
    # 1. CLIENTES
    op.create_table(
        'clientes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('nombre', sa.Text, nullable=False),
        sa.Column('sector', sa.Text),
        sa.Column('industria', sa.Text),
        sa.Column('notas', sa.Text),
        sa.Column('contacto_principal', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('contactos_adicionales', postgresql.JSONB, server_default='[]'),
        sa.Column('direccion', postgresql.JSONB),
        sa.Column('configuracion', postgresql.JSONB, server_default='{}'),
        sa.Column('activo', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('creado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('actualizado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('creado_por', postgresql.UUID(as_uuid=True)),
        sa.Column('actualizado_por', postgresql.UUID(as_uuid=True)),
        schema='iot_schema'
    )
    
    # 2. PROYECTOS
    op.create_table(
        'proyectos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nombre', sa.Text, nullable=False),
        sa.Column('descripcion', sa.Text),
        sa.Column('estado', sa.Text, nullable=False, server_default='planificado'),
        sa.Column('fecha_inicio', sa.Date),
        sa.Column('fecha_fin', sa.Date),
        sa.Column('presupuesto', sa.DECIMAL(15, 2)),
        sa.Column('prioridad', sa.Integer, server_default='1'),
        sa.Column('configuracion', postgresql.JSONB, server_default='{}'),
        sa.Column('activo', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('creado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('actualizado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('creado_por', postgresql.UUID(as_uuid=True)),
        sa.Column('actualizado_por', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['cliente_id'], ['iot_schema.clientes.id'], ondelete='CASCADE'),
        schema='iot_schema'
    )
    
    # 3. UNIDADES_PROYECTO
    op.create_table(
        'unidades_proyecto',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nombre', sa.Text, nullable=False),
        sa.Column('descripcion', sa.Text),
        sa.Column('ubicacion', sa.Text),
        sa.Column('responsable', sa.Text),
        sa.Column('responsable_email', sa.Text),
        sa.Column('responsable_telefono', sa.Text),
        sa.Column('lat', sa.Float),
        sa.Column('lon', sa.Float),
        sa.Column('configuracion', postgresql.JSONB, server_default='{}'),
        sa.Column('activo', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('creado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('actualizado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('creado_por', postgresql.UUID(as_uuid=True)),
        sa.Column('actualizado_por', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['proyecto_id'], ['iot_schema.proyectos.id'], ondelete='CASCADE'),
        schema='iot_schema'
    )
    
    # 4. SESIONES
    op.create_table(
        'sesiones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('unidad_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nombre', sa.Text),
        sa.Column('descripcion', sa.Text),
        sa.Column('inicio', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('fin', postgresql.TIMESTAMP(timezone=True)),
        sa.Column('estado', sa.String(50), server_default='activa'),
        sa.Column('observaciones', sa.Text),
        sa.Column('configuracion', postgresql.JSONB, server_default='{}'),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('creado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('actualizado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('creado_por', postgresql.UUID(as_uuid=True)),
        sa.Column('actualizado_por', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['unidad_id'], ['iot_schema.unidades_proyecto.id'], ondelete='CASCADE'),
        schema='iot_schema'
    )
    
    # 5. DISPOSITIVOS
    op.create_table(
        'dispositivos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('tipo', sa.Text, nullable=False),
        sa.Column('fabricante', sa.Text),
        sa.Column('modelo', sa.Text),
        sa.Column('identificador_unico', sa.Text, unique=True, nullable=False),
        sa.Column('protocolo', sa.Text, nullable=False, server_default='MQTT'),
        sa.Column('vida_util_meses', sa.Integer),
        sa.Column('especificaciones_tecnicas', postgresql.JSONB, server_default='{}'),
        sa.Column('configuracion_protocolo', postgresql.JSONB, server_default='{}'),
        sa.Column('firmware_version', sa.Text),
        sa.Column('hardware_version', sa.Text),
        sa.Column('certificaciones', postgresql.JSONB, server_default='[]'),
        sa.Column('activo', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('creado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('actualizado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('creado_por', postgresql.UUID(as_uuid=True)),
        sa.Column('actualizado_por', postgresql.UUID(as_uuid=True)),
        schema='iot_schema'
    )
    
    # 6. DISPOSITIVOS_PROYECTO
    op.create_table(
        'dispositivos_proyecto',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dispositivo_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('unidad_id', postgresql.UUID(as_uuid=True)),
        sa.Column('nombre_personalizado', sa.Text),
        sa.Column('descripcion', sa.Text),
        sa.Column('fecha_instalacion', sa.Date, nullable=False, server_default=sa.text('CURRENT_DATE')),
        sa.Column('fecha_retiro', sa.Date),
        sa.Column('estado', sa.Text, nullable=False, server_default='activo'),
        sa.Column('configuracion', postgresql.JSONB, server_default='{}'),
        sa.Column('ubicacion_fisica', sa.Text),
        sa.Column('responsable', sa.Text),
        sa.Column('responsable_email', sa.Text),
        sa.Column('responsable_telefono', sa.Text),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('creado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('actualizado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('creado_por', postgresql.UUID(as_uuid=True)),
        sa.Column('actualizado_por', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['proyecto_id'], ['iot_schema.proyectos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dispositivo_id'], ['iot_schema.dispositivos.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['unidad_id'], ['iot_schema.unidades_proyecto.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('proyecto_id', 'dispositivo_id', name='uq_dispositivo_proyecto'),
        schema='iot_schema'
    )
    
    # 7. CANALES
    op.create_table(
        'canales',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('dispositivo_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nombre', sa.Text, nullable=False),
        sa.Column('etiqueta', sa.Text),
        sa.Column('descripcion', sa.Text),
        sa.Column('unidad_medida', sa.Text),
        sa.Column('tipo', sa.Text, nullable=False),
        sa.Column('rango_min', sa.Float),
        sa.Column('rango_max', sa.Float),
        sa.Column('precision_valor', sa.Integer),
        sa.Column('frecuencia_muestreo', sa.Integer),
        sa.Column('umbral_alto', sa.Float),
        sa.Column('umbral_bajo', sa.Float),
        sa.Column('metadatos', postgresql.JSONB, server_default='{}'),
        sa.Column('configuracion', postgresql.JSONB, server_default='{}'),
        sa.Column('activo', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('creado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('actualizado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('creado_por', postgresql.UUID(as_uuid=True)),
        sa.Column('actualizado_por', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['dispositivo_id'], ['iot_schema.dispositivos.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('dispositivo_id', 'nombre', name='uq_canal_dispositivo_nombre'),
        schema='iot_schema'
    )
    
    # 8. REGISTROS_DATOS (particionado por tiempo)
    op.create_table(
        'registros_datos',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('canal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ts', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('valor_num', sa.Float),
        sa.Column('valor_int', sa.Integer),
        sa.Column('valor_bool', sa.Boolean),
        sa.Column('valor_text', sa.Text),
        sa.Column('valor_json', postgresql.JSONB),
        sa.Column('calidad', sa.Text, server_default='OK'),
        sa.Column('calidad_porcentaje', sa.Integer, server_default='100'),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('procesado', sa.Boolean, server_default='false'),
        sa.Column('validado', sa.Boolean, server_default='false'),
        sa.ForeignKeyConstraint(['canal_id'], ['iot_schema.canales.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', 'ts'),
        schema='iot_schema'
    )
    
    # 9. EVENTOS_ALARMAS
    op.create_table(
        'eventos_alarmas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('canal_id', postgresql.UUID(as_uuid=True)),
        sa.Column('unidad_id', postgresql.UUID(as_uuid=True)),
        sa.Column('dispositivo_id', postgresql.UUID(as_uuid=True)),
        sa.Column('ts', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('severidad', sa.Text, nullable=False, server_default='info'),
        sa.Column('codigo', sa.Text),
        sa.Column('titulo', sa.Text, nullable=False),
        sa.Column('descripcion', sa.Text),
        sa.Column('detalles', postgresql.JSONB, server_default='{}'),
        sa.Column('estado', sa.String(50), server_default='activa'),
        sa.Column('reconocida_por', postgresql.UUID(as_uuid=True)),
        sa.Column('reconocida_en', postgresql.TIMESTAMP(timezone=True)),
        sa.Column('resuelta_por', postgresql.UUID(as_uuid=True)),
        sa.Column('resuelta_en', postgresql.TIMESTAMP(timezone=True)),
        sa.Column('comentarios', sa.Text),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('creado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('actualizado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('creado_por', postgresql.UUID(as_uuid=True)),
        sa.Column('actualizado_por', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['proyecto_id'], ['iot_schema.proyectos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['canal_id'], ['iot_schema.canales.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['unidad_id'], ['iot_schema.unidades_proyecto.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['dispositivo_id'], ['iot_schema.dispositivos.id'], ondelete='SET NULL'),
        schema='iot_schema'
    )
    
    # 10. USUARIOS
    op.create_table(
        'usuarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', postgresql.CITEXT, unique=True, nullable=False),
        sa.Column('nombre', sa.Text, nullable=False),
        sa.Column('apellido', sa.Text),
        sa.Column('password_hash', sa.Text, nullable=False),
        sa.Column('rol', sa.Text, nullable=False, server_default='lectura'),
        sa.Column('activo', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('ultimo_login', postgresql.TIMESTAMP(timezone=True)),
        sa.Column('configuracion', postgresql.JSONB, server_default='{}'),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('creado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('actualizado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('creado_por', postgresql.UUID(as_uuid=True)),
        sa.Column('actualizado_por', postgresql.UUID(as_uuid=True)),
        schema='iot_schema'
    )
    
    # 11. USUARIOS_SCOPE
    op.create_table(
        'usuarios_scope',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True)),
        sa.Column('proyecto_id', postgresql.UUID(as_uuid=True)),
        sa.Column('permisos', postgresql.JSONB, server_default='{}'),
        sa.Column('activo', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('creado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['usuario_id'], ['iot_schema.usuarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cliente_id'], ['iot_schema.clientes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['proyecto_id'], ['iot_schema.proyectos.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('usuario_id', 'cliente_id', 'proyecto_id', name='uq_usuario_scope'),
        schema='iot_schema'
    )
    
    # 12. CONFIG_MIDDLEWARE
    op.create_table(
        'config_middleware',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('clave', sa.Text, nullable=False),
        sa.Column('valor', postgresql.JSONB, nullable=False),
        sa.Column('descripcion', sa.Text),
        sa.Column('categoria', sa.Text),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('sensible', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('vigente', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('activo', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('creado_por', postgresql.UUID(as_uuid=True)),
        sa.Column('creado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('actualizado_en', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('actualizado_por', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['creado_por'], ['iot_schema.usuarios.id']),
        sa.ForeignKeyConstraint(['actualizado_por'], ['iot_schema.usuarios.id']),
        schema='iot_schema'
    )
    
    # 13. AUDITORIA
    op.create_table(
        'auditoria',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True)),
        sa.Column('entidad', sa.Text, nullable=False),
        sa.Column('entidad_id', postgresql.UUID(as_uuid=True)),
        sa.Column('accion', sa.Text, nullable=False),
        sa.Column('cambios', postgresql.JSONB, server_default='{}'),
        sa.Column('ip_origen', postgresql.INET),
        sa.Column('user_agent', sa.Text),
        sa.Column('contexto', postgresql.JSONB, server_default='{}'),
        sa.Column('ts', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['usuario_id'], ['iot_schema.usuarios.id']),
        schema='iot_schema'
    )
    
    # Crear índices para optimización
    op.create_index('idx_clientes_activo', 'clientes', ['activo'], schema='iot_schema')
    op.create_index('idx_clientes_contacto', 'clientes', ['contacto_principal'], schema='iot_schema', postgresql_using='gin')
    
    op.create_index('idx_proyectos_cliente', 'proyectos', ['cliente_id'], schema='iot_schema')
    op.create_index('idx_proyectos_estado', 'proyectos', ['estado'], schema='iot_schema')
    op.create_index('idx_proyectos_activo', 'proyectos', ['activo'], schema='iot_schema')
    
    op.create_index('idx_unidades_proyecto_proyecto', 'unidades_proyecto', ['proyecto_id'], schema='iot_schema')
    op.create_index('idx_unidades_proyecto_activo', 'unidades_proyecto', ['activo'], schema='iot_schema')
    
    op.create_index('idx_sesiones_unidad', 'sesiones', ['unidad_id'], schema='iot_schema')
    op.create_index('idx_sesiones_rango', 'sesiones', ['inicio', 'fin'], schema='iot_schema')
    op.create_index('idx_sesiones_estado', 'sesiones', ['estado'], schema='iot_schema')
    
    op.create_index('idx_dispositivos_tipo', 'dispositivos', ['tipo'], schema='iot_schema')
    op.create_index('idx_dispositivos_protocolo', 'dispositivos', ['protocolo'], schema='iot_schema')
    op.create_index('idx_dispositivos_activo', 'dispositivos', ['activo'], schema='iot_schema')
    op.create_index('idx_dispositivos_especificaciones', 'dispositivos', ['especificaciones_tecnicas'], schema='iot_schema', postgresql_using='gin')
    
    op.create_index('idx_disp_proj_proyecto', 'dispositivos_proyecto', ['proyecto_id'], schema='iot_schema')
    op.create_index('idx_disp_proj_unidad', 'dispositivos_proyecto', ['unidad_id'], schema='iot_schema')
    op.create_index('idx_disp_proj_estado', 'dispositivos_proyecto', ['estado'], schema='iot_schema')
    
    op.create_index('idx_canales_dispositivo', 'canales', ['dispositivo_id'], schema='iot_schema')
    op.create_index('idx_canales_tipo', 'canales', ['tipo'], schema='iot_schema')
    op.create_index('idx_canales_activo', 'canales', ['activo'], schema='iot_schema')
    op.create_index('idx_canales_metadatos', 'canales', ['metadatos'], schema='iot_schema', postgresql_using='gin')
    
    op.create_index('idx_reg_datos_canal_ts', 'registros_datos', ['canal_id', 'ts'], schema='iot_schema')
    op.create_index('idx_reg_datos_ts', 'registros_datos', ['ts'], schema='iot_schema')
    op.create_index('idx_reg_datos_calidad', 'registros_datos', ['calidad'], schema='iot_schema')
    op.create_index('idx_reg_datos_procesado', 'registros_datos', ['procesado'], schema='iot_schema')
    op.create_index('idx_reg_datos_validado', 'registros_datos', ['validado'], schema='iot_schema')
    op.create_index('idx_reg_metadata', 'registros_datos', ['metadata'], schema='iot_schema', postgresql_using='gin')
    
    op.create_index('idx_eventos_proyecto_ts', 'eventos_alarmas', ['proyecto_id', 'ts'], schema='iot_schema')
    op.create_index('idx_eventos_canal_ts', 'eventos_alarmas', ['canal_id', 'ts'], schema='iot_schema')
    op.create_index('idx_eventos_unidad_ts', 'eventos_alarmas', ['unidad_id', 'ts'], schema='iot_schema')
    op.create_index('idx_eventos_severidad', 'eventos_alarmas', ['severidad'], schema='iot_schema')
    op.create_index('idx_eventos_estado', 'eventos_alarmas', ['estado'], schema='iot_schema')
    op.create_index('idx_eventos_ts', 'eventos_alarmas', ['ts'], schema='iot_schema')
    op.create_index('idx_eventos_detalles', 'eventos_alarmas', ['detalles'], schema='iot_schema', postgresql_using='gin')
    
    op.create_index('idx_usuarios_email', 'usuarios', ['email'], schema='iot_schema')
    op.create_index('idx_usuarios_rol', 'usuarios', ['rol'], schema='iot_schema')
    op.create_index('idx_usuarios_activo', 'usuarios', ['activo'], schema='iot_schema')
    op.create_index('idx_usuarios_config', 'usuarios', ['configuracion'], schema='iot_schema', postgresql_using='gin')
    
    op.create_index('idx_usuarios_scope_usuario', 'usuarios_scope', ['usuario_id'], schema='iot_schema')
    op.create_index('idx_usuarios_scope_cliente', 'usuarios_scope', ['cliente_id'], schema='iot_schema')
    op.create_index('idx_usuarios_scope_proyecto', 'usuarios_scope', ['proyecto_id'], schema='iot_schema')
    
    op.create_index('idx_config_clave_vigente', 'config_middleware', ['clave', 'vigente'], schema='iot_schema')
    op.create_index('idx_config_categoria', 'config_middleware', ['categoria'], schema='iot_schema')
    op.create_index('idx_config_activo', 'config_middleware', ['activo'], schema='iot_schema')
    
    op.create_index('idx_auditoria_entidad_ts', 'auditoria', ['entidad', 'ts'], schema='iot_schema')
    op.create_index('idx_auditoria_usuario_ts', 'auditoria', ['usuario_id', 'ts'], schema='iot_schema')
    op.create_index('idx_auditoria_accion_ts', 'auditoria', ['accion', 'ts'], schema='iot_schema')
    
    # Crear vistas útiles
    op.execute("""
        CREATE OR REPLACE VIEW iot_schema.v_resumen_proyectos AS
        SELECT 
          p.id,
          p.nombre,
          p.estado,
          p.fecha_inicio,
          p.fecha_fin,
          c.nombre as cliente_nombre,
          c.sector as cliente_sector,
          COUNT(DISTINCT up.id) as total_unidades,
          COUNT(DISTINCT dp.id) as total_dispositivos,
          COUNT(DISTINCT ca.id) as total_canales,
          COUNT(DISTINCT ea.id) as total_eventos_activos
        FROM iot_schema.proyectos p
        JOIN iot_schema.clientes c ON p.cliente_id = c.id
        LEFT JOIN iot_schema.unidades_proyecto up ON p.id = up.proyecto_id AND up.activo = true
        LEFT JOIN iot_schema.dispositivos_proyecto dp ON p.id = dp.proyecto_id AND dp.estado = 'activo'
        LEFT JOIN iot_schema.dispositivos d ON dp.dispositivo_id = d.id
        LEFT JOIN iot_schema.canales ca ON d.id = ca.dispositivo_id AND ca.activo = true
        LEFT JOIN iot_schema.eventos_alarmas ea ON p.id = ea.proyecto_id AND ea.estado = 'activa'
        WHERE p.activo = true
        GROUP BY p.id, p.nombre, p.estado, p.fecha_inicio, p.fecha_fin, c.nombre, c.sector;
    """)
    
    op.execute("""
        CREATE OR REPLACE VIEW iot_schema.v_resumen_dispositivos AS
        SELECT 
          d.id,
          d.tipo,
          d.fabricante,
          d.modelo,
          d.identificador_unico,
          d.protocolo,
          dp.estado as estado_dispositivo,
          dp.nombre_personalizado,
          dp.fecha_instalacion,
          dp.fecha_retiro,
          p.nombre as proyecto_nombre,
          up.nombre as unidad_nombre,
          COUNT(ca.id) as total_canales,
          COUNT(CASE WHEN ca.activo = true THEN 1 END) as canales_activos
        FROM iot_schema.dispositivos d
        JOIN iot_schema.dispositivos_proyecto dp ON d.id = dp.dispositivo_id
        JOIN iot_schema.proyectos p ON dp.proyecto_id = p.id
        LEFT JOIN iot_schema.unidades_proyecto up ON dp.unidad_id = up.id
        LEFT JOIN iot_schema.canales ca ON d.id = ca.dispositivo_id
        WHERE d.activo = true AND dp.estado != 'retirado'
        GROUP BY d.id, d.tipo, d.fabricante, d.modelo, d.identificador_unico, d.protocolo, 
                 dp.estado, dp.nombre_personalizado, dp.fecha_instalacion, dp.fecha_retiro,
                 p.nombre, up.nombre;
    """)
    
    # Insertar datos iniciales
    op.execute("""
        INSERT INTO iot_schema.usuarios (email, nombre, apellido, password_hash, rol, activo)
        VALUES (
          'admin@iot-middleware.com',
          'Administrador',
          'Sistema',
          crypt('admin123', gen_salt('bf')),
          'admin',
          true
        ) ON CONFLICT (email) DO NOTHING;
    """)
    
    op.execute("""
        INSERT INTO iot_schema.clientes (nombre, sector, industria, contacto_principal)
        VALUES (
          'Cliente Demo',
          'Industrial',
          'Manufactura',
          '{"nombre": "Juan Pérez", "email": "juan.perez@cliente.com", "telefono": "+1234567890", "cargo": "Gerente de Operaciones"}'
        ) ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    """Revertir la migración inicial"""
    
    # Eliminar vistas
    op.execute('DROP VIEW IF EXISTS iot_schema.v_resumen_dispositivos')
    op.execute('DROP VIEW IF EXISTS iot_schema.v_resumen_proyectos')
    
    # Eliminar tablas en orden inverso (por dependencias)
    op.drop_table('auditoria', schema='iot_schema')
    op.drop_table('config_middleware', schema='iot_schema')
    op.drop_table('usuarios_scope', schema='iot_schema')
    op.drop_table('usuarios', schema='iot_schema')
    op.drop_table('eventos_alarmas', schema='iot_schema')
    op.drop_table('registros_datos', schema='iot_schema')
    op.drop_table('canales', schema='iot_schema')
    op.drop_table('dispositivos_proyecto', schema='iot_schema')
    op.drop_table('dispositivos', schema='iot_schema')
    op.drop_table('sesiones', schema='iot_schema')
    op.drop_table('unidades_proyecto', schema='iot_schema')
    op.drop_table('proyectos', schema='iot_schema')
    op.drop_table('clientes', schema='iot_schema')
    
    # Eliminar tipos ENUM
    op.execute("""
        DROP TYPE IF EXISTS iot_schema.estado_dispositivo CASCADE;
        DROP TYPE IF EXISTS iot_schema.severidad_evento CASCADE;
        DROP TYPE IF EXISTS iot_schema.calidad_dato CASCADE;
        DROP TYPE IF EXISTS iot_schema.rol_sistema CASCADE;
        DROP TYPE IF EXISTS iot_schema.tipo_dato CASCADE;
        DROP TYPE IF EXISTS iot_schema.protocolo_comunicacion CASCADE;
        DROP TYPE IF EXISTS iot_schema.estado_proyecto CASCADE;
    """)
    
    # Eliminar esquema
    op.execute('DROP SCHEMA IF EXISTS iot_schema CASCADE')
