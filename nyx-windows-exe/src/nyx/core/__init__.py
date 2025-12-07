"""Core modules for Nyx executable."""

# Import resource paths for easy access
from nyx.core.resource_paths import (
    get_base_path,
    get_cache_path,
    get_config_path,
    get_data_path,
    get_database_path,
    get_log_path,
    get_resource_path,
    get_user_data_path,
)

__all__ = [
    "get_base_path",
    "get_data_path",
    "get_config_path",
    "get_resource_path",
    "get_user_data_path",
    "get_cache_path",
    "get_log_path",
    "get_database_path",
]

