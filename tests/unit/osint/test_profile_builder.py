"""Tests for profile builder."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from nyx.models.target import Target
from nyx.osint.profile_builder import ProfileBuilder


class TestProfileBuilder:
    """Test ProfileBuilder functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.search_service = MagicMock()
        self.builder = ProfileBuilder(self.search_service)

    @pytest.mark.asyncio
    async def test_build_profile(self):
        """Test profile building."""
        search_results = {
            "Twitter": {"found": True, "url": "https://twitter.com/testuser"},
            "GitHub": {"found": True, "url": "https://github.com/testuser"},
        }
        self.search_service.search_username = AsyncMock(return_value=search_results)

        profile = await self.builder.build_profile("testuser")

        assert profile["username"] == "testuser"
        assert profile["found_on_platforms"] == 2
        assert len(profile["platforms"]) == 2
        assert "Twitter" in profile["platform_details"]
        assert "GitHub" in profile["platform_details"]

    @pytest.mark.asyncio
    async def test_build_profile_no_results(self):
        """Test profile building with no results."""
        self.search_service.search_username = AsyncMock(return_value={})

        profile = await self.builder.build_profile("testuser")

        assert profile["username"] == "testuser"
        assert profile["found_on_platforms"] == 0
        assert len(profile["platforms"]) == 0

    @pytest.mark.asyncio
    async def test_build_profile_exclude_nsfw(self):
        """Test profile building excluding NSFW."""
        search_results = {"Twitter": {"found": True, "url": "https://twitter.com/testuser"}}
        self.search_service.search_username = AsyncMock(return_value=search_results)

        profile = await self.builder.build_profile("testuser", exclude_nsfw=True)

        self.search_service.search_username.assert_called_once_with(
            "testuser", exclude_nsfw=True, timeout=None
        )

    @pytest.mark.asyncio
    async def test_build_target_profile(self):
        """Test target profile building."""
        target = Target(name="testuser", category="person")
        target.id = 1
        target.profiles = []

        search_results = {
            "Twitter": {"found": True, "url": "https://twitter.com/testuser", "username": "testuser"}
        }
        self.search_service.search_username = AsyncMock(return_value=search_results)

        await self.builder.build_target_profile(target)

        assert len(target.profiles) == 1
        assert target.profiles[0].platform == "Twitter"

    @pytest.mark.asyncio
    async def test_build_target_profile_multiple_usernames(self):
        """Test target profile building with multiple usernames."""
        target = Target(name="testuser", category="person")
        target.id = 1
        target.profiles = []

        search_results1 = {
            "Twitter": {"found": True, "url": "https://twitter.com/testuser", "username": "testuser"}
        }
        search_results2 = {
            "GitHub": {"found": True, "url": "https://github.com/user2", "username": "user2"}
        }
        self.search_service.search_username = AsyncMock(
            side_effect=[search_results1, search_results2]
        )

        await self.builder.build_target_profile(target, usernames=["testuser", "user2"])

        assert len(target.profiles) == 2

    def test_correlate_profiles(self):
        """Test profile correlation."""
        profiles = {
            "user1": {
                "username": "user1",
                "platforms": {"Twitter": {}, "GitHub": {}, "Facebook": {}},
            },
            "user2": {
                "username": "user2",
                "platforms": {"Twitter": {}, "GitHub": {}, "LinkedIn": {}},
            },
            "user3": {
                "username": "user3",
                "platforms": {"Instagram": {}, "TikTok": {}},
            },
        }

        correlations = self.builder.correlate_profiles(profiles)

        assert "shared_platforms" in correlations
        assert "potential_same_person" in correlations
        assert len(correlations["shared_platforms"]) > 0
        # user1 and user2 share Twitter and GitHub (2 platforms)
        # Should have shared_platforms entry but not potential_same_person (needs 3+)

    def test_correlate_profiles_strong_correlation(self):
        """Test profile correlation with strong correlation."""
        profiles = {
            "user1": {
                "username": "user1",
                "platforms": {"Twitter": {}, "GitHub": {}, "Facebook": {}, "LinkedIn": {}},
            },
            "user2": {
                "username": "user2",
                "platforms": {"Twitter": {}, "GitHub": {}, "Facebook": {}, "LinkedIn": {}},
            },
        }

        correlations = self.builder.correlate_profiles(profiles)

        assert len(correlations["potential_same_person"]) > 0
        assert correlations["potential_same_person"][0]["confidence"] > 0

    def test_correlate_profiles_no_overlap(self):
        """Test profile correlation with no overlap."""
        profiles = {
            "user1": {"username": "user1", "platforms": {"Twitter": {}}},
            "user2": {"username": "user2", "platforms": {"GitHub": {}}},
        }

        correlations = self.builder.correlate_profiles(profiles)

        assert len(correlations["shared_platforms"]) == 0
        assert len(correlations["potential_same_person"]) == 0

    def test_generate_profile_report(self):
        """Test profile report generation."""
        profile = {
            "username": "testuser",
            "found_on_platforms": 2,
            "platform_details": {
                "Twitter": {"url": "https://twitter.com/testuser", "response_time": 0.5},
                "GitHub": {"url": "https://github.com/testuser"},
            },
        }

        report = self.builder.generate_profile_report(profile)

        assert "testuser" in report
        assert "Twitter" in report
        assert "GitHub" in report
        assert "https://twitter.com/testuser" in report

    def test_generate_profile_report_empty(self):
        """Test profile report generation with empty profile."""
        profile = {
            "username": "testuser",
            "found_on_platforms": 0,
            "platform_details": {},
        }

        report = self.builder.generate_profile_report(profile)

        assert "testuser" in report
        assert "Platforms Found: 0" in report

