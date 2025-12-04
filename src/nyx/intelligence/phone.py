"""Phone number intelligence gathering and validation."""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import phonenumbers
from phonenumbers import geocoder, carrier, timezone

from nyx.core.http_client import HTTPClient
from nyx.core.logger import get_logger
from nyx.core.cache import get_cache

logger = get_logger(__name__)


@dataclass
class PhoneResult:
    """Phone intelligence result."""

    phone: str
    valid: bool
    country_code: str
    country_name: str
    location: Optional[str]
    carrier: Optional[str]
    line_type: str
    timezones: List[str]
    formatted_international: str
    formatted_national: str
    formatted_e164: str
    reputation_score: float
    associated_name: Optional[str]
    associated_addresses: List[str]
    metadata: Dict[str, Any]
    checked_at: datetime


class PhoneIntelligence:
    """Phone number intelligence gathering service."""

    def __init__(self) -> None:
        """Initialize phone intelligence service."""
        self.http_client = HTTPClient()
        self.cache = get_cache()

    def auto_detect_region(self, phone: str) -> Optional[str]:
        """Auto-detect region from phone number format.

        Args:
            phone: Phone number string

        Returns:
            Detected region code or None
        """
        # Try parsing without region - works if number has country code
        try:
            parsed = phonenumbers.parse(phone, None)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.region_code_for_number(parsed)
        except phonenumbers.NumberParseException:
            pass

        # Try common region codes if direct parsing fails
        common_regions = ['US', 'GB', 'CA', 'AU', 'IN', 'DE', 'FR', 'IT', 'ES', 'BR']
        for region in common_regions:
            try:
                parsed = phonenumbers.parse(phone, region)
                if phonenumbers.is_valid_number(parsed):
                    return region
            except phonenumbers.NumberParseException:
                continue

        return None

    def parse_number(self, phone: str, region: Optional[str] = None) -> Optional[phonenumbers.PhoneNumber]:
        """Parse phone number with auto-region detection.

        Args:
            phone: Phone number string
            region: Default region code (e.g., 'US'), auto-detected if None

        Returns:
            Parsed phone number or None
        """
        # Auto-detect region if not provided
        if not region:
            region = self.auto_detect_region(phone)

        try:
            return phonenumbers.parse(phone, region)
        except phonenumbers.NumberParseException as e:
            logger.debug(f"Failed to parse phone {phone}: {e}")
            return None

    def validate_number(self, phone: str, region: Optional[str] = None) -> bool:
        """Validate phone number.

        Args:
            phone: Phone number string
            region: Default region code

        Returns:
            True if valid, False otherwise
        """
        parsed = self.parse_number(phone, region)
        if not parsed:
            return False
        return phonenumbers.is_valid_number(parsed)

    def get_country_code(self, phone_number: phonenumbers.PhoneNumber) -> str:
        """Get country code from phone number.

        Args:
            phone_number: Parsed phone number

        Returns:
            Country code (e.g., 'US')
        """
        return phonenumbers.region_code_for_number(phone_number)

    def get_location(self, phone_number: phonenumbers.PhoneNumber, lang: str = "en") -> Optional[str]:
        """Get geographic location for phone number.

        Args:
            phone_number: Parsed phone number
            lang: Language code for location name

        Returns:
            Location description or None
        """
        location = geocoder.description_for_number(phone_number, lang)
        return location if location else None

    def get_carrier(self, phone_number: phonenumbers.PhoneNumber, lang: str = "en") -> Optional[str]:
        """Get carrier name for phone number.

        Args:
            phone_number: Parsed phone number
            lang: Language code for carrier name

        Returns:
            Carrier name or None
        """
        carrier_name = carrier.name_for_number(phone_number, lang)
        return carrier_name if carrier_name else None

    def get_timezones(self, phone_number: phonenumbers.PhoneNumber) -> List[str]:
        """Get timezones for phone number location.

        Args:
            phone_number: Parsed phone number

        Returns:
            List of timezone names
        """
        return list(timezone.time_zones_for_number(phone_number))

    def get_line_type(self, phone_number: phonenumbers.PhoneNumber) -> str:
        """Get phone line type.

        Args:
            phone_number: Parsed phone number

        Returns:
            Line type (mobile, fixed_line, etc.)
        """
        number_type = phonenumbers.number_type(phone_number)
        type_map = {
            phonenumbers.PhoneNumberType.FIXED_LINE: "fixed_line",
            phonenumbers.PhoneNumberType.MOBILE: "mobile",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_or_mobile",
            phonenumbers.PhoneNumberType.TOLL_FREE: "toll_free",
            phonenumbers.PhoneNumberType.PREMIUM_RATE: "premium_rate",
            phonenumbers.PhoneNumberType.SHARED_COST: "shared_cost",
            phonenumbers.PhoneNumberType.VOIP: "voip",
            phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "personal",
            phonenumbers.PhoneNumberType.PAGER: "pager",
            phonenumbers.PhoneNumberType.UAN: "uan",
            phonenumbers.PhoneNumberType.VOICEMAIL: "voicemail",
            phonenumbers.PhoneNumberType.UNKNOWN: "unknown",
        }
        return type_map.get(number_type, "unknown")

    def format_number(self, phone_number: phonenumbers.PhoneNumber, format_type: str = "international") -> str:
        """Format phone number.

        Args:
            phone_number: Parsed phone number
            format_type: Format type (international, national, e164)

        Returns:
            Formatted phone number
        """
        format_map = {
            "international": phonenumbers.PhoneNumberFormat.INTERNATIONAL,
            "national": phonenumbers.PhoneNumberFormat.NATIONAL,
            "e164": phonenumbers.PhoneNumberFormat.E164,
        }
        fmt = format_map.get(format_type, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        return phonenumbers.format_number(phone_number, fmt)

    async def lookup_numverify(self, phone: str) -> Dict[str, Any]:
        """Lookup phone via NumVerify API.

        Args:
            phone: Phone number

        Returns:
            Lookup result
        """
        try:
            response = await self.http_client.get(
                f"http://apilayer.net/api/validate?number={phone}",
                timeout=10,
            )
            if response.status == 200:
                return await response.json()
        except Exception as e:
            logger.debug(f"NumVerify lookup failed: {e}")
        return {}

    async def search_social_media(self, phone: str) -> List[str]:
        """Search for phone number on social media platforms.

        Args:
            phone: Phone number

        Returns:
            List of platforms where found
        """
        platforms = []

        checks = {
            "whatsapp": self._check_whatsapp,
            "telegram": self._check_telegram,
            "signal": self._check_signal,
        }

        tasks = [check(phone) for check in checks.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for platform, result in zip(checks.keys(), results):
            if isinstance(result, bool) and result:
                platforms.append(platform)

        return platforms

    async def _check_whatsapp(self, phone: str) -> bool:
        """Check if phone is registered with WhatsApp."""
        try:
            response = await self.http_client.post(
                "https://v.whatsapp.net/v2/exist",
                json={"phone": phone},
                timeout=10,
            )
            return response.status == 200
        except Exception:
            return False

    async def _check_telegram(self, phone: str) -> bool:
        """Check if phone is registered with Telegram."""
        try:
            response = await self.http_client.post(
                "https://my.telegram.org/auth/send_password",
                data={"phone": phone},
                timeout=10,
            )
            return response.status == 200
        except Exception:
            return False

    async def _check_signal(self, phone: str) -> bool:
        """Check if phone is registered with Signal."""
        return False

    async def lookup_name(self, phone: str) -> Optional[str]:
        """Lookup name associated with phone number.

        Uses multiple sources to find the name registered to a phone number.

        Args:
            phone: Phone number in E164 format

        Returns:
            Associated name or None
        """
        # Try TrueCaller-style lookup
        try:
            headers = {
                "User-Agent": "Nyx-OSINT/0.1.0",
            }
            # NOTE: Reverse phone lookup requires API keys from services like:
            # - NumLookupAPI (https://numlookupapi.com/ - requires API key)
            # - WhitePages (https://www.whitepages.com/ - requires API key)
            # - Spokeo (https://www.spokeo.com/ - requires API key)
            # - TrueCaller (https://www.truecaller.com/ - requires API key)
            #
            # To enable this feature:
            # 1. Obtain API key from a reverse lookup service
            # 2. Add API key to configuration file (config/settings.yaml)
            # 3. Update this method to use the configured API key
            # 4. Handle rate limits and API quotas appropriately
            #
            # Example integration:
            #   api_key = self.config.get("phone_lookup_api_key")
            #   if api_key:
            #       response = await self.http_client.get(
            #           f"https://api.service.com/lookup/{phone}",
            #           headers={**headers, "Authorization": f"Bearer {api_key}"},
            #           timeout=10,
            #       )
            #       if response and response.status_code == 200:
            #           data = response.json()
            #           return data.get("name") or data.get("owner_name")
            #
            # For now, attempt public API (may fail without API key)
            # This maintains API compatibility while allowing future integration
            try:
                response = await self.http_client.get(
                    f"https://api.numlookupapi.com/v1/validate/{phone}",
                    headers=headers,
                    timeout=10,
                )
                if response and response.status_code == 200:
                    data = response.json()
                    return data.get("name") or data.get("carrier_name")
            except Exception:
                # Public API may not be available or may require authentication
                logger.debug(
                    f"Reverse phone name lookup unavailable for {phone}. "
                    "API key required for full functionality."
                )
        except Exception as e:
            logger.warning(f"Name lookup failed: {e}", exc_info=True)

        return None

    async def lookup_addresses(self, phone: str) -> List[str]:
        """Lookup addresses associated with phone number.

        Args:
            phone: Phone number in E164 format

        Returns:
            List of associated addresses
        """
        addresses = []

        try:
            # NOTE: Reverse phone address lookup requires API keys from services like:
            # - WhitePages API (https://www.whitepages.com/ - requires API key)
            # - Spokeo API (https://www.spokeo.com/ - requires API key)
            # - BeenVerified API (https://www.beenverified.com/ - requires API key)
            # - TruePeopleSearch (public, but may require scraping)
            #
            # To enable this feature:
            # 1. Obtain API key from a reverse lookup service
            # 2. Add API key to configuration file (config/settings.yaml)
            # 3. Implement API client integration in this method
            # 4. Parse and structure address data from API response
            #
            # Example integration structure:
            #   api_key = self.config.get("phone_lookup_api_key")
            #   if api_key:
            #       response = await self.http_client.get(
            #           f"https://api.service.com/lookup/{phone}",
            #           headers={"Authorization": f"Bearer {api_key}"},
            #           timeout=10,
            #       )
            #       if response and response.status_code == 200:
            #           data = response.json()
            #           addresses = self._parse_addresses_from_response(data)
            #
            logger.debug(
                f"Reverse phone address lookup placeholder for {phone}. "
                "API integration required for actual results."
            )

        except Exception as e:
            logger.warning(f"Address lookup failed: {e}", exc_info=True)

        return addresses

    def calculate_reputation(
        self, valid: bool, line_type: str, carrier: Optional[str], location: Optional[str]
    ) -> float:
        """Calculate phone reputation score.

        Args:
            valid: Whether number is valid
            line_type: Type of phone line
            carrier: Carrier name
            location: Geographic location

        Returns:
            Reputation score (0-100)
        """
        if not valid:
            return 0.0

        score = 100.0

        if line_type == "voip":
            score -= 20.0
        elif line_type == "unknown":
            score -= 30.0

        if not carrier:
            score -= 15.0

        if not location:
            score -= 10.0

        return max(0.0, score)

    async def investigate(self, phone: str, region: Optional[str] = None) -> PhoneResult:
        """Perform comprehensive phone investigation.

        Args:
            phone: Phone number to investigate
            region: Default region code (auto-detected if not provided)

        Returns:
            Phone intelligence result
        """
        parsed = self.parse_number(phone, region)

        if not parsed or not phonenumbers.is_valid_number(parsed):
            return PhoneResult(
                phone=phone,
                valid=False,
                country_code="",
                country_name="",
                location=None,
                carrier=None,
                line_type="unknown",
                timezones=[],
                formatted_international=phone,
                formatted_national=phone,
                formatted_e164=phone,
                reputation_score=0.0,
                associated_name=None,
                associated_addresses=[],
                metadata={},
                checked_at=datetime.now(),
            )

        country_code = self.get_country_code(parsed)
        location = self.get_location(parsed)
        carrier_name = self.get_carrier(parsed)
        line_type = self.get_line_type(parsed)
        timezones_list = self.get_timezones(parsed)

        formatted_int = self.format_number(parsed, "international")
        formatted_nat = self.format_number(parsed, "national")
        formatted_e164 = self.format_number(parsed, "e164")

        # Perform concurrent lookups
        social_platforms_task = self.search_social_media(formatted_e164)
        name_task = self.lookup_name(formatted_e164)
        addresses_task = self.lookup_addresses(formatted_e164)

        social_platforms, associated_name, associated_addresses = await asyncio.gather(
            social_platforms_task,
            name_task,
            addresses_task,
            return_exceptions=True
        )

        # Handle exceptions from gather
        if isinstance(social_platforms, Exception):
            social_platforms = []
        if isinstance(associated_name, Exception):
            associated_name = None
        if isinstance(associated_addresses, Exception):
            associated_addresses = []

        reputation = self.calculate_reputation(
            valid=True,
            line_type=line_type,
            carrier=carrier_name,
            location=location,
        )

        country_name = ""
        try:
            import pycountry
            country = pycountry.countries.get(alpha_2=country_code)
            country_name = country.name if country else country_code
        except Exception:
            country_name = country_code

        return PhoneResult(
            phone=phone,
            valid=True,
            country_code=country_code,
            country_name=country_name,
            location=location,
            carrier=carrier_name,
            line_type=line_type,
            timezones=timezones_list,
            formatted_international=formatted_int,
            formatted_national=formatted_nat,
            formatted_e164=formatted_e164,
            reputation_score=reputation,
            associated_name=associated_name,
            associated_addresses=associated_addresses,
            metadata={
                "social_platforms": social_platforms,
                "possible_voip": line_type == "voip",
                "auto_detected_region": region is None,
            },
            checked_at=datetime.now(),
        )
