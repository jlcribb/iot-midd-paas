-- ============================================================================
-- Esquema de Base de Datos para IoT Middleware
-- ============================================================================
-- 
-- Este archivo contiene la estructura completa de la base de datos para
-- el sistema IoT Middleware, incluyendo todas las entidades, relaciones,
-- índices y funcionalidades de auditoría.
--
-- Características principales:
-- - Normalización y performance optimizada
-- - Particionamiento temporal para registros de datos
-- - Campos JSONB para flexibilidad y extensibilidad
-- - Sistema completo de auditoría
-- - Seguridad y encriptación
-- - Geo-localización opcional
-- ============================================================================

-- Crear esquema principal
CREATE SCHEMA IF NOT EXISTS iot_schema;

-- Activar extensiones útiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- PostGIS (opcional, comentar si no se usa)
-- CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- ENUMS Y TIPOS PERSONALIZADOS
-- ============================================================================

DO $$
BEGIN
  -- Estado de proyectos
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_proyecto') THEN
    CREATE TYPE estado_proyecto AS ENUM (
      'planificado', 'activo', 'pausado', 'cerrado', 'cancelado'
    );
  END IF;

  -- Protocolos de comunicación
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'protocolo_comunicacion') THEN
    CREATE TYPE protocolo_comunicacion AS ENUM (
      'MQTT', 'BLE', 'HTTP', 'RF', 'LoRa', 'Modbus', 'OPC_UA', 'Otro'
    );
  END IF;

  -- Tipos de datos para canales
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_dato') THEN
    CREATE TYPE tipo_dato AS ENUM (
      'int', 'float', 'bool', 'string', 'json', 'binary', 'timestamp'
    );
  END IF;

  -- Roles del sistema
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rol_sistema') THEN
    CREATE TYPE rol_sistema AS ENUM (
      'admin', 'tecnico', 'cliente', 'lectura', 'supervisor'
    );
  END IF;

  -- Calidad de datos (estándar OPC UA)
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'calidad_dato') THEN
    CREATE TYPE calidad_dato AS ENUM (
      'OK', 'GOOD', 'UNCERTAIN', 'BAD', 'SUSPECTO', 'MALO'
    );
  END IF;

  -- Severidad de eventos/alarmas
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'severidad_evento') THEN
    CREATE TYPE severidad_evento AS ENUM (
      'info', 'warning', 'error', 'critical', 'fatal'
    );
  END IF;

  -- Estados de dispositivos
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_dispositivo') THEN
    CREATE TYPE estado_dispositivo AS ENUM (
      'activo', 'inactivo', 'mantenimiento', 'error', 'desconectado'
    );
  END IF;
END$$;

-- ============================================================================
-- TABLAS PRINCIPALES
-- ============================================================================

-- 1) CLIENTES
CREATE TABLE IF NOT EXISTS iot_schema.clientes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nombre TEXT NOT NULL,
  sector TEXT,
  industria TEXT,
  notas TEXT,
  contacto_principal JSONB NOT NULL DEFAULT '{}', -- {nombre, email, telefono, cargo}
  contactos_adicionales JSONB DEFAULT '[]', -- [{nombre, email, telefono, cargo, tipo}]
  direccion JSONB, -- {calle, ciudad, estado, pais, codigo_postal}
  configuracion JSONB DEFAULT '{}', -- configuraciones específicas del cliente
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  creado_por UUID,
  actualizado_por UUID
);

-- 2) PROYECTOS
CREATE TABLE IF NOT EXISTS iot_schema.proyectos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  cliente_id UUID NOT NULL REFERENCES iot_schema.clientes(id) ON DELETE CASCADE,
  nombre TEXT NOT NULL,
  descripcion TEXT,
  estado estado_proyecto NOT NULL DEFAULT 'planificado',
  fecha_inicio DATE,
  fecha_fin DATE,
  presupuesto DECIMAL(15,2),
  prioridad SMALLINT DEFAULT 1, -- 1=baja, 2=media, 3=alta, 4=crítica
  configuracion JSONB DEFAULT '{}', -- configuraciones específicas del proyecto
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  creado_por UUID,
  actualizado_por UUID
);

