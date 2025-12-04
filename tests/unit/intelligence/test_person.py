"""Tests for person intelligence module."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from nyx.intelligence.person import PersonIntelligence, PersonResult


class TestPersonResult:
    """Test PersonResult dataclass."""

    def test_person_result_creation(self):
        """Test PersonResult creation with all fields."""
        result = PersonResult(
            first_name="John",
            middle_name="M",
            last_name="Doe",
            state="CA",
            age=30,
            age_range="30-35",
            addresses=["123 Main St, Los Angeles, CA"],
            phone_numbers=["+14155551234"],
            email_addresses=["john@example.com"],
            relatives=["Jane Doe"],
            associates=["Bob Smith"],
            social_profiles={"Twitter": "https://twitter.com/johndoe"},
            education=["University of California"],
            employment=["Software Engineer at Tech Corp"],
            metadata={"full_name": "John M Doe"},
            checked_at=datetime.now(),
        )
        assert result.first_name == "John"
        assert result.middle_name == "M"
        assert result.last_name == "Doe"
        assert result.state == "CA"
        assert len(result.addresses) == 1
        assert len(result.social_profiles) == 1

    def test_person_result_minimal(self):
        """Test PersonResult creation with minimal fields."""
        result = PersonResult(
            first_name="Jane",
            middle_name=None,
            last_name="Smith",
            state=None,
            age=None,
            age_range=None,
            addresses=[],
            phone_numbers=[],
            email_addresses=[],
            relatives=[],
            associates=[],
            social_profiles={},
            education=[],
            employment=[],
            metadata={},
            checked_at=datetime.now(),
        )
        assert result.first_name == "Jane"
        assert result.middle_name is None
        assert result.addresses == []


class TestPersonIntelligence:
    """Test PersonIntelligence functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        with patch("nyx.intelligence.person.HTTPClient"), patch(
            "nyx.intelligence.person.get_cache"
        ):
            self.person_intel = PersonIntelligence()
            self.person_intel.cache = AsyncMock()

    def test_format_name_with_middle(self):
        """Test name formatting with middle name."""
        result = self.person_intel.format_name("John", "M", "Doe")
        assert result == "John M Doe"

    def test_format_name_without_middle(self):
        """Test name formatting without middle name."""
        result = self.person_intel.format_name("John", None, "Doe")
        assert result == "John Doe"

    @pytest.mark.asyncio
    async def test_search_public_records_cached(self):
        """Test public records search with cache hit."""
        cached_data = {
            "addresses": ["123 Main St"],
            "phone_numbers": ["+14155551234"],
            "age": 30,
            "age_range": "30-35",
        }
        self.person_intel.cache.get = AsyncMock(return_value=cached_data)

        result = await self.person_intel.search_public_records(
            "John", None, "Doe", "CA"
        )

        assert result == cached_data
        self.person_intel.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_public_records_no_cache(self):
        """Test public records search without cache."""
        self.person_intel.cache.get = AsyncMock(return_value=None)
        self.person_intel.cache.set = AsyncMock()

        result = await self.person_intel.search_public_records(
            "John", None, "Doe", "CA"
        )

        assert result["addresses"] == []
        assert result["phone_numbers"] == []
        assert result["age"] is None
        self.person_intel.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_public_records_error(self):
        """Test public records search error handling."""
        self.person_intel.cache.get = AsyncMock(side_effect=Exception("Cache error"))

        result = await self.person_intel.search_public_records(
            "John", None, "Doe", "CA"
        )

        assert result["addresses"] == []
        assert result["phone_numbers"] == []

    @pytest.mark.asyncio
    async def test_search_social_media(self):
        """Test social media search."""
        with patch("nyx.intelligence.person.SearchService") as mock_search_class:
            mock_service = AsyncMock()
            mock_search_class.return_value = mock_service
            mock_service.search_username = AsyncMock(
                return_value={
                    "Twitter": {"found": True, "url": "https://twitter.com/johndoe"},
                    "GitHub": {"found": True, "url": "https://github.com/johndoe"},
                }
            )
            mock_service.aclose = AsyncMock()

            result = await self.person_intel.search_social_media(
                "John", None, "Doe", "CA"
            )

            assert "Twitter" in result
            assert result["Twitter"] == "https://twitter.com/johndoe"
            mock_service.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_social_media_no_results(self):
        """Test social media search with no results."""
        with patch("nyx.intelligence.person.SearchService") as mock_search_class:
            mock_service = AsyncMock()
            mock_search_class.return_value = mock_service
            mock_service.search_username = AsyncMock(return_value={})
            mock_service.aclose = AsyncMock()

            result = await self.person_intel.search_social_media(
                "John", None, "Doe", "CA"
            )

            assert result == {}
            mock_service.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_social_media_error(self):
        """Test social media search error handling."""
        with patch("nyx.intelligence.person.SearchService") as mock_search_class:
            mock_service = AsyncMock()
            mock_search_class.return_value = mock_service
            mock_service.search_username = AsyncMock(side_effect=Exception("Error"))
            mock_service.aclose = AsyncMock()

            result = await self.person_intel.search_social_media(
                "John", None, "Doe", "CA"
            )

            assert result == {}
            mock_service.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_professional_networks(self):
        """Test professional network search."""
        result = await self.person_intel.search_professional_networks(
            "John", None, "Doe"
        )

        assert isinstance(result, list)
        assert result == []

    @pytest.mark.asyncio
    async def test_search_relatives_associates(self):
        """Test relatives and associates search."""
        relatives, associates = await self.person_intel.search_relatives_associates(
            "John", "Doe", ["123 Main St"]
        )

        assert isinstance(relatives, list)
        assert isinstance(associates, list)
        assert relatives == []
        assert associates == []

    @pytest.mark.asyncio
    async def test_investigate_complete(self):
        """Test complete investigation."""
        with patch.object(
            self.person_intel, "search_public_records", new_callable=AsyncMock
        ) as mock_public, patch.object(
            self.person_intel, "search_social_media", new_callable=AsyncMock
        ) as mock_social, patch.object(
            self.person_intel, "search_professional_networks", new_callable=AsyncMock
        ) as mock_professional, patch.object(
            self.person_intel, "search_relatives_associates", new_callable=AsyncMock
        ) as mock_relatives:

            mock_public.return_value = {
                "addresses": ["123 Main St"],
                "phone_numbers": ["+14155551234"],
                "age": 30,
                "age_range": "30-35",
            }
            mock_social.return_value = {"Twitter": "https://twitter.com/johndoe"}
            mock_professional.return_value = ["Software Engineer"]
            mock_relatives.return_value = (["Jane Doe"], ["Bob Smith"])

            result = await self.person_intel.investigate(
                "John", "Doe", middle_name=None, state="CA"
            )

            assert isinstance(result, PersonResult)
            assert result.first_name == "John"
            assert result.last_name == "Doe"
            assert len(result.addresses) == 1
            assert len(result.social_profiles) == 1
            assert len(result.relatives) == 1
            assert len(result.associates) == 1
            assert result.metadata["full_name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_investigate_with_middle_name(self):
        """Test investigation with middle name."""
        with patch.object(
            self.person_intel, "search_public_records", new_callable=AsyncMock
        ) as mock_public, patch.object(
            self.person_intel, "search_social_media", new_callable=AsyncMock
        ) as mock_social, patch.object(
            self.person_intel, "search_professional_networks", new_callable=AsyncMock
        ) as mock_professional, patch.object(
            self.person_intel, "search_relatives_associates", new_callable=AsyncMock
        ):

            mock_public.return_value = {
                "addresses": [],
                "phone_numbers": [],
                "age": None,
                "age_range": None,
            }
            mock_social.return_value = {}
            mock_professional.return_value = []
            mock_relatives = AsyncMock(return_value=([], []))

            result = await self.person_intel.investigate(
                "John", "Doe", middle_name="M", state="CA"
            )

            assert result.middle_name == "M"
            assert result.metadata["full_name"] == "John M Doe"

    @pytest.mark.asyncio
    async def test_investigate_error_handling(self):
        """Test investigation error handling."""
        with patch.object(
            self.person_intel, "search_public_records", new_callable=AsyncMock
        ) as mock_public, patch.object(
            self.person_intel, "search_social_media", new_callable=AsyncMock
        ) as mock_social, patch.object(
            self.person_intel, "search_professional_networks", new_callable=AsyncMock
        ) as mock_professional:

            mock_public.side_effect = Exception("Public records error")
            mock_social.side_effect = Exception("Social media error")
            mock_professional.side_effect = Exception("Professional error")

            result = await self.person_intel.investigate("John", "Doe")

            assert isinstance(result, PersonResult)
            assert result.addresses == []
            assert result.social_profiles == {}
            assert result.employment == []

    @pytest.mark.asyncio
    async def test_investigate_with_addresses_triggers_relatives_search(self):
        """Test that investigation triggers relatives search when addresses found."""
        with patch.object(
            self.person_intel, "search_public_records", new_callable=AsyncMock
        ) as mock_public, patch.object(
            self.person_intel, "search_social_media", new_callable=AsyncMock
        ) as mock_social, patch.object(
            self.person_intel, "search_professional_networks", new_callable=AsyncMock
        ) as mock_professional, patch.object(
            self.person_intel, "search_relatives_associates", new_callable=AsyncMock
        ) as mock_relatives:

            mock_public.return_value = {
                "addresses": ["123 Main St"],
                "phone_numbers": [],
                "age": None,
                "age_range": None,
            }
            mock_social.return_value = {}
            mock_professional.return_value = []
            mock_relatives.return_value = (["Jane Doe"], [])

            result = await self.person_intel.investigate("John", "Doe")

            mock_relatives.assert_called_once_with("John", "Doe", ["123 Main St"])
            assert len(result.relatives) == 1

    @pytest.mark.asyncio
    async def test_investigate_no_addresses_skips_relatives_search(self):
        """Test that investigation skips relatives search when no addresses."""
        with patch.object(
            self.person_intel, "search_public_records", new_callable=AsyncMock
        ) as mock_public, patch.object(
            self.person_intel, "search_social_media", new_callable=AsyncMock
        ) as mock_social, patch.object(
            self.person_intel, "search_professional_networks", new_callable=AsyncMock
        ) as mock_professional, patch.object(
            self.person_intel, "search_relatives_associates", new_callable=AsyncMock
        ) as mock_relatives:

            mock_public.return_value = {
                "addresses": [],
                "phone_numbers": [],
                "age": None,
                "age_range": None,
            }
            mock_social.return_value = {}
            mock_professional.return_value = []

            result = await self.person_intel.investigate("John", "Doe")

            mock_relatives.assert_not_called()
            assert result.relatives == []
            assert result.associates == []

