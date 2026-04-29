"""
Router CRUD para Proyectos
"""

from fastapi import APIRouter, Request, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import date
import logging
import re
import json
from uuid import UUID, uuid5, NAMESPACE_DNS
from sqlalchemy import text

from iot_middleware.storage.repositories import (
    ProyectoRepository,
    ClienteRepository,
    UnidadProyectoRepository,
    DispositivoProyectoRepository,
)
from iot_middleware.models.entities import (
    Proyecto,
    UnidadProyecto,
    Dispositivo,
    DispositivoProyecto,
    Canal,
)
from iot_middleware.models.enums import ProtocoloComunicacion, TipoDato, EstadoDispositivo
ALLOWED_ESTADOS = {
    "planificado",
    "activo",
    "pausado",
    "cerrado",
    "cancelado",
}

logger = logging.getLogger(__name__)

router = APIRouter()
CORE_SYNC_NAMESPACE = uuid5(NAMESPACE_DNS, "iot-middleware-core-public-v1")


# Modelos Pydantic
class ProyectoCreate(BaseModel):
    cliente_id: str
    nombre: str
    descripcion: Optional[str] = None
    estado: str = "planificado"
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    presupuesto: Optional[float] = None
    prioridad: int = 1
    configuracion: Dict[str, Any] = {}
    auto_provision_topologia: bool = True
    crear_gemelo_mix: bool = False
    
    @field_validator("fecha_inicio", "fecha_fin", mode="before")
    def _coerce_empty_date(cls, value):
        if value in ("", None):
            return None
        return value
    
    @field_validator("presupuesto", mode="before")
    def _coerce_empty_float(cls, value):
        if value in ("", None):
            return None
        return value


class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    presupuesto: Optional[float] = None
    prioridad: Optional[int] = None
    activo: Optional[bool] = None
    configuracion: Optional[Dict[str, Any]] = None
    
    @field_validator("fecha_inicio", "fecha_fin", mode="before")
    def _coerce_empty_date(cls, value):
        if value in ("", None):
            return None
        return value
    
    @field_validator("presupuesto", mode="before")
    def _coerce_empty_float(cls, value):
        if value in ("", None):
            return None
        return value


class ProyectoResponse(BaseModel):
    id: str
    cliente_id: str
    nombre: str
    descripcion: Optional[str]
    estado: str
    fecha_inicio: Optional[date]
    fecha_fin: Optional[date]
    presupuesto: Optional[float]
    prioridad: int
    activo: bool
    creado_en: str
    actualizado_en: str

    class Config:
        from_attributes = True


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized or "item"


def _topic_path(proyecto_slug: str, unidad_slug: str, placa_slug: str, canal_slug: str) -> str:
    return f"iot/{proyecto_slug}/{unidad_slug}/{placa_slug}/{canal_slug}"


def _stable_core_uuid(kind: str, legacy_id: str) -> str:
    return str(uuid5(CORE_SYNC_NAMESPACE, f"{kind}:{legacy_id}"))


def _map_legacy_project_status(legacy_estado: Any, legacy_activo: bool) -> str:
    if not legacy_activo:
        return "archived"
    value = str(getattr(legacy_estado, "value", legacy_estado)).strip().lower()
    if value == "activo":
        return "active"
    if value in {"cerrado", "cancelado"}:
        return "archived"
    return "inactive"


def _infer_core_asset_type(device_tipo: Optional[str], name_hint: Optional[str]) -> str:
    text_ref = f"{device_tipo or ''} {name_hint or ''}".lower()
    if any(token in text_ref for token in ("sensor", "nivel", "temperature", "temp", "humedad", "pressure")):
        return "sensor"
    if any(token in text_ref for token in ("valvula", "electrovalvula", "servo", "motor", "actuador", "relay")):
        return "actuator"
    if any(token in text_ref for token in ("gateway", "pasarela")):
        return "gateway"
    return "programmable_node"


def _map_legacy_device_status(legacy_estado: Any) -> str:
    value = str(getattr(legacy_estado, "value", legacy_estado)).strip().lower()
    if value == "activo":
        return "active"
    if value == "inactivo":
        return "inactive"
    if value == "mantenimiento":
        return "maintenance"
    if value == "error":
        return "fault"
    if value == "desconectado":
        return "offline"
    return "inactive"


