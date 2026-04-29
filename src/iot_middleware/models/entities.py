"""
Modelos de Entidades SQLAlchemy - IoT Middleware
===============================================

Este archivo contiene todos los modelos SQLAlchemy que reflejan
las entidades de la base de datos PostgreSQL.
"""

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, Date, 
    ForeignKey, UniqueConstraint, Index, CheckConstraint, PrimaryKeyConstraint, Identity, func
)
from sqlalchemy.dialects.postgresql import (
    UUID, JSONB, TIMESTAMP, INET, CITEXT
)
from sqlalchemy import DECIMAL
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import text
from datetime import datetime
from .base import Base, generate_uuid
from .enums import (
    create_postgresql_enum, EstadoProyecto, ProtocoloComunicacion,
    TipoDato, RolSistema, CalidadDato, SeveridadEvento, EstadoDispositivo
)

# ============================================================================
# MODELOS PRINCIPALES
# ============================================================================

class Cliente(Base):
    """Modelo para clientes/organizaciones"""
    __tablename__ = 'clientes'
    __table_args__ = {'schema': 'iot_schema'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    nombre = Column(Text, nullable=False)
    sector = Column(Text)
    industria = Column(Text)
    notas = Column(Text)
    contacto_principal = Column(JSONB, nullable=False, default=dict)
    contactos_adicionales = Column(JSONB, default=list)
    direccion = Column(JSONB)
    configuracion = Column(JSONB, default=dict)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    creado_por = Column(UUID(as_uuid=True))
    actualizado_por = Column(UUID(as_uuid=True))
    
    # Relaciones
    proyectos = relationship("Proyecto", back_populates="cliente", cascade="all, delete-orphan")
    usuarios_scope = relationship("UsuarioScope", back_populates="cliente")
    
    # Índices
    __table_args__ = (
        Index('idx_clientes_activo', 'activo'),
        Index('idx_clientes_contacto', 'contacto_principal', postgresql_using='gin'),
        {'schema': 'iot_schema'}
    )

class Proyecto(Base):
    """Modelo para proyectos"""
    __tablename__ = 'proyectos'
    __table_args__ = {'schema': 'iot_schema'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.clientes.id'), nullable=False)
    nombre = Column(Text, nullable=False)
    descripcion = Column(Text)
    estado = Column(create_postgresql_enum(EstadoProyecto), nullable=False, default=EstadoProyecto.PLANIFICADO)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    presupuesto = Column(DECIMAL(15, 2))
    prioridad = Column(Integer, default=1)
    configuracion = Column(JSONB, default=dict)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    creado_por = Column(UUID(as_uuid=True))
    actualizado_por = Column(UUID(as_uuid=True))
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="proyectos")
    unidades = relationship("UnidadProyecto", back_populates="proyecto", cascade="all, delete-orphan")
    dispositivos_proyecto = relationship("DispositivoProyecto", back_populates="proyecto", cascade="all, delete-orphan")
    eventos_alarmas = relationship("EventoAlarma", back_populates="proyecto", cascade="all, delete-orphan")
    usuarios_scope = relationship("UsuarioScope", back_populates="proyecto")
    
    # Índices
    __table_args__ = (
        Index('idx_proyectos_cliente', 'cliente_id'),
        Index('idx_proyectos_estado', 'estado'),
        Index('idx_proyectos_activo', 'activo'),
        {'schema': 'iot_schema'}
    )

class UnidadProyecto(Base):
    """Modelo para unidades de proyecto"""
    __tablename__ = 'unidades_proyecto'
    __table_args__ = {'schema': 'iot_schema'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.proyectos.id'), nullable=False)
    nombre = Column(Text, nullable=False)
    descripcion = Column(Text)
    ubicacion = Column(Text)
    responsable = Column(Text)
    responsable_email = Column(Text)
    responsable_telefono = Column(Text)
    lat = Column(Float)
    lon = Column(Float)
    configuracion = Column(JSONB, default=dict)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    creado_por = Column(UUID(as_uuid=True))
    actualizado_por = Column(UUID(as_uuid=True))
    
    # Relaciones
    proyecto = relationship("Proyecto", back_populates="unidades")
    sesiones = relationship("Sesion", back_populates="unidad", cascade="all, delete-orphan")
    dispositivos_proyecto = relationship("DispositivoProyecto", back_populates="unidad")
    eventos_alarmas = relationship("EventoAlarma", back_populates="unidad")
    
    # Índices
    __table_args__ = (
        Index('idx_unidades_proyecto_proyecto', 'proyecto_id'),
        Index('idx_unidades_proyecto_activo', 'activo'),
        {'schema': 'iot_schema'}
    )

class Sesion(Base):
    """Modelo para sesiones de toma de datos"""
    __tablename__ = 'sesiones'
    __table_args__ = {'schema': 'iot_schema'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    unidad_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.unidades_proyecto.id'), nullable=False)
    nombre = Column(Text)
    descripcion = Column(Text)
    inicio = Column(TIMESTAMP(timezone=True), nullable=False)
    fin = Column(TIMESTAMP(timezone=True))
    estado = Column(String(50), default='activa')
    observaciones = Column(Text)
    configuracion = Column(JSONB, default=dict)
    metadatos = Column('metadata', JSONB, default=dict)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    creado_por = Column(UUID(as_uuid=True))
    actualizado_por = Column(UUID(as_uuid=True))
    
    # Relaciones
    unidad = relationship("UnidadProyecto", back_populates="sesiones")
    
    # Índices
    __table_args__ = (
        Index('idx_sesiones_unidad', 'unidad_id'),
        Index('idx_sesiones_rango', 'inicio', 'fin'),
        Index('idx_sesiones_estado', 'estado'),
        {'schema': 'iot_schema'}
    )

class Dispositivo(Base):
    """Modelo para dispositivos IoT"""
    __tablename__ = 'dispositivos'
    __table_args__ = {'schema': 'iot_schema'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    tipo = Column(Text, nullable=False)
    fabricante = Column(Text)
    modelo = Column(Text)
    identificador_unico = Column(Text, unique=True, nullable=False)
    protocolo = Column(create_postgresql_enum(ProtocoloComunicacion), nullable=False, default=ProtocoloComunicacion.MQTT)
    vida_util_meses = Column(Integer)
    especificaciones_tecnicas = Column(JSONB, default=dict)
    configuracion_protocolo = Column(JSONB, default=dict)
    firmware_version = Column(Text)
    hardware_version = Column(Text)
    certificaciones = Column(JSONB, default=list)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    creado_por = Column(UUID(as_uuid=True))
    actualizado_por = Column(UUID(as_uuid=True))
    
    # Relaciones
    canales = relationship("Canal", back_populates="dispositivo", cascade="all, delete-orphan")
    dispositivos_proyecto = relationship("DispositivoProyecto", back_populates="dispositivo")
    eventos_alarmas = relationship("EventoAlarma", back_populates="dispositivo")
    
    # Índices
    __table_args__ = (
        Index('idx_dispositivos_tipo', 'tipo'),
        Index('idx_dispositivos_protocolo', 'protocolo'),
        Index('idx_dispositivos_activo', 'activo'),
        Index('idx_dispositivos_especificaciones', 'especificaciones_tecnicas', postgresql_using='gin'),
        {'schema': 'iot_schema'}
    )

class DispositivoProyecto(Base):
    """Modelo para dispositivos en proyectos"""
    __tablename__ = 'dispositivos_proyecto'
    __table_args__ = {'schema': 'iot_schema'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.proyectos.id'), nullable=False)
    dispositivo_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.dispositivos.id'), nullable=False)
    unidad_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.unidades_proyecto.id'))
    nombre_personalizado = Column(Text)
    descripcion = Column(Text)
    fecha_instalacion = Column(Date, nullable=False, default=func.current_date())
    fecha_retiro = Column(Date)
    estado = Column(create_postgresql_enum(EstadoDispositivo), nullable=False, default=EstadoDispositivo.ACTIVO)
    configuracion = Column(JSONB, default=dict)
    ubicacion_fisica = Column(Text)
    responsable = Column(Text)
    responsable_email = Column(Text)
    responsable_telefono = Column(Text)
    metadatos = Column('metadata', JSONB, default=dict)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    creado_por = Column(UUID(as_uuid=True))
    actualizado_por = Column(UUID(as_uuid=True))
    
    # Relaciones
    proyecto = relationship("Proyecto", back_populates="dispositivos_proyecto")
    dispositivo = relationship("Dispositivo", back_populates="dispositivos_proyecto")
    unidad = relationship("UnidadProyecto", back_populates="dispositivos_proyecto")
    
    # Restricciones
    __table_args__ = (
        UniqueConstraint('proyecto_id', 'dispositivo_id', name='uq_dispositivo_proyecto'),
        Index('idx_disp_proj_proyecto', 'proyecto_id'),
        Index('idx_disp_proj_unidad', 'unidad_id'),
        Index('idx_disp_proj_estado', 'estado'),
        {'schema': 'iot_schema'}
    )

class Canal(Base):
    """Modelo para canales/sensores de dispositivos"""
    __tablename__ = 'canales'
    __table_args__ = {'schema': 'iot_schema'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    dispositivo_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.dispositivos.id'), nullable=False)
    nombre = Column(Text, nullable=False)
    etiqueta = Column(Text)
    descripcion = Column(Text)
    unidad_medida = Column(Text)
    tipo = Column(create_postgresql_enum(TipoDato), nullable=False)
    rango_min = Column(Float)
    rango_max = Column(Float)
    precision_valor = Column(Integer)
    frecuencia_muestreo = Column(Integer)
    umbral_alto = Column(Float)
    umbral_bajo = Column(Float)
    metadatos = Column(JSONB, default=dict)
    configuracion = Column(JSONB, default=dict)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    creado_por = Column(UUID(as_uuid=True))
    actualizado_por = Column(UUID(as_uuid=True))
    
    # Relaciones
    dispositivo = relationship("Dispositivo", back_populates="canales")
    registros_datos = relationship("RegistroDatos", back_populates="canal", cascade="all, delete-orphan")
    eventos_alarmas = relationship("EventoAlarma", back_populates="canal")
    
    # Restricciones
    __table_args__ = (
        UniqueConstraint('dispositivo_id', 'nombre', name='uq_canal_dispositivo_nombre'),
        Index('idx_canales_dispositivo', 'dispositivo_id'),
        Index('idx_canales_tipo', 'tipo'),
        Index('idx_canales_activo', 'activo'),
        Index('idx_canales_metadatos', 'metadatos', postgresql_using='gin'),
        {'schema': 'iot_schema'}
    )

class RegistroDatos(Base):
    """Modelo para registros de datos (particionado por tiempo)"""
    __tablename__ = 'registros_datos'
    __table_args__ = {'schema': 'iot_schema'}
    
    id = Column(Integer, Identity(), nullable=False)
    canal_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.canales.id'), nullable=False)
    ts = Column(TIMESTAMP(timezone=True), nullable=False)
    valor_num = Column(Float)
    valor_int = Column(Integer)
    valor_bool = Column(Boolean)
    valor_text = Column(Text)
    valor_json = Column(JSONB)
    calidad = Column(create_postgresql_enum(CalidadDato), default=CalidadDato.OK)
    calidad_porcentaje = Column(Integer, default=100)
    metadatos = Column('metadata', JSONB, default=dict)
    procesado = Column(Boolean, default=False)
    validado = Column(Boolean, default=False)
    
    # Relaciones
    canal = relationship("Canal", back_populates="registros_datos")
    
    # Restricciones
    __table_args__ = (
        # Clave primaria compuesta para particionamiento
        PrimaryKeyConstraint('id', 'ts'),
        # Índices para consultas frecuentes
        Index('idx_reg_datos_canal_ts', 'canal_id', 'ts'),
        Index('idx_reg_datos_ts', 'ts'),
        Index('idx_reg_datos_calidad', 'calidad'),
        Index('idx_reg_datos_procesado', 'procesado'),
        Index('idx_reg_datos_validado', 'validado'),
        # Índice GIN para metadatos JSONB
        Index('idx_reg_metadata', 'metadata', postgresql_using='gin'),
        {'schema': 'iot_schema'}
    )

class EventoAlarma(Base):
    """Modelo para eventos y alarmas"""
    __tablename__ = 'eventos_alarmas'
    __table_args__ = {'schema': 'iot_schema'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.proyectos.id'), nullable=False)
    canal_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.canales.id'))
    unidad_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.unidades_proyecto.id'))
    dispositivo_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.dispositivos.id'))
    ts = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    severidad = Column(create_postgresql_enum(SeveridadEvento), nullable=False, default=SeveridadEvento.INFO)
    codigo = Column(Text)
    titulo = Column(Text, nullable=False)
    descripcion = Column(Text)
    detalles = Column(JSONB, default=dict)
    estado = Column(String(50), default='activa')
    reconocida_por = Column(UUID(as_uuid=True))
    reconocida_en = Column(TIMESTAMP(timezone=True))
    resuelta_por = Column(UUID(as_uuid=True))
    resuelta_en = Column(TIMESTAMP(timezone=True))
    comentarios = Column(Text)
    metadatos = Column('metadata', JSONB, default=dict)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    creado_por = Column(UUID(as_uuid=True))
    actualizado_por = Column(UUID(as_uuid=True))
    
    # Relaciones
    proyecto = relationship("Proyecto", back_populates="eventos_alarmas")
    canal = relationship("Canal", back_populates="eventos_alarmas")
    unidad = relationship("UnidadProyecto", back_populates="eventos_alarmas")
    dispositivo = relationship("Dispositivo", back_populates="eventos_alarmas")
    
    # Índices
    __table_args__ = (
        Index('idx_eventos_proyecto_ts', 'proyecto_id', 'ts'),
        Index('idx_eventos_canal_ts', 'canal_id', 'ts'),
        Index('idx_eventos_unidad_ts', 'unidad_id', 'ts'),
        Index('idx_eventos_severidad', 'severidad'),
        Index('idx_eventos_estado', 'estado'),
        Index('idx_eventos_ts', 'ts'),
        Index('idx_eventos_detalles', 'detalles', postgresql_using='gin'),
        {'schema': 'iot_schema'}
    )

class Usuario(Base):
    """Modelo para usuarios del sistema"""
    __tablename__ = 'usuarios'
    __table_args__ = {'schema': 'iot_schema'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    email = Column(CITEXT, unique=True, nullable=False)
    nombre = Column(Text, nullable=False)
    apellido = Column(Text)
    password_hash = Column(Text, nullable=False)
    rol = Column(create_postgresql_enum(RolSistema), nullable=False, default=RolSistema.LECTURA)
    activo = Column(Boolean, nullable=False, default=True)
    ultimo_login = Column(TIMESTAMP(timezone=True))
    configuracion = Column(JSONB, default=dict)
    metadatos = Column('metadata', JSONB, default=dict)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    creado_por = Column(UUID(as_uuid=True))
    actualizado_por = Column(UUID(as_uuid=True))
    
    # Relaciones
    usuarios_scope = relationship("UsuarioScope", back_populates="usuario", cascade="all, delete-orphan")
    configuraciones_creadas = relationship("ConfigMiddleware", foreign_keys="ConfigMiddleware.creado_por", back_populates="creado_por_usuario")
    configuraciones_actualizadas = relationship("ConfigMiddleware", foreign_keys="ConfigMiddleware.actualizado_por", back_populates="actualizado_por_usuario")
    
    # Índices
    __table_args__ = (
        Index('idx_usuarios_email', 'email'),
        Index('idx_usuarios_rol', 'rol'),
        Index('idx_usuarios_activo', 'activo'),
        Index('idx_usuarios_config', 'configuracion', postgresql_using='gin'),
        {'schema': 'iot_schema'}
    )

    @property
    def active_scope(self):
        """Retorna el primer scope activo para compatibilidad con código existente."""
        for scope in self.usuarios_scope:
            if scope.activo:
                return scope
        return None

    @property
    def cliente_id(self):
        scope = self.active_scope
        return scope.cliente_id if scope else None

    @property
    def proyecto_id(self):
        scope = self.active_scope
        return scope.proyecto_id if scope else None

    @property
    def unidad_id(self):
        # El modelo actual no persiste unidad en UsuarioScope.
        return None

    @property
    def ultimo_acceso(self):
        return self.ultimo_login

    @ultimo_acceso.setter
    def ultimo_acceso(self, value):
        self.ultimo_login = value

class UsuarioScope(Base):
    """Modelo para alcance de usuarios en clientes/proyectos"""
    __tablename__ = 'usuarios_scope'
    __table_args__ = {'schema': 'iot_schema'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.usuarios.id'), nullable=False)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.clientes.id'))
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.proyectos.id'))
    permisos = Column(JSONB, default=dict)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="usuarios_scope")
    cliente = relationship("Cliente", back_populates="usuarios_scope")
    proyecto = relationship("Proyecto", back_populates="usuarios_scope")
    
    # Restricciones
    __table_args__ = (
        UniqueConstraint(
            'usuario_id', 
            'cliente_id', 
            'proyecto_id', 
            name='uq_usuario_scope'
        ),
        Index('idx_usuarios_scope_usuario', 'usuario_id'),
        Index('idx_usuarios_scope_cliente', 'cliente_id'),
        Index('idx_usuarios_scope_proyecto', 'proyecto_id'),
        {'schema': 'iot_schema'}
    )

class ConfigMiddleware(Base):
    """Modelo para configuraciones del middleware"""
    __tablename__ = 'config_middleware'
    __table_args__ = {'schema': 'iot_schema'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    clave = Column(Text, nullable=False)
    valor = Column(JSONB, nullable=False)
    descripcion = Column(Text)
    categoria = Column(Text)
    version = Column(Integer, nullable=False, default=1)
    sensible = Column(Boolean, nullable=False, default=False)
    vigente = Column(Boolean, nullable=False, default=True)
    activo = Column(Boolean, nullable=False, default=True)
    creado_por = Column(UUID(as_uuid=True), ForeignKey('iot_schema.usuarios.id'))
    creado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    actualizado_en = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    actualizado_por = Column(UUID(as_uuid=True), ForeignKey('iot_schema.usuarios.id'))
    
    # Relaciones
    creado_por_usuario = relationship("Usuario", foreign_keys=[creado_por], back_populates="configuraciones_creadas")
    actualizado_por_usuario = relationship("Usuario", foreign_keys=[actualizado_por], back_populates="configuraciones_actualizadas")
    
    # Índices
    __table_args__ = (
        Index('idx_config_clave_vigente', 'clave', 'vigente'),
        Index('idx_config_categoria', 'categoria'),
        Index('idx_config_activo', 'activo'),
        {'schema': 'iot_schema'}
    )

class Auditoria(Base):
    """Modelo para auditoría del sistema"""
    __tablename__ = 'auditoria'
    __table_args__ = {'schema': 'iot_schema'}
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('iot_schema.usuarios.id'))
    entidad = Column(Text, nullable=False)
    entidad_id = Column(UUID(as_uuid=True))
    accion = Column(Text, nullable=False)
    cambios = Column(JSONB, default=dict)
    ip_origen = Column(INET)
    user_agent = Column(Text)
    contexto = Column(JSONB, default=dict)
    ts = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    
    # Relaciones
    usuario = relationship("Usuario")
    
    # Índices
    __table_args__ = (
        Index('idx_auditoria_entidad_ts', 'entidad', 'ts'),
        Index('idx_auditoria_usuario_ts', 'usuario_id', 'ts'),
        Index('idx_auditoria_accion_ts', 'accion', 'ts'),
        {'schema': 'iot_schema'}
    )
