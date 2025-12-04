"""Tests for plugin system."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from nyx.core.types import PlatformMatch
from nyx.models.platform import Platform, PlatformCategory
from nyx.osint.plugin import (
    PlatformCheckerPlugin,
    PluginRegistry,
    get_plugin_registry,
    register_plugin,
)


class TestPlugin(PlatformCheckerPlugin):
    """Test plugin implementation."""

    def __init__(self):
        """Initialize test plugin."""
        self.name = "TestPlugin"
        self.version = "1.0.0"

    async def check(self, username: str, platform: Platform) -> PlatformMatch | None:
        """Check username on platform."""
        if username == "testuser" and platform.name == "TestPlatform":
            return {"found": True, "url": f"https://test.com/{username}"}
        return None

    def get_name(self) -> str:
        """Get plugin name."""
        return self.name

    def get_version(self) -> str:
        """Get plugin version."""
        return self.version

    def supports_platform(self, platform: Platform) -> bool:
        """Check if plugin supports platform."""
        return platform.name == "TestPlatform"


class TestPlatformCheckerPlugin:
    """Test PlatformCheckerPlugin interface."""

    def test_plugin_interface(self):
        """Test that plugin implements required methods."""
        plugin = TestPlugin()
        assert plugin.get_name() == "TestPlugin"
        assert plugin.get_version() == "1.0.0"
        assert plugin.supports_platform is not None

    def test_supports_platform_default(self):
        """Test default supports_platform implementation."""
        plugin = TestPlugin()
        platform = Platform(
            name="AnyPlatform",
            url="https://example.com",
            category=PlatformCategory.SOCIAL_MEDIA,
        )
        # TestPlugin overrides supports_platform, so this will return False
        assert plugin.supports_platform(platform) is False

    @pytest.mark.asyncio
    async def test_plugin_check(self):
        """Test plugin check method."""
        plugin = TestPlugin()
        platform = Platform(
            name="TestPlatform",
            url="https://test.com",
            category=PlatformCategory.SOCIAL_MEDIA,
        )

        result = await plugin.check("testuser", platform)
        assert result is not None
        assert result["found"] is True

    @pytest.mark.asyncio
    async def test_plugin_check_not_found(self):
        """Test plugin check when user not found."""
        plugin = TestPlugin()
        platform = Platform(
            name="TestPlatform",
            url="https://test.com",
            category=PlatformCategory.SOCIAL_MEDIA,
        )

        result = await plugin.check("otheruser", platform)
        assert result is None


class TestPluginRegistry:
    """Test PluginRegistry functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.registry = PluginRegistry()

    def test_registry_initialization(self):
        """Test registry initialization."""
        assert self.registry._plugins == {}
        assert self.registry._instances == {}

    def test_register_plugin(self):
        """Test plugin registration."""
        self.registry.register(TestPlugin)
        assert "TestPlugin" in self.registry._plugins
        assert self.registry._plugins["TestPlugin"] == TestPlugin

    def test_register_plugin_custom_name(self):
        """Test plugin registration with custom name."""
        self.registry.register(TestPlugin, name="CustomName")
        assert "CustomName" in self.registry._plugins
        assert "TestPlugin" not in self.registry._plugins

    def test_get_plugin(self):
        """Test getting plugin instance."""
        self.registry.register(TestPlugin)
        plugin = self.registry.get_plugin("TestPlugin")
        assert plugin is not None
        assert isinstance(plugin, TestPlugin)

    def test_get_plugin_not_found(self):
        """Test getting non-existent plugin."""
        plugin = self.registry.get_plugin("NonExistent")
        assert plugin is None

    def test_get_plugin_caches_instance(self):
        """Test that plugin instances are cached."""
        self.registry.register(TestPlugin)
        plugin1 = self.registry.get_plugin("TestPlugin")
        plugin2 = self.registry.get_plugin("TestPlugin")
        assert plugin1 is plugin2  # Same instance

    def test_list_plugins(self):
        """Test listing registered plugins."""
        assert self.registry.list_plugins() == []

        self.registry.register(TestPlugin)
        plugins = self.registry.list_plugins()
        assert "TestPlugin" in plugins
        assert len(plugins) == 1

    def test_find_plugin_for_platform(self):
        """Test finding plugin for platform."""
        self.registry.register(TestPlugin)
        platform = Platform(
            name="TestPlatform",
            url="https://test.com",
            category=PlatformCategory.SOCIAL_MEDIA,
        )

        plugin = self.registry.find_plugin_for_platform(platform)
        assert plugin is not None
        assert isinstance(plugin, TestPlugin)

    def test_find_plugin_for_platform_not_supported(self):
        """Test finding plugin when platform not supported."""
        self.registry.register(TestPlugin)
        platform = Platform(
            name="OtherPlatform",
            url="https://other.com",
            category=PlatformCategory.SOCIAL_MEDIA,
        )

        plugin = self.registry.find_plugin_for_platform(platform)
        assert plugin is None

    def test_find_plugin_for_platform_no_plugins(self):
        """Test finding plugin when no plugins registered."""
        platform = Platform(
            name="TestPlatform",
            url="https://test.com",
            category=PlatformCategory.SOCIAL_MEDIA,
        )

        plugin = self.registry.find_plugin_for_platform(platform)
        assert plugin is None


class TestGlobalPluginRegistry:
    """Test global plugin registry functions."""

    def test_get_plugin_registry_singleton(self):
        """Test that get_plugin_registry returns singleton."""
        registry1 = get_plugin_registry()
        registry2 = get_plugin_registry()
        assert registry1 is registry2

    def test_register_plugin_convenience(self):
        """Test register_plugin convenience function."""
        # Clear registry first
        registry = get_plugin_registry()
        registry._plugins.clear()
        registry._instances.clear()

        register_plugin(TestPlugin)
        assert "TestPlugin" in registry._plugins

    def test_register_plugin_custom_name(self):
        """Test register_plugin with custom name."""
        registry = get_plugin_registry()
        registry._plugins.clear()
        registry._instances.clear()

        register_plugin(TestPlugin, name="CustomPlugin")
        assert "CustomPlugin" in registry._plugins