def _sync_project_to_core_schema(request: Request, proyecto_id: str, *, archived: bool = False) -> Dict[str, Any]:
    """Sincroniza proyecto legacy (iot_schema) hacia core schema (public)."""
    db_handler = request.app.state.db_handler
    if not db_handler:
        raise ValueError("db_handler no disponible")

    with db_handler.get_session() as session:
        project_row = session.execute(
            text(
                """
                SELECT id, nombre, descripcion, estado, activo, configuracion
                FROM iot_schema.proyectos
                WHERE id = CAST(:project_id AS uuid)
                """
            ),
            {"project_id": proyecto_id},
        ).mappings().first()
        if not project_row:
            raise ValueError(f"Proyecto no encontrado para sync core: {proyecto_id}")

        core_project_id = _stable_core_uuid("project", str(project_row["id"]))
        core_project_status = "archived" if archived else _map_legacy_project_status(
            project_row["estado"], bool(project_row["activo"])
        )
        project_metadata = json.dumps(
            {
                "source": "legacy_iot_schema",
                "legacy_project_id": str(project_row["id"]),
                "legacy_estado": str(getattr(project_row["estado"], "value", project_row["estado"])),
            },
            ensure_ascii=True,
        )

        session.execute(
            text(
                """
                INSERT INTO public.projects (id, name, description, status, metadata, created_at, updated_at)
                VALUES (
                    CAST(:id AS uuid),
                    :name,
                    :description,
                    CAST(:status AS project_status_enum),
                    CAST(:metadata AS jsonb),
                    now(),
                    now()
                )
                ON CONFLICT (id) DO UPDATE
                SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    metadata = EXCLUDED.metadata,
                    updated_at = now()
                """
            ),
            {
                "id": core_project_id,
                "name": project_row["nombre"],
                "description": project_row["descripcion"],
                "status": core_project_status,
                "metadata": project_metadata,
            },
        )

        if archived or core_project_status == "archived":
            session.execute(
                text(
                    """
                    UPDATE public.assets
                    SET
                        status = CAST('inactive' AS asset_status_enum),
                        metadata = COALESCE(metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb,
                        updated_at = now()
                    WHERE project_id = CAST(:project_id AS uuid)
                    """
                ),
                {"project_id": core_project_id},
            )
            session.execute(
                text(
                    """
                    UPDATE public.topology_links
                    SET
                        status = CAST('inactive' AS link_status_enum),
                        metadata = COALESCE(metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb,
                        updated_at = now()
                    WHERE project_id = CAST(:project_id AS uuid)
                    """
                ),
                {"project_id": core_project_id},
            )
            session.execute(
                text(
                    """
                    UPDATE public.sectors
                    SET
                        metadata = COALESCE(metadata, '{}'::jsonb) || '{"is_active": false}'::jsonb,
                        updated_at = now()
                    WHERE project_id = CAST(:project_id AS uuid)
                    """
                ),
                {"project_id": core_project_id},
            )
            archived_counts = session.execute(
                text(
                    """
                    SELECT
                        (SELECT count(*) FROM public.sectors WHERE project_id = CAST(:project_id AS uuid)) AS sectors,
                        (SELECT count(*) FROM public.assets WHERE project_id = CAST(:project_id AS uuid)) AS assets,
                        (SELECT count(*) FROM public.topology_links WHERE project_id = CAST(:project_id AS uuid)) AS links
                    """
                ),
                {"project_id": core_project_id},
            ).mappings().first()
            return {
                "project_id": proyecto_id,
                "core_project_id": core_project_id,
                "status": core_project_status,
                "sectors": int(archived_counts["sectors"]),
                "assets": int(archived_counts["assets"]),
                "links": int(archived_counts["links"]),
            }

        # Rebuild full project topology in core schema for deterministic sync.
        session.execute(
            text("DELETE FROM public.topology_links WHERE project_id = CAST(:project_id AS uuid)"),
            {"project_id": core_project_id},
        )
        session.execute(
            text("DELETE FROM public.assets WHERE project_id = CAST(:project_id AS uuid)"),
            {"project_id": core_project_id},
        )
        session.execute(
            text("DELETE FROM public.sectors WHERE project_id = CAST(:project_id AS uuid)"),
            {"project_id": core_project_id},
        )

        units = session.execute(
            text(
                """
                SELECT id, nombre, descripcion, activo
                FROM iot_schema.unidades_proyecto
                WHERE proyecto_id = CAST(:project_id AS uuid)
                """
            ),
            {"project_id": proyecto_id},
        ).mappings().all()

        sector_by_unit: Dict[str, str] = {}
        sector_count = 0
        for unit in units:
            if not bool(unit["activo"]):
                continue
            legacy_unit_id = str(unit["id"])
            core_sector_id = _stable_core_uuid("sector", legacy_unit_id)
            sector_by_unit[legacy_unit_id] = core_sector_id
            sector_count += 1
            sector_metadata = json.dumps(
                {
                    "source": "legacy_iot_schema",
                    "legacy_unit_id": legacy_unit_id,
                    "is_active": True,
                },
                ensure_ascii=True,
            )
            session.execute(
                text(
                    """
                    INSERT INTO public.sectors (
                        id, project_id, location_id, name, code, description, metadata, created_at, updated_at
                    )
                    VALUES (
                        CAST(:id AS uuid),
                        CAST(:project_id AS uuid),
                        NULL,
                        :name,
                        :code,
                        :description,
                        CAST(:metadata AS jsonb),
                        now(),
                        now()
                    )
                    ON CONFLICT (id) DO UPDATE
                    SET
                        project_id = EXCLUDED.project_id,
                        name = EXCLUDED.name,
                        code = EXCLUDED.code,
                        description = EXCLUDED.description,
                        metadata = EXCLUDED.metadata,
                        updated_at = now()
                    """
                ),
                {
                    "id": core_sector_id,
                    "project_id": core_project_id,
                    "name": unit["nombre"],
                    "code": f"legacy-unit-{legacy_unit_id}",
                    "description": unit["descripcion"],
                    "metadata": sector_metadata,
                },
            )

        devices = session.execute(
            text(
                """
                SELECT
                    dp.id AS dp_id,
                    dp.unidad_id,
                    dp.nombre_personalizado,
                    dp.descripcion AS dp_descripcion,
                    dp.estado AS dp_estado,
                    d.id AS dispositivo_id,
                    d.tipo AS dispositivo_tipo,
                    d.fabricante,
                    d.modelo,
                    d.identificador_unico,
                    d.firmware_version,
                    d.hardware_version
                FROM iot_schema.dispositivos_proyecto dp
                JOIN iot_schema.dispositivos d ON d.id = dp.dispositivo_id
                WHERE dp.proyecto_id = CAST(:project_id AS uuid)
                """
            ),
            {"project_id": proyecto_id},
        ).mappings().all()

        asset_count = 0
        link_count = 0
        for device in devices:
            unit_id = str(device["unidad_id"]) if device["unidad_id"] else None
            if not unit_id or unit_id not in sector_by_unit:
                continue

            legacy_dp_id = str(device["dp_id"])
            core_asset_id = _stable_core_uuid("asset", legacy_dp_id)
            core_sector_id = sector_by_unit[unit_id]
            display_name = device["nombre_personalizado"] or device["modelo"] or device["dispositivo_tipo"] or legacy_dp_id
            asset_type = _infer_core_asset_type(device["dispositivo_tipo"], display_name)
            asset_status = _map_legacy_device_status(device["dp_estado"])
            subtype = (device["modelo"] or device["dispositivo_tipo"] or "generic").strip()
            asset_metadata = json.dumps(
                {
                    "source": "legacy_iot_schema",
                    "legacy_dispositivo_proyecto_id": legacy_dp_id,
                    "legacy_dispositivo_id": str(device["dispositivo_id"]),
                    "legacy_unidad_id": unit_id,
                    "identificador_unico": device["identificador_unico"],
                    "firmware_version": device["firmware_version"],
                    "hardware_version": device["hardware_version"],
                },
                ensure_ascii=True,
            )

            session.execute(
                text(
                    """
                    INSERT INTO public.assets (
                        id,
                        project_id,
                        sector_id,
                        location_id,
                        parent_asset_id,
                        asset_type,
                        subtype,
                        name,
                        code,
                        description,
                        status,
                        role,
                        serial_number,
                        manufacturer,
                        model,
                        firmware_version,
                        hardware_version,
                        mac_address,
                        ip_address,
                        last_seen_at,
                        metadata,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        CAST(:id AS uuid),
                        CAST(:project_id AS uuid),
                        CAST(:sector_id AS uuid),
                        NULL,
                        NULL,
                        CAST(:asset_type AS asset_type_enum),
                        :subtype,
                        :name,
                        :code,
                        :description,
                        CAST(:status AS asset_status_enum),
                        NULL,
                        :serial_number,
                        :manufacturer,
                        :model,
                        :firmware_version,
                        :hardware_version,
                        NULL,
                        NULL,
                        NULL,
                        CAST(:metadata AS jsonb),
                        now(),
                        now()
                    )
                    ON CONFLICT (id) DO UPDATE
                    SET
                        project_id = EXCLUDED.project_id,
                        sector_id = EXCLUDED.sector_id,
                        asset_type = EXCLUDED.asset_type,
                        subtype = EXCLUDED.subtype,
                        name = EXCLUDED.name,
                        code = EXCLUDED.code,
                        description = EXCLUDED.description,
                        status = EXCLUDED.status,
                        serial_number = EXCLUDED.serial_number,
                        manufacturer = EXCLUDED.manufacturer,
                        model = EXCLUDED.model,
                        firmware_version = EXCLUDED.firmware_version,
                        hardware_version = EXCLUDED.hardware_version,
                        metadata = EXCLUDED.metadata,
                        updated_at = now()
                    """
                ),
                {
                    "id": core_asset_id,
                    "project_id": core_project_id,
                    "sector_id": core_sector_id,
                    "asset_type": asset_type,
                    "subtype": subtype,
                    "name": display_name,
                    "code": f"legacy-dp-{legacy_dp_id}",
                    "description": device["dp_descripcion"],
                    "status": asset_status,
                    "serial_number": device["identificador_unico"],
                    "manufacturer": device["fabricante"],
                    "model": device["modelo"],
                    "firmware_version": device["firmware_version"],
                    "hardware_version": device["hardware_version"],
                    "metadata": asset_metadata,
                },
            )
            asset_count += 1

            link_id = _stable_core_uuid("link_contains", f"{core_sector_id}:{core_asset_id}")
            link_metadata = json.dumps(
                {"source": "legacy_iot_schema", "legacy_dispositivo_proyecto_id": legacy_dp_id},
                ensure_ascii=True,
            )
            session.execute(
                text(
                    """
                    INSERT INTO public.topology_links (
                        id,
                        project_id,
                        source_asset_id,
                        target_asset_id,
                        source_sector_id,
                        target_sector_id,
                        relation_type,
                        connection_medium,
                        protocol,
                        ports,
                        link_quality,
                        status,
                        metadata,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        CAST(:id AS uuid),
                        CAST(:project_id AS uuid),
                        NULL,
                        CAST(:target_asset_id AS uuid),
                        CAST(:source_sector_id AS uuid),
                        NULL,
                        CAST('contains' AS topology_relation_enum),
                        NULL,
                        NULL,
                        '[]'::jsonb,
                        NULL,
                        CAST('active' AS link_status_enum),
                        CAST(:metadata AS jsonb),
                        now(),
                        now()
                    )
                    ON CONFLICT (id) DO UPDATE
                    SET
                        target_asset_id = EXCLUDED.target_asset_id,
                        source_sector_id = EXCLUDED.source_sector_id,
                        status = EXCLUDED.status,
                        metadata = EXCLUDED.metadata,
                        updated_at = now()
                    """
                ),
                {
                    "id": link_id,
                    "project_id": core_project_id,
                    "target_asset_id": core_asset_id,
                    "source_sector_id": core_sector_id,
                    "metadata": link_metadata,
                },
            )
            link_count += 1

        return {
            "project_id": proyecto_id,
            "core_project_id": core_project_id,
            "status": core_project_status,
            "sectors": sector_count,
            "assets": asset_count,
            "links": link_count,
        }


