"""HTTP client wrapper with rate limiting and retry logic."""

import asyncio
import time
from typing import Optional, Dict, Any

import httpx


class RateLimiter:
    """Rate limiter for HTTP requests."""

    def __init__(self, requests_per_second: float = 10.0):
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        async with self.lock:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self.last_request_time = time.time()


class HTTPClient:
    """Async HTTP client with rate limiting and retries."""

    def __init__(
        self,
        timeout: int = 10,
        retries: int = 3,
        backoff_factor: float = 0.5,
        rate_limit: float = 10.0,
        user_agent: Optional[str] = None,
    ):
        """Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds
            retries: Number of retries on failure
            backoff_factor: Exponential backoff factor
            rate_limit: Requests per second
            user_agent: Custom user agent
        """
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.rate_limiter = RateLimiter(rate_limit)
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Nyx/0.1.0"
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "HTTPClient":
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Optional[httpx.Response]:
        """Make GET request.

        Args:
            url: Request URL
            headers: Custom headers
            **kwargs: Additional request arguments

        Returns:
            Response or None on failure
        """
        return await self._request("GET", url, headers=headers, **kwargs)

    async def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Optional[httpx.Response]:
        """Make POST request.

        Args:
            url: Request URL
            headers: Custom headers
            **kwargs: Additional request arguments

        Returns:
            Response or None on failure
        """
        return await self._request("POST", url, headers=headers, **kwargs)

    async def _request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Optional[httpx.Response]:
        """Make HTTP request with rate limiting and retries.

        Args:
            method: HTTP method
            url: Request URL
            headers: Custom headers
            **kwargs: Additional request arguments

        Returns:
            Response or None on failure
        """
        if not self.client:
            raise RuntimeError("HTTPClient not initialized. Use async with context manager.")

        # Prepare headers
        request_headers = {"User-Agent": self.user_agent}
        if headers:
            request_headers.update(headers)

        # Apply rate limiting
        await self.rate_limiter.acquire()

        # Retry loop
        for attempt in range(self.retries):
            try:
                response = await self.client.request(method, url, headers=request_headers, **kwargs)
                return response
            except (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
            ) as e:
                if attempt == self.retries - 1:
                    return None

                # Exponential backoff
                wait_time = self.backoff_factor * (2 ** attempt)
                await asyncio.sleep(wait_time)
            except Exception:
                return None

        return None

    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
