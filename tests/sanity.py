"""Sanity test suite for Nyx-OSINT.

This suite provides basic smoke tests to verify core functionality
after installation or major updates. Run with: pytest tests/sanity.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nyx.config.base import load_config
from nyx.core.database import DatabaseManager
from nyx.intelligence.smart import SmartSearchInput, SmartSearchService
from nyx.osint.platforms import get_platform_database
from nyx.osint.search import SearchService


class TestSanitySuite:
    """Basic sanity tests for core functionality."""

    def test_config_loading(self):
        """Test that configuration can be loaded."""
        config = load_config()
        assert config is not None
        assert hasattr(config, "database")
        assert hasattr(config, "http")
        assert hasattr(config, "cache")

    def test_platform_database_loading(self):
        """Test that platform database loads successfully."""
        db = get_platform_database()
        assert db is not None
        assert db.count_platforms() > 0

    def test_search_service_initialization(self):
        """Test that SearchService can be initialized."""
        service = SearchService()
        assert service is not None
        assert service.platform_db is not None
        assert service.max_concurrent_searches > 0

    def test_smart_search_service_initialization(self):
        """Test that SmartSearchService can be initialized."""
        with patch("nyx.intelligence.smart.SearchService"), patch(
            "nyx.intelligence.smart.MetaSearchEngine"
        ):
            service = SmartSearchService()
            assert service is not None

    def test_smart_search_input_creation(self):
        """Test SmartSearchInput dataclass."""
        input_obj = SmartSearchInput(raw_text="test query", region="US")
        assert input_obj.raw_text == "test query"
        assert input_obj.region == "US"

    @pytest.mark.asyncio
    async def test_search_service_cleanup(self):
        """Test that SearchService properly cleans up resources."""
        service = SearchService()
        service.http_client.close = AsyncMock()
        await service.aclose()
        service.http_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_smart_search_service_cleanup(self):
        """Test that SmartSearchService properly cleans up resources."""
        with patch("nyx.intelligence.smart.SearchService") as mock_search, patch(
            "nyx.intelligence.smart.MetaSearchEngine"
        ) as mock_meta:
            mock_search_instance = MagicMock()
            mock_search_instance.aclose = AsyncMock()
            mock_search.return_value = mock_search_instance

            mock_meta_instance = MagicMock()
            mock_meta_instance.close = AsyncMock()
            mock_meta.return_value = mock_meta_instance

            service = SmartSearchService()
            service._owns_search_service = True
            service.search_service = mock_search_instance
            service.meta_search = mock_meta_instance

            await service.aclose()

            mock_search_instance.aclose.assert_called_once()
            mock_meta_instance.close.assert_called_once()

    def test_plugin_registry(self):
        """Test plugin registry functionality."""
        from nyx.osint.plugin import PluginRegistry, register_plugin

        registry = PluginRegistry()
        assert registry is not None
        assert isinstance(registry.list_plugins(), list)

    def test_deep_investigation_service_initialization(self):
        """Test DeepInvestigationService initialization."""
        with patch("nyx.intelligence.deep.SearchService"), patch(
            "nyx.intelligence.deep.SmartSearchService"
        ):
            from nyx.intelligence.deep import DeepInvestigationService

            service = DeepInvestigationService()
            assert service is not None

    @pytest.mark.asyncio
    async def test_database_manager_health_check(self):
        """Test database manager health check."""
        # Use in-memory database for testing
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)
        await db_manager.initialize()
        try:
            health = await db_manager.health_check()
            assert health is True
        finally:
            await db_manager.close()