def _default_topologia_payload(proyecto_nombre: str) -> Dict[str, Any]:
    proyecto_slug = _slug(proyecto_nombre)
    return {
        "unidades": [
            {
                "nombre": "Producción",
                "slug": "produccion",
                "placas": [
                    {
                        "nombre": "Placa Principal",
                        "slug": "placa_principal",
                        "sensores": [
                            {"nombre": "temperatura", "tipo": "float", "unidad_medida": "°C"},
                            {"nombre": "humedad", "tipo": "float", "unidad_medida": "%"},
                        ],
                        "actuadores": [
                            {"nombre": "rele_bomba", "tipo": "bool", "unidad_medida": "on_off"},
                        ],
                    }
                ],
            }
        ],
        "topic_root": f"iot/{proyecto_slug}",
    }


def _default_gemelo_mix_topologia_payload(proyecto_nombre: str) -> Dict[str, Any]:
    proyecto_slug = _slug(proyecto_nombre)
    return {
        "unidades": [
            {
                "nombre": "tambores tinta",
                "slug": "tambores_tinta",
                "descripcion": "Unidad de produccion para tambores de tinta",
                "placas": [
                    {
                        "nombre": "sensor_nivel_tambor_azul",
                        "slug": "sensor_nivel_tambor_azul",
                        "tipo": "sensor_nivel",
                        "modelo": "ultrasonico_nivel",
                        "protocolo": "MQTT",
                        "sensores": [
                            {
                                "nombre": "nivel_tinta_azul",
                                "tipo": "float",
                                "unidad_medida": "%",
                                "rango_min": 0,
                                "rango_max": 100,
                                "umbral_bajo": 15,
                                "umbral_alto": 95,
                            }
                        ],
                    },
                    {
                        "nombre": "electrovalvula_tambor_azul",
                        "slug": "electrovalvula_tambor_azul",
                        "tipo": "electrovalvula",
                        "modelo": "ev_24v",
                        "protocolo": "MQTT",
                        "actuadores": [
                            {
                                "nombre": "ev_tinta_azul",
                                "tipo": "bool",
                                "unidad_medida": "open_close",
                            }
                        ],
                    },
                    {
                        "nombre": "sensor_nivel_tambor_rojo",
                        "slug": "sensor_nivel_tambor_rojo",
                        "tipo": "sensor_nivel",
                        "modelo": "ultrasonico_nivel",
                        "protocolo": "MQTT",
                        "sensores": [
                            {
                                "nombre": "nivel_tinta_roja",
                                "tipo": "float",
                                "unidad_medida": "%",
                                "rango_min": 0,
                                "rango_max": 100,
                                "umbral_bajo": 15,
                                "umbral_alto": 95,
                            }
                        ],
                    },
                    {
                        "nombre": "electrovalvula_tambor_rojo",
                        "slug": "electrovalvula_tambor_rojo",
                        "tipo": "electrovalvula",
                        "modelo": "ev_24v",
                        "protocolo": "MQTT",
                        "actuadores": [
                            {
                                "nombre": "ev_tinta_roja",
                                "tipo": "bool",
                                "unidad_medida": "open_close",
                            }
                        ],
                    }
                ],
            }
            ,
            {
                "nombre": "deposito mezcla",
                "slug": "deposito_mezcla",
                "descripcion": "Unidad de produccion para deposito de mezcla",
                "placas": [
                    {
                        "nombre": "sensor_nivel_deposito_mezcla",
                        "slug": "sensor_nivel_deposito_mezcla",
                        "tipo": "sensor_nivel",
                        "modelo": "ultrasonico_nivel",
                        "protocolo": "MQTT",
                        "sensores": [
                            {
                                "nombre": "nivel_deposito_mezcla",
                                "tipo": "float",
                                "unidad_medida": "%",
                                "rango_min": 0,
                                "rango_max": 100,
                                "umbral_bajo": 10,
                                "umbral_alto": 95,
                            }
                        ],
                    },
                    {
                        "nombre": "servomotor_deposito_mezcla",
                        "slug": "servomotor_deposito_mezcla",
                        "tipo": "servomotor",
                        "modelo": "servo_sg90",
                        "protocolo": "MQTT",
                        "actuadores": [
                            {
                                "nombre": "servo_mezcla",
                                "tipo": "float",
                                "unidad_medida": "grados",
                                "rango_min": 0,
                                "rango_max": 180,
                            }
                        ],
                    }
                ],
            },
        ],
        "topic_root": f"iot/{proyecto_slug}",
    }