-- 3) UNIDADES DE PROYECTO
CREATE TABLE IF NOT EXISTS iot_schema.unidades_proyecto (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  proyecto_id UUID NOT NULL REFERENCES iot_schema.proyectos(id) ON DELETE CASCADE,
  nombre TEXT NOT NULL,
  descripcion TEXT,
  ubicacion TEXT,
  responsable TEXT,
  responsable_email TEXT,
  responsable_telefono TEXT,
  -- Geo-localización: usa UNA de las dos opciones
  lat DOUBLE PRECISION,
  lon DOUBLE PRECISION,
  -- geom geometry(Point,4326), -- si usas PostGIS
  configuracion JSONB DEFAULT '{}', -- configuraciones específicas de la unidad
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  creado_por UUID,
  actualizado_por UUID
);

-- 4) SESIONES DE TOMA DE DATOS
CREATE TABLE IF NOT EXISTS iot_schema.sesiones (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  unidad_id UUID NOT NULL REFERENCES iot_schema.unidades_proyecto(id) ON DELETE CASCADE,
  nombre TEXT,
  descripcion TEXT,
  inicio TIMESTAMPTZ NOT NULL,
  fin TIMESTAMPTZ,
  estado TEXT DEFAULT 'activa', -- activa, pausada, finalizada, cancelada
  observaciones TEXT,
  configuracion JSONB DEFAULT '{}', -- configuraciones de la sesión
  metadata JSONB DEFAULT '{}', -- datos adicionales de la sesión
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  creado_por UUID,
  actualizado_por UUID
);

-- 5) DISPOSITIVOS (catálogo)
CREATE TABLE IF NOT EXISTS iot_schema.dispositivos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tipo TEXT NOT NULL, -- sensor, actuador, gateway, etc.
  fabricante TEXT,
  modelo TEXT,
  identificador_unico TEXT UNIQUE NOT NULL, -- MAC/Serial/UUID del equipo
  protocolo protocolo_comunicacion NOT NULL DEFAULT 'MQTT',
  vida_util_meses INTEGER,
  especificaciones_tecnicas JSONB DEFAULT '{}', -- datasheets, p.ej. {sensibilidad:"...", rango:"..."}
  configuracion_protocolo JSONB DEFAULT '{}', -- configuraciones específicas del protocolo
  firmware_version TEXT,
  hardware_version TEXT,
  certificaciones JSONB DEFAULT '[]', -- lista de certificaciones
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  creado_por UUID,
  actualizado_por UUID
);

-- 6) DISPOSITIVOS EN PROYECTO (asignación y ubicación)
CREATE TABLE IF NOT EXISTS iot_schema.dispositivos_proyecto (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  proyecto_id UUID NOT NULL REFERENCES iot_schema.proyectos(id) ON DELETE CASCADE,
  dispositivo_id UUID NOT NULL REFERENCES iot_schema.dispositivos(id) ON DELETE RESTRICT,
  unidad_id UUID REFERENCES iot_schema.unidades_proyecto(id) ON DELETE SET NULL,
  nombre_personalizado TEXT, -- nombre específico en el proyecto
  descripcion TEXT,
  fecha_instalacion DATE NOT NULL DEFAULT CURRENT_DATE,
  fecha_retiro DATE,
  estado estado_dispositivo NOT NULL DEFAULT 'activo',
  configuracion JSONB DEFAULT '{}', -- configuraciones específicas del proyecto
  ubicacion_fisica TEXT, -- ubicación específica dentro de la unidad
  responsable TEXT,
  responsable_email TEXT,
  responsable_telefono TEXT,
  metadata JSONB DEFAULT '{}', -- datos adicionales del dispositivo en el proyecto
  UNIQUE (proyecto_id, dispositivo_id),
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  creado_por UUID,
  actualizado_por UUID
);

-- 7) CANALES / SENSORES de un DISPOSITIVO
CREATE TABLE IF NOT EXISTS iot_schema.canales (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  dispositivo_id UUID NOT NULL REFERENCES iot_schema.dispositivos(id) ON DELETE CASCADE,
  nombre TEXT NOT NULL,            -- ej. "temperatura"
  etiqueta TEXT,                   -- label amigable
  descripcion TEXT,
  unidad_medida TEXT,              -- ej. "°C", "ppm", "pH"
  tipo tipo_dato NOT NULL,         -- validación de tipo
  rango_min DOUBLE PRECISION,
  rango_max DOUBLE PRECISION,
  precision_valor INTEGER,         -- número de decimales
  frecuencia_muestreo INTEGER,     -- en segundos
  umbral_alto DOUBLE PRECISION,    -- umbral de alarma alta
  umbral_bajo DOUBLE PRECISION,    -- umbral de alarma baja
  metadatos JSONB DEFAULT '{}',    -- libre: {qos, topic, precision, ...}
  configuracion JSONB DEFAULT '{}', -- configuraciones específicas del canal
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE (dispositivo_id, nombre),
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  creado_por UUID,
  actualizado_por UUID
);

