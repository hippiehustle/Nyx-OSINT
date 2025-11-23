"""Tests for email intelligence module."""

import pytest
from datetime import datetime
from nyx.intelligence.email import EmailIntelligence, EmailResult


class TestEmailIntelligence:
    """Test email intelligence functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.email_intel = EmailIntelligence()

    def test_validate_email_valid(self):
        """Test valid email validation."""
        assert self.email_intel.validate_email("test@example.com")
        assert self.email_intel.validate_email("user.name@domain.co.uk")
        assert self.email_intel.validate_email("test+tag@example.com")

    def test_validate_email_invalid(self):
        """Test invalid email validation."""
        assert not self.email_intel.validate_email("invalid")
        assert not self.email_intel.validate_email("@example.com")
        assert not self.email_intel.validate_email("test@")
        assert not self.email_intel.validate_email("test @example.com")

    def test_is_disposable(self):
        """Test disposable email detection."""
        assert self.email_intel.is_disposable("test@tempmail.com")
        assert self.email_intel.is_disposable("user@guerrillamail.com")
        assert not self.email_intel.is_disposable("test@gmail.com")

    def test_get_provider(self):
        """Test email provider detection."""
        assert self.email_intel.get_provider("test@gmail.com") == "Google Gmail"
        assert self.email_intel.get_provider("test@yahoo.com") == "Yahoo Mail"
        assert self.email_intel.get_provider("test@unknown.com") is None

    def test_calculate_reputation(self):
        """Test reputation calculation."""
        score1 = self.email_intel.calculate_reputation(False, 0, False, "Gmail")
        assert score1 == 100.0

        score2 = self.email_intel.calculate_reputation(True, 3, False, "Gmail")
        assert score2 < 100.0

        score3 = self.email_intel.calculate_reputation(False, 0, True, None)
        assert score3 < 50.0

    @pytest.mark.asyncio
    async def test_investigate_invalid_email(self):
        """Test investigation of invalid email."""
        result = await self.email_intel.investigate("invalid")
        assert not result.valid
        assert result.reputation_score == 0.0
