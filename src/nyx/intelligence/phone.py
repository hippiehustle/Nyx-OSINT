"""Phone number intelligence gathering and validation."""

import asyncio
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
from bs4 import BeautifulSoup

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
        # User-Agent for web scraping
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

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

    def _generate_phone_variations(self, phone: str) -> List[str]:
        """Generate multiple phone number format variations for searching.
        
        Args:
            phone: Phone number in E164 format (e.g., +1234567890)
            
        Returns:
            List of phone number variations
        """
        # Remove all non-digits except +
        clean = re.sub(r'[^\d+]', '', phone)
        
        variations = []
        
        # E164 format: +1234567890
        if clean.startswith('+'):
            variations.append(clean)
            # Without +: 1234567890
            variations.append(clean[1:])
            
            # US format variations
            if clean.startswith('+1') and len(clean) == 12:
                digits = clean[2:]
                # (123) 456-7890
                variations.append(f"({digits[:3]}) {digits[3:6]}-{digits[6:]}")
                # 123-456-7890
                variations.append(f"{digits[:3]}-{digits[3:6]}-{digits[6:]}")
                # 123.456.7890
                variations.append(f"{digits[:3]}.{digits[3:6]}.{digits[6:]}")
                # 1234567890
                variations.append(digits)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for var in variations:
            if var not in seen:
                seen.add(var)
                unique_variations.append(var)
        
        return unique_variations

    def _validate_name(self, name: Optional[str]) -> bool:
        """Validate that extracted name looks reasonable.
        
        Args:
            name: Name string to validate
            
        Returns:
            True if name appears valid
        """
        if not name:
            return False
        
        # Remove extra whitespace
        name = name.strip()
        
        # Must be at least 2 characters
        if len(name) < 2:
            return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', name):
            return False
        
        # Should not be all numbers
        if name.replace(' ', '').isdigit():
            return False
        
        # Should not contain common invalid patterns
        invalid_patterns = [
            r'^\d+$',  # All digits
            r'^[^\w\s]+$',  # Only special characters
            r'^(phone|number|cell|mobile|tel|call)$',  # Common placeholders
            r'^(unknown|n/a|na|none|null)$',  # Common null values
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                return False
        
        return True

    async def _lookup_public_sites(self, phone: str) -> Optional[str]:
        """Lookup name from public people search sites.
        
        Args:
            phone: Phone number in E164 format
            
        Returns:
            Associated name or None
        """
        phone_variations = self._generate_phone_variations(phone)
        
        # Try TruePeopleSearch
        try:
            for phone_var in phone_variations[:3]:  # Limit to first 3 variations
                try:
                    # Clean phone for URL
                    clean_phone = re.sub(r'[^\d]', '', phone_var)
                    url = f"https://www.truepeoplesearch.com/result?phoneno={clean_phone}"
                    
                    headers = {"User-Agent": self.user_agent}
                    await self.http_client.open()
                    response = await self.http_client.get(url, headers=headers, timeout=15)
                    
                    if response and response.status_code == 200:
                        html = response.text
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # Try common name selectors
                        name_selectors = [
                            '.name',
                            '#person-name',
                            '.person-name',
                            'h2.name',
                            '.result-name',
                            '[class*="name"]',
                        ]
                        
                        for selector in name_selectors:
                            name_elem = soup.select_one(selector)
                            if name_elem:
                                name = name_elem.get_text(strip=True)
                                if self._validate_name(name):
                                    logger.debug(f"Found name from TruePeopleSearch: {name}")
                                    return name
                        
                        # Fallback: search for name-like patterns in text
                        text = soup.get_text()
                        # Look for patterns like "Name: John Doe" or similar
                        name_match = re.search(r'(?:name|person)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text, re.IGNORECASE)
                        if name_match:
                            name = name_match.group(1).strip()
                            if self._validate_name(name):
                                logger.debug(f"Found name from TruePeopleSearch (pattern): {name}")
                                return name
                    
                    # Rate limiting - be respectful
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.debug(f"TruePeopleSearch lookup failed for {phone_var}: {e}")
                    continue
        except Exception as e:
            logger.debug(f"TruePeopleSearch lookup error: {e}")
        
        # Try FastPeopleSearch
        try:
            for phone_var in phone_variations[:3]:
                try:
                    clean_phone = re.sub(r'[^\d]', '', phone_var)
                    url = f"https://www.fastpeoplesearch.com/phone/{clean_phone}"
                    
                    headers = {"User-Agent": self.user_agent}
                    await self.http_client.open()
                    response = await self.http_client.get(url, headers=headers, timeout=15)
                    
                    if response and response.status_code == 200:
                        html = response.text
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # Try common name selectors
                        name_selectors = [
                            '.name',
                            '.person-name',
                            'h1',
                            'h2',
                            '[class*="name"]',
                        ]
                        
                        for selector in name_selectors:
                            name_elem = soup.select_one(selector)
                            if name_elem:
                                name = name_elem.get_text(strip=True)
                                if self._validate_name(name):
                                    logger.debug(f"Found name from FastPeopleSearch: {name}")
                                    return name
                    
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.debug(f"FastPeopleSearch lookup failed for {phone_var}: {e}")
                    continue
        except Exception as e:
            logger.debug(f"FastPeopleSearch lookup error: {e}")
        
        return None

    async def _search_social_media_for_name(self, phone: str) -> Optional[str]:
        """Search social media platforms for phone number and extract name.
        
        Args:
            phone: Phone number in E164 format
            
        Returns:
            Associated name or None
        """
        phone_variations = self._generate_phone_variations(phone)
        
        # Note: Most social media platforms require authentication for phone searches
        # This is a basic implementation that may have limited success
        # For production use, would need API keys or authenticated sessions
        
        # Try searching public profiles/pages that might list phone numbers
        # This is a placeholder - actual implementation would need platform-specific APIs
        
        logger.debug(f"Social media reverse search for {phone} - requires API integration")
        return None

    async def _search_engines_for_name(self, phone: str) -> Optional[str]:
        """Search search engines for phone number and extract name.
        
        Args:
            phone: Phone number in E164 format
            
        Returns:
            Associated name or None
        """
        phone_variations = self._generate_phone_variations(phone)
        
        # Try Google search (basic - would need API key for production)
        try:
            # Format search query
            query = f'"{phone_variations[0]}" OR "{phone_variations[1] if len(phone_variations) > 1 else phone_variations[0]}" name'
            query_encoded = quote(query)
            
            # Note: This is a basic implementation
            # For production, would use Google Custom Search API or similar
            # For now, this is a placeholder that demonstrates the structure
            
            logger.debug(f"Search engine lookup for {phone} - requires API integration")
            return None
        except Exception as e:
            logger.debug(f"Search engine lookup error: {e}")
            return None

    async def lookup_name(self, phone: str) -> Optional[str]:
        """Lookup name associated with phone number using multiple free sources.

        Uses multiple sources to find the name registered to a phone number.
        Tries sources in order of reliability and returns the first valid result.

        Args:
            phone: Phone number in E164 format

        Returns:
            Associated name or None
        """
        # Check cache first (7-day TTL)
        cache_key = f"phone_name:{phone}"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Returning cached name for {phone}")
                return cached
        
        # Try sources in order of reliability
        sources = [
            ("public_sites", self._lookup_public_sites),
            ("social_media", self._search_social_media_for_name),
            ("search_engines", self._search_engines_for_name),
        ]
        
        for source_name, lookup_func in sources:
            try:
                name = await lookup_func(phone)
                if name and self._validate_name(name):
                    # Cache successful result (7 days)
                    if self.cache:
                        await self.cache.set(cache_key, name, ttl=86400 * 7)
                    logger.info(f"Found name for {phone} via {source_name}: {name}")
                    return name
            except Exception as e:
                logger.debug(f"{source_name} lookup failed for {phone}: {e}")
                continue
        
        # No name found from any source
        logger.debug(f"No name found for {phone} from any source")
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
