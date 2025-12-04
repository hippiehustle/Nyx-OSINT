"""Tests for deep investigation service."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from nyx.intelligence.deep import DeepInvestigationResult, DeepInvestigationService
from nyx.intelligence.smart import SmartSearchInput, SmartSearchResult


class TestDeepInvestigationResult:
    """Test DeepInvestigationResult dataclass."""

    def test_result_creation(self):
        """Test DeepInvestigationResult creation."""
        result = DeepInvestigationResult(
            query="test",
            timestamp=datetime.utcnow(),
            username_results={"Twitter": {"found": True}},
            metadata={"region": "US"},
        )
        assert result.query == "test"
        assert len(result.username_results) == 1
        assert result.metadata["region"] == "US"

    def test_result_defaults(self):
        """Test DeepInvestigationResult with defaults."""
        result = DeepInvestigationResult(
            query="test", timestamp=datetime.utcnow()
        )
        assert result.username_results == {}
        assert result.email_results is None
        assert result.phone_results is None
        assert result.person_results is None
        assert result.smart_results is None
        assert result.web_results == {}


class TestDeepInvestigationService:
    """Test DeepInvestigationService functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        with patch("nyx.intelligence.deep.SearchService"), patch(
            "nyx.intelligence.deep.SmartSearchService"
        ), patch("nyx.intelligence.deep.EmailIntelligence"), patch(
            "nyx.intelligence.deep.PhoneIntelligence"
        ), patch(
            "nyx.intelligence.deep.PersonIntelligence"
        ):
            self.service = DeepInvestigationService()

    def test_initialization_with_services(self):
        """Test initialization with provided services."""
        mock_search = MagicMock()
        mock_smart = MagicMock()

        service = DeepInvestigationService(
            search_service=mock_search, smart_service=mock_smart
        )

        assert service.search_service == mock_search
        assert service.smart_service == mock_smart
        assert service._owns_search_service is False

    def test_initialization_without_services(self):
        """Test initialization without provided services."""
        with patch("nyx.intelligence.deep.SearchService") as mock_search_class, patch(
            "nyx.intelligence.deep.SmartSearchService"
        ) as mock_smart_class:
            service = DeepInvestigationService()
            assert service._owns_search_service is True

    def test_looks_like_phone_valid(self):
        """Test phone detection with valid phone numbers."""
        assert DeepInvestigationService._looks_like_phone("+14155551234")
        assert DeepInvestigationService._looks_like_phone("415-555-1234")
        assert DeepInvestigationService._looks_like_phone("(415) 555-1234")
        assert DeepInvestigationService._looks_like_phone("+442071838750")

    def test_looks_like_phone_invalid(self):
        """Test phone detection with invalid inputs."""
        assert not DeepInvestigationService._looks_like_phone("123")
        assert not DeepInvestigationService._looks_like_phone("test@example.com")
        assert not DeepInvestigationService._looks_like_phone("John Doe")
        assert not DeepInvestigationService._looks_like_phone("123456789")  # Too short

    def test_looks_like_name_valid(self):
        """Test name detection with valid names."""
        assert DeepInvestigationService._looks_like_name("John Doe")
        assert DeepInvestigationService._looks_like_name("Jane M Smith")
        assert DeepInvestigationService._looks_like_name("Robert John Williams")

    def test_looks_like_name_invalid(self):
        """Test name detection with invalid inputs."""
        assert not DeepInvestigationService._looks_like_name("John")
        assert not DeepInvestigationService._looks_like_name("test@example.com")
        assert not DeepInvestigationService._looks_like_name("+14155551234")
        assert not DeepInvestigationService._looks_like_name("john doe")  # Not capitalized

    @pytest.mark.asyncio
    async def test_investigate_username_only(self):
        """Test investigation with username query."""
        self.service.search_service.search_username = AsyncMock(
            return_value={"Twitter": {"found": True, "url": "https://twitter.com/test"}}
        )
        self.service.email_intel.investigate = AsyncMock()
        self.service.phone_intel.investigate = AsyncMock()
        self.service.person_intel.investigate = AsyncMock()
        self.service.smart_service.smart_search = AsyncMock()

        result = await self.service.investigate("testuser", include_smart=False)

        assert isinstance(result, DeepInvestigationResult)
        assert result.query == "testuser"
        assert len(result.username_results) == 1
        self.service.search_service.search_username.assert_called_once()

    @pytest.mark.asyncio
    async def test_investigate_email(self):
        """Test investigation with email query."""
        self.service.search_service.search_username = AsyncMock(return_value={})
        mock_email_result = MagicMock()
        self.service.email_intel.investigate = AsyncMock(return_value=mock_email_result)
        self.service.smart_service.smart_search = AsyncMock()

        result = await self.service.investigate("test@example.com", include_smart=False)

        assert result.email_results == mock_email_result
        self.service.email_intel.investigate.assert_called_once()

    @pytest.mark.asyncio
    async def test_investigate_phone(self):
        """Test investigation with phone query."""
        self.service.search_service.search_username = AsyncMock(return_value={})
        mock_phone_result = MagicMock()
        self.service.phone_intel.investigate = AsyncMock(return_value=mock_phone_result)
        self.service.smart_service.smart_search = AsyncMock()

        result = await self.service.investigate(
            "+14155551234", region="US", include_smart=False
        )

        assert result.phone_results == mock_phone_result
        self.service.phone_intel.investigate.assert_called_once_with(
            "+14155551234", region="US"
        )

    @pytest.mark.asyncio
    async def test_investigate_person_name(self):
        """Test investigation with person name query."""
        self.service.search_service.search_username = AsyncMock(return_value={})
        mock_person_result = MagicMock()
        self.service.person_intel.investigate = AsyncMock(return_value=mock_person_result)
        self.service.smart_service.smart_search = AsyncMock()

        result = await self.service.investigate(
            "John Doe", region="CA", include_smart=False
        )

        assert result.person_results == mock_person_result
        self.service.person_intel.investigate.assert_called_once_with(
            first_name="John", last_name="Doe", middle_name=None, state="CA"
        )

    @pytest.mark.asyncio
    async def test_investigate_with_smart_search(self):
        """Test investigation with Smart search enabled."""
        self.service.search_service.search_username = AsyncMock(return_value={})
        mock_smart_result = MagicMock()
        mock_smart_result.web_results = {"test": []}
        self.service.smart_service.smart_search = AsyncMock(return_value=mock_smart_result)

        result = await self.service.investigate("test", include_smart=True)

        assert result.smart_results == mock_smart_result
        assert result.web_results == mock_smart_result.web_results
        self.service.smart_service.smart_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_investigate_with_web_search_only(self):
        """Test investigation with web search but not Smart search."""
        self.service.search_service.search_username = AsyncMock(return_value={})
        with patch(
            "nyx.intelligence.deep.MetaSearchEngine"
        ) as mock_meta_class:
            mock_meta = AsyncMock()
            mock_meta_class.return_value = mock_meta
            mock_meta.search = AsyncMock(return_value=[{"title": "Test", "url": "http://test.com"}])
            mock_meta.close = AsyncMock()

            result = await self.service.investigate(
                "test", include_smart=False, include_web_search=True
            )

            assert "test" in result.web_results
            mock_meta.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_investigate_error_handling(self):
        """Test investigation error handling."""
        self.service.search_service.search_username = AsyncMock(
            side_effect=Exception("Search error")
        )
        self.service.email_intel.investigate = AsyncMock(side_effect=Exception("Email error"))
        self.service.smart_service.smart_search = AsyncMock()

        result = await self.service.investigate("test", include_smart=False)

        assert isinstance(result, DeepInvestigationResult)
        assert result.username_results == {}
        assert result.email_results is None

    @pytest.mark.asyncio
    async def test_investigate_metadata(self):
        """Test investigation metadata recording."""
        self.service.search_service.search_username = AsyncMock(return_value={})
        self.service.smart_service.smart_search = AsyncMock()

        result = await self.service.investigate(
            "test",
            region="US",
            timeout=60,
            include_smart=False,
            include_web_search=False,
        )

        assert result.metadata["region"] == "US"
        assert result.metadata["timeout"] == 60
        assert result.metadata["include_smart"] is False
        assert result.metadata["include_web_search"] is False
        assert "duration_seconds" in result.metadata

    @pytest.mark.asyncio
    async def test_investigate_filters_found_results(self):
        """Test that investigation filters only found username results."""
        self.service.search_service.search_username = AsyncMock(
            return_value={
                "Twitter": {"found": True, "url": "https://twitter.com/test"},
                "GitHub": {"found": False},
                "Facebook": {"found": True, "url": "https://facebook.com/test"},
            }
        )
        self.service.smart_service.smart_search = AsyncMock()

        result = await self.service.investigate("test", include_smart=False)

        assert len(result.username_results) == 2
        assert "Twitter" in result.username_results
        assert "Facebook" in result.username_results
        assert "GitHub" not in result.username_results

    @pytest.mark.asyncio
    async def test_investigate_person_name_with_middle(self):
        """Test investigation with person name including middle name."""
        self.service.search_service.search_username = AsyncMock(return_value={})
        mock_person_result = MagicMock()
        self.service.person_intel.investigate = AsyncMock(return_value=mock_person_result)
        self.service.smart_service.smart_search = AsyncMock()

        result = await self.service.investigate(
            "John M Doe", region="CA", include_smart=False
        )

        self.service.person_intel.investigate.assert_called_once_with(
            first_name="John", last_name="Doe", middle_name="M", state="CA"
        )

    @pytest.mark.asyncio
    async def test_aclose_with_owned_service(self):
        """Test resource cleanup when service owns SearchService."""
        self.service._owns_search_service = True
        self.service.search_service.aclose = AsyncMock()
        self.service.smart_service.aclose = AsyncMock()

        await self.service.aclose()

        self.service.search_service.aclose.assert_called_once()
        self.service.smart_service.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_aclose_without_owned_service(self):
        """Test resource cleanup when service doesn't own SearchService."""
        self.service._owns_search_service = False
        self.service.search_service.aclose = AsyncMock()
        self.service.smart_service.aclose = AsyncMock()

        await self.service.aclose()

        self.service.search_service.aclose.assert_not_called()
        self.service.smart_service.aclose.assert_called_once()

