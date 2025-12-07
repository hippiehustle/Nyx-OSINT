"""Configuration management for Nyx OSINT platform."""

from nyx.config.base import Config, load_config
from nyx.config.encryption import EncryptionManager

# Try to import updater config (may not be available in all builds)
try:
    from nyx.config.updater_config import UpdaterConfig
    __all__ = [
        "Config",
        "load_config",
        "EncryptionManager",
        "UpdaterConfig",
    ]
except ImportError:
    __all__ = [
        "Config",
        "load_config",
        "EncryptionManager",
    ]
