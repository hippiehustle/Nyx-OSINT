"""Plugin system for extending Nyx with custom platform checkers."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from nyx.core.types import PlatformMatch
from nyx.models.platform import Platform


class PlatformCheckerPlugin(ABC):
    """Plugin interface for custom platform checkers.
    
    This allows users to create custom checker implementations that extend
    Nyx's platform detection capabilities beyond the built-in checkers.
    """

    @abstractmethod
    async def check(self, username: str, platform: Platform) -> Optional[PlatformMatch]:
        """Check if username exists on platform.

        Args:
            username: Username to check
            platform: Platform configuration

        Returns:
            PlatformMatch if found, None otherwise
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get plugin name."""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Get plugin version."""
        pass

    def supports_platform(self, platform: Platform) -> bool:
        """Check if this plugin supports the given platform.

        Override this method to filter which platforms the plugin handles.

        Args:
            platform: Platform to check

        Returns:
            True if plugin supports this platform
        """
        return True


class PluginRegistry:
    """Registry for platform checker plugins."""

    def __init__(self):
        """Initialize plugin registry."""
        self._plugins: Dict[str, Type[PlatformCheckerPlugin]] = {}
        self._instances: Dict[str, PlatformCheckerPlugin] = {}

    def register(
        self,
        plugin_class: Type[PlatformCheckerPlugin],
        name: Optional[str] = None,
    ) -> None:
        """Register a plugin class.

        Args:
            plugin_class: Plugin class to register
            name: Optional custom name (defaults to class name)
        """
        plugin_name = name or plugin_class.__name__
        self._plugins[plugin_name] = plugin_class

    def get_plugin(self, name: str) -> Optional[PlatformCheckerPlugin]:
        """Get plugin instance by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        if name not in self._instances:
            if name in self._plugins:
                self._instances[name] = self._plugins[name]()
        return self._instances.get(name)

    def list_plugins(self) -> list[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())

    def find_plugin_for_platform(self, platform: Platform) -> Optional[PlatformCheckerPlugin]:
        """Find a plugin that supports the given platform.

        Args:
            platform: Platform to find plugin for

        Returns:
            Plugin instance or None if no plugin supports this platform
        """
        for name in self._plugins:
            plugin = self.get_plugin(name)
            if plugin and plugin.supports_platform(platform):
                return plugin
        return None


# Global plugin registry
_plugin_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """Get global plugin registry."""
    global _plugin_registry
    if _plugin_registry is None:
        _plugin_registry = PluginRegistry()
    return _plugin_registry


def register_plugin(
    plugin_class: Type[PlatformCheckerPlugin],
    name: Optional[str] = None,
) -> None:
    """Register a plugin (convenience function).

    Args:
        plugin_class: Plugin class to register
        name: Optional custom name
    """
    get_plugin_registry().register(plugin_class, name=name)

