"""Tests for search service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nyx.models.platform import Platform, PlatformCategory
from nyx.osint.search import SearchService


class TestSearchService:
    """Test SearchService functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        with patch("nyx.osint.search.load_config"), patch(
            "nyx.osint.search.get_cache"
        ), patch("nyx.osint.search.get_platform_database"), patch(
            "nyx.osint.search.get_event_bus"
        ), patch("nyx.osint.search.HTTPClient"):
            self.service = SearchService()
            self.service.platform_db = MagicMock()
            self.service.platform_db.platforms = {}
            self.service.platform_db.get_nsfw_platforms = MagicMock(return_value=[])
            self.service.platform_db.count_platforms = MagicMock(return_value=0)
            self.service.cache = AsyncMock()
            self.service.event_bus = AsyncMock()

    def test_initialization(self):
        """Test SearchService initialization."""
        assert self.service.max_concurrent_searches > 0
        assert self.service.platform_db is not None
        assert self.service.cache is not None

    def test_get_cache_key(self):
        """Test cache key generation."""
        key = self.service._get_cache_key("testuser", "Twitter")
        assert key == "search:testuser:twitter"

    def test_filter_platforms_all(self):
        """Test platform filtering with no filters."""
        platform1 = Platform(
            name="Twitter",
            url="https://twitter.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            is_active=True,
        )
        platform2 = Platform(
            name="GitHub",
            url="https://github.com",
            category=PlatformCategory.PROFESSIONAL,
            is_active=True,
        )
        self.service.platform_db.platforms = {
            "twitter": platform1,
            "github": platform2,
        }

        filtered = self.service._filter_platforms()
        assert len(filtered) == 2

    def test_filter_platforms_by_name(self):
        """Test platform filtering by name."""
        platform1 = Platform(
            name="Twitter",
            url="https://twitter.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            is_active=True,
        )
        platform2 = Platform(
            name="GitHub",
            url="https://github.com",
            category=PlatformCategory.PROFESSIONAL,
            is_active=True,
        )
        self.service.platform_db.platforms = {
            "twitter": platform1,
            "github": platform2,
        }

        filtered = self.service._filter_platforms(platform_names=["Twitter"])
        assert len(filtered) == 1
        assert "twitter" in filtered

    def test_filter_platforms_by_category(self):
        """Test platform filtering by category."""
        platform1 = Platform(
            name="Twitter",
            url="https://twitter.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            is_active=True,
        )
        platform2 = Platform(
            name="GitHub",
            url="https://github.com",
            category=PlatformCategory.PROFESSIONAL,
            is_active=True,
        )
        self.service.platform_db.platforms = {
            "twitter": platform1,
            "github": platform2,
        }

        filtered = self.service._filter_platforms(categories=["social_media"])
        assert len(filtered) == 1
        assert "twitter" in filtered

    def test_filter_platforms_exclude_nsfw(self):
        """Test platform filtering excluding NSFW."""
        platform1 = Platform(
            name="Twitter",
            url="https://twitter.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            is_active=True,
            is_nsfw=False,
        )
        platform2 = Platform(
            name="NSFWPlatform",
            url="https://nsfw.com",
            category=PlatformCategory.ADULT,
            is_active=True,
            is_nsfw=True,
        )
        self.service.platform_db.platforms = {
            "twitter": platform1,
            "nsfw": platform2,
        }

        filtered = self.service._filter_platforms(exclude_nsfw=True)
        assert len(filtered) == 1
        assert "twitter" in filtered
        assert "nsfw" not in filtered

    def test_filter_platforms_inactive(self):
        """Test platform filtering excludes inactive platforms."""
        platform1 = Platform(
            name="Twitter",
            url="https://twitter.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            is_active=True,
        )
        platform2 = Platform(
            name="Inactive",
            url="https://inactive.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            is_active=False,
        )
        self.service.platform_db.platforms = {
            "twitter": platform1,
            "inactive": platform2,
        }

        filtered = self.service._filter_platforms()
        assert len(filtered) == 1
        assert "twitter" in filtered

    @pytest.mark.asyncio
    async def test_check_platform_cached(self):
        """Test platform check with cache hit."""
        platform = Platform(
            name="Twitter",
            url="https://twitter.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            search_url="https://twitter.com/{username}",
            detection_method="status_code",
            exists_status_code=200,
        )
        cached_result = {"found": True, "url": "https://twitter.com/testuser"}
        self.service.cache.get = AsyncMock(return_value=cached_result)

        result = await self.service._check_platform(platform, "testuser")

        assert result == cached_result
        self.service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_platform_no_cache(self):
        """Test platform check without cache."""
        platform = Platform(
            name="Twitter",
            url="https://twitter.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            search_url="https://twitter.com/{username}",
            detection_method="status_code",
            exists_status_code=200,
        )
        self.service.cache.get = AsyncMock(return_value=None)
        self.service.cache.set = AsyncMock()

        with patch("nyx.osint.search.StatusCodeChecker") as mock_checker_class:
            mock_checker = AsyncMock()
            mock_checker_class.return_value = mock_checker
            mock_checker.check = AsyncMock(
                return_value={"found": True, "url": "https://twitter.com/testuser"}
            )

            result = await self.service._check_platform(platform, "testuser")

            assert result is not None
            assert result["found"] is True
            self.service.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_platform_error(self):
        """Test platform check error handling."""
        platform = Platform(
            name="Twitter",
            url="https://twitter.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            search_url="https://twitter.com/{username}",
            detection_method="status_code",
        )
        self.service.cache.get = AsyncMock(return_value=None)

        with patch("nyx.osint.search.StatusCodeChecker") as mock_checker_class:
            mock_checker = AsyncMock()
            mock_checker_class.return_value = mock_checker
            mock_checker.check = AsyncMock(side_effect=Exception("Error"))

            result = await self.service._check_platform(platform, "testuser")

            assert result is None

    @pytest.mark.asyncio
    async def test_search_username(self):
        """Test username search."""
        platform1 = Platform(
            name="Twitter",
            url="https://twitter.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            search_url="https://twitter.com/{username}",
            detection_method="status_code",
            is_active=True,
        )
        self.service.platform_db.platforms = {"twitter": platform1}

        with patch.object(
            self.service, "_check_platform", new_callable=AsyncMock
        ) as mock_check:
            mock_check.return_value = {
                "found": True,
                "url": "https://twitter.com/testuser",
            }

            results = await self.service.search_username("testuser", timeout=5)

            assert len(results) == 1
            assert "Twitter" in results
            self.service.event_bus.publish.assert_called()

    @pytest.mark.asyncio
    async def test_search_username_timeout(self):
        """Test username search with timeout."""
        platform1 = Platform(
            name="Twitter",
            url="https://twitter.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            search_url="https://twitter.com/{username}",
            detection_method="status_code",
            is_active=True,
        )
        self.service.platform_db.platforms = {"twitter": platform1}

        with patch.object(
            self.service, "_check_platform", new_callable=AsyncMock
        ) as mock_check:
            import asyncio

            async def slow_check(*args, **kwargs):
                await asyncio.sleep(10)
                return {"found": True}

            mock_check.side_effect = slow_check

            results = await self.service.search_username("testuser", timeout=1)

            assert isinstance(results, dict)

    @pytest.mark.asyncio
    async def test_search_username_progress_callback(self):
        """Test username search with progress callback."""
        platform1 = Platform(
            name="Twitter",
            url="https://twitter.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            search_url="https://twitter.com/{username}",
            detection_method="status_code",
            is_active=True,
        )
        self.service.platform_db.platforms = {"twitter": platform1}

        callback_calls = []

        def progress_callback(platform_name, status):
            callback_calls.append((platform_name, status))

        with patch.object(
            self.service, "_check_platform", new_callable=AsyncMock
        ) as mock_check:
            mock_check.return_value = {"found": True}

            await self.service.search_username(
                "testuser", progress_callback=progress_callback, timeout=5
            )

            assert len(callback_calls) > 0

    @pytest.mark.asyncio
    async def test_search_username_no_platforms(self):
        """Test username search with no matching platforms."""
        self.service.platform_db.platforms = {}

        results = await self.service.search_username("testuser")

        assert results == {}

    @pytest.mark.asyncio
    async def test_aclose(self):
        """Test resource cleanup."""
        self.service.http_client.close = AsyncMock()

        await self.service.aclose()

        self.service.http_client.close.assert_called_once()

    def test_get_platform_stats(self):
        """Test platform statistics."""
        platform1 = Platform(
            name="Twitter",
            url="https://twitter.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            is_active=True,
            is_nsfw=False,
        )
        platform2 = Platform(
            name="NSFW",
            url="https://nsfw.com",
            category=PlatformCategory.ADULT,
            is_active=True,
            is_nsfw=True,
        )
        self.service.platform_db.platforms = {
            "twitter": platform1,
            "nsfw": platform2,
        }
        self.service.platform_db.count_platforms = MagicMock(return_value=2)
        self.service.platform_db.get_nsfw_platforms = MagicMock(
            return_value=[platform2]
        )

        stats = self.service.get_platform_stats()

        assert stats["total_platforms"] == 2
        assert stats["active_platforms"] == 2
        assert stats["nsfw_platforms"] == 1
        assert stats["sfw_platforms"] == 1

