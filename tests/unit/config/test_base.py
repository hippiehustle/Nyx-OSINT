"""Tests for configuration management."""

from pathlib import Path

import pytest

from nyx.config.base import Config, load_config


class TestConfig:
    """Test Config class."""

    def test_default_config_creation(self) -> None:
        """Test creating default config."""
        config = Config()
        assert config.debug is False
        assert config.database.pool_size == 20
        assert config.http.timeout == 10

    def test_config_from_yaml(self, config_file: Path) -> None:
        """Test loading config from YAML."""
        config = Config.from_yaml(str(config_file))
        assert config.debug is True
        assert config.http.retries == 1

    def test_config_to_yaml(self, tmp_dir: Path) -> None:
        """Test saving config to YAML."""
        config = Config(debug=True)
        output_path = tmp_dir / "output.yaml"
        config.to_yaml(str(output_path))
        assert output_path.exists()
        loaded = Config.from_yaml(str(output_path))
        assert loaded.debug is True

    def test_config_from_env(self, monkeypatch) -> None:
        """Test loading config from environment variables."""
        monkeypatch.setenv("NYX_DEBUG", "true")
        monkeypatch.setenv("NYX_DATA_DIR", "/custom/data")
        config = Config.from_env()
        assert config.debug is True
        assert config.data_dir == "/custom/data"

    def test_load_config_default(self) -> None:
        """Test loading config with default fallback."""
        config = load_config()
        assert isinstance(config, Config)
        assert config.database.pool_size == 20


class TestDatabaseConfig:
    """Test database configuration."""

    def test_database_config_defaults(self) -> None:
        """Test database config defaults."""
        config = Config()
        assert config.database.url == "sqlite:///./nyx.db"
        assert config.database.pool_size == 20

    def test_database_config_custom(self) -> None:
        """Test custom database config."""
        from nyx.config.base import DatabaseConfig

        db_config = DatabaseConfig(
            url="postgresql://user:pass@localhost/nyx",
            pool_size=50,
        )
        assert db_config.url == "postgresql://user:pass@localhost/nyx"
        assert db_config.pool_size == 50


class TestCacheConfig:
    """Test cache configuration."""

    def test_cache_config_defaults(self) -> None:
        """Test cache config defaults."""
        config = Config()
        assert config.cache.enabled is True
        assert config.cache.ttl == 3600
        assert config.cache.backend == "memory"

    def test_cache_disabled(self) -> None:
        """Test disabling cache."""
        from nyx.config.base import CacheConfig

        cache = CacheConfig(enabled=False)
        assert cache.enabled is False


class TestSecurityConfig:
    """Test security configuration."""

    def test_security_config_defaults(self) -> None:
        """Test security config defaults."""
        config = Config()
        assert config.security.enable_encryption is True
        assert config.security.require_master_password is True
        assert config.security.password_hash_iterations == 100000
