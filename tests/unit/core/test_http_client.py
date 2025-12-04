"""Tests for HTTP client module."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from nyx.core.http_client import HTTPClient, RateLimiter


class TestRateLimiter:
    """Test RateLimiter functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting behavior."""
        limiter = RateLimiter(requests_per_second=10.0)
        start_time = asyncio.get_event_loop().time()

        await limiter.acquire()
        await limiter.acquire()

        elapsed = asyncio.get_event_loop().time() - start_time
        # Should have waited at least min_interval between requests
        assert elapsed >= limiter.min_interval * 0.9  # Allow small timing variance

    @pytest.mark.asyncio
    async def test_rate_limiter_minimum_rate(self):
        """Test that rate limiter handles very low rates."""
        limiter = RateLimiter(requests_per_second=0.1)
        assert limiter.requests_per_second >= 0.1

    @pytest.mark.asyncio
    async def test_rate_limiter_concurrent(self):
        """Test rate limiter with concurrent requests."""
        limiter = RateLimiter(requests_per_second=100.0)

        async def make_request():
            await limiter.acquire()

        # Make multiple concurrent requests
        await asyncio.gather(*[make_request() for _ in range(10)])


class TestHTTPClient:
    """Test HTTPClient functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = HTTPClient(timeout=5, retries=2, rate_limit=10.0)

    def test_initialization(self):
        """Test HTTPClient initialization."""
        assert self.client.timeout == 5
        assert self.client.retries == 2
        assert self.client.rate_limiter is not None
        assert self.client.client is None

    def test_initialization_minimum_values(self):
        """Test that initialization enforces minimum values."""
        client = HTTPClient(retries=-1, backoff_factor=-1.0, rate_limit=-1.0)
        assert client.retries >= 0
        assert client.backoff_factor >= 0.0
        assert client.rate_limiter.requests_per_second >= 0.1

    @pytest.mark.asyncio
    async def test_open(self):
        """Test explicit client opening."""
        await self.client.open()
        assert self.client.client is not None
        assert isinstance(self.client.client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test HTTPClient as async context manager."""
        async with HTTPClient() as client:
            assert client.client is not None

    @pytest.mark.asyncio
    async def test_get_request(self):
        """Test GET request."""
        await self.client.open()
        mock_response = MagicMock()
        mock_response.status_code = 200
        self.client.client.request = AsyncMock(return_value=mock_response)

        response = await self.client.get("https://example.com")

        assert response == mock_response
        self.client.client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_request(self):
        """Test POST request."""
        await self.client.open()
        mock_response = MagicMock()
        mock_response.status_code = 200
        self.client.client.request = AsyncMock(return_value=mock_response)

        response = await self.client.post("https://example.com", json={"key": "value"})

        assert response == mock_response

    @pytest.mark.asyncio
    async def test_request_success(self):
        """Test successful request."""
        await self.client.open()
        mock_response = MagicMock()
        mock_response.status_code = 200
        self.client.client.request = AsyncMock(return_value=mock_response)

        response = await self.client._request("GET", "https://example.com")

        assert response == mock_response

    @pytest.mark.asyncio
    async def test_request_retry_on_timeout(self):
        """Test request retry on timeout."""
        await self.client.open()
        self.client.retries = 2

        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ReadTimeout("Timeout")
            return MagicMock(status_code=200)

        self.client.client.request = mock_request

        response = await self.client._request("GET", "https://example.com")

        assert response is not None
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_request_retry_exhausted(self):
        """Test request when retries exhausted."""
        await self.client.open()
        self.client.retries = 2

        self.client.client.request = AsyncMock(side_effect=httpx.ReadTimeout("Timeout"))

        response = await self.client._request("GET", "https://example.com")

        assert response is None

    @pytest.mark.asyncio
    async def test_request_429_retry(self):
        """Test request retry on 429 status."""
        await self.client.open()
        self.client.retries = 2

        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.status_code = 429
            response.headers = {}
            if call_count < 3:
                return response
            response.status_code = 200
            return response

        self.client.client.request = mock_request

        response = await self.client._request("GET", "https://example.com")

        assert response is not None
        assert response.status_code == 200
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_request_429_with_retry_after(self):
        """Test request 429 handling with Retry-After header."""
        await self.client.open()
        self.client.retries = 2

        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.status_code = 429
            response.headers = {"Retry-After": "1"}
            if call_count < 2:
                return response
            response.status_code = 200
            return response

        self.client.client.request = mock_request

        response = await self.client._request("GET", "https://example.com")

        assert response is not None

    @pytest.mark.asyncio
    async def test_request_429_final_attempt(self):
        """Test that 429 on final attempt returns response."""
        await self.client.open()
        self.client.retries = 1

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}
        self.client.client.request = AsyncMock(return_value=mock_response)

        response = await self.client._request("GET", "https://example.com")

        assert response is not None
        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_request_unexpected_error(self):
        """Test request with unexpected error."""
        await self.client.open()
        self.client.client.request = AsyncMock(side_effect=ValueError("Unexpected"))

        response = await self.client._request("GET", "https://example.com")

        assert response is None

    @pytest.mark.asyncio
    async def test_request_lazy_open(self):
        """Test that request opens client if not opened."""
        self.client.client = None
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("nyx.core.http_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.request = AsyncMock(return_value=mock_response)

            response = await self.client._request("GET", "https://example.com")

            assert response is not None
            mock_client_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self):
        """Test client closing."""
        await self.client.open()
        self.client.client.aclose = AsyncMock()

        await self.client.close()

        self.client.client.aclose.assert_called_once()
        assert self.client.client is None

    @pytest.mark.asyncio
    async def test_close_no_client(self):
        """Test closing when client not opened."""
        self.client.client = None

        await self.client.close()

        # Should not raise

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff timing."""
        await self.client.open()
        self.client.retries = 3
        self.client.backoff_factor = 0.1

        call_times = []

        async def mock_request(*args, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 3:
                raise httpx.ReadTimeout("Timeout")
            return MagicMock(status_code=200)

        self.client.client.request = mock_request

        await self.client._request("GET", "https://example.com")

        # Verify backoff occurred (times should be increasing)
        if len(call_times) >= 2:
            assert call_times[1] > call_times[0]

