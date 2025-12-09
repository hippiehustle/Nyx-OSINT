"""Search service for coordinating platform searches."""

import asyncio
import re
import time
from typing import Dict, List, Optional
from urllib.parse import quote

from nyx.config.base import load_config
from nyx.core.cache import get_cache
from nyx.core.events import (
    SearchStartedEvent,
    SearchCompleteEvent,
    ProfileFoundEvent,
    get_event_bus,
)
from nyx.core.http_client import HTTPClient
from nyx.core.logger import get_logger
from nyx.core.types import PlatformMatch
from nyx.models.platform import Platform
from nyx.osint.checker import BasePlatformChecker, StatusCodeChecker
from nyx.osint.platforms import get_platform_database
from nyx.osint.plugin import get_plugin_registry

logger = get_logger(__name__)


class SearchService:
    """Service for coordinating searches across multiple platforms."""

    def __init__(
        self,
        max_concurrent_searches: Optional[int] = None,
        cache_enabled: bool = True,
        http_client: Optional[HTTPClient] = None,
    ):
        """Initialize search service.

        Args:
            max_concurrent_searches: Maximum concurrent platform checks
            cache_enabled: Whether to use caching
        """
        # Load config to derive sane defaults when explicit values are not given
        cfg = load_config()

        self.max_concurrent_searches = (
            max_concurrent_searches or cfg.http.max_concurrent_requests
        )
        self.cache_enabled = cache_enabled
        self.semaphore = asyncio.Semaphore(self.max_concurrent_searches)
        self.platform_db = get_platform_database()
        self.cache = get_cache() if cache_enabled else None
        self.event_bus = get_event_bus()

        # Shared HTTP client reused across all platform checks for connection reuse
        # Note: rate_limit (requests/second) is separate from max_concurrent_requests
        # Using a reasonable default of 10.0 requests/second to avoid overwhelming targets
        self.http_client = http_client or HTTPClient(
            timeout=cfg.http.timeout,
            retries=cfg.http.retries,
            rate_limit=10.0,  # Reasonable default: 10 requests/second
            user_agent=cfg.http.user_agent,
        )

    async def aclose(self) -> None:
        """Close underlying HTTP resources.

        This should be called when the service is no longer needed to avoid
        leaking open HTTP connections in long-running processes.
        """
        await self.http_client.close()

    def _get_cache_key(self, username: str, platform_name: str) -> str:
        """Generate cache key for search result.

        Args:
            username: Username searched
            platform_name: Platform name

        Returns:
            Cache key
        """
        return f"search:{username}:{platform_name}".lower()
    
    def _get_cache_key_email(self, email: str, platform_name: str) -> str:
        """Generate cache key for email search result.
        
        Args:
            email: Email searched
            platform_name: Platform name
            
        Returns:
            Cache key
        """
        return f"search:email:{email}:{platform_name}".lower()
    
    def _get_cache_key_phone(self, phone: str, platform_name: str) -> str:
        """Generate cache key for phone search result.
        
        Args:
            phone: Phone number searched
            platform_name: Platform name
            
        Returns:
            Cache key
        """
        return f"search:phone:{phone}:{platform_name}".lower()
    
    @staticmethod
    def normalize_email_for_search(email: str) -> str:
        """Normalize email for URL insertion.
        
        Args:
            email: Email address
            
        Returns:
            Normalized email (URL encoded)
        """
        return quote(email.lower().strip())
    
    @staticmethod
    def normalize_phone_for_search(phone: str, format: str = "e164") -> str:
        """Normalize phone number for search.
        
        Args:
            phone: Phone number
            format: Desired format (e164, national, digits)
            
        Returns:
            Normalized phone number
        """
        try:
            import phonenumbers
            parsed = phonenumbers.parse(phone, None)
            
            if format == "e164":
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            elif format == "national":
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
            elif format == "digits":
                # Just digits, no formatting
                return re.sub(r'[^\d]', '', phone)
            else:
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            # Fallback: just clean the phone
            return re.sub(r'[^\d+]', '', phone)
    
    @staticmethod
    def generate_phone_search_variations(phone: str) -> List[str]:
        """Generate phone format variations for different platforms.
        
        Args:
            phone: Phone number
            
        Returns:
            List of phone format variations
        """
        variations = []
        
        # Try to parse and generate formats
        try:
            import phonenumbers
            parsed = phonenumbers.parse(phone, None)
            
            # E164: +1234567890
            variations.append(phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164))
            
            # National: (123) 456-7890 or similar
            variations.append(phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL))
            
            # International: +1 234 567 8900
            variations.append(phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
            
            # Just digits
            digits = re.sub(r'[^\d]', '', phone)
            if digits:
                variations.append(digits)
        except Exception:
            # Fallback: basic variations
            clean = re.sub(r'[^\d+]', '', phone)
            variations.append(clean)
            if clean.startswith('+'):
                variations.append(clean[1:])
        
        # Remove duplicates
        seen = set()
        unique = []
        for var in variations:
            if var and var not in seen:
                seen.add(var)
                unique.append(var)
        
        return unique

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

        # Use provided checker, plugin, or create default
        if not checker:
            # Check for custom plugin first
            plugin_registry = get_plugin_registry()
            plugin = plugin_registry.find_plugin_for_platform(platform)
            if plugin:
                # Use plugin checker (wrap it to match BasePlatformChecker interface)
                from nyx.osint.checker import BasePlatformChecker
                
                class PluginCheckerWrapper(BasePlatformChecker):
                    def __init__(self, platform, plugin_instance, http_client=None):
                        super().__init__(platform, http_client=http_client)
                        self.plugin = plugin_instance
                    
                    async def check(self, username: str):
                        return await self.plugin.check(username, self.platform)
                
                checker = PluginCheckerWrapper(platform, plugin, http_client=self.http_client)
            elif platform.detection_method == "status_code":
                checker = StatusCodeChecker(platform, http_client=self.http_client)
            else:
                checker = StatusCodeChecker(platform, http_client=self.http_client)

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
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, PlatformMatch]:
        """Search for username across platforms.

        Args:
            username: Username to search for
            platforms: Specific platforms to search (None = all)
            categories: Categories to search (None = all)
            exclude_nsfw: Exclude NSFW platforms
            timeout: Overall search timeout in seconds
            progress_callback: Optional callback for progress updates (platform_name, status)

        Returns:
            Dictionary of results keyed by platform name
        """
        start_time = time.time()

        # Publish search started event
        await self.event_bus.publish(
            SearchStartedEvent(
                source="SearchService",
                data={
                    "username": username,
                    "platform_count": len(self.platform_db.platforms),
                },
            )
        )

        # Filter platforms
        platforms_to_search = self._filter_platforms(platforms, categories, exclude_nsfw)

        if not platforms_to_search:
            logger.warning(f"No platforms found matching filters")
            return {}

        # Create tasks with platform mapping to maintain association
        task_to_platform = {}
        for platform in platforms_to_search.values():
            task = asyncio.create_task(self._check_platform(platform, username, progress_callback=progress_callback))
            task_to_platform[task] = platform

        # Execute searches with timeout - collect results from completed tasks
        if timeout:
            done, pending = await asyncio.wait(task_to_platform.keys(), timeout=timeout)

            # If timeout occurred, cancel remaining tasks but keep completed results
            if pending:
                logger.warning(f"Search timeout after {timeout} seconds - {len(done)} completed, {len(pending)} cancelled")
                for task in pending:
                    task.cancel()
                # Wait for cancellation to complete
                await asyncio.gather(*pending, return_exceptions=True)
        else:
            # No timeout - wait for all tasks
            done, pending = await asyncio.wait(task_to_platform.keys())

        # Process results from completed tasks
        found_profiles: Dict[str, PlatformMatch] = {}

        for task in done:
            platform = task_to_platform[task]
            try:
                result = task.result()
                if result and result.get("found"):
                    found_profiles[platform.name] = result

                    # Publish profile found event
                    await self.event_bus.publish(
                        ProfileFoundEvent(
                            source="SearchService",
                            data={"username": username, "platform": platform.name, "url": result.get("url")},
                        )
                    )
            except Exception as e:
                logger.debug(f"Task failed for {platform.name}: {e}")

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

    async def _check_platform_by_email(
        self,
        platform: Platform,
        email: str,
        progress_callback: Optional[callable] = None,
    ) -> Optional[PlatformMatch]:
        """Check single platform for email-based profile search.
        
        Args:
            platform: Platform to check
            email: Email address to search
            progress_callback: Optional callback for progress updates
            
        Returns:
            Search result or None
        """
        if not platform.email_search_url:
            return None
        
        # Check cache first
        if self.cache_enabled and self.cache:
            cache_key = self._get_cache_key_email(email, platform.name)
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                if progress_callback:
                    progress_callback(platform.name, "cached")
                return cached_result
        
        try:
            async with self.semaphore:
                if progress_callback:
                    progress_callback(platform.name, "checking")
                
                # Normalize email for URL
                normalized_email = self.normalize_email_for_search(email)
                
                # Build search URL
                if platform.email_param:
                    # Use parameter name: ?email=value or ?q=value
                    search_url = platform.email_search_url.replace(f"{{{platform.email_param}}}", normalized_email)
                else:
                    # Default to {email} placeholder
                    search_url = platform.email_search_url.replace("{email}", normalized_email)
                
                # Make request
                # Note: http_client.get() will auto-open if needed, no explicit open() required
                response = await self.http_client.get(search_url, timeout=platform.timeout)
                
                if response:
                    # Check if profile found (similar to username search)
                    found = False
                    profile_url = search_url
                    
                    if platform.exists_status_code and response.status_code == platform.exists_status_code:
                        found = True
                    elif platform.not_exists_status_code and response.status_code == platform.not_exists_status_code:
                        found = False
                    else:
                        # Default: 200 means found
                        found = response.status_code == 200
                    
                    result = {
                        "found": found,
                        "url": profile_url if found else None,
                        "platform": platform.name,
                        "status_code": response.status_code,
                    }
                    
                    # Cache result
                    if self.cache_enabled and self.cache:
                        cache_key = self._get_cache_key_email(email, platform.name)
                        await self.cache.set(cache_key, result)
                    
                    if progress_callback:
                        status = "found" if found else "not_found"
                        progress_callback(platform.name, status)
                    
                    return result
                
                return None
        except Exception as e:
            logger.debug(f"Error checking {platform.name} for email {email}: {e}")
            if progress_callback:
                progress_callback(platform.name, "error")
            return None

    async def _check_platform_by_phone(
        self,
        platform: Platform,
        phone: str,
        progress_callback: Optional[callable] = None,
    ) -> Optional[PlatformMatch]:
        """Check single platform for phone-based profile search.
        
        Args:
            platform: Platform to check
            phone: Phone number to search
            progress_callback: Optional callback for progress updates
            
        Returns:
            Search result or None
        """
        if not platform.phone_search_url:
            return None
        
        # Check cache first
        if self.cache_enabled and self.cache:
            cache_key = self._get_cache_key_phone(phone, platform.name)
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                if progress_callback:
                    progress_callback(platform.name, "cached")
                return cached_result
        
        try:
            async with self.semaphore:
                if progress_callback:
                    progress_callback(platform.name, "checking")
                
                # Generate phone variations and try each
                phone_variations = self.generate_phone_search_variations(phone)
                
                for phone_var in phone_variations[:3]:  # Limit to first 3 variations
                    try:
                        # Normalize phone for URL
                        normalized_phone = quote(phone_var)
                        
                        # Build search URL
                        if platform.phone_param:
                            search_url = platform.phone_search_url.replace(f"{{{platform.phone_param}}}", normalized_phone)
                        else:
                            # Default to {phone} placeholder
                            search_url = platform.phone_search_url.replace("{phone}", normalized_phone)
                        
                        # Make request
                        # Note: http_client.get() will auto-open if needed, no explicit open() required
                        response = await self.http_client.get(search_url, timeout=platform.timeout)
                        
                        if response:
                            # Check if profile found
                            found = False
                            profile_url = search_url
                            
                            if platform.exists_status_code and response.status_code == platform.exists_status_code:
                                found = True
                            elif platform.not_exists_status_code and response.status_code == platform.not_exists_status_code:
                                found = False
                            else:
                                # Default: 200 means found
                                found = response.status_code == 200
                            
                            if found:
                                result = {
                                    "found": True,
                                    "url": profile_url,
                                    "platform": platform.name,
                                    "status_code": response.status_code,
                                }
                                
                                # Cache result
                                if self.cache_enabled and self.cache:
                                    cache_key = self._get_cache_key_phone(phone, platform.name)
                                    await self.cache.set(cache_key, result)
                                
                                if progress_callback:
                                    progress_callback(platform.name, "found")
                                
                                return result
                    except Exception as e:
                        logger.debug(f"Error checking {platform.name} with phone variation {phone_var}: {e}")
                        continue
                
                # No profile found with any variation
                result = {
                    "found": False,
                    "url": None,
                    "platform": platform.name,
                    "status_code": None,
                }
                
                if progress_callback:
                    progress_callback(platform.name, "not_found")
                
                return result
        except Exception as e:
            logger.debug(f"Error checking {platform.name} for phone {phone}: {e}")
            if progress_callback:
                progress_callback(platform.name, "error")
            return None

    async def search_by_email(
        self,
        email: str,
        platforms: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        exclude_nsfw: bool = False,
        timeout: Optional[int] = None,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, PlatformMatch]:
        """Search for profiles using email address across platforms.
        
        Args:
            email: Email address to search
            platforms: Specific platforms to search (None = all that support email)
            categories: Categories to search (None = all)
            exclude_nsfw: Exclude NSFW platforms
            timeout: Overall search timeout in seconds
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary of results keyed by platform name
        """
        start_time = time.time()
        
        # Filter platforms that support email search
        all_platforms = self._filter_platforms(platforms, categories, exclude_nsfw)
        email_platforms = {
            name: p for name, p in all_platforms.items()
            if p.email_search_url is not None
        }
        
        if not email_platforms:
            logger.warning("No platforms found that support email-based profile search")
            return {}
        
        # Create tasks
        task_to_platform = {}
        for platform in email_platforms.values():
            task = asyncio.create_task(
                self._check_platform_by_email(platform, email, progress_callback=progress_callback)
            )
            task_to_platform[task] = platform
        
        # Execute with timeout
        if timeout:
            done, pending = await asyncio.wait(task_to_platform.keys(), timeout=timeout)
            if pending:
                logger.warning(f"Email search timeout after {timeout} seconds")
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
        else:
            done, pending = await asyncio.wait(task_to_platform.keys())
        
        # Process results
        found_profiles: Dict[str, PlatformMatch] = {}
        for task in done:
            platform = task_to_platform[task]
            try:
                result = task.result()
                if result and result.get("found"):
                    found_profiles[platform.name] = result
            except Exception as e:
                logger.debug(f"Task failed for {platform.name}: {e}")
        
        duration = time.time() - start_time
        logger.info(f"Email search for '{email}' complete: found {len(found_profiles)} profiles in {duration:.2f}s")
        
        return found_profiles

    async def search_by_phone(
        self,
        phone: str,
        platforms: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        exclude_nsfw: bool = False,
        timeout: Optional[int] = None,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, PlatformMatch]:
        """Search for profiles using phone number across platforms.
        
        Args:
            phone: Phone number to search
            platforms: Specific platforms to search (None = all that support phone)
            categories: Categories to search (None = all)
            exclude_nsfw: Exclude NSFW platforms
            timeout: Overall search timeout in seconds
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary of results keyed by platform name
        """
        start_time = time.time()
        
        # Filter platforms that support phone search
        all_platforms = self._filter_platforms(platforms, categories, exclude_nsfw)
        phone_platforms = {
            name: p for name, p in all_platforms.items()
            if p.phone_search_url is not None
        }
        
        if not phone_platforms:
            logger.warning("No platforms found that support phone-based profile search")
            return {}
        
        # Create tasks
        task_to_platform = {}
        for platform in phone_platforms.values():
            task = asyncio.create_task(
                self._check_platform_by_phone(platform, phone, progress_callback=progress_callback)
            )
            task_to_platform[task] = platform
        
        # Execute with timeout
        if timeout:
            done, pending = await asyncio.wait(task_to_platform.keys(), timeout=timeout)
            if pending:
                logger.warning(f"Phone search timeout after {timeout} seconds")
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
        else:
            done, pending = await asyncio.wait(task_to_platform.keys())
        
        # Process results
        found_profiles: Dict[str, PlatformMatch] = {}
        for task in done:
            platform = task_to_platform[task]
            try:
                result = task.result()
                if result and result.get("found"):
                    found_profiles[platform.name] = result
            except Exception as e:
                logger.debug(f"Task failed for {platform.name}: {e}")
        
        duration = time.time() - start_time
        logger.info(f"Phone search for '{phone}' complete: found {len(found_profiles)} profiles in {duration:.2f}s")
        
        return found_profiles

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