def _is_gemelo_mix_requested(
    proyecto_nombre: str,
    descripcion: Optional[str],
    configuracion: Dict[str, Any],
    force: bool = False,
) -> bool:
    if force:
        return True

    config = configuracion or {}
    dt_config = config.get("digital_twin", {}) if isinstance(config.get("digital_twin"), dict) else {}
    tipo_proyecto = str(config.get("tipo_proyecto") or config.get("tipo") or "").strip().lower()
    dt_model = str(dt_config.get("model") or dt_config.get("modelo") or "").strip().lower()
    dt_enabled = bool(dt_config.get("enabled", False))

    if tipo_proyecto in {"gemelo_digital", "digital_twin", "dte", "gemelo_mix"}:
        return True
    if dt_enabled and dt_model in {"", "mixing_unit", "gemelo_mix", "mix"}:
        return True

    text = f"{proyecto_nombre} {descripcion or ''}".lower()
    return "gemelo" in text and "mix" in text


def _ensure_gemelo_mix_project_config(
    proyecto_nombre: str,
    configuracion: Dict[str, Any],
) -> Dict[str, Any]:
    config = dict(configuracion or {})

    digital_twin = dict(config.get("digital_twin") or {})
    digital_twin.setdefault("enabled", True)
    digital_twin.setdefault("model", "mixing_unit")
    digital_twin.setdefault("entity_id", "mix_1")
    digital_twin.setdefault("mode", "HYBRID")
    entity_id = str(digital_twin.get("entity_id") or "mix_1")
    digital_twin.setdefault(
        "sync_topics",
        {
            "state": f"twins/{entity_id}/state",
            "command": f"twins/{entity_id}/command",
            "events": f"twins/{entity_id}/events",
        },
    )
    config["digital_twin"] = digital_twin
    config.setdefault("tipo_proyecto", "gemelo_digital")

    provisioning = dict(config.get("provisioning") or {})
    if not provisioning.get("topologia"):
        provisioning["topologia"] = _default_gemelo_mix_topologia_payload(proyecto_nombre)
    config["provisioning"] = provisioning

    dashboard = dict(config.get("dashboard") or {})
    dashboard.setdefault("template", "gemelo_mix")
    dashboard.setdefault("titulo", f"Dashboard Gemelo Mix - {proyecto_nombre}")
    dashboard.setdefault("descripcion", "Monitoreo en tiempo real, control y resultados del gemelo mix")
    config["dashboard"] = dashboard

    return config


