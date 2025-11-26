"""Base platform checker implementation."""

import asyncio
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urlparse

import httpx

from nyx.core.logger import get_logger
from nyx.core.types import PlatformMatch
from nyx.models.platform import Platform, PlatformResult

# Silence httpx INFO logging
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = get_logger(__name__)


class BasePlatformChecker(ABC):
    """Base class for platform checkers."""

    def __init__(
        self,
        platform: Platform,
        timeout: int = 10,
        retries: int = 3,
        user_agent: Optional[str] = None,
    ):
        """Initialize platform checker.

        Args:
            platform: Platform configuration
            timeout: Request timeout in seconds
            retries: Number of retries on failure
            user_agent: Custom user agent
        """
        self.platform = platform
        self.timeout = timeout or platform.timeout
        self.retries = retries
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Nyx/0.1.0"

    @abstractmethod
    async def check(self, username: str) -> Optional[PlatformMatch]:
        """Check if username exists on platform.

        Args:
            username: Username to search for

        Returns:
            Match result or None if not found
        """
        pass

    async def _request(self, url: str, method: str = "GET", follow_redirects: bool = True, **kwargs) -> Optional[httpx.Response]:
        """Make HTTP request with retries.

        Args:
            url: Request URL
            method: HTTP method
            follow_redirects: Whether to follow redirects
            **kwargs: Additional request arguments

        Returns:
            Response or None on failure
        """
        headers = kwargs.pop("headers", {})
        headers["User-Agent"] = self.user_agent
        if self.platform.headers:
            headers.update(self.platform.headers)

        for attempt in range(self.retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=follow_redirects) as client:
                    response = await client.request(method, url, headers=headers, **kwargs)
                    return response
            except asyncio.TimeoutError:
                if attempt == self.retries - 1:
                    return None
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception:
                if attempt == self.retries - 1:
                    return None
                await asyncio.sleep(2 ** attempt)

        return None

    async def save_result(self, username: str, found: bool, profile_url: Optional[str] = None) -> PlatformResult:
        """Save search result to database.

        Args:
            username: Username searched
            found: Whether profile was found
            profile_url: URL to profile if found

        Returns:
            Saved result
        """
        result = PlatformResult(
            platform_id=self.platform.id,
            username=username,
            found=found,
            profile_url=profile_url,
        )
        return result


class StatusCodeChecker(BasePlatformChecker):
    """Check platform by HTTP status code."""

    # Common false positive indicators
    FALSE_POSITIVE_PATTERNS = [
        r'(sign.?up|register|join|create.?account)',  # Signup/registration pages
        r'(log.?in|sign.?in|auth|login)',  # Login pages
        r'(404|not.?found|does.?not.?exist)',  # Error messages
        r'(user.?not.?found|profile.?not.?found|no.?user)',  # User not found
        r'(search.?results|browse|explore)',  # Search/browse pages
    ]

    async def check(self, username: str) -> Optional[PlatformMatch]:
        """Check username by status code with false positive detection.

        Args:
            username: Username to search for

        Returns:
            Match result or None
        """
        url = self.platform.search_url.format(username=username)

        start_time = time.time()
        response = await self._request(url, follow_redirects=True)
        response_time = time.time() - start_time

        if not response:
            return None

        # Check if found based on status code
        found = False
        if self.platform.exists_status_code and response.status_code == self.platform.exists_status_code:
            found = True
        elif self.platform.not_exists_status_code and response.status_code == self.platform.not_exists_status_code:
            found = False
        else:
            # Default: 200 = found, 404 = not found
            found = response.status_code == 200

        # Additional validation for 200 responses to reduce false positives
        if found and response.status_code == 200:
            found = self._validate_profile_page(response, username, url)

        return {
            "username": username,
            "platform": self.platform.name,
            "found": found,
            "url": url if found else None,
            "status_code": response.status_code,
            "response_time": response_time,
        }

    def _validate_profile_page(self, response: httpx.Response, username: str, original_url: str) -> bool:
        """Validate that a 200 response is actually a user profile, not a false positive.

        Args:
            response: HTTP response
            username: Username being searched
            original_url: Original search URL

        Returns:
            True if likely a real profile, False if likely a false positive
        """
        final_url = str(response.url)
        final_path = urlparse(final_url).path.lower()
        original_path = urlparse(original_url).path.lower()
        username_lower = username.lower()

        # CRITICAL CHECK: Detect homepage/root redirects
        # If we requested a profile URL but got redirected to just the homepage, it's a false positive
        parsed_original = urlparse(original_url)
        parsed_final = urlparse(final_url)

        # Check if original URL had a meaningful path (with username) but final is just root
        original_has_path = parsed_original.path and parsed_original.path not in ['/', '']
        final_is_root = parsed_final.path in ['/', '', '/index.html', '/home', '/index', '/index.php']

        if original_has_path and final_is_root:
            # Redirected from /users/username to just / - definitely a false positive
            logger.debug(f"False positive detected: {self.platform.name} - redirected to homepage")
            return False

        # SECONDARY CHECK: If redirected to a different path, verify username is still in the URL
        if final_path != original_path:
            # Only reject if BOTH conditions are true:
            # 1. Username is not in the final path
            # 2. Final path is the root/homepage
            if username_lower not in final_path and final_is_root:
                logger.debug(f"False positive detected: {self.platform.name} - no username in redirect to root")
                return False

        # OPTIONAL CHECK: Look for strong "not found" indicators in content
        # Only check for very obvious false positives, don't be too aggressive
        try:
            content_lower = response.text.lower()

            # Only reject if we find STRONG indicators that this is not a profile
            strong_false_positive_patterns = [
                r'user.?not.?found',
                r'profile.?not.?found',
                r'account.?not.?found',
                r'page.?not.?found',
                r'error.?404',
            ]

            for pattern in strong_false_positive_patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    # Only reject if the username is NOT in the content at all
                    # (if username is present, might be a valid profile with these words)
                    if username_lower not in content_lower:
                        logger.debug(f"False positive detected: {self.platform.name} - 'not found' in content")
                        return False
        except Exception:
            # If we can't read content, don't reject - better to have false positives than miss real profiles
            pass

        # Passed validation - likely a real profile
        return True


class RegexChecker(BasePlatformChecker):
    """Check platform by regex pattern matching."""

    async def check(self, username: str) -> Optional[PlatformMatch]:
        """Check username by regex pattern.

        Args:
            username: Username to search for

        Returns:
            Match result or None
        """
        import re

        url = self.platform.search_url.format(username=username)

        start_time = time.time()
        response = await self._request(url)
        response_time = time.time() - start_time

        if not response:
            return None

        content = response.text
        found = False

        # Check for found pattern
        if self.platform.exists_pattern and re.search(self.platform.exists_pattern, content):
            found = True
        # Check for not found pattern
        elif self.platform.not_exists_pattern and re.search(self.platform.not_exists_pattern, content):
            found = False
        else:
            # Default: check if we got a successful response
            found = response.status_code == 200

        return {
            "username": username,
            "platform": self.platform.name,
            "found": found,
            "url": url if found else None,
            "status_code": response.status_code,
            "response_time": response_time,
        }