-- 8) REGISTROS DE DATOS (particionados por tiempo)
-- Tabla padre
CREATE TABLE IF NOT EXISTS iot_schema.registros_datos (
  id BIGSERIAL,
  canal_id UUID NOT NULL REFERENCES iot_schema.canales(id) ON DELETE CASCADE,
  ts TIMESTAMPTZ NOT NULL,
  valor_num DOUBLE PRECISION,
  valor_int BIGINT,
  valor_bool BOOLEAN,
  valor_text TEXT,
  valor_json JSONB,
  calidad calidad_dato DEFAULT 'OK',
  calidad_porcentaje INTEGER DEFAULT 100, -- porcentaje de calidad (0-100)
  metadata JSONB DEFAULT '{}',           -- e.g. {qos, ip, device_status, rssi, etc.}
  procesado BOOLEAN DEFAULT FALSE,       -- si el dato ya fue procesado
  validado BOOLEAN DEFAULT FALSE,        -- si el dato pasó validación
  PRIMARY KEY (id, ts)
) PARTITION BY RANGE (ts);

-- 9) EVENTOS / ALARMAS
CREATE TABLE IF NOT EXISTS iot_schema.eventos_alarmas (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  proyecto_id UUID NOT NULL REFERENCES iot_schema.proyectos(id) ON DELETE CASCADE,
  canal_id UUID REFERENCES iot_schema.canales(id) ON DELETE SET NULL,
  unidad_id UUID REFERENCES iot_schema.unidades_proyecto(id) ON DELETE SET NULL,
  dispositivo_id UUID REFERENCES iot_schema.dispositivos(id) ON DELETE SET NULL,
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  severidad severidad_evento NOT NULL DEFAULT 'info',
  codigo TEXT,                             -- opcional código estándar/OPC UA
  titulo TEXT NOT NULL,
  descripcion TEXT,
  detalles JSONB DEFAULT '{}',             -- valores que dispararon el evento
  estado TEXT DEFAULT 'activa',            -- activa, reconocida, resuelta, cerrada
  reconocida_por UUID,
  reconocida_en TIMESTAMPTZ,
  resuelta_por UUID,
  resuelta_en TIMESTAMPTZ,
  comentarios TEXT,
  metadata JSONB DEFAULT '{}',
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  creado_por UUID,
  actualizado_por UUID
);

-- 10) USUARIOS, ROLES y ÁMBITO (scope)
CREATE TABLE IF NOT EXISTS iot_schema.usuarios (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email CITEXT UNIQUE NOT NULL,
  nombre TEXT NOT NULL,
  apellido TEXT,
  password_hash TEXT NOT NULL,
  rol rol_sistema NOT NULL DEFAULT 'lectura',
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  ultimo_login TIMESTAMPTZ,
  configuracion JSONB DEFAULT '{}', -- preferencias del usuario
  metadata JSONB DEFAULT '{}',
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  creado_por UUID,
  actualizado_por UUID
);

-- Asociación usuario → cliente/proyecto (scoping)
CREATE TABLE IF NOT EXISTS iot_schema.usuarios_scope (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  usuario_id UUID NOT NULL REFERENCES iot_schema.usuarios(id) ON DELETE CASCADE,
  cliente_id UUID REFERENCES iot_schema.clientes(id) ON DELETE CASCADE,
  proyecto_id UUID REFERENCES iot_schema.proyectos(id) ON DELETE CASCADE,
  permisos JSONB DEFAULT '{}', -- permisos específicos en este scope
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (usuario_id, COALESCE(cliente_id, '00000000-0000-0000-0000-000000000000'), COALESCE(proyecto_id,'00000000-0000-0000-0000-000000000000'))
);

