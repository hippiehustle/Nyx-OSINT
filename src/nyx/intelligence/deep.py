"""Centralized deep investigation orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from nyx.core.logger import get_logger
from nyx.intelligence.email import EmailIntelligence
from nyx.intelligence.person import PersonIntelligence
from nyx.intelligence.phone import PhoneIntelligence
from nyx.intelligence.smart import SmartSearchInput, SmartSearchService
from nyx.osint.search import SearchService

logger = get_logger(__name__)


@dataclass
class DeepInvestigationResult:
    """Result of a deep investigation."""

    query: str
    timestamp: datetime
    username_results: Dict[str, Any] = field(default_factory=dict)
    email_results: Optional[Any] = None
    phone_results: Optional[Any] = None
    person_results: Optional[Any] = None
    smart_results: Optional[Any] = None
    web_results: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeepInvestigationService:
    """Centralized service for deep investigations.

    This service orchestrates multiple intelligence modules to perform
    comprehensive investigations on a target query.
    """

    def __init__(
        self,
        search_service: Optional[SearchService] = None,
        smart_service: Optional[SmartSearchService] = None,
    ):
        """Initialize deep investigation service.

        Args:
            search_service: Optional shared SearchService instance
            smart_service: Optional shared SmartSearchService instance
        """
        self.search_service = search_service or SearchService()
        self._owns_search_service = search_service is None
        self.smart_service = smart_service or SmartSearchService(
            search_service=self.search_service
        )
        self.email_intel = EmailIntelligence()
        self.phone_intel = PhoneIntelligence()
        self.person_intel = PersonIntelligence()

    async def investigate(
        self,
        query: str,
        region: Optional[str] = None,
        timeout: Optional[int] = 120,
        include_smart: bool = True,
        include_web_search: bool = True,
    ) -> DeepInvestigationResult:
        """Perform deep investigation on a query.

        This method:
        - Attempts username search
        - Checks if query is an email and runs email intelligence
        - Checks if query is a phone and runs phone intelligence
        - Attempts person lookup if query looks like a name
        - Optionally runs Smart search for comprehensive analysis
        - Optionally performs web searches

        Args:
            query: Query to investigate
            region: Optional region hint for phone/person searches
            timeout: Search timeout in seconds
            include_smart: Whether to run Smart search
            include_web_search: Whether to perform web searches

        Returns:
            DeepInvestigationResult with all collected intelligence
        """
        logger.info(f"Starting deep investigation: {query}")
        start_time = datetime.utcnow()

        result = DeepInvestigationResult(
            query=query,
            timestamp=start_time,
            metadata={
                "region": region,
                "timeout": timeout,
                "include_smart": include_smart,
                "include_web_search": include_web_search,
            },
        )

        query_clean = query.strip()

        # 1. Username search (always try)
        try:
            logger.debug("Running username search")
            username_results = await self.search_service.search_username(
                username=query_clean,
                exclude_nsfw=True,
                timeout=timeout or 60,
            )
            result.username_results = {
                k: v for k, v in username_results.items() if v.get("found")
            }
            logger.debug(f"Username search found {len(result.username_results)} matches")
        except Exception as e:
            logger.debug(f"Username search failed: {e}")

        # 2. Email intelligence (if query looks like email)
        if "@" in query_clean and "." in query_clean:
            try:
                logger.debug("Running email intelligence")
                email_result = await self.email_intel.investigate(
                    query_clean, search_profiles=True
                )
                result.email_results = email_result
                logger.debug("Email intelligence complete")
            except Exception as e:
                logger.debug(f"Email intelligence failed: {e}")

        # 3. Phone intelligence (if query looks like phone)
        if self._looks_like_phone(query_clean):
            try:
                logger.debug("Running phone intelligence")
                phone_result = await self.phone_intel.investigate(
                    query_clean, region=region
                )
                result.phone_results = phone_result
                logger.debug("Phone intelligence complete")
            except Exception as e:
                logger.debug(f"Phone intelligence failed: {e}")

        # 4. Person intelligence (if query looks like name)
        if self._looks_like_name(query_clean):
            try:
                logger.debug("Running person intelligence")
                parts = query_clean.split()
                if len(parts) >= 2:
                    person_result = await self.person_intel.investigate(
                        first_name=parts[0],
                        last_name=parts[-1],
                        middle_name=parts[1] if len(parts) == 3 else None,
                        state=region,
                    )
                    result.person_results = person_result
                    logger.debug("Person intelligence complete")
            except Exception as e:
                logger.debug(f"Person intelligence failed: {e}")

        # 5. Smart search (optional, comprehensive)
        if include_smart:
            try:
                logger.debug("Running Smart search")
                smart_input = SmartSearchInput(raw_text=query_clean, region=region)
                smart_result = await self.smart_service.smart_search(
                    smart_input, timeout=timeout, persist_to_db=False
                )
                result.smart_results = smart_result
                result.web_results = smart_result.web_results
                logger.debug("Smart search complete")
            except Exception as e:
                logger.debug(f"Smart search failed: {e}")

        # 6. Web search (if not already done by Smart search)
        if include_web_search and not include_smart:
            try:
                logger.debug("Running web search")
                from nyx.search_engines.implementations import MetaSearchEngine

                meta_search = MetaSearchEngine()
                web_results = await meta_search.search(query_clean, num_results=10)
                result.web_results[query_clean] = web_results
                await meta_search.close()
                logger.debug("Web search complete")
            except Exception as e:
                logger.debug(f"Web search failed: {e}")

        duration = (datetime.utcnow() - start_time).total_seconds()
        result.metadata["duration_seconds"] = duration
        logger.info(f"Deep investigation complete in {duration:.2f}s")

        return result

    async def aclose(self) -> None:
        """Close underlying resources."""
        if self._owns_search_service:
            await self.search_service.aclose()
        await self.smart_service.aclose()

    @staticmethod
    def _looks_like_phone(text: str) -> bool:
        """Check if text looks like a phone number."""
        # Remove common separators
        cleaned = "".join(c for c in text if c.isdigit() or c in "+-()")
        digits = sum(1 for c in cleaned if c.isdigit())
        # Phone numbers typically have 10-15 digits
        return 10 <= digits <= 15

    @staticmethod
    def _looks_like_name(text: str) -> bool:
        """Check if text looks like a person name."""
        # Simple heuristic: 2-4 words, mostly letters, capitalized
        words = text.split()
        if not (2 <= len(words) <= 4):
            return False
        # Check if most words start with capital letter
        capitalized = sum(1 for w in words if w and w[0].isupper())
        return capitalized >= len(words) * 0.7


__all__ = [
    "DeepInvestigationResult",
    "DeepInvestigationService",
    "PlatformCheckerPlugin",
]

