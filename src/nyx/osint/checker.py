"""Base platform checker implementation."""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from nyx.core.types import PlatformMatch
from nyx.models.platform import Platform, PlatformResult


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

    async def _request(self, url: str, method: str = "GET", **kwargs) -> Optional[httpx.Response]:
        """Make HTTP request with retries.

        Args:
            url: Request URL
            method: HTTP method
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
                async with httpx.AsyncClient(timeout=self.timeout) as client:
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

    async def check(self, username: str) -> Optional[PlatformMatch]:
        """Check username by status code.

        Args:
            username: Username to search for

        Returns:
            Match result or None
        """
        url = self.platform.search_url.format(username=username)

        start_time = time.time()
        response = await self._request(url)
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

        return {
            "username": username,
            "platform": self.platform.name,
            "found": found,
            "url": url if found else None,
            "status_code": response.status_code,
            "response_time": response_time,
        }


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