-- 11) CONFIGURACIONES DEL MIDDLEWARE (versionadas)
CREATE TABLE IF NOT EXISTS iot_schema.config_middleware (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  clave TEXT NOT NULL,
  valor JSONB NOT NULL,                 -- frecuencias, umbrales, reglas
  descripcion TEXT,
  categoria TEXT,                        -- agrupación de configuraciones
  version INTEGER NOT NULL DEFAULT 1,
  sensible BOOLEAN NOT NULL DEFAULT FALSE, -- true: se cifra parte del contenido
  vigente BOOLEAN NOT NULL DEFAULT TRUE,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_por UUID REFERENCES iot_schema.usuarios(id),
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_por UUID REFERENCES iot_schema.usuarios(id)
);

-- 12) AUDITORÍA
CREATE TABLE IF NOT EXISTS iot_schema.auditoria (
  id BIGSERIAL PRIMARY KEY,
  usuario_id UUID REFERENCES iot_schema.usuarios(id),
  entidad TEXT NOT NULL,           -- p.ej. 'config_middleware','eventos_alarmas','canales'
  entidad_id UUID,
  accion TEXT NOT NULL,            -- 'INSERT','UPDATE','DELETE'
  cambios JSONB DEFAULT '{}',      -- diff o snapshot: {antes:{}, despues:{}}
  ip_origen INET,
  user_agent TEXT,
  contexto JSONB DEFAULT '{}',     -- información adicional del contexto
  ts TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- ============================================================================

-- Índices básicos
CREATE INDEX IF NOT EXISTS idx_clientes_activo ON iot_schema.clientes(activo);
CREATE INDEX IF NOT EXISTS idx_proyectos_cliente ON iot_schema.proyectos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_proyectos_estado ON iot_schema.proyectos(estado);
CREATE INDEX IF NOT EXISTS idx_proyectos_activo ON iot_schema.proyectos(activo);
CREATE INDEX IF NOT EXISTS idx_unidades_proyecto_proyecto ON iot_schema.unidades_proyecto(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_unidades_proyecto_activo ON iot_schema.unidades_proyecto(activo);
CREATE INDEX IF NOT EXISTS idx_sesiones_unidad ON iot_schema.sesiones(unidad_id);
CREATE INDEX IF NOT EXISTS idx_sesiones_rango ON iot_schema.sesiones(inicio, fin);
CREATE INDEX IF NOT EXISTS idx_sesiones_estado ON iot_schema.sesiones(estado);
CREATE INDEX IF NOT EXISTS idx_dispositivos_tipo ON iot_schema.dispositivos(tipo);
CREATE INDEX IF NOT EXISTS idx_dispositivos_protocolo ON iot_schema.dispositivos(protocolo);
CREATE INDEX IF NOT EXISTS idx_dispositivos_activo ON iot_schema.dispositivos(activo);
CREATE INDEX IF NOT EXISTS idx_disp_proj_proyecto ON iot_schema.dispositivos_proyecto(proyecto_id);
CREATE INDEX IF NOT EXISTS idx_disp_proj_unidad ON iot_schema.dispositivos_proyecto(unidad_id);
CREATE INDEX IF NOT EXISTS idx_disp_proj_estado ON iot_schema.dispositivos_proyecto(estado);
CREATE INDEX IF NOT EXISTS idx_canales_dispositivo ON iot_schema.canales(dispositivo_id);
CREATE INDEX IF NOT EXISTS idx_canales_tipo ON iot_schema.canales(tipo);
CREATE INDEX IF NOT EXISTS idx_canales_activo ON iot_schema.canales(activo);

-- Índices para registros de datos
CREATE INDEX IF NOT EXISTS idx_reg_datos_canal_ts ON iot_schema.registros_datos(canal_id, ts);
CREATE INDEX IF NOT EXISTS idx_reg_datos_ts ON iot_schema.registros_datos(ts);
CREATE INDEX IF NOT EXISTS idx_reg_datos_calidad ON iot_schema.registros_datos(calidad);
CREATE INDEX IF NOT EXISTS idx_reg_datos_procesado ON iot_schema.registros_datos(procesado);
CREATE INDEX IF NOT EXISTS idx_reg_datos_validado ON iot_schema.registros_datos(validado);

-- Índices para eventos/alarmas
CREATE INDEX IF NOT EXISTS idx_eventos_proyecto_ts ON iot_schema.eventos_alarmas(proyecto_id, ts);
CREATE INDEX IF NOT EXISTS idx_eventos_canal_ts ON iot_schema.eventos_alarmas(canal_id, ts);
CREATE INDEX IF NOT EXISTS idx_eventos_unidad_ts ON iot_schema.eventos_alarmas(unidad_id, ts);
CREATE INDEX IF NOT EXISTS idx_eventos_severidad ON iot_schema.eventos_alarmas(severidad);
CREATE INDEX IF NOT EXISTS idx_eventos_estado ON iot_schema.eventos_alarmas(estado);
CREATE INDEX IF NOT EXISTS idx_eventos_ts ON iot_schema.eventos_alarmas(ts);

-- Índices para usuarios
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON iot_schema.usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON iot_schema.usuarios(rol);
CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON iot_schema.usuarios(activo);
CREATE INDEX IF NOT EXISTS idx_usuarios_scope_usuario ON iot_schema.usuarios_scope(usuario_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_scope_cliente ON iot_schema.usuarios_scope(cliente_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_scope_proyecto ON iot_schema.usuarios_scope(proyecto_id);

-- Índices para configuraciones
CREATE INDEX IF NOT EXISTS idx_config_clave_vigente ON iot_schema.config_middleware(clave, vigente);
CREATE INDEX IF NOT EXISTS idx_config_categoria ON iot_schema.config_middleware(categoria);
CREATE INDEX IF NOT EXISTS idx_config_activo ON iot_schema.config_middleware(activo);

-- Índices para auditoría
CREATE INDEX IF NOT EXISTS idx_auditoria_entidad_ts ON iot_schema.auditoria(entidad, ts);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario_ts ON iot_schema.auditoria(usuario_id, ts);
CREATE INDEX IF NOT EXISTS idx_auditoria_accion_ts ON iot_schema.auditoria(accion, ts);

-- Índices JSONB para búsquedas avanzadas
CREATE INDEX IF NOT EXISTS idx_reg_metadata ON iot_schema.registros_datos USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_canales_metadatos ON iot_schema.canales USING GIN (metadatos);
CREATE INDEX IF NOT EXISTS idx_eventos_detalles ON iot_schema.eventos_alarmas USING GIN (detalles);
CREATE INDEX IF NOT EXISTS idx_dispositivos_especificaciones ON iot_schema.dispositivos USING GIN (especificaciones_tecnicas);
CREATE INDEX IF NOT EXISTS idx_clientes_contacto ON iot_schema.clientes USING GIN (contacto_principal);
CREATE INDEX IF NOT EXISTS idx_usuarios_config ON iot_schema.usuarios USING GIN (configuracion);

-- ============================================================================
-- FUNCIONES Y TRIGGERS DE AUDITORÍA
-- ============================================================================

-- Función genérica de auditoría
CREATE OR REPLACE FUNCTION iot_schema.fn_auditar_cambios()
RETURNS trigger AS $$
DECLARE
  v_usuario_id UUID;
  v_cambios JSONB;
BEGIN
  -- Obtener usuario actual (implementar según tu sistema de autenticación)
  v_usuario_id := current_setting('app.current_user_id', true)::UUID;
  
  IF TG_OP = 'INSERT' THEN
    v_cambios := jsonb_build_object('despues', row_to_json(NEW));
    
    INSERT INTO iot_schema.auditoria(usuario_id, entidad, entidad_id, accion, cambios)
    VALUES (v_usuario_id, TG_TABLE_NAME, NEW.id, 'INSERT', v_cambios);
    
    RETURN NEW;
    
  ELSIF TG_OP = 'UPDATE' THEN
    v_cambios := jsonb_build_object(
      'antes', row_to_json(OLD),
      'despues', row_to_json(NEW)
    );
    
    INSERT INTO iot_schema.auditoria(usuario_id, entidad, entidad_id, accion, cambios)
    VALUES (v_usuario_id, TG_TABLE_NAME, NEW.id, 'UPDATE', v_cambios);
    
    RETURN NEW;
    
  ELSIF TG_OP = 'DELETE' THEN
    v_cambios := jsonb_build_object('antes', row_to_json(OLD));
    
    INSERT INTO iot_schema.auditoria(usuario_id, entidad, entidad_id, accion, cambios)
    VALUES (v_usuario_id, TG_TABLE_NAME, OLD.id, 'DELETE', v_cambios);
    
    RETURN OLD;
  END IF;
  
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Función para actualizar timestamp de actualización
CREATE OR REPLACE FUNCTION iot_schema.fn_actualizar_timestamp()
RETURNS trigger AS $$
BEGIN
  NEW.actualizado_en = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS DE AUDITORÍA
-- ============================================================================

-- Triggers para auditoría en tablas principales
DO $$
DECLARE
  tabla TEXT;
BEGIN
  FOR tabla IN 
    SELECT unnest(ARRAY[
      'clientes', 'proyectos', 'unidades_proyecto', 'sesiones',
      'dispositivos', 'dispositivos_proyecto', 'canales',
      'eventos_alarmas', 'usuarios', 'usuarios_scope', 'config_middleware'
    ])
  LOOP
    EXECUTE format('
      DROP TRIGGER IF EXISTS trg_auditar_%s ON iot_schema.%s;
      CREATE TRIGGER trg_auditar_%s
        AFTER INSERT OR UPDATE OR DELETE ON iot_schema.%s
        FOR EACH ROW EXECUTE FUNCTION iot_schema.fn_auditar_cambios();
    ', tabla, tabla, tabla, tabla);
  END LOOP;
END$$;

-- Triggers para actualización de timestamps
DO $$
DECLARE
  tabla TEXT;
BEGIN
  FOR tabla IN 
    SELECT unnest(ARRAY[
      'clientes', 'proyectos', 'unidades_proyecto', 'sesiones',
      'dispositivos', 'dispositivos_proyecto', 'canales',
      'eventos_alarmas', 'usuarios', 'usuarios_scope', 'config_middleware'
    ])
  LOOP
    EXECUTE format('
      DROP TRIGGER IF EXISTS trg_timestamp_%s ON iot_schema.%s;
      CREATE TRIGGER trg_timestamp_%s
        BEFORE UPDATE ON iot_schema.%s
        FOR EACH ROW EXECUTE FUNCTION iot_schema.fn_actualizar_timestamp();
    ', tabla, tabla, tabla, tabla);
  END LOOP;
END$$;

-- ============================================================================
-- FUNCIONES UTILITARIAS
-- ============================================================================

-- Función para crear particiones mensuales automáticamente
CREATE OR REPLACE FUNCTION iot_schema.crear_particion_mensual(fecha DATE)
RETURNS TEXT AS $$
DECLARE
  nombre_particion TEXT;
  fecha_inicio DATE;
  fecha_fin DATE;
  sql_particion TEXT;
BEGIN
  -- Calcular fechas de la partición
  fecha_inicio := date_trunc('month', fecha);
  fecha_fin := fecha_inicio + interval '1 month';
  nombre_particion := 'registros_datos_' || to_char(fecha_inicio, 'YYYY_MM');
  
  -- Crear partición si no existe
  IF NOT EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relname = nombre_particion AND n.nspname = 'iot_schema'
  ) THEN
    sql_particion := format('
      CREATE TABLE IF NOT EXISTS iot_schema.%I
      PARTITION OF iot_schema.registros_datos
      FOR VALUES FROM (%L) TO (%L)
    ', nombre_particion, fecha_inicio, fecha_fin);
    
    EXECUTE sql_particion;
    
    -- Crear índices específicos para la partición
    EXECUTE format('
      CREATE INDEX IF NOT EXISTS idx_%s_canal_ts ON iot_schema.%I(canal_id, ts);
      CREATE INDEX IF NOT EXISTS idx_%s_ts ON iot_schema.%I(ts);
      CREATE INDEX IF NOT EXISTS idx_%s_calidad ON iot_schema.%I(calidad);
    ', nombre_particion, nombre_particion, nombre_particion, nombre_particion, nombre_particion, nombre_particion);
    
    RETURN 'Partición creada: ' || nombre_particion;
  ELSE
    RETURN 'Partición ya existe: ' || nombre_particion;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Función para limpiar particiones antiguas
CREATE OR REPLACE FUNCTION iot_schema.limpiar_particiones_antiguas(meses_retener INTEGER DEFAULT 12)
RETURNS TEXT AS $$
DECLARE
  particion_a_eliminar TEXT;
  fecha_limite DATE;
  sql_eliminar TEXT;
  eliminadas INTEGER := 0;
BEGIN
  fecha_limite := current_date - interval '1 month' * meses_retener;
  
  FOR particion_a_eliminar IN
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname = 'iot_schema' 
      AND tablename LIKE 'registros_datos_%'
      AND tablename < 'registros_datos_' || to_char(fecha_limite, 'YYYY_MM')
  LOOP
    sql_eliminar := format('DROP TABLE IF EXISTS iot_schema.%I', particion_a_eliminar);
    EXECUTE sql_eliminar;
    eliminadas := eliminadas + 1;
  END LOOP;
  
  RETURN format('Particiones eliminadas: %s', eliminadas);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VISTAS ÚTILES
-- ============================================================================

-- Vista para resumen de proyectos
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

-- Vista para resumen de dispositivos
CREATE OR REPLACE VIEW iot_schema.v_resumen_dispositivos AS
SELECT 
  d.id,
  d.tipo,
  d.fabricante,
  d.modelo,
  d.identificador_unico,
  d.protocolo,
  d.estado_dispositivo,
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
         d.estado_dispositivo, dp.nombre_personalizado, dp.fecha_instalacion, dp.fecha_retiro,
         p.nombre, up.nombre;

-- ============================================================================
-- POLÍTICAS DE SEGURIDAD (RLS - Row Level Security)
-- ============================================================================

-- Habilitar RLS en tablas sensibles
ALTER TABLE iot_schema.config_middleware ENABLE ROW LEVEL SECURITY;
ALTER TABLE iot_schema.auditoria ENABLE ROW LEVEL SECURITY;

-- Política para configuraciones (solo admins pueden ver configuraciones sensibles)
CREATE POLICY pol_config_admin ON iot_schema.config_middleware
  FOR ALL USING (
    NOT sensible OR 
    EXISTS (
      SELECT 1 FROM iot_schema.usuarios 
      WHERE id = current_setting('app.current_user_id', true)::UUID 
        AND rol = 'admin'
    )
  );

-- Política para auditoría (solo admins pueden ver auditoría completa)
CREATE POLICY pol_auditoria_admin ON iot_schema.auditoria
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM iot_schema.usuarios 
      WHERE id = current_setting('app.current_user_id', true)::UUID 
        AND rol = 'admin'
    )
  );

-- ============================================================================
-- DATOS INICIALES
-- ============================================================================

-- Insertar usuario administrador por defecto
INSERT INTO iot_schema.usuarios (email, nombre, apellido, password_hash, rol, activo)
VALUES (
  'admin@iot-middleware.com',
  'Administrador',
  'Sistema',
  crypt('admin123', gen_salt('bf')), -- Cambiar en producción
  'admin',
  true
) ON CONFLICT (email) DO NOTHING;

-- Insertar cliente de ejemplo
INSERT INTO iot_schema.clientes (nombre, sector, industria, contacto_principal)
VALUES (
  'Cliente Demo',
  'Industrial',
  'Manufactura',
  '{"nombre": "Juan Pérez", "email": "juan.perez@cliente.com", "telefono": "+1234567890", "cargo": "Gerente de Operaciones"}'
) ON CONFLICT DO NOTHING;

-- ============================================================================
-- COMENTARIOS FINALES
-- ============================================================================

COMMENT ON SCHEMA iot_schema IS 'Esquema principal para el sistema IoT Middleware';
COMMENT ON TABLE iot_schema.clientes IS 'Organizaciones o personas que utilizan el sistema';
COMMENT ON TABLE iot_schema.proyectos IS 'Proyectos asociados a clientes';
COMMENT ON TABLE iot_schema.unidades_proyecto IS 'Subdivisiones físicas y lógicas de proyectos';
COMMENT ON TABLE iot_schema.sesiones IS 'Períodos de recolección de datos';
COMMENT ON TABLE iot_schema.dispositivos IS 'Catálogo de dispositivos IoT';
COMMENT ON TABLE iot_schema.dispositivos_proyecto IS 'Asignación de dispositivos a proyectos';
COMMENT ON TABLE iot_schema.canales IS 'Sensores o canales de datos de dispositivos';
COMMENT ON TABLE iot_schema.registros_datos IS 'Datos capturados por los canales (particionado por tiempo)';
COMMENT ON TABLE iot_schema.eventos_alarmas IS 'Eventos y alarmas del sistema';
COMMENT ON TABLE iot_schema.usuarios IS 'Usuarios del sistema con roles y permisos';
COMMENT ON TABLE iot_schema.usuarios_scope IS 'Alcance de usuarios en clientes/proyectos';
COMMENT ON TABLE iot_schema.config_middleware IS 'Configuraciones del middleware IoT';
COMMENT ON TABLE iot_schema.auditoria IS 'Registro de cambios para auditoría';

-- ============================================================================
-- FIN DEL ESQUEMA
-- ============================================================================
