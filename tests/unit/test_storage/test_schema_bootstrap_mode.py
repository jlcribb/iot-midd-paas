from iot_middleware.storage.db_handler import DEFAULT_SCHEMA_BOOTSTRAP_MODE, get_schema_bootstrap_mode


def test_schema_bootstrap_mode_defaults_to_alembic(monkeypatch):
    monkeypatch.delenv("IOT_MW_SCHEMA_BOOTSTRAP_MODE", raising=False)
    assert get_schema_bootstrap_mode() == DEFAULT_SCHEMA_BOOTSTRAP_MODE


def test_schema_bootstrap_mode_accepts_legacy(monkeypatch):
    monkeypatch.setenv("IOT_MW_SCHEMA_BOOTSTRAP_MODE", "legacy")
    assert get_schema_bootstrap_mode() == "legacy"


def test_schema_bootstrap_mode_falls_back_on_invalid_value(monkeypatch):
    monkeypatch.setenv("IOT_MW_SCHEMA_BOOTSTRAP_MODE", "invalid-mode")
    assert get_schema_bootstrap_mode() == DEFAULT_SCHEMA_BOOTSTRAP_MODE
