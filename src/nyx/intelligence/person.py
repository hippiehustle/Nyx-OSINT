"""Person intelligence gathering and WHOIS lookups."""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from nyx.core.http_client import HTTPClient
from nyx.core.logger import get_logger
from nyx.core.cache import get_cache

logger = get_logger(__name__)


@dataclass
class PersonResult:
    """Person intelligence result."""

    first_name: str
    middle_name: Optional[str]
    last_name: str
    state: Optional[str]
    age: Optional[int]
    age_range: Optional[str]
    addresses: List[str]
    phone_numbers: List[str]
    email_addresses: List[str]
    relatives: List[str]
    associates: List[str]
    social_profiles: Dict[str, str]
    education: List[str]
    employment: List[str]
    metadata: Dict[str, Any]
    checked_at: datetime


class PersonIntelligence:
    """Person intelligence gathering service."""

    def __init__(self) -> None:
        """Initialize person intelligence service."""
        self.http_client = HTTPClient()
        self.cache = get_cache()

    def format_name(self, first: str, middle: Optional[str], last: str) -> str:
        """Format full name.

        Args:
            first: First name
            middle: Middle name or initial (optional)
            last: Last name

        Returns:
            Formatted full name
        """
        if middle:
            return f"{first} {middle} {last}"
        return f"{first} {last}"

    async def search_public_records(
        self, first: str, middle: Optional[str], last: str, state: Optional[str]
    ) -> Dict[str, Any]:
        """Search public records for person information.

        Args:
            first: First name
            middle: Middle name or initial
            last: Last name
            state: State code (e.g., 'CA', 'NY')

        Returns:
            Public records information
        """
        full_name = self.format_name(first, middle, last)
        logger.info(f"Searching public records for: {full_name}")

        records = {
            "addresses": [],
            "phone_numbers": [],
            "age": None,
            "age_range": None,
        }

        # Note: In production, integrate with services like:
        # - TruePeopleSearch
        # - FastPeopleSearch
        # - Whitepages
        # - Spokeo
        # - BeenVerified
        # - PublicRecords.com

        try:
            cache_key = f"person_records:{first}:{last}:{state or 'any'}"
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

            # NOTE: Public records API integration requires API keys from services like:
            # - TruePeopleSearch (https://www.truepeoplesearch.com/)
            # - FastPeopleSearch (https://www.fastpeoplesearch.com/)
            # - Whitepages (https://www.whitepages.com/ - requires API key)
            # - Spokeo (https://www.spokeo.com/ - requires API key)
            # - BeenVerified (https://www.beenverified.com/ - requires API key)
            # - PublicRecords.com (https://www.publicrecords.com/ - requires API key)
            #
            # To enable this feature:
            # 1. Obtain API keys from one or more of these services
            # 2. Add API keys to configuration file (config/settings.yaml)
            # 3. Implement API client integration in this method
            # 4. Handle rate limits and API quotas appropriately
            #
            # Example integration structure:
            #   api_key = self.config.get("public_records_api_key")
            #   if api_key:
            #       response = await self.http_client.get(
            #           f"https://api.service.com/search",
            #           params={"name": full_name, "state": state, "api_key": api_key}
            #       )
            #       if response and response.status_code == 200:
            #           data = response.json()
            #           records = self._parse_public_records_response(data)
            #
            # For now, return empty structure to maintain API compatibility
            logger.debug(
                f"Public records search placeholder: {full_name} "
                f"(state={state or 'any'}). API integration required for actual results."
            )
            await self.cache.set(cache_key, records, ttl=86400)

        except Exception as e:
            logger.warning(f"Public records search failed: {e}", exc_info=True)
            # Return empty structure on error to maintain API compatibility

        return records

    async def search_social_media(
        self, first: str, middle: Optional[str], last: str, state: Optional[str]
    ) -> Dict[str, str]:
        """Search for social media profiles.

        Args:
            first: First name
            middle: Middle name or initial
            last: Last name
            state: State code

        Returns:
            Dictionary of platform names to profile URLs
        """
        from nyx.osint.search import SearchService

        profiles = {}
        search_service = SearchService()

        try:
            # Try various username combinations
            username_variants = [
                f"{first}{last}".lower(),
                f"{first}.{last}".lower(),
                f"{first}_{last}".lower(),
                f"{first[0]}{last}".lower(),
            ]

            if middle:
                username_variants.extend([
                    f"{first}{middle[0]}{last}".lower(),
                    f"{first}.{middle[0]}.{last}".lower(),
                ])

            # Search for each variant
            for username in username_variants[:3]:  # Limit to first 3 variants
                try:
                    results = await search_service.search_username(
                        username=username,
                        exclude_nsfw=True,
                        timeout=30
                    )

                    for platform_name, result in results.items():
                        if result.get('found') and platform_name not in profiles:
                            profiles[platform_name] = result.get('url', '')

                except Exception as e:
                    logger.debug(f"Search failed for username {username}: {e}")
                    continue

        except Exception as e:
            logger.debug(f"Social media search failed: {e}")
        finally:
            await search_service.aclose()

        return profiles

    async def search_professional_networks(
        self, first: str, middle: Optional[str], last: str
    ) -> List[str]:
        """Search professional networks (LinkedIn, Indeed, etc).

        Args:
            first: First name
            middle: Middle name or initial
            last: Last name

        Returns:
            List of employment/education information
        """
        employment = []

        full_name = self.format_name(first, middle, last)

        try:
            # NOTE: Professional network search requires API access or web scraping:
            # - LinkedIn: Requires LinkedIn API access (limited availability)
            # - Indeed: Public search available, but API requires partnership
            # - Glassdoor: Public search available, but API requires partnership
            #
            # To enable this feature:
            # 1. For LinkedIn: Apply for LinkedIn API access (very limited)
            # 2. For Indeed/Glassdoor: Consider web scraping with respect to ToS
            # 3. Add API keys/credentials to configuration if available
            # 4. Implement search logic with proper rate limiting
            #
            # Example integration structure:
            #   linkedin_api_key = self.config.get("linkedin_api_key")
            #   if linkedin_api_key:
            #       results = await self._search_linkedin(full_name, linkedin_api_key)
            #       employment.extend(results)
            #
            # Legal and ethical considerations:
            # - Always respect Terms of Service
            # - Implement rate limiting to avoid overwhelming services
            # - Consider using official APIs when available
            # - Be transparent about data sources in results
            #
            logger.debug(
                f"Professional network search placeholder: {full_name}. "
                "API integration required for actual results."
            )

        except Exception as e:
            logger.warning(f"Professional network search failed: {e}", exc_info=True)

        return employment

    async def search_relatives_associates(
        self, first: str, last: str, addresses: List[str]
    ) -> tuple[List[str], List[str]]:
        """Search for relatives and associates.

        Args:
            first: First name
            last: Last name
            addresses: Known addresses

        Returns:
            Tuple of (relatives, associates)
        """
        relatives = []
        associates = []

        try:
            # NOTE: Relative/associate lookup requires public records API access:
            # - WhitePages API (https://www.whitepages.com/ - requires API key)
            # - Spokeo API (https://www.spokeo.com/ - requires API key)
            # - BeenVerified API (https://www.beenverified.com/ - requires API key)
            # - TruePeopleSearch (public, but may require scraping)
            #
            # To enable this feature:
            # 1. Obtain API keys from public records services
            # 2. Add API keys to configuration file
            # 3. Implement API client integration
            # 4. Parse and structure relative/associate data
            #
            # Example integration structure:
            #   api_key = self.config.get("public_records_api_key")
            #   if api_key and addresses:
            #       for address in addresses:
            #           response = await self.http_client.get(
            #               f"https://api.service.com/relatives",
            #               params={"name": f"{first} {last}", "address": address, "api_key": api_key}
            #           )
            #           if response and response.status_code == 200:
            #               data = response.json()
            #               relatives.extend(data.get("relatives", []))
            #               associates.extend(data.get("associates", []))
            #
            logger.debug(
                f"Relative/associate search placeholder: {first} {last} "
                f"(addresses={len(addresses)}). API integration required for actual results."
            )

        except Exception as e:
            logger.warning(f"Relative/associate search failed: {e}", exc_info=True)

        return relatives, associates

    async def investigate(
        self,
        first_name: str,
        last_name: str,
        middle_name: Optional[str] = None,
        state: Optional[str] = None,
    ) -> PersonResult:
        """Perform comprehensive person investigation.

        Args:
            first_name: First name
            last_name: Last name
            middle_name: Middle name or initial (optional)
            state: State code (optional, e.g., 'CA', 'NY')

        Returns:
            Person intelligence result
        """
        # Concurrent searches
        public_records_task = self.search_public_records(first_name, middle_name, last_name, state)
        social_task = self.search_social_media(first_name, middle_name, last_name, state)
        professional_task = self.search_professional_networks(first_name, middle_name, last_name)

        public_records, social_profiles, employment = await asyncio.gather(
            public_records_task,
            social_task,
            professional_task,
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(public_records, Exception):
            public_records = {"addresses": [], "phone_numbers": [], "age": None, "age_range": None}
        if isinstance(social_profiles, Exception):
            social_profiles = {}
        if isinstance(employment, Exception):
            employment = []

        # Search for relatives/associates if we have addresses
        relatives, associates = [], []
        if public_records.get("addresses"):
            relatives, associates = await self.search_relatives_associates(
                first_name,
                last_name,
                public_records["addresses"]
            )

        return PersonResult(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            state=state,
            age=public_records.get("age"),
            age_range=public_records.get("age_range"),
            addresses=public_records.get("addresses", []),
            phone_numbers=public_records.get("phone_numbers", []),
            email_addresses=public_records.get("email_addresses", []),
            relatives=relatives,
            associates=associates,
            social_profiles=social_profiles,
            education=public_records.get("education", []),
            employment=employment,
            metadata={
                "full_name": self.format_name(first_name, middle_name, last_name),
                "search_state": state,
            },
            checked_at=datetime.now(),
        )
