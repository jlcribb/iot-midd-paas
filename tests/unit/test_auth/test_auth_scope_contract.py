from uuid import uuid4

from iot_middleware.api.auth.auth_middleware import AuthMiddleware
from iot_middleware.api.auth.jwt_handler import JWTHandler
from iot_middleware.models.entities import Usuario, UsuarioScope
from iot_middleware.models.enums import RolSistema


def build_user_with_scope():
    usuario = Usuario(
        id=uuid4(),
        email="user@example.com",
        nombre="Usuario Test",
        password_hash="hashed",
        rol=RolSistema.CLIENTE,
        activo=True,
    )
    scope = UsuarioScope(
        id=uuid4(),
        usuario_id=usuario.id,
        cliente_id=uuid4(),
        proyecto_id=uuid4(),
        activo=True,
    )
    usuario.usuarios_scope = [scope]
    return usuario, scope


def test_usuario_properties_are_derived_from_active_scope():
    usuario, scope = build_user_with_scope()

    assert usuario.active_scope is scope
    assert usuario.cliente_id == scope.cliente_id
    assert usuario.proyecto_id == scope.proyecto_id
    assert usuario.unidad_id is None


def test_usuario_ultimo_acceso_aliases_ultimo_login():
    usuario, _ = build_user_with_scope()

    usuario.ultimo_acceso = "2025-01-01T00:00:00"

    assert usuario.ultimo_login == "2025-01-01T00:00:00"
    assert usuario.ultimo_acceso == "2025-01-01T00:00:00"


def test_jwt_tokens_include_scope_ids_from_usuario_scope():
    usuario, scope = build_user_with_scope()
    handler = JWTHandler(secret_key="test-secret")

    tokens = handler.create_user_tokens(usuario)
    payload = handler.verify_token(tokens["access_token"])

    assert payload is not None
    assert payload["sub"] == str(usuario.id)
    assert payload["cliente_id"] == str(scope.cliente_id)
    assert payload["proyecto_id"] == str(scope.proyecto_id)
    assert payload["unidad_id"] is None


def test_auth_response_uses_normalized_role_and_scope_properties():
    usuario, scope = build_user_with_scope()
    auth = AuthMiddleware(JWTHandler(secret_key="test-secret"), db_handler=None)

    response = auth.create_auth_response(usuario)
    user_data = response["data"]["user"]

    assert user_data["rol"] == "cliente"
    assert user_data["cliente_id"] == str(scope.cliente_id)
    assert user_data["proyecto_id"] == str(scope.proyecto_id)
