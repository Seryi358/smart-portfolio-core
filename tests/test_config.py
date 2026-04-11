"""tests/test_config.py — Tests para src/config.py (Sesión 5.2)."""
import os
import pytest

from config import Settings, AppSettings


class TestSettings:
    def test_load_con_key_valida(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_KEY", "test_key_123")
        monkeypatch.setenv("ENVIRONMENT", "dev")
        s = Settings.load()
        assert s.alpha_vantage_key == "test_key_123"
        assert s.environment == "dev"

    def test_load_entorno_prod(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_KEY", "key_prod")
        monkeypatch.setenv("ENVIRONMENT", "prod")
        s = Settings.load()
        assert s.environment == "prod"

    def test_load_entorno_test(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_KEY", "key_test")
        monkeypatch.setenv("ENVIRONMENT", "test")
        s = Settings.load()
        assert s.environment == "test"

    def test_load_sin_key_lanza_error(self, monkeypatch):
        monkeypatch.delenv("ALPHA_VANTAGE_KEY", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "dev")
        with pytest.raises(RuntimeError, match="ALPHA_VANTAGE_KEY"):
            Settings.load()

    def test_entorno_invalido_lanza_error(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_KEY", "somekey")
        monkeypatch.setenv("ENVIRONMENT", "staging")
        with pytest.raises(ValueError, match="ENVIRONMENT"):
            Settings.load()

    def test_masked_key(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_KEY", "ABCD1234")
        monkeypatch.setenv("ENVIRONMENT", "dev")
        s = Settings.load()
        assert s.masked_key == "ABCD****"
        assert "1234" not in s.masked_key

    def test_info_contiene_environment(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_KEY", "XYZKEY")
        monkeypatch.setenv("ENVIRONMENT", "dev")
        s = Settings.load()
        assert "dev" in s.info()

    def test_es_inmutable(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_KEY", "key")
        monkeypatch.setenv("ENVIRONMENT", "dev")
        s = Settings.load()
        with pytest.raises(Exception):
            s.environment = "prod"  # type: ignore[misc]


class TestAppSettings:
    def test_crea_con_defaults(self, monkeypatch):
        monkeypatch.delenv("ALPHA_VANTAGE_KEY", raising=False)
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        cfg = AppSettings()
        assert cfg.environment == "dev"
        assert cfg.alpha_vantage_key == "demo_key"

    def test_lee_variable_de_entorno(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_KEY", "env_key")
        monkeypatch.setenv("ENVIRONMENT", "prod")
        cfg = AppSettings()
        assert cfg.alpha_vantage_key == "env_key"
        assert cfg.environment == "prod"

    def test_masked_key(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_KEY", "ABCD9999")
        cfg = AppSettings()
        assert cfg.masked_key.startswith("ABCD")
        assert "9999" not in cfg.masked_key

    def test_info_retorna_string(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_KEY", "demo_key")
        cfg = AppSettings()
        assert isinstance(cfg.info(), str)
