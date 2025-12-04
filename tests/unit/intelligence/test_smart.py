"""Tests for Smart search functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nyx.intelligence.smart import (
    SmartCandidateProfile,
    SmartSearchInput,
    SmartSearchResult,
    SmartSearchService,
)


@pytest.fixture
def smart_service():
    """Create SmartSearchService instance for testing."""
    with patch("nyx.intelligence.smart.SearchService"), patch(
        "nyx.intelligence.smart.MetaSearchEngine"
    ):
        service = SmartSearchService()
        service.search_service = AsyncMock()
        service.meta_search = AsyncMock()
        service.profile_builder = MagicMock()
        service.email_intel = MagicMock()
        service.phone_intel = MagicMock()
        service.person_intel = MagicMock()
        return service


class TestSmartSearchInput:
    """Test SmartSearchInput dataclass."""

    def test_basic_input(self):
        """Test basic input creation."""
        input_obj = SmartSearchInput(raw_text="test query")
        assert input_obj.raw_text == "test query"
        assert input_obj.region is None
        assert input_obj.usernames == []
        assert input_obj.emails == []
        assert input_obj.phones == []
        assert input_obj.names == []

    def test_input_with_hints(self):
        """Test input with explicit hints."""
        input_obj = SmartSearchInput(
            raw_text="test",
            region="US",
            usernames=["user1"],
            emails=["test@example.com"],
            phones=["+1234567890"],
            names=["John Doe"],
        )
        assert input_obj.region == "US"
        assert input_obj.usernames == ["user1"]
        assert input_obj.emails == ["test@example.com"]
        assert input_obj.phones == ["+1234567890"]
        assert input_obj.names == ["John Doe"]


class TestSmartSearchService:
    """Test SmartSearchService."""

    def test_extract_identifiers_email(self, smart_service):
        """Test email extraction."""
        input_obj = SmartSearchInput(raw_text="Contact me at john@example.com")
        identifiers = smart_service._extract_identifiers(input_obj)
        assert "john@example.com" in identifiers["emails"]

    def test_extract_identifiers_phone(self, smart_service):
        """Test phone extraction."""
        input_obj = SmartSearchInput(raw_text="Call me at 415-555-1234")
        identifiers = smart_service._extract_identifiers(input_obj)
        assert len(identifiers["phones"]) > 0

    def test_extract_identifiers_username(self, smart_service):
        """Test username extraction."""
        input_obj = SmartSearchInput(raw_text="Follow me @johndoe")
        identifiers = smart_service._extract_identifiers(input_obj)
        assert "johndoe" in identifiers["usernames"]

    def test_extract_identifiers_name(self, smart_service):
        """Test name extraction."""
        input_obj = SmartSearchInput(raw_text="My name is John Doe")
        identifiers = smart_service._extract_identifiers(input_obj)
        assert len(identifiers["names"]) > 0

    def test_build_candidates_username(self, smart_service):
        """Test candidate building from username profiles."""
        identifiers = {"usernames": ["testuser"], "emails": [], "phones": [], "names": []}
        username_profiles = {
            "testuser": {
                "username": "testuser",
                "found_on_platforms": 5,
                "platforms": {"Twitter": {}, "GitHub": {}},
            }
        }
        candidates = smart_service._build_candidates(
            smart_input=SmartSearchInput(raw_text="test"),
            identifiers=identifiers,
            username_profiles=username_profiles,
            email_results={},
            phone_results={},
            person_results={},
        )
        assert len(candidates) > 0
        assert candidates[0].identifier == "testuser"
        assert candidates[0].identifier_type == "username"

    def test_build_candidates_email(self, smart_service):
        """Test candidate building from email results."""
        identifiers = {"usernames": [], "emails": ["test@example.com"], "phones": [], "names": []}
        email_result = MagicMock()
        email_result.valid = True
        email_result.breached = False
        email_result.reputation_score = 80.0
        email_result.online_profiles = {"Twitter": "https://twitter.com/test"}
        email_result.disposable = False
        email_result.__dict__ = {
            "valid": True,
            "breached": False,
            "reputation_score": 80.0,
            "online_profiles": {"Twitter": "https://twitter.com/test"},
            "disposable": False,
        }
        candidates = smart_service._build_candidates(
            smart_input=SmartSearchInput(raw_text="test"),
            identifiers=identifiers,
            username_profiles={},
            email_results={"test@example.com": email_result},
            phone_results={},
            person_results={},
        )
        assert len(candidates) > 0
        assert any(c.identifier == "test@example.com" for c in candidates)

    def test_determine_target_name(self, smart_service):
        """Test target name determination."""
        result = SmartSearchResult(
            input=SmartSearchInput(raw_text="test"),
            identifiers={"usernames": ["user1"], "emails": [], "phones": [], "names": []},
            username_profiles={},
            email_results={},
            phone_results={},
            person_results={},
            web_results={},
            candidates=[
                SmartCandidateProfile(
                    identifier="user1",
                    identifier_type="username",
                    data={},
                    confidence=0.8,
                    reason="test",
                )
            ],
        )
        name = smart_service._determine_target_name(result)
        assert name == "user1"

    def test_infer_category(self, smart_service):
        """Test category inference."""
        result = SmartSearchResult(
            input=SmartSearchInput(raw_text="test"),
            identifiers={"usernames": [], "emails": [], "phones": [], "names": ["John Doe"]},
            username_profiles={},
            email_results={},
            phone_results={},
            person_results={},
            web_results={},
            candidates=[],
        )
        category = smart_service._infer_category(result)
        assert category == "person"

    @pytest.mark.asyncio
    async def test_smart_search_basic(self, smart_service):
        """Test basic smart search execution."""
        # Mock all intelligence modules
        smart_service.profile_builder.build_profile = AsyncMock(
            return_value={"username": "test", "found_on_platforms": 0, "platforms": {}}
        )
        smart_service.email_intel.investigate = AsyncMock(return_value=MagicMock())
        smart_service.phone_intel.investigate = AsyncMock(return_value=MagicMock())
        smart_service.person_intel.investigate = AsyncMock(return_value=MagicMock())
        smart_service.meta_search.search = AsyncMock(return_value=[])

        input_obj = SmartSearchInput(raw_text="test user @testuser")
        result = await smart_service.smart_search(input_obj, timeout=5, persist_to_db=False)

        assert isinstance(result, SmartSearchResult)
        assert result.input == input_obj
        assert "testuser" in result.identifiers["usernames"]

    @pytest.mark.asyncio
    async def test_aclose(self, smart_service):
        """Test resource cleanup."""
        smart_service._owns_search_service = True
        smart_service.search_service.aclose = AsyncMock()
        smart_service.meta_search.close = AsyncMock()

        await smart_service.aclose()

        smart_service.search_service.aclose.assert_called_once()
        smart_service.meta_search.close.assert_called_once()

