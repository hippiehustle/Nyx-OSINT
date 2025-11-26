"""Search service for coordinating platform searches."""

import asyncio
import time
from typing import Dict, List, Optional, Set

from nyx.core.cache import get_cache
from nyx.core.events import SearchStartedEvent, SearchProgressEvent, SearchCompleteEvent, ProfileFoundEvent, get_event_bus
from nyx.core.logger import get_logger
from nyx.core.types import PlatformMatch
from nyx.models.platform import Platform, PlatformResult
from nyx.osint.checker import BasePlatformChecker, StatusCodeChecker
from nyx.osint.platforms import get_platform_database

logger = get_logger(__name__)


class SearchService:
    """Service for coordinating searches across multiple platforms."""

    def __init__(self, max_concurrent_searches: int = 100, cache_enabled: bool = True):
        """Initialize search service.

        Args:
            max_concurrent_searches: Maximum concurrent platform checks
            cache_enabled: Whether to use caching
        """
        self.max_concurrent_searches = max_concurrent_searches
        self.cache_enabled = cache_enabled
        self.semaphore = asyncio.Semaphore(max_concurrent_searches)
        self.platform_db = get_platform_database()
        self.cache = get_cache() if cache_enabled else None
        self.event_bus = get_event_bus()

    def _get_cache_key(self, username: str, platform_name: str) -> str:
        """Generate cache key for search result.

        Args:
            username: Username searched
            platform_name: Platform name

        Returns:
            Cache key
        """
        return f"search:{username}:{platform_name}".lower()

    async def _check_platform(
        self,
        platform: Platform,
        username: str,
        checker: Optional[BasePlatformChecker] = None,
        progress_callback: Optional[callable] = None,
    ) -> Optional[PlatformMatch]:
        """Check single platform for username.

        Args:
            platform: Platform to check
            username: Username to search for
            checker: Custom checker instance
            progress_callback: Optional callback for progress updates

        Returns:
            Search result or None
        """
        # Check cache first
        if self.cache_enabled and self.cache:
            cache_key = self._get_cache_key(username, platform.name)
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                if progress_callback:
                    progress_callback(platform.name, "cached")
                return cached_result

        # Use provided checker or create default
        if not checker:
            if platform.detection_method == "status_code":
                checker = StatusCodeChecker(platform)
            else:
                checker = StatusCodeChecker(platform)  # Default to status code

        try:
            async with self.semaphore:
                if progress_callback:
                    progress_callback(platform.name, "checking")
                result = await checker.check(username)
                if progress_callback:
                    status = "found" if result and result.get("found") else "not_found"
                    progress_callback(platform.name, status)

            # Cache result
            if self.cache_enabled and self.cache and result:
                cache_key = self._get_cache_key(username, platform.name)
                await self.cache.set(cache_key, result)

            return result
        except Exception as e:
            logger.debug(f"Error checking {platform.name}: {e}")
            if progress_callback:
                progress_callback(platform.name, "error")
            return None

    async def search_username(
        self,
        username: str,
        platforms: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        exclude_nsfw: bool = False,
        timeout: Optional[int] = None,
    ) -> Dict[str, PlatformMatch]:
        """Search for username across platforms.

        Args:
            username: Username to search for
            platforms: Specific platforms to search (None = all)
            categories: Categories to search (None = all)
            exclude_nsfw: Exclude NSFW platforms
            timeout: Overall search timeout in seconds

        Returns:
            Dictionary of results keyed by platform name
        """
        start_time = time.time()

        # Publish search started event
        await self.event_bus.publish(
            SearchStartedEvent(
                source="SearchService",
                data={"username": username, "platform_count": len(self.platform_db.platforms)},
            )
        )

        # Filter platforms
        platforms_to_search = self._filter_platforms(platforms, categories, exclude_nsfw)

        if not platforms_to_search:
            logger.warning(f"No platforms found matching filters")
            return {}

        # Create tasks for all platform checks
        tasks = [
            self._check_platform(platform, username)
            for platform in platforms_to_search.values()
        ]

        # Execute searches with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Search timeout after {timeout} seconds")
            results = []

        # Process results
        found_profiles: Dict[str, PlatformMatch] = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                continue
            if result and result.get("found"):
                platform_name = list(platforms_to_search.values())[i].name
                found_profiles[platform_name] = result

                # Publish profile found event
                await self.event_bus.publish(
                    ProfileFoundEvent(
                        source="SearchService",
                        data={"username": username, "platform": platform_name, "url": result.get("url")},
                    )
                )

        # Publish search complete event
        duration = time.time() - start_time
        await self.event_bus.publish(
            SearchCompleteEvent(
                source="SearchService",
                data={
                    "username": username,
                    "platforms_searched": len(platforms_to_search),
                    "results_found": len(found_profiles),
                    "duration_seconds": duration,
                },
            )
        )

        logger.info(f"Search for '{username}' complete: found {len(found_profiles)} profiles in {duration:.2f}s")

        return found_profiles

    def _filter_platforms(
        self,
        platform_names: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        exclude_nsfw: bool = False,
    ) -> Dict[str, Platform]:
        """Filter platforms based on criteria.

        Args:
            platform_names: Specific platforms to include
            categories: Categories to include
            exclude_nsfw: Whether to exclude NSFW platforms

        Returns:
            Filtered platforms dictionary
        """
        platforms = {}

        for name, platform in self.platform_db.platforms.items():
            # Check if platform is active
            if not platform.is_active:
                continue

            # Check NSFW filter
            if exclude_nsfw and platform.is_nsfw:
                continue

            # Check specific platforms filter
            if platform_names:
                if platform.name.lower() not in [p.lower() for p in platform_names]:
                    continue

            # Check categories filter
            if categories:
                if platform.category.value not in [c.lower() for c in categories]:
                    continue

            platforms[name] = platform

        return platforms

    async def search_email(
        self,
        email: str,
        breach_check: bool = True,
        timeout: Optional[int] = None,
    ) -> Dict[str, PlatformMatch]:
        """Search for email across email-checking services.

        Args:
            email: Email to search for
            breach_check: Whether to check breach databases
            timeout: Overall timeout in seconds

        Returns:
            Dictionary of services where email was found
        """
        # Get email-specific platforms (like Holehe integration points)
        email_platforms = self.platform_db.get_by_category("email") if hasattr(self.platform_db, "get_by_category") else []

        if not email_platforms:
            logger.warning("No email checking platforms configured")
            return {}

        results = await self.search_username(email, platforms=[p.name for p in email_platforms], timeout=timeout)

        return results

    async def search_phone(
        self,
        phone: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, PlatformMatch]:
        """Search for phone number across services.

        Args:
            phone: Phone number to search for
            timeout: Overall timeout in seconds

        Returns:
            Dictionary of services where phone was found
        """
        results = await self.search_username(phone, categories=["phone"], timeout=timeout)

        return results

    def get_platform_stats(self) -> Dict[str, int]:
        """Get statistics about configured platforms.

        Returns:
            Dictionary of platform statistics
        """
        total = self.platform_db.count_platforms()
        active = len([p for p in self.platform_db.platforms.values() if p.is_active])
        nsfw = len(self.platform_db.get_nsfw_platforms())

        stats = {
            "total_platforms": total,
            "active_platforms": active,
            "nsfw_platforms": nsfw,
            "sfw_platforms": active - nsfw,
        }

        return stats
