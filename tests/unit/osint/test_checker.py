"""Tests for platform checker implementations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from nyx.models.platform import Platform, PlatformCategory
from nyx.osint.checker import StatusCodeChecker, RegexChecker


class TestStatusCodeChecker:
    """Test StatusCodeChecker functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.platform = Platform(
            name="TestPlatform",
            url="https://test.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            search_url="https://test.com/{username}",
            detection_method="status_code",
            exists_status_code=200,
            not_exists_status_code=404,
        )

    @pytest.mark.asyncio
    async def test_check_found(self):
        """Test checker when user is found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://test.com/testuser"
        mock_response.text = "testuser profile"

        checker = StatusCodeChecker(self.platform)
        with patch.object(checker, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await checker.check("testuser")

            assert result is not None
            assert result["found"] is True
            assert result["url"] == "https://test.com/testuser"
            assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_check_not_found(self):
        """Test checker when user is not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.url = "https://test.com/testuser"

        checker = StatusCodeChecker(self.platform)
        with patch.object(checker, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await checker.check("testuser")

            assert result is not None
            assert result["found"] is False
            assert result["url"] is None

    @pytest.mark.asyncio
    async def test_check_no_response(self):
        """Test checker when request fails."""
        checker = StatusCodeChecker(self.platform)
        with patch.object(checker, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = None

            result = await checker.check("testuser")

            assert result is None

    @pytest.mark.asyncio
    async def test_check_false_positive_homepage_redirect(self):
        """Test false positive detection for homepage redirect."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://test.com/"  # Redirected to homepage
        mock_response.text = "Welcome to test.com"

        checker = StatusCodeChecker(self.platform)
        with patch.object(checker, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await checker.check("testuser")

            assert result is not None
            assert result["found"] is False  # Should be rejected as false positive

    @pytest.mark.asyncio
    async def test_check_false_positive_username_not_in_url(self):
        """Test false positive detection when username not in final URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://test.com/search?q=something"
        mock_response.text = "Search results"

        checker = StatusCodeChecker(self.platform)
        with patch.object(checker, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await checker.check("testuser")

            assert result is not None
            assert result["found"] is False  # Should be rejected

    @pytest.mark.asyncio
    async def test_check_false_positive_not_found_content(self):
        """Test false positive detection for 'not found' content."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://test.com/testuser"
        mock_response.text = "User not found on this platform"

        checker = StatusCodeChecker(self.platform)
        with patch.object(checker, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await checker.check("testuser")

            assert result is not None
            assert result["found"] is False  # Should be rejected

    @pytest.mark.asyncio
    async def test_check_valid_profile(self):
        """Test that valid profile passes validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://test.com/testuser"
        mock_response.text = "This is testuser's profile page"

        checker = StatusCodeChecker(self.platform)
        with patch.object(checker, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await checker.check("testuser")

            assert result is not None
            assert result["found"] is True

    @pytest.mark.asyncio
    async def test_check_with_http_client(self):
        """Test checker with shared HTTP client."""
        mock_http_client = MagicMock()
        mock_http_client._request = AsyncMock()

        checker = StatusCodeChecker(self.platform, http_client=mock_http_client)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://test.com/testuser"
        mock_response.text = "testuser"
        mock_http_client._request.return_value = mock_response

        result = await checker.check("testuser")

        assert result is not None
        mock_http_client._request.assert_called_once()


class TestRegexChecker:
    """Test RegexChecker functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.platform = Platform(
            name="TestPlatform",
            url="https://test.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            search_url="https://test.com/{username}",
            detection_method="regex",
            exists_pattern=r"profile.*found",
            not_exists_pattern=r"user.*not.*found",
        )

    @pytest.mark.asyncio
    async def test_check_found_by_pattern(self):
        """Test checker when pattern matches."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "This is a profile found page"

        checker = RegexChecker(self.platform)
        with patch.object(checker, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await checker.check("testuser")

            assert result is not None
            assert result["found"] is True

    @pytest.mark.asyncio
    async def test_check_not_found_by_pattern(self):
        """Test checker when not found pattern matches."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User not found on this platform"

        checker = RegexChecker(self.platform)
        with patch.object(checker, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await checker.check("testuser")

            assert result is not None
            assert result["found"] is False

    @pytest.mark.asyncio
    async def test_check_no_response(self):
        """Test checker when request fails."""
        checker = RegexChecker(self.platform)
        with patch.object(checker, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = None

            result = await checker.check("testuser")

            assert result is None

    @pytest.mark.asyncio
    async def test_check_default_200(self):
        """Test checker defaults to 200 = found when no patterns."""
        platform = Platform(
            name="TestPlatform",
            url="https://test.com",
            category=PlatformCategory.SOCIAL_MEDIA,
            search_url="https://test.com/{username}",
            detection_method="regex",
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Some content"

        checker = RegexChecker(platform)
        with patch.object(checker, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await checker.check("testuser")

            assert result is not None
            assert result["found"] is True

