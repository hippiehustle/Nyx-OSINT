"""Tests for phone intelligence module."""

import pytest
from nyx.intelligence.phone import PhoneIntelligence


class TestPhoneIntelligence:
    """Test phone intelligence functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.phone_intel = PhoneIntelligence()

    def test_validate_number_valid(self):
        """Test valid phone validation."""
        assert self.phone_intel.validate_number("+14155552671", "US")
        assert self.phone_intel.validate_number("+442071838750", "GB")

    def test_validate_number_invalid(self):
        """Test invalid phone validation."""
        assert not self.phone_intel.validate_number("123", "US")
        assert not self.phone_intel.validate_number("invalid", "US")

    def test_parse_number(self):
        """Test phone number parsing."""
        parsed = self.phone_intel.parse_number("+14155552671")
        assert parsed is not None

        parsed_invalid = self.phone_intel.parse_number("invalid")
        assert parsed_invalid is None

    def test_get_country_code(self):
        """Test country code extraction."""
        parsed = self.phone_intel.parse_number("+14155552671")
        if parsed:
            country = self.phone_intel.get_country_code(parsed)
            assert country == "US"

    def test_calculate_reputation(self):
        """Test reputation calculation."""
        score1 = self.phone_intel.calculate_reputation(True, "mobile", "Carrier", "US")
        assert score1 == 100.0

        score2 = self.phone_intel.calculate_reputation(True, "voip", None, None)
        assert score2 < 100.0

        score3 = self.phone_intel.calculate_reputation(False, "unknown", None, None)
        assert score3 == 0.0

    @pytest.mark.asyncio
    async def test_investigate_invalid_phone(self):
        """Test investigation of invalid phone."""
        result = await self.phone_intel.investigate("invalid")
        assert not result.valid
        assert result.reputation_score == 0.0
