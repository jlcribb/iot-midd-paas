from uuid import uuid4

from iot_middleware.api.auth.role_checker import RoleChecker
from iot_middleware.api.auth.scope_handler import ScopeHandler
from iot_middleware.models.entities import Usuario, UsuarioScope
from iot_middleware.models.enums import RolSistema


def build_user(role=RolSistema.CLIENTE, with_scope=True):
    usuario = Usuario(
        id=uuid4(),
        email="user@example.com",
        nombre="Usuario Test",
        password_hash="hashed",
        rol=role,
        activo=True,
    )
    if with_scope:
        usuario.usuarios_scope = [
            UsuarioScope(
                id=uuid4(),
                usuario_id=usuario.id,
                cliente_id=uuid4(),
                proyecto_id=uuid4(),
                activo=True,
            )
        ]
    else:
        usuario.usuarios_scope = []
    return usuario


def test_scope_handler_exposes_filters_for_scoped_user():
    usuario = build_user(role=RolSistema.CLIENTE)
    handler = ScopeHandler()

    filters = handler.get_user_scope_filters(usuario)

    assert filters["cliente_id"] == str(usuario.cliente_id)
    assert filters["proyecto_id"] == str(usuario.proyecto_id)


def test_scope_handler_allows_unrestricted_roles():
    usuario = build_user(role=RolSistema.ADMIN, with_scope=False)
    handler = ScopeHandler()

    assert handler.get_user_scope_filters(usuario) == {}
    assert handler.validate_resource_access(usuario, {"cliente_id": "x", "proyecto_id": "y"}) is True


def test_scope_handler_denies_mismatched_project_access():
    usuario = build_user(role=RolSistema.CLIENTE)
    handler = ScopeHandler()

    assert handler.validate_resource_access(
        usuario,
        {"proyecto_id": str(uuid4())},
    ) is False


def test_role_checker_project_management_uses_project_scope_for_client():
    usuario = build_user(role=RolSistema.CLIENTE)
    checker = RoleChecker(auth_middleware=None)

    assert checker.check_permission(usuario, "project_management", str(usuario.proyecto_id)) is True
    assert checker.check_permission(usuario, "project_management", str(uuid4())) is False


def test_role_checker_operator_permissions():
    usuario = build_user(role=RolSistema.TECNICO, with_scope=False)
    checker = RoleChecker(auth_middleware=None)

    assert checker.check_permission(usuario, "event_management", "whatever") is True
    assert checker.check_permission(usuario, "system_config") is True