def _build_topic_catalog(topologia: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    catalog: Dict[str, List[Dict[str, Any]]] = {"sensores": [], "actuadores": []}

    for unidad in topologia.get("unidades", []):
        unidad_nombre = unidad.get("nombre")
        for placa in unidad.get("placas", []):
            placa_nombre = placa.get("nombre")
            for sensor in placa.get("sensores", []):
                topic = sensor.get("topic")
                if topic:
                    catalog["sensores"].append(
                        {
                            "nombre": sensor.get("nombre"),
                            "topic": topic,
                            "unidad": unidad_nombre,
                            "placa": placa_nombre,
                        }
                    )
            for actuador in placa.get("actuadores", []):
                topic = actuador.get("topic")
                if topic:
                    catalog["actuadores"].append(
                        {
                            "nombre": actuador.get("nombre"),
                            "topic": topic,
                            "unidad": unidad_nombre,
                            "placa": placa_nombre,
                        }
                    )
    return catalog


def _merge_default_dict(target: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(target or {})
    for key, value in defaults.items():
        if key not in merged:
            merged[key] = value
            continue
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _merge_default_dict(merged[key], value)
    return merged


def _default_dashboard_payload(proyecto_nombre: str, topologia: Dict[str, Any]) -> Dict[str, Any]:
    catalog = _build_topic_catalog(topologia)
    topic_index = {
        item["nombre"]: item["topic"]
        for group in ("sensores", "actuadores")
        for item in catalog.get(group, [])
    }

    def topic_of(name: str) -> Optional[str]:
        return topic_index.get(name)

    def topics_of(names: List[str]) -> List[str]:
        return [value for value in (topic_of(name) for name in names) if value]

    monitoreo_topics = topics_of(["nivel_tinta_azul", "nivel_tinta_roja", "nivel_deposito_mezcla"])
    alertas_topics = monitoreo_topics
    control_topics = topics_of(["ev_tinta_azul", "ev_tinta_roja", "servo_mezcla"])
    resultados_topics = topics_of(["nivel_deposito_mezcla", "ev_tinta_azul", "ev_tinta_roja", "servo_mezcla"])

    return {
        "template": "gemelo_mix",
        "titulo": f"Dashboard Gemelo Mix - {proyecto_nombre}",
        "secciones": {
            "monitoreo": monitoreo_topics,
            "alertas": alertas_topics,
            "control": control_topics,
            "resultados": resultados_topics,
        },
        "widgets": [
            {
                "id": "niveles_mezcla",
                "tipo": "line_chart",
                "titulo": "Niveles de tambores y deposito",
                "topics": monitoreo_topics,
            },
            {
                "id": "alertas_operacion",
                "tipo": "status_panel",
                "titulo": "Alertas por nivel",
                "topics": alertas_topics,
            },
            {
                "id": "control_actuadores",
                "tipo": "control_panel",
                "titulo": "Control de electrovalvulas y servomotor",
                "topics": control_topics,
            },
            {
                "id": "resultados_proceso",
                "tipo": "results_panel",
                "titulo": "Resultados de operacion",
                "topics": resultados_topics,
            },
        ],
        "topics": catalog,
    }


def _merge_project_config_with_topology(
    current_config: Dict[str, Any],
    topologia: Dict[str, Any],
    mqtt_broker: Dict[str, Any],
    proyecto_nombre: str,
) -> Dict[str, Any]:
    merged = dict(current_config or {})
    merged["topologia_iot"] = topologia

    publish_topics: List[str] = []
    for unidad in topologia.get("unidades", []):
        for placa in unidad.get("placas", []):
            for sensor in placa.get("sensores", []):
                publish_topics.append(sensor["topic"])
            for actuador in placa.get("actuadores", []):
                publish_topics.append(actuador["topic"])

    merged["publisher"] = {
        "client_id": f"pub-{_slug(topologia.get('topic_root', 'iot'))}",
        "broker_host": mqtt_broker.get("host"),
        "broker_port": mqtt_broker.get("port"),
        "username": mqtt_broker.get("username"),
        "password": mqtt_broker.get("password"),
        "topic_root": topologia.get("topic_root"),
        "publish_topics": publish_topics,
        "qos": 1,
        "retain_default": False,
    }

    default_dashboard = _default_dashboard_payload(proyecto_nombre, topologia)
    merged["dashboard"] = _merge_default_dict(merged.get("dashboard") or {}, default_dashboard)
    merged["topics_catalog"] = _build_topic_catalog(topologia)

    return merged


def _provision_topologia_iot(request: Request, proyecto: Proyecto) -> Dict[str, Any]:
    """Crea unidad/dispositivo/canales por defecto y retorna topología con tópicos."""
    db_handler = request.app.state.db_handler
    project_name = proyecto.nombre or "proyecto"
    proyecto_slug = _slug(project_name)
    topologia = _default_topologia_payload(project_name)

    # Permitir override opcional desde configuracion de alta
    provided_topology = (proyecto.configuracion or {}).get("provisioning", {}).get("topologia")
    if provided_topology:
        topologia = provided_topology
        topologia.setdefault("topic_root", f"iot/{proyecto_slug}")

    mqtt_broker = {}
    try:
        mqtt_broker = request.app.state.config.mqtt.broker
    except Exception:
        mqtt_broker = {"host": "mosquitto", "port": 1883}

    with db_handler.get_session() as session:
        project_id = UUID(str(proyecto.id))
        for unidad in topologia.get("unidades", []):
            unidad_nombre = unidad.get("nombre", "Unidad")
            unidad_slug = unidad.get("slug") or _slug(unidad_nombre)

            unidad_entity = UnidadProyecto(
                proyecto_id=project_id,
                nombre=unidad_nombre,
                descripcion=unidad.get("descripcion"),
                ubicacion=unidad.get("ubicacion"),
                responsable=unidad.get("responsable"),
                configuracion=unidad.get("configuracion") or {},
                activo=True,
            )
            session.add(unidad_entity)
            session.flush()

            for placa in unidad.get("placas", []):
                placa_nombre = placa.get("nombre", "Placa")
                placa_slug = placa.get("slug") or _slug(placa_nombre)
                identificador = placa.get("identificador_unico") or f"{proyecto_slug}-{unidad_slug}-{placa_slug}"

                dispositivo_entity = (
                    session.query(Dispositivo)
                    .filter(Dispositivo.identificador_unico == identificador)
                    .one_or_none()
                )
                if dispositivo_entity is None:
                    dispositivo_entity = Dispositivo(
                        tipo=placa.get("tipo", "placa"),
                        fabricante=placa.get("fabricante"),
                        modelo=placa.get("modelo"),
                        identificador_unico=identificador,
                        protocolo=placa.get("protocolo", ProtocoloComunicacion.MQTT),
                        activo=True,
                    )
                    session.add(dispositivo_entity)
                    session.flush()
                else:
                    dispositivo_entity.tipo = placa.get("tipo", dispositivo_entity.tipo)
                    dispositivo_entity.fabricante = placa.get("fabricante")
                    dispositivo_entity.modelo = placa.get("modelo")
                    dispositivo_entity.protocolo = placa.get("protocolo", dispositivo_entity.protocolo)
                    dispositivo_entity.activo = True
                    session.add(dispositivo_entity)
                    session.flush()

                disp_proj_entity = (
                    session.query(DispositivoProyecto)
                    .filter(
                        DispositivoProyecto.proyecto_id == project_id,
                        DispositivoProyecto.dispositivo_id == dispositivo_entity.id,
                    )
                    .one_or_none()
                )
                if disp_proj_entity is None:
                    disp_proj_entity = DispositivoProyecto(
                        proyecto_id=project_id,
                        unidad_id=unidad_entity.id,
                        dispositivo_id=dispositivo_entity.id,
                        nombre_personalizado=placa_nombre,
                        descripcion=placa.get("descripcion"),
                        estado=EstadoDispositivo.ACTIVO,
                        configuracion=placa.get("configuracion") or {},
                    )
                    session.add(disp_proj_entity)
                else:
                    disp_proj_entity.unidad_id = unidad_entity.id
                    disp_proj_entity.nombre_personalizado = placa_nombre
                    disp_proj_entity.descripcion = placa.get("descripcion")
                    disp_proj_entity.estado = EstadoDispositivo.ACTIVO
                    disp_proj_entity.configuracion = placa.get("configuracion") or {}
                    session.add(disp_proj_entity)

                for group_name, tipo_default in (("sensores", TipoDato.FLOAT), ("actuadores", TipoDato.BOOL)):
                    channel_specs = placa.get(group_name, [])
                    for channel in channel_specs:
                        canal_nombre = channel.get("nombre", f"{group_name[:-1]}_{len(channel_specs)}")
                        canal_slug = channel.get("slug") or _slug(canal_nombre)
                        topic = _topic_path(proyecto_slug, unidad_slug, placa_slug, canal_slug)

                        canal_entity = (
                            session.query(Canal)
                            .filter(
                                Canal.dispositivo_id == dispositivo_entity.id,
                                Canal.nombre == canal_nombre,
                            )
                            .one_or_none()
                        )
                        channel_metadata = {
                            "topic": topic,
                            "categoria": "sensor" if group_name == "sensores" else "actuador",
                        }
                        if canal_entity is None:
                            canal_entity = Canal(
                                dispositivo_id=dispositivo_entity.id,
                                nombre=canal_nombre,
                                etiqueta=channel.get("etiqueta"),
                                descripcion=channel.get("descripcion"),
                                unidad_medida=channel.get("unidad_medida"),
                                tipo=channel.get("tipo", tipo_default),
                                rango_min=channel.get("rango_min"),
                                rango_max=channel.get("rango_max"),
                                umbral_alto=channel.get("umbral_alto"),
                                umbral_bajo=channel.get("umbral_bajo"),
                                metadatos=channel_metadata,
                                configuracion=channel.get("configuracion") or {},
                                activo=True,
                            )
                            session.add(canal_entity)
                        else:
                            canal_entity.etiqueta = channel.get("etiqueta")
                            canal_entity.descripcion = channel.get("descripcion")
                            canal_entity.unidad_medida = channel.get("unidad_medida")
                            canal_entity.tipo = channel.get("tipo", canal_entity.tipo)
                            canal_entity.rango_min = channel.get("rango_min")
                            canal_entity.rango_max = channel.get("rango_max")
                            canal_entity.umbral_alto = channel.get("umbral_alto")
                            canal_entity.umbral_bajo = channel.get("umbral_bajo")
                            canal_entity.metadatos = channel_metadata
                            canal_entity.configuracion = channel.get("configuracion") or {}
                            canal_entity.activo = True
                            session.add(canal_entity)

                        channel["topic"] = topic

        project_entity = session.get(Proyecto, project_id)
        if project_entity is None:
            raise ValueError(f"Proyecto no encontrado para aprovisionar: {project_id}")

        project_entity.configuracion = _merge_project_config_with_topology(
            project_entity.configuracion or {}, topologia, mqtt_broker, project_name
        )
        session.add(project_entity)
        session.commit()
        session.refresh(project_entity)

    return topologia


def get_repositories(request: Request):
    """Obtener repositorios desde el request"""
    db_handler = request.app.state.db_handler
    if not db_handler:
        raise HTTPException(status_code=500, detail="Base de datos no inicializada")
    
    repos = {
        'proyecto': ProyectoRepository(db_handler),
        'cliente': ClienteRepository(db_handler),
    }
    try:
        repos['unidad'] = UnidadProyectoRepository(db_handler)
    except Exception:
        repos['unidad'] = None
    try:
        repos['dispositivo_proyecto'] = DispositivoProyectoRepository(db_handler)
    except Exception:
        repos['dispositivo_proyecto'] = None
    return repos


@router.get("/", response_model=List[ProyectoResponse])
async def list_proyectos(
    request: Request,
    cliente_id: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    activo: Optional[bool] = Query(True)
):
    """Listar proyectos con filtros opcionales"""
    try:
        repos = get_repositories(request)
        proyecto_repo = repos['proyecto']
        
        if cliente_id:
            proyectos = proyecto_repo.get_by_cliente(cliente_id)
        else:
            proyectos = proyecto_repo.get_all()

        if estado:
            normalized_estado = estado.strip().lower()
            if normalized_estado not in ALLOWED_ESTADOS:
                return []
            proyectos = [
                p for p in proyectos
                if (p.estado.value if hasattr(p.estado, 'value') else str(p.estado)) == normalized_estado
            ]
        if activo is not None:
            proyectos = [p for p in proyectos if bool(p.activo) == bool(activo)]
        
        return [
            ProyectoResponse(
                id=str(p.id),
                cliente_id=str(p.cliente_id),
                nombre=p.nombre,
                descripcion=p.descripcion,
                estado=p.estado.value if hasattr(p.estado, 'value') else str(p.estado),
                fecha_inicio=p.fecha_inicio,
                fecha_fin=p.fecha_fin,
                presupuesto=float(p.presupuesto) if p.presupuesto else None,
                prioridad=p.prioridad,
                activo=p.activo,
                creado_en=p.creado_en.isoformat() if p.creado_en else "",
                actualizado_en=p.actualizado_en.isoformat() if p.actualizado_en else ""
            )
            for p in proyectos
        ]
    except Exception as e:
        logger.error(f"Error al listar proyectos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proyecto_id}", response_model=ProyectoResponse)
async def get_proyecto(request: Request, proyecto_id: str):
    """Obtener un proyecto por ID"""
    try:
        repos = get_repositories(request)
        proyecto = repos['proyecto'].get_by_id(proyecto_id)
        
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        return ProyectoResponse(
            id=str(proyecto.id),
            cliente_id=str(proyecto.cliente_id),
            nombre=proyecto.nombre,
            descripcion=proyecto.descripcion,
            estado=proyecto.estado.value if hasattr(proyecto.estado, 'value') else str(proyecto.estado),
            fecha_inicio=proyecto.fecha_inicio,
            fecha_fin=proyecto.fecha_fin,
            presupuesto=float(proyecto.presupuesto) if proyecto.presupuesto else None,
            prioridad=proyecto.prioridad,
            activo=proyecto.activo,
            creado_en=proyecto.creado_en.isoformat() if proyecto.creado_en else "",
            actualizado_en=proyecto.actualizado_en.isoformat() if proyecto.actualizado_en else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener proyecto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ProyectoResponse)
async def create_proyecto(request: Request, proyecto_data: ProyectoCreate):
    """Crear un nuevo proyecto"""
    try:
        repos = get_repositories(request)
        
        # Normalizar cliente_id: aceptar UUID o nombre y crear si no existe
        raw_cliente_id = proyecto_data.cliente_id.strip()
        try:
            cliente_uuid = UUID(raw_cliente_id)
        except Exception:
            cliente_uuid = uuid5(NAMESPACE_DNS, raw_cliente_id)
        
        cliente_id = str(cliente_uuid)
        cliente = repos['cliente'].get_by_id(cliente_id)
        if not cliente:
            cliente = repos['cliente'].create({
                'id': cliente_id,
                'nombre': raw_cliente_id,
                'contacto_principal': {},
                'activo': True
            })
        
        if not cliente:
            raise HTTPException(status_code=500, detail="No se pudo crear el cliente")
        
        # Crear proyecto
        data = proyecto_data.model_dump()
        data['cliente_id'] = cliente_id
        auto_provision = bool(data.pop("auto_provision_topologia", True))
        crear_gemelo_mix = bool(data.pop("crear_gemelo_mix", False))
        normalized_estado = (proyecto_data.estado or "planificado").strip().lower()
        if normalized_estado not in ALLOWED_ESTADOS:
            raise HTTPException(status_code=422, detail="Estado inválido")
        data['estado'] = normalized_estado

        if _is_gemelo_mix_requested(
            proyecto_nombre=proyecto_data.nombre,
            descripcion=proyecto_data.descripcion,
            configuracion=data.get("configuracion") or {},
            force=crear_gemelo_mix,
        ):
            data["configuracion"] = _ensure_gemelo_mix_project_config(
                proyecto_nombre=proyecto_data.nombre,
                configuracion=data.get("configuracion") or {},
            )
        
        proyecto = repos['proyecto'].create(data)
        
        if not proyecto:
            raise HTTPException(status_code=500, detail="Error al crear proyecto")

        if auto_provision:
            try:
                _provision_topologia_iot(request, proyecto)
            except Exception as provision_error:
                logger.error(f"Error aprovisionando topología IoT: {provision_error}")
                repos['proyecto'].delete(str(proyecto.id))
                raise HTTPException(
                    status_code=500,
                    detail="Proyecto creado pero falló el aprovisionamiento automático; se revirtió la creación."
                )
            refreshed = repos['proyecto'].get_by_id(str(proyecto.id))
            if refreshed:
                proyecto = refreshed

        try:
            sync_result = _sync_project_to_core_schema(request, str(proyecto.id), archived=not bool(proyecto.activo))
            logger.info("Sync core schema OK (create): %s", sync_result)
        except Exception as sync_error:
            logger.error("Error sincronizando core schema en alta de proyecto: %s", sync_error)
            raise HTTPException(
                status_code=500,
                detail="Proyecto creado, pero falló la sincronización al core schema (public).",
            )
        
        return ProyectoResponse(
            id=str(proyecto.id),
            cliente_id=str(proyecto.cliente_id),
            nombre=proyecto.nombre,
            descripcion=proyecto.descripcion,
            estado=proyecto.estado.value if hasattr(proyecto.estado, 'value') else str(proyecto.estado),
            fecha_inicio=proyecto.fecha_inicio,
            fecha_fin=proyecto.fecha_fin,
            presupuesto=float(proyecto.presupuesto) if proyecto.presupuesto else None,
            prioridad=proyecto.prioridad,
            activo=proyecto.activo,
            creado_en=proyecto.creado_en.isoformat() if proyecto.creado_en else "",
            actualizado_en=proyecto.actualizado_en.isoformat() if proyecto.actualizado_en else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear proyecto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{proyecto_id}", response_model=ProyectoResponse)
async def update_proyecto(request: Request, proyecto_id: str, proyecto_data: ProyectoUpdate):
    """Actualizar un proyecto"""
    try:
        repos = get_repositories(request)
        
        # Preparar datos de actualización
        data = proyecto_data.model_dump(exclude_unset=True)
        if 'estado' in data and data['estado']:
            normalized_estado = str(data['estado']).strip().lower()
            if normalized_estado not in ALLOWED_ESTADOS:
                raise HTTPException(status_code=422, detail="Estado inválido")
            data['estado'] = normalized_estado
        
        proyecto = repos['proyecto'].update(proyecto_id, data)
        
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        try:
            sync_result = _sync_project_to_core_schema(request, str(proyecto.id), archived=not bool(proyecto.activo))
            logger.info("Sync core schema OK (update): %s", sync_result)
        except Exception as sync_error:
            logger.error("Error sincronizando core schema en actualización de proyecto: %s", sync_error)
            raise HTTPException(
                status_code=500,
                detail="Proyecto actualizado, pero falló la sincronización al core schema (public).",
            )
        
        return ProyectoResponse(
            id=str(proyecto.id),
            cliente_id=str(proyecto.cliente_id),
            nombre=proyecto.nombre,
            descripcion=proyecto.descripcion,
            estado=proyecto.estado.value if hasattr(proyecto.estado, 'value') else str(proyecto.estado),
            fecha_inicio=proyecto.fecha_inicio,
            fecha_fin=proyecto.fecha_fin,
            presupuesto=float(proyecto.presupuesto) if proyecto.presupuesto else None,
            prioridad=proyecto.prioridad,
            activo=proyecto.activo,
            creado_en=proyecto.creado_en.isoformat() if proyecto.creado_en else "",
            actualizado_en=proyecto.actualizado_en.isoformat() if proyecto.actualizado_en else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar proyecto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{proyecto_id}")
async def delete_proyecto(request: Request, proyecto_id: str):
    """Eliminar un proyecto (soft delete)"""
    try:
        repos = get_repositories(request)
        
        proyecto_actual = repos['proyecto'].get_by_id(proyecto_id)
        if not proyecto_actual:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        # Soft delete del proyecto.
        proyecto = repos['proyecto'].update(proyecto_id, {'activo': False})
        
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        unidades_actualizadas = 0
        if repos.get('unidad'):
            unidades = repos['unidad'].get_by_proyecto(proyecto_id)
            for unidad in unidades:
                if not bool(unidad.activo):
                    continue
                updated = repos['unidad'].update(str(unidad.id), {'activo': False})
                if updated:
                    unidades_actualizadas += 1

        dispositivos_actualizados = 0
        if repos.get('dispositivo_proyecto'):
            dispositivos = repos['dispositivo_proyecto'].get_by_proyecto(proyecto_id)
            for dispositivo in dispositivos:
                estado = (
                    str(dispositivo.estado.value).lower()
                    if hasattr(dispositivo.estado, "value")
                    else str(dispositivo.estado).lower()
                )
                if estado == "inactivo":
                    continue
                update_data = {'estado': EstadoDispositivo.INACTIVO}
                if not dispositivo.fecha_retiro:
                    update_data['fecha_retiro'] = date.today()
                updated = repos['dispositivo_proyecto'].update(str(dispositivo.id), update_data)
                if updated:
                    dispositivos_actualizados += 1

        try:
            sync_result = _sync_project_to_core_schema(request, proyecto_id, archived=True)
            logger.info("Sync core schema OK (delete/soft): %s", sync_result)
        except Exception as sync_error:
            logger.error("Error sincronizando core schema en baja lógica de proyecto: %s", sync_error)
            raise HTTPException(
                status_code=500,
                detail="Proyecto desactivado, pero falló la sincronización al core schema (public).",
            )
        
        return {
            "message": "Proyecto eliminado exitosamente",
            "id": proyecto_id,
            "unidades_actualizadas": unidades_actualizadas,
            "dispositivos_actualizados": dispositivos_actualizados,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar proyecto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{proyecto_id}/sync-core")
async def sync_proyecto_core(request: Request, proyecto_id: str):
    """Re-sincronizar manualmente un proyecto legacy hacia core schema (public)."""
    try:
        repos = get_repositories(request)
        proyecto = repos["proyecto"].get_by_id(proyecto_id)
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        payload = _sync_project_to_core_schema(request, proyecto_id, archived=not bool(proyecto.activo))
        return {"ok": True, "result": payload}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en sync core manual: {e}")
        raise HTTPException(status_code=500, detail=str(e))
