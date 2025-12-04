"""Integration tests for search pipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nyx.intelligence.deep import DeepInvestigationService
from nyx.intelligence.smart import SmartSearchInput, SmartSearchService
from nyx.osint.search import SearchService


class TestSearchPipelineIntegration:
    """Test end-to-end search pipeline."""

    @pytest.mark.asyncio
    async def test_username_search_pipeline(self):
        """Test end-to-end username search."""
        with patch("nyx.osint.search.get_platform_database") as mock_db, patch(
            "nyx.osint.search.get_cache"
        ), patch("nyx.osint.search.get_event_bus"), patch(
            "nyx.osint.search.load_config"
        ), patch("nyx.osint.search.HTTPClient"):

            mock_platform_db = MagicMock()
            mock_platform_db.platforms = {
                "twitter": MagicMock(
                    name="Twitter",
                    is_active=True,
                    is_nsfw=False,
                    search_url="https://twitter.com/{username}",
                    detection_method="status_code",
                )
            }
            mock_db.return_value = mock_platform_db

            service = SearchService()
            service.platform_db = mock_platform_db
            service.cache = AsyncMock()
            service.cache.get = AsyncMock(return_value=None)
            service.cache.set = AsyncMock()
            service.event_bus = AsyncMock()

            with patch.object(service, "_check_platform", new_callable=AsyncMock) as mock_check:
                mock_check.return_value = {
                    "found": True,
                    "url": "https://twitter.com/testuser",
                }

                results = await service.search_username("testuser", timeout=5)

                assert isinstance(results, dict)
                mock_check.assert_called()

            await service.aclose()

    @pytest.mark.asyncio
    async def test_email_investigation_pipeline(self):
        """Test end-to-end email investigation."""
        with patch("nyx.intelligence.email.SearchService") as mock_search_class, patch(
            "nyx.intelligence.email.HTTPClient"
        ), patch("nyx.intelligence.email.get_cache"):

            from nyx.intelligence.email import EmailIntelligence

            email_intel = EmailIntelligence()
            email_intel.http_client = MagicMock()
            email_intel.cache = AsyncMock()
            email_intel.cache.get = AsyncMock(return_value=None)
            email_intel.cache.set = AsyncMock()

            # Mock validation methods
            email_intel.validate_email = MagicMock(return_value=True)
            email_intel.is_disposable = MagicMock(return_value=False)
            email_intel.get_provider = MagicMock(return_value="Gmail")
            email_intel.check_breach = AsyncMock(return_value={"breached": False, "count": 0})
            email_intel.check_email_services = AsyncMock(return_value=[])

            result = await email_intel.investigate("test@example.com", search_profiles=False)

            assert result is not None
            assert result.valid is True

    @pytest.mark.asyncio
    async def test_phone_investigation_pipeline(self):
        """Test end-to-end phone investigation."""
        with patch("nyx.intelligence.phone.HTTPClient"), patch(
            "nyx.intelligence.phone.get_cache"
        ):

            from nyx.intelligence.phone import PhoneIntelligence

            phone_intel = PhoneIntelligence()
            phone_intel.http_client = MagicMock()
            phone_intel.cache = AsyncMock()
            phone_intel.cache.get = AsyncMock(return_value=None)
            phone_intel.cache.set = AsyncMock()

            # Mock phone parsing
            phone_intel.parse_number = MagicMock(return_value=MagicMock())
            phone_intel.get_country_code = MagicMock(return_value="US")
            phone_intel.get_carrier = AsyncMock(return_value="AT&T")
            phone_intel.get_line_type = MagicMock(return_value="mobile")

            result = await phone_intel.investigate("+14155551234", region="US")

            assert result is not None
            assert result.valid is True

    @pytest.mark.asyncio
    async def test_smart_search_pipeline(self):
        """Test Smart search end-to-end pipeline."""
        with patch("nyx.intelligence.smart.SearchService") as mock_search_class, patch(
            "nyx.intelligence.smart.MetaSearchEngine"
        ) as mock_meta_class, patch("nyx.intelligence.smart.EmailIntelligence"), patch(
            "nyx.intelligence.smart.PhoneIntelligence"
        ), patch("nyx.intelligence.smart.PersonIntelligence"):

            mock_search = AsyncMock()
            mock_search_class.return_value = mock_search
            mock_search.search_username = AsyncMock(return_value={})
            mock_search.aclose = AsyncMock()

            mock_meta = AsyncMock()
            mock_meta_class.return_value = mock_meta
            mock_meta.search = AsyncMock(return_value=[])
            mock_meta.close = AsyncMock()

            service = SmartSearchService()
            service.search_service = mock_search
            service.meta_search = mock_meta
            service.profile_builder = MagicMock()
            service.email_intel = MagicMock()
            service.phone_intel = MagicMock()
            service.person_intel = MagicMock()

            input_obj = SmartSearchInput(raw_text="test user @testuser")
            result = await service.smart_search(input_obj, timeout=5, persist_to_db=False)

            assert result is not None
            assert result.input == input_obj

            await service.aclose()

    @pytest.mark.asyncio
    async def test_deep_investigation_pipeline(self):
        """Test deep investigation end-to-end pipeline."""
        with patch("nyx.intelligence.deep.SearchService") as mock_search_class, patch(
            "nyx.intelligence.deep.SmartSearchService"
        ) as mock_smart_class, patch("nyx.intelligence.deep.EmailIntelligence"), patch(
            "nyx.intelligence.deep.PhoneIntelligence"
        ), patch("nyx.intelligence.deep.PersonIntelligence"):

            mock_search = AsyncMock()
            mock_search_class.return_value = mock_search
            mock_search.search_username = AsyncMock(return_value={})
            mock_search.aclose = AsyncMock()

            mock_smart = AsyncMock()
            mock_smart_class.return_value = mock_smart
            mock_smart.smart_search = AsyncMock(return_value=MagicMock(web_results={}))
            mock_smart.aclose = AsyncMock()

            service = DeepInvestigationService()
            service.search_service = mock_search
            service.smart_service = mock_smart
            service.email_intel = MagicMock()
            service.phone_intel = MagicMock()
            service.person_intel = MagicMock()

            result = await service.investigate("testuser", include_smart=False)

            assert result is not None
            assert result.query == "testuser"

            await service.aclose()

