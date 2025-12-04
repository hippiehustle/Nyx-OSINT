"""HTTP client wrapper with rate limiting and retry logic."""

import asyncio
import time
from typing import Optional, Dict

import httpx


class RateLimiter:
    """Simple async rate limiter for HTTP requests."""

    def __init__(self, requests_per_second: float = 10.0):
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
        """
        self.requests_per_second = max(requests_per_second, 0.1)
        self.min_interval = 1.0 / self.requests_per_second
        self.last_request_time = 0.0
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request respecting max RPS."""
        async with self.lock:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self.last_request_time = time.time()


class HTTPClient:
    """Async HTTP client with rate limiting and retries.

    This class is designed to be long-lived and reused across requests.
    Use it as an async context manager or call ``open()``/``close()`` manually.
    """

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
        self.retries = max(retries, 0)
        self.backoff_factor = max(backoff_factor, 0.0)
        self.rate_limiter = RateLimiter(rate_limit)
        self.user_agent = (
            user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Nyx/0.1.0"
        )
        self.client: Optional[httpx.AsyncClient] = None

    async def open(self) -> None:
        """Explicitly open underlying AsyncClient if not already open."""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout)

    async def __aenter__(self) -> "HTTPClient":
        """Async context manager entry."""
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Optional[httpx.Response]:
        """Make GET request."""
        return await self._request("GET", url, headers=headers, **kwargs)

    async def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Optional[httpx.Response]:
        """Make POST request."""
        return await self._request("POST", url, headers=headers, **kwargs)

    async def _request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Optional[httpx.Response]:
        """Make HTTP request with rate limiting and retries.

        Returns a ``httpx.Response`` on success or ``None`` on failure.
        """
        if not self.client:
            # Allow using without explicit context manager if caller forgot to open
            await self.open()

        # Prepare headers
        request_headers: Dict[str, str] = {"User-Agent": self.user_agent}
        if headers:
            request_headers.update(headers)

        # Apply rate limiting
        await self.rate_limiter.acquire()

        # Retry loop: make initial attempt + retries attempts (total: retries + 1)
        # attempt values: 0, 1, 2, ..., retries
        for attempt in range(self.retries + 1):
            try:
                response = await self.client.request(
                    method, url, headers=request_headers, **kwargs
                )

                # Basic 429 / rate-limit handling: back off and retry if allowed
                # Retry on 429 for all attempts except the final one (when attempt == self.retries)
                # This ensures we make retries+1 total attempts before giving up
                if response.status_code == 429:
                    if attempt < self.retries:
                        # We have more attempts remaining, retry after backoff
                        retry_after = response.headers.get("Retry-After")
                        try:
                            wait_time = float(retry_after)
                        except (TypeError, ValueError):
                            wait_time = self.backoff_factor * (2**attempt or 1)
                        await asyncio.sleep(wait_time)
                        continue
                    # Final attempt: return 429 response instead of retrying forever
                    return response

                return response
            except (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
            ):
                if attempt == self.retries:
                    return None
                # Exponential backoff
                wait_time = self.backoff_factor * (2**attempt or 1)
                await asyncio.sleep(wait_time)
            except Exception as e:
                # On unexpected error, log but don't propagate network internals to callers
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Unexpected error in HTTP request to {url}: {e}", exc_info=False)
                if attempt == self.retries:
                    return None
                # Continue retry loop
                wait_time = self.backoff_factor * (2**attempt or 1)
                await asyncio.sleep(wait_time)

        return None

    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
