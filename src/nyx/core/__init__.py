"""Core infrastructure modules for Nyx."""

from nyx.core.logger import get_logger, setup_logging
from nyx.core.database import (
    ensure_database_initialized,
    get_database_manager,
    get_database_manager_async,
    initialize_database,
)
from nyx.core.http_client import HTTPClient, RateLimiter
from nyx.core.cache import initialize_cache, get_cache, MultiLevelCache
from nyx.core.events import get_event_bus, start_event_bus, Event

# Try to import update modules (may not be available in all builds)
try:
    from nyx.core.version import (
        Version,
        compare_versions,
        get_current_version,
        get_version_info,
        is_update_available,
        parse_version,
    )
    from nyx.core.updater import (
        UpdateChecker,
        UpdateDownloader,
        UpdateInstaller,
        UpdateScheduler,
    )
    from nyx.core.update_client import CustomUpdateClient, GitHubReleasesClient
    from nyx.core.update_service import UpdateService
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
        # Logger
        "get_logger",
        "setup_logging",
        # Database
        "initialize_database",
        "ensure_database_initialized",
        "get_database_manager",
        "get_database_manager_async",
        # HTTP
        "HTTPClient",
        "RateLimiter",
        # Cache
        "initialize_cache",
        "get_cache",
        "MultiLevelCache",
        # Events
        "get_event_bus",
        "start_event_bus",
        "Event",
        # Version
        "Version",
        "get_current_version",
        "get_version_info",
        "parse_version",
        "compare_versions",
        "is_update_available",
        # Updater
        "UpdateChecker",
        "UpdateDownloader",
        "UpdateInstaller",
        "UpdateScheduler",
        "UpdateService",
        # Update Clients
        "GitHubReleasesClient",
        "CustomUpdateClient",
        # Resource Paths
        "get_base_path",
        "get_data_path",
        "get_config_path",
        "get_resource_path",
        "get_user_data_path",
        "get_cache_path",
        "get_log_path",
        "get_database_path",
    ]
except ImportError:
    __all__ = [
        # Logger
        "get_logger",
        "setup_logging",
        # Database
        "initialize_database",
        "ensure_database_initialized",
        "get_database_manager",
        "get_database_manager_async",
        # HTTP
        "HTTPClient",
        "RateLimiter",
        # Cache
        "initialize_cache",
        "get_cache",
        "MultiLevelCache",
        # Events
        "get_event_bus",
        "start_event_bus",
        "Event",
    ]
