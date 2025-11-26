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
            # Placeholder for public records API integration
            cache_key = f"person_records:{first}:{last}:{state or 'any'}"
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

            # In production, make actual API calls here
            # For now, return empty structure
            await self.cache.set(cache_key, records, ttl=86400)

        except Exception as e:
            logger.debug(f"Public records search failed: {e}")

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
            # Placeholder for LinkedIn, Indeed, Glassdoor searches
            # In production, use APIs or scraping (with respect to ToS)
            pass

        except Exception as e:
            logger.debug(f"Professional network search failed: {e}")

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
            # Placeholder for relative/associate lookup
            # In production, use public records services
            pass

        except Exception as e:
            logger.debug(f"Relative/associate search failed: {e}")

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
