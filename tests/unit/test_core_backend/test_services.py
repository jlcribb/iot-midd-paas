from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from iot_middleware.core_backend.errors import ConflictError
from iot_middleware.core_backend.schemas import CreateAssetPayload
from iot_middleware.core_backend.services import AssetService, ProjectService, SectorService, TopologyService


class _FakeDbHandler:
    @contextmanager
    def get_session(self):
        yield MagicMock()


def test_creacion_valida_de_nodo():
    db = _FakeDbHandler()
    project_repo = MagicMock()
    sector_repo = MagicMock()
    location_repo = MagicMock()
    asset_repo = MagicMock()
    topology_repo = MagicMock()

    project_repo.get_by_id.return_value = {"id": "p1"}
    sector_repo.get_by_id.return_value = {"id": "s1", "project_id": "p1"}
    asset_repo.create.return_value = {"id": "a1", "asset_type": "programmable_node", "project_id": "p1", "sector_id": "s1"}

    service = AssetService(
        db,
        project_repo=project_repo,
        sector_repo=sector_repo,
        location_repo=location_repo,
        asset_repo=asset_repo,
        topology_repo=topology_repo,
    )

    created = service.create(
        {
            "project_id": "p1",
            "sector_id": "s1",
            "asset_type": "programmable_node",
            "subtype": "esp32",
            "name": "Nodo principal",
            "metadata": {},
        }
    )
    assert created["id"] == "a1"
    asset_repo.create.assert_called_once()


def test_rechaza_sensor_con_padre_de_otro_proyecto():
    db = _FakeDbHandler()
    project_repo = MagicMock()
    sector_repo = MagicMock()
    location_repo = MagicMock()
    asset_repo = MagicMock()

    project_repo.get_by_id.return_value = {"id": "p1"}
    sector_repo.get_by_id.return_value = {"id": "s1", "project_id": "p1"}
    asset_repo.get_by_id.return_value = {
        "id": "parent-1",
        "project_id": "p2",
        "sector_id": "s2",
        "asset_type": "programmable_node",
    }

    service = AssetService(
        db,
        project_repo=project_repo,
        sector_repo=sector_repo,
        location_repo=location_repo,
        asset_repo=asset_repo,
    )

    with pytest.raises(ConflictError):
        service.create(
            {
                "project_id": "p1",
                "sector_id": "s1",
                "parent_asset_id": "parent-1",
                "asset_type": "sensor",
                "subtype": "ultrasonic",
                "name": "Sensor nivel",
                "metadata": {},
            }
        )


def test_rechaza_topology_link_entre_proyectos_distintos():
    db = _FakeDbHandler()
    project_repo = MagicMock()
    sector_repo = MagicMock()
    asset_repo = MagicMock()
    topology_repo = MagicMock()

    project_repo.get_by_id.return_value = {"id": "p1"}

    def _asset_lookup(session, asset_id):
        if asset_id == "a-source":
            return {"id": asset_id, "project_id": "p1"}
        return {"id": asset_id, "project_id": "p2"}

    asset_repo.get_by_id.side_effect = _asset_lookup
    topology_repo.exists_same_relation.return_value = False

    service = TopologyService(
        db,
        project_repo=project_repo,
        sector_repo=sector_repo,
        asset_repo=asset_repo,
        topology_repo=topology_repo,
    )

    with pytest.raises(ConflictError):
        service.create(
            {
                "project_id": "p1",
                "source_asset_id": "a-source",
                "target_asset_id": "a-target",
                "relation_type": "reads",
                "ports": [],
                "metadata": {},
            }
        )


def test_obtiene_hijos_de_nodo():
    db = _FakeDbHandler()
    asset_repo = MagicMock()
    asset_repo.get_by_id.return_value = {"id": "n1"}
    asset_repo.list_children.return_value = [{"id": "s1"}, {"id": "a1"}]

    service = AssetService(db, asset_repo=asset_repo)
    children = service.list_children("n1")
    assert len(children) == 2
    asset_repo.list_children.assert_called_once()


def test_obtiene_topologia_de_proyecto():
    db = _FakeDbHandler()
    project_repo = MagicMock()
    topology_repo = MagicMock()
    project_repo.get_by_id.return_value = {"id": "p1"}
    topology_repo.get_project_topology.return_value = [{"id": "l1", "relation_type": "contains"}]

    service = TopologyService(db, project_repo=project_repo, topology_repo=topology_repo)
    topology = service.get_project_topology("p1")
    assert topology[0]["id"] == "l1"


