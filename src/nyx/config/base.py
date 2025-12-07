"""Base configuration management using Pydantic V2."""

import json
import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, ConfigDict


class DatabaseConfig(BaseModel):
    """Database configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    url: str = Field(default="sqlite:///./nyx.db", description="Database URL")
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=40, description="Maximum overflow connections")
    echo: bool = Field(default=False, description="Echo SQL statements")
    
    def get_resolved_url(self) -> str:
        """Get database URL with resolved path for executables.
        
        Returns:
            Resolved database URL
        """
        if self.url.startswith("sqlite:///"):
            # Try to use resource paths if available
            try:
                from nyx.core.resource_paths import get_database_path
                db_path = get_database_path()
                # Convert to absolute path for SQLite
                return f"sqlite:///{db_path.absolute()}"
            except ImportError:
                # Fall back to original URL
                pass
        return self.url


class HTTPConfig(BaseModel):
    """HTTP client configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    timeout: int = Field(default=10, description="Request timeout in seconds")
    retries: int = Field(default=3, description="Number of retries on failure")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Nyx/0.1.0",
        description="User-Agent header",
    )
    max_concurrent_requests: int = Field(default=100, description="Max concurrent HTTP requests")


class CacheConfig(BaseModel):
    """Cache configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    enabled: bool = Field(default=True, description="Enable caching")
    ttl: int = Field(default=3600, description="Cache TTL in seconds")
    max_size: int = Field(default=1000, description="Max cache entries")
    backend: str = Field(default="memory", description="Cache backend: memory or redis")


class GUIConfig(BaseModel):
    """GUI configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    theme: str = Field(default="dark", description="GUI theme")
    window_width: int = Field(default=1400, description="Default window width")
    window_height: int = Field(default=900, description="Default window height")
    font_size: int = Field(default=10, description="Base font size")


class SecurityConfig(BaseModel):
    """Security configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    enable_encryption: bool = Field(default=True, description="Enable encryption")
    require_master_password: bool = Field(default=True, description="Require master password")
    password_hash_iterations: int = Field(default=100000, description="PBKDF2 iterations")
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format",
    )
    file_path: str = Field(default="logs/nyx.log", description="Log file path")
    max_file_size: int = Field(default=10485760, description="Max log file size in bytes")
    backup_count: int = Field(default=5, description="Number of backup log files")


class ProxyConfig(BaseModel):
    """Proxy configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    enabled: bool = Field(default=False, description="Enable proxy")
    http_proxy: Optional[str] = Field(default=None, description="HTTP proxy URL")
    https_proxy: Optional[str] = Field(default=None, description="HTTPS proxy URL")
    socks_proxy: Optional[str] = Field(default=None, description="SOCKS proxy URL")


class TorConfig(BaseModel):
    """Tor configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    enabled: bool = Field(default=False, description="Enable Tor")
    socks_host: str = Field(default="127.0.0.1", description="Tor SOCKS host")
    socks_port: int = Field(default=9050, description="Tor SOCKS port")
    control_host: str = Field(default="127.0.0.1", description="Tor control host")
    control_port: int = Field(default=9051, description="Tor control port")
    use_new_identity: bool = Field(default=False, description="Request new identity per request")


class Config(BaseModel):
    """Main application configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    debug: bool = Field(default=False, description="Debug mode")
    data_dir: str = Field(default="./data", description="Data directory")
    config_dir: str = Field(default="./config", description="Configuration directory")

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    http: HTTPConfig = Field(default_factory=HTTPConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    gui: GUIConfig = Field(default_factory=GUIConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    tor: TorConfig = Field(default_factory=TorConfig)
    
    # Updater config (optional, with defaults)
    updater: Optional["UpdaterConfig"] = Field(default=None, description="Update configuration")
    
    def __init__(self, **data):
        """Initialize config with optional updater."""
        # Import here to avoid circular dependency
        try:
            from nyx.config.updater_config import UpdaterConfig
        except ImportError:
            # UpdaterConfig not available (e.g., in some builds)
            UpdaterConfig = None
        
        # Set default updater if not provided
        if "updater" not in data and UpdaterConfig:
            data["updater"] = UpdaterConfig()
        
        super().__init__(**data)

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    @classmethod
    def from_json(cls, path: str) -> "Config":
        """Load configuration from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            debug=os.getenv("NYX_DEBUG", "false").lower() == "true",
            data_dir=os.getenv("NYX_DATA_DIR", "./data"),
            config_dir=os.getenv("NYX_CONFIG_DIR", "./config"),
        )

    def to_yaml(self, path: str) -> None:
        """Save configuration to YAML file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)

    def to_json(self, path: str) -> None:
        """Save configuration to JSON file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.model_dump(), f, indent=2)


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from various sources with fallback."""
    if config_path and os.path.exists(config_path):
        if config_path.endswith(".yaml") or config_path.endswith(".yml"):
            return Config.from_yaml(config_path)
        elif config_path.endswith(".json"):
            return Config.from_json(config_path)

    # Try to use resource path utilities if available (executable mode)
    try:
        from nyx.core.resource_paths import get_config_path, get_resource_path
        
        # Try bundled config first
        bundled_config = get_resource_path("config/settings.yaml")
        if bundled_config.exists():
            return Config.from_yaml(str(bundled_config))
        
        # Try config directory
        config_dir = get_config_path()
        default_yaml = config_dir / "settings.yaml"
        default_json = config_dir / "settings.json"
        
        if default_yaml.exists():
            return Config.from_yaml(str(default_yaml))
        elif default_json.exists():
            return Config.from_json(str(default_json))
    except ImportError:
        # Development mode: use relative paths
        default_yaml = Path("config/settings.yaml")
        default_json = Path("config/settings.json")

        if default_yaml.exists():
            return Config.from_yaml(str(default_yaml))
        elif default_json.exists():
            return Config.from_json(str(default_json))

    # Fall back to environment variables or defaults
    return Config.from_env()
