"""Email intelligence gathering and validation."""

import asyncio
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from nyx.core.http_client import HTTPClient
from nyx.core.logger import get_logger
from nyx.core.cache import get_cache

logger = get_logger(__name__)


@dataclass
class EmailResult:
    """Email intelligence result."""

    email: str
    valid: bool
    exists: bool
    breached: bool
    breach_count: int
    breaches: List[str]
    providers: List[str]
    disposable: bool
    reputation_score: float
    online_profiles: Dict[str, str]
    metadata: Dict[str, Any]
    checked_at: datetime


class EmailIntelligence:
    """Email intelligence gathering service."""

    DISPOSABLE_DOMAINS = {
        "tempmail.com",
        "guerrillamail.com",
        "10minutemail.com",
        "mailinator.com",
        "throwaway.email",
        "getnada.com",
        "maildrop.cc",
        "tempr.email",
        "sharklasers.com",
        "trashmail.com",
    }

    EMAIL_PROVIDERS = {
        "gmail.com": "Google Gmail",
        "yahoo.com": "Yahoo Mail",
        "outlook.com": "Microsoft Outlook",
        "hotmail.com": "Microsoft Hotmail",
        "icloud.com": "Apple iCloud",
        "protonmail.com": "ProtonMail",
        "aol.com": "AOL Mail",
        "mail.com": "Mail.com",
        "zoho.com": "Zoho Mail",
        "yandex.com": "Yandex Mail",
    }

    def __init__(self) -> None:
        """Initialize email intelligence service."""
        self.http_client = HTTPClient()
        self.cache = get_cache()

    def validate_email(self, email: str) -> bool:
        """Validate email format.

        Args:
            email: Email address to validate

        Returns:
            True if valid format, False otherwise
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def is_disposable(self, email: str) -> bool:
        """Check if email is from disposable provider.

        Args:
            email: Email address to check

        Returns:
            True if disposable, False otherwise
        """
        domain = email.split("@")[-1].lower()
        return domain in self.DISPOSABLE_DOMAINS

    def get_provider(self, email: str) -> Optional[str]:
        """Get email provider name.

        Args:
            email: Email address

        Returns:
            Provider name or None
        """
        domain = email.split("@")[-1].lower()
        return self.EMAIL_PROVIDERS.get(domain)

    async def check_breach(self, email: str) -> Dict[str, Any]:
        """Check if email appears in known data breaches.

        Args:
            email: Email address to check

        Returns:
            Breach information
        """
        cache_key = f"email_breach:{email}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        result = {
            "breached": False,
            "breach_count": 0,
            "breaches": [],
            "sources": [],
        }

        try:
            headers = {
                "User-Agent": "Nyx-OSINT/0.1.0",
            }
            response = await self.http_client.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                headers=headers,
                timeout=10,
            )

            if response.status == 200:
                data = await response.json()
                result["breached"] = True
                result["breach_count"] = len(data)
                result["breaches"] = [breach.get("Name", "") for breach in data]
                result["sources"] = ["HaveIBeenPwned"]
            elif response.status == 404:
                result["breached"] = False
        except Exception as e:
            logger.warning(f"Breach check failed for {email}: {e}")

        await self.cache.set(cache_key, result, ttl=86400)
        return result

    async def check_email_services(self, email: str) -> List[str]:
        """Check which services email is registered with.

        Args:
            email: Email address

        Returns:
            List of services
        """
        services = []

        checks = {
            "google": self._check_google,
            "twitter": self._check_twitter,
            "github": self._check_github,
            "instagram": self._check_instagram,
            "spotify": self._check_spotify,
        }

        tasks = [check(email) for check in checks.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for service, result in zip(checks.keys(), results):
            if isinstance(result, bool) and result:
                services.append(service)

        return services

    async def _check_google(self, email: str) -> bool:
        """Check if email is registered with Google."""
        try:
            response = await self.http_client.post(
                "https://accounts.google.com/_/lookup/accountlookup",
                json={"email": email},
                timeout=10,
            )
            return response.status == 200
        except Exception:
            return False

    async def _check_twitter(self, email: str) -> bool:
        """Check if email is registered with Twitter."""
        try:
            response = await self.http_client.post(
                "https://api.twitter.com/i/users/email_available.json",
                json={"email": email},
                timeout=10,
            )
            data = await response.json()
            return not data.get("valid", True)
        except Exception:
            return False

    async def _check_github(self, email: str) -> bool:
        """Check if email is registered with GitHub."""
        try:
            response = await self.http_client.get(
                f"https://api.github.com/search/users?q={email}+in:email",
                timeout=10,
            )
            data = await response.json()
            return data.get("total_count", 0) > 0
        except Exception:
            return False

    async def _check_instagram(self, email: str) -> bool:
        """Check if email is registered with Instagram."""
        try:
            response = await self.http_client.post(
                "https://www.instagram.com/accounts/web_create_ajax/attempt/",
                data={"email": email},
                timeout=10,
            )
            data = await response.json()
            return data.get("email_is_taken", False)
        except Exception:
            return False

    async def _check_spotify(self, email: str) -> bool:
        """Check if email is registered with Spotify."""
        try:
            response = await self.http_client.get(
                f"https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={email}",
                timeout=10,
            )
            data = await response.json()
            return data.get("status", 0) == 20
        except Exception:
            return False

    async def search_online_profiles(self, email: str) -> Dict[str, str]:
        """Search for online profiles created with this email.

        Args:
            email: Email address to search for

        Returns:
            Dictionary of platform names to profile URLs
        """
        from nyx.osint.search import SearchService

        profiles = {}

        # Use the username search service to look for email-based profiles
        search_service = SearchService()

        try:
            # Extract username from email (part before @)
            username = email.split('@')[0]

            # Search for username matches
            results = await search_service.search_username(
                username=username,
                exclude_nsfw=True,
                timeout=60
            )

            for platform_name, result in results.items():
                if result.get('found'):
                    profiles[platform_name] = result.get('url', '')

            # Also try searching with the full email address on select platforms
            email_platforms = ['gravatar', 'github', 'about.me']
            for platform_name in email_platforms:
                try:
                    platform_results = await search_service.search_username(
                        username=email,
                        platforms=[platform_name],
                        timeout=10
                    )
                    if platform_results.get(platform_name, {}).get('found'):
                        profiles[platform_name] = platform_results[platform_name].get('url', '')
                except Exception as platform_error:
                    logger.debug(
                        f"Failed to check {platform_name} for email {email}: {platform_error}",
                        exc_info=False
                    )
                    # Continue with other platforms
                    continue

        except Exception as e:
            logger.debug(f"Profile search failed for {email}: {e}")
        finally:
            await search_service.aclose()

        return profiles

    def calculate_reputation(
        self, breached: bool, breach_count: int, disposable: bool, provider: Optional[str]
    ) -> float:
        """Calculate email reputation score.

        Args:
            breached: Whether email has been breached
            breach_count: Number of breaches
            disposable: Whether email is disposable
            provider: Email provider name

        Returns:
            Reputation score (0-100)
        """
        score = 100.0

        if disposable:
            score -= 50.0

        if breached:
            score -= min(breach_count * 5, 30)

        if not provider:
            score -= 10.0

        return max(0.0, score)

    async def investigate(self, email: str, search_profiles: bool = False) -> EmailResult:
        """Perform comprehensive email investigation.

        Args:
            email: Email address to investigate
            search_profiles: Whether to search for online profiles (slower but more thorough)

        Returns:
            Email intelligence result
        """
        if not self.validate_email(email):
            return EmailResult(
                email=email,
                valid=False,
                exists=False,
                breached=False,
                breach_count=0,
                breaches=[],
                providers=[],
                disposable=False,
                reputation_score=0.0,
                online_profiles={},
                metadata={},
                checked_at=datetime.now(),
            )

        disposable = self.is_disposable(email)
        provider = self.get_provider(email)

        # Concurrent lookups
        breach_task = self.check_breach(email)
        services_task = self.check_email_services(email)

        # Conditional profile search
        if search_profiles:
            profiles_task = self.search_online_profiles(email)
            breach_info, services, online_profiles = await asyncio.gather(
                breach_task,
                services_task,
                profiles_task,
                return_exceptions=True
            )
            if isinstance(online_profiles, Exception):
                online_profiles = {}
        else:
            breach_info, services = await asyncio.gather(
                breach_task,
                services_task,
                return_exceptions=True
            )
            online_profiles = {}

        # Handle exceptions
        if isinstance(breach_info, Exception):
            breach_info = {"breached": False, "breach_count": 0, "breaches": [], "sources": []}
        if isinstance(services, Exception):
            services = []

        providers = services.copy()
        if provider:
            providers.append(provider)

        reputation = self.calculate_reputation(
            breached=breach_info["breached"],
            breach_count=breach_info["breach_count"],
            disposable=disposable,
            provider=provider,
        )

        return EmailResult(
            email=email,
            valid=True,
            exists=len(services) > 0,
            breached=breach_info["breached"],
            breach_count=breach_info["breach_count"],
            breaches=breach_info["breaches"],
            providers=providers,
            disposable=disposable,
            reputation_score=reputation,
            online_profiles=online_profiles,
            metadata={
                "domain": email.split("@")[-1],
                "provider": provider,
                "breach_sources": breach_info.get("sources", []),
                "profile_search_enabled": search_profiles,
            },
            checked_at=datetime.now(),
        )