def test_consulta_offline_assets():
    db = _FakeDbHandler()
    project_repo = MagicMock()
    asset_repo = MagicMock()
    project_repo.get_by_id.return_value = {"id": "p1"}
    asset_repo.get_offline_assets.return_value = [{"id": "a-off", "status": "offline"}]

    service = AssetService(db, project_repo=project_repo, asset_repo=asset_repo)
    offline_assets = service.get_offline_assets("p1", offline_minutes=15)
    assert offline_assets[0]["id"] == "a-off"
    asset_repo.get_offline_assets.assert_called_once()


def test_conflicto_por_duplicado_razonable_en_sector():
    db = _FakeDbHandler()
    project_repo = MagicMock()
    location_repo = MagicMock()
    sector_repo = MagicMock()
    asset_repo = MagicMock()
    topology_repo = MagicMock()

    project_repo.get_by_id.return_value = {"id": "p1"}
    sector_repo.exists_name.return_value = True
    sector_repo.exists_code.return_value = False

    service = SectorService(
        db,
        project_repo=project_repo,
        location_repo=location_repo,
        sector_repo=sector_repo,
        asset_repo=asset_repo,
        topology_repo=topology_repo,
    )

    with pytest.raises(ConflictError):
        service.create(
            {
                "project_id": "p1",
                "name": "Tanque Norte",
                "metadata": {},
            }
        )


def test_validacion_payload_invalido_asset_type():
    with pytest.raises(ValidationError):
        CreateAssetPayload(
            project_id="p1",
            sector_id="s1",
            asset_type="invalid_type",
            subtype="any",
            name="invalid",
            metadata={},
        )


def test_soft_delete_sector_inactiva_links_de_assets_del_sector():
    db = _FakeDbHandler()
    project_repo = MagicMock()
    location_repo = MagicMock()
    sector_repo = MagicMock()
    asset_repo = MagicMock()
    topology_repo = MagicMock()

    sector_repo.get_by_id.return_value = {"id": "s1", "project_id": "p1"}
    sector_repo.set_active.return_value = {"id": "s1", "is_active": False}
    asset_repo.list_by_sector.return_value = [{"id": "a1"}, {"id": "a2"}]
    topology_repo.list_by_project.return_value = [
        {"id": "l1", "source_asset_id": "a1", "target_asset_id": "x"},
        {"id": "l2", "source_asset_id": "x", "target_asset_id": "a2"},
        {"id": "l3", "source_sector_id": "s1", "target_asset_id": "z"},
    ]
    sector_repo.get_by_id.side_effect = [
        {"id": "s1", "project_id": "p1"},
        {"id": "s1", "project_id": "p1", "is_active": False},
    ]

    service = SectorService(
        db,
        project_repo=project_repo,
        location_repo=location_repo,
        sector_repo=sector_repo,
        asset_repo=asset_repo,
        topology_repo=topology_repo,
    )
    service.soft_delete("s1")
    assert topology_repo.update.call_count == 3


def test_archivar_proyecto_desactiva_scope_completo():
    db = _FakeDbHandler()
    project_repo = MagicMock()
    project_repo.get_by_id.return_value = {"id": "p1", "status": "active"}
    project_repo.update.return_value = {"id": "p1", "status": "archived"}

    # Monkeypatch class constructors used internally in ProjectService.update
    from iot_middleware.core_backend import services as services_module

    sector_repo = MagicMock()
    asset_repo = MagicMock()
    topology_repo = MagicMock()

    sector_repo.list_by_project.return_value = [{"id": "s1"}, {"id": "s2"}]
    asset_repo.list_by_project.return_value = [{"id": "a1"}, {"id": "a2"}]
    topology_repo.list_by_project.return_value = [{"id": "l1"}, {"id": "l2"}]

    original_sector_repo = services_module.SectorRepository
    original_asset_repo = services_module.AssetRepository
    original_topology_repo = services_module.TopologyLinkRepository

    services_module.SectorRepository = lambda: sector_repo
    services_module.AssetRepository = lambda: asset_repo
    services_module.TopologyLinkRepository = lambda: topology_repo
    try:
        service = ProjectService(db, project_repo=project_repo)
        updated = service.update("p1", {"status": "archived"})
        assert updated["status"] == "archived"
    finally:
        services_module.SectorRepository = original_sector_repo
        services_module.AssetRepository = original_asset_repo
        services_module.TopologyLinkRepository = original_topology_repo

    assert sector_repo.set_active.call_count == 2
    assert asset_repo.set_status.call_count == 2
    assert topology_repo.update.call_count == 2
