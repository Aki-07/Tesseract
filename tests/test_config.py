import importlib
import sys

from config.config import Settings


def import_fresh(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_settings_defaults_without_env(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_env == "dev"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000


def test_settings_instance_uses_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9000")

    module = import_fresh("config.config")

    assert module.settings.app_env == "prod"
    assert module.settings.host == "127.0.0.1"
    assert module.settings.port == 9000

    # Reload once more to clear the cached settings object using default env.
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    import_fresh("config.config")
