"""Smart search orchestration for free-form target information.

This module implements a higher-level "Smart search" feature that:

- Accepts free-form information about a target (notes, identifiers, etc.)
- Extracts structured identifiers (usernames, emails, phone numbers, names)
- Runs existing OSINT modules (username search, email/phone/person intelligence)
- Optionally queries web search engines for additional context
- Correlates and scores results to identify high-probability matches
- Optionally persists results to database (Target/TargetProfile/SearchHistory)

The implementation includes refined extraction algorithms and confidence scoring,
with optional database persistence for long-term investigation tracking.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from nyx.analysis.correlation import CorrelationAnalyzer
from nyx.core.database import get_database_manager
from nyx.core.logger import get_logger
from nyx.core.types import Profile
from nyx.intelligence.email import EmailIntelligence
from nyx.intelligence.person import PersonIntelligence
from nyx.intelligence.phone import PhoneIntelligence
from nyx.models.target import SearchHistory, Target, TargetProfile
from nyx.osint.profile_builder import ProfileBuilder
from nyx.osint.search import SearchService
from nyx.search_engines.implementations import MetaSearchEngine
from sqlalchemy import select

logger = get_logger(__name__)


@dataclass
class SmartSearchInput:
    """Free-form information known about a target."""

    raw_text: str
    region: Optional[str] = None

    # Optional explicit hints (if caller already parsed some data)
    usernames: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    names: List[str] = field(default_factory=list)


@dataclass
class SmartCandidateProfile:
    """Candidate profile believed to belong to the target."""

    identifier: str
    identifier_type: str  # username, email, phone, name
    data: Dict[str, Any]
    confidence: float
    reason: str


@dataclass
class SmartSearchResult:
    """Aggregated Smart search result."""

    input: SmartSearchInput
    identifiers: Dict[str, List[str]]
    username_profiles: Dict[str, Profile]
    email_results: Dict[str, Any]
    phone_results: Dict[str, Any]
    person_results: Dict[str, Any]
    web_results: Dict[str, List[Dict[str, Any]]]
    candidates: List[SmartCandidateProfile]


class SmartSearchService:
    """High-level Smart search orchestrator."""

    def __init__(
        self,
        search_service: Optional[SearchService] = None,
        correlation_analyzer: Optional[CorrelationAnalyzer] = None,
    ) -> None:
        """Initialize Smart search service.

        Args:
            search_service: Optional shared SearchService instance
            correlation_analyzer: Optional shared CorrelationAnalyzer
        """
        self.search_service = search_service or SearchService()
        # Track whether this instance owns the SearchService lifecycle so we
        # know if we should close its HTTP resources when finished.
        self._owns_search_service = search_service is None
        self.profile_builder = ProfileBuilder(self.search_service)
        self.correlation_analyzer = correlation_analyzer or CorrelationAnalyzer()
        self.email_intel = EmailIntelligence()
        self.phone_intel = PhoneIntelligence()
        self.person_intel = PersonIntelligence()
        self.meta_search = MetaSearchEngine()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def smart_search(
        self,
        smart_input: SmartSearchInput,
        timeout: Optional[int] = 120,
        persist_to_db: bool = False,
    ) -> SmartSearchResult:
        """Execute Smart search for a target.

        This will:
        - Parse identifiers from free-form text
        - Run username / email / phone / person intelligence
        - Query web search engines for additional context
        - Correlate and score candidates
        - Optionally persist results to database

        Args:
            smart_input: Free-form target information
            timeout: Search timeout in seconds
            persist_to_db: Whether to persist results to database

        Returns:
            Smart search result with candidates and metadata
        """
        logger.info("Starting Smart search")
        start_time = datetime.utcnow()

        identifiers = self._extract_identifiers(smart_input)

        # ------------------------------------------------------------------
        # Run core intelligence modules in parallel
        # ------------------------------------------------------------------
        username_profiles: Dict[str, Profile] = {}
        email_results: Dict[str, Any] = {}
        phone_results: Dict[str, Any] = {}
        person_results: Dict[str, Any] = {}
        web_results: Dict[str, List[Dict[str, Any]]] = {}

        async def run_username_profiles() -> None:
            for username in identifiers["usernames"]:
                try:
                    profile = await self.profile_builder.build_profile(
                        username=username,
                        exclude_nsfw=False,
                        timeout=timeout,
                    )
                    username_profiles[username] = profile
                except Exception as exc:  # pragma: no cover - network failures
                    logger.debug(f"Username profile build failed for {username}: {exc}")

        async def run_email_intel() -> None:
            for email in identifiers["emails"]:
                try:
                    result = await self.email_intel.investigate(
                        email, search_profiles=True
                    )
                    email_results[email] = result
                except Exception as exc:  # pragma: no cover - network failures
                    logger.debug(f"Email intelligence failed for {email}: {exc}")

        async def run_phone_intel() -> None:
            for phone in identifiers["phones"]:
                try:
                    result = await self.phone_intel.investigate(
                        phone, region=smart_input.region
                    )
                    phone_results[phone] = result
                except Exception as exc:  # pragma: no cover - network failures
                    logger.debug(f"Phone intelligence failed for {phone}: {exc}")

        async def run_person_intel() -> None:
            # Use first parsed name as the primary person hint
            if not identifiers["names"]:
                return
            for full_name in identifiers["names"]:
                parts = full_name.split()
                if len(parts) < 2:
                    continue
                first_name = parts[0]
                last_name = parts[-1]
                middle_name = parts[1] if len(parts) == 3 else None
                try:
                    result = await self.person_intel.investigate(
                        first_name=first_name,
                        last_name=last_name,
                        middle_name=middle_name,
                        state=smart_input.region,
                    )
                    person_results[full_name] = result
                except Exception as exc:  # pragma: no cover - network failures
                    logger.debug(f"Person intelligence failed for {full_name}: {exc}")

        async def run_web_searches() -> None:
            # Run meta search for each identifier for additional context
            queries: List[str] = (
                identifiers["usernames"]
                + identifiers["emails"]
                + identifiers["phones"]
                + identifiers["names"]
            )
            for q in queries:
                try:
                    results = await self.meta_search.search(q, num_results=10)
                    web_results[q] = results
                except Exception as exc:  # pragma: no cover - network failures
                    logger.debug(f"Meta search failed for query {q}: {exc}")

        await asyncio.gather(
            run_username_profiles(),
            run_email_intel(),
            run_phone_intel(),
            run_person_intel(),
            run_web_searches(),
        )

        # ------------------------------------------------------------------
        # Build and score candidate profiles
        # ------------------------------------------------------------------
        candidates = self._build_candidates(
            smart_input=smart_input,
            identifiers=identifiers,
            username_profiles=username_profiles,
            email_results=email_results,
            phone_results=phone_results,
            person_results=person_results,
        )

        # Sort candidates by confidence descending
        candidates.sort(key=lambda c: c.confidence, reverse=True)

        result = SmartSearchResult(
            input=smart_input,
            identifiers=identifiers,
            username_profiles=username_profiles,
            email_results=email_results,
            phone_results=phone_results,
            person_results=person_results,
            web_results=web_results,
            candidates=candidates,
        )

        # Persist to database if requested
        if persist_to_db:
            try:
                await self._persist_to_database(result, start_time)
            except Exception as exc:
                logger.warning(f"Failed to persist Smart search to database: {exc}")

        return result

    async def aclose(self) -> None:
        """Close any underlying resources owned by this service."""
        if self._owns_search_service:
            await self.search_service.aclose()
        # Ensure meta search HTTP clients are closed
        await self.meta_search.close()

    # ------------------------------------------------------------------
    # Identifier extraction
    # ------------------------------------------------------------------

    def _extract_identifiers(
        self,
        smart_input: SmartSearchInput,
    ) -> Dict[str, List[str]]:
        """Extract identifiers from free-form input plus explicit hints.

        Uses improved regex patterns for better accuracy:
        - Email: RFC 5322 compliant pattern
        - Phone: International and US formats
        - Username: @handles and standalone usernames
        - Names: Capitalized word sequences with validation
        """
        text = smart_input.raw_text

        # Improved email pattern (RFC 5322 compliant, simplified)
        email_pattern = r"\b[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}\b"
        emails = set(re.findall(email_pattern, text, re.IGNORECASE))

        # Improved phone patterns (international and US formats)
        # International: +[country][number] or 00[country][number]
        # US: (XXX) XXX-XXXX, XXX-XXX-XXXX, XXX.XXX.XXXX, XXXXXXXXXX
        phone_patterns = [
            r"\+?\d{1,4}[\s.-]?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{1,9}",  # International
            r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}",  # US format
        ]
        phones = set()
        for pattern in phone_patterns:
            phones.update(re.findall(pattern, text))
        # Clean phone numbers (remove common separators for deduplication)
        phones = {re.sub(r"[\s().-]", "", p) for p in phones if len(re.sub(r"[\s().-]", "", p)) >= 10}

        # Improved username patterns
        # @handle format or standalone username (3-30 chars, alphanumeric + _ . -)
        username_patterns = [
            r"@([A-Za-z0-9_.-]{3,30})",  # @handle format
            r"\b([A-Za-z0-9][A-Za-z0-9_.-]{2,29})\b(?=\s|$|[^\w.-])",  # Standalone username
        ]
        usernames = set()
        for pattern in username_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            # Handle both string matches and tuple matches
            for match in matches:
                if isinstance(match, tuple):
                    usernames.update(m for m in match if m)
                else:
                    usernames.add(match)

        # Improved name pattern (2-4 capitalized words, avoiding common false positives)
        # Exclude common words that aren't names
        common_words = {
            "the", "and", "for", "are", "but", "not", "you", "all", "can", "her",
            "was", "one", "our", "out", "day", "get", "has", "him", "his", "how",
            "its", "may", "new", "now", "old", "see", "two", "way", "who", "boy",
            "did", "its", "let", "put", "say", "she", "too", "use", "usa", "uk",
        }
        name_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b"
        name_matches = re.findall(name_pattern, text)
        # Filter out common words and validate (at least 2 words, not all common)
        names = set()
        for match in name_matches:
            words = match.split()
            if len(words) >= 2 and not all(w.lower() in common_words for w in words):
                # Additional validation: names typically don't contain numbers
                if not any(char.isdigit() for char in match):
                    names.add(match)

        # Merge with explicit hints
        emails.update(smart_input.emails)
        phones.update(smart_input.phones)
        usernames.update(smart_input.usernames)
        names.update(smart_input.names)

        identifiers = {
            "usernames": sorted(set(u.lstrip("@").lower() for u in usernames if len(u.lstrip("@")) >= 3)),
            "emails": sorted(emails),
            "phones": sorted(phones),
            "names": sorted(names),
        }

        logger.debug(f"Smart search extracted identifiers: {identifiers}")
        return identifiers

    # ------------------------------------------------------------------
    # Candidate building and confidence scoring
    # ------------------------------------------------------------------

    def _build_candidates(
        self,
        smart_input: SmartSearchInput,
        identifiers: Dict[str, List[str]],
        username_profiles: Dict[str, Profile],
        email_results: Dict[str, Any],
        phone_results: Dict[str, Any],
        person_results: Dict[str, Any],
    ) -> List[SmartCandidateProfile]:
        """Build and score candidate profiles from component results."""
        candidates: List[SmartCandidateProfile] = []

        # Username-based candidates with refined scoring
        for username, profile in username_profiles.items():
            found_platforms = profile.get("found_on_platforms", 0)
            platforms = profile.get("platforms", {})
            
            # Base confidence from platform count (diminishing returns)
            base_conf = min(0.25 + 0.08 * min(found_platforms, 5), 0.75)
            
            # Boost for verified platforms or high-profile sites
            high_value_platforms = {"twitter", "instagram", "facebook", "linkedin", "github", "reddit"}
            high_value_count = sum(1 for p in platforms.keys() if p.lower() in high_value_platforms)
            if high_value_count > 0:
                base_conf += min(0.15 * high_value_count, 0.2)
            
            # Boost for username length and format (longer, more structured = higher confidence)
            if len(username) >= 5 and username.replace("_", "").replace(".", "").isalnum():
                base_conf += 0.05
            
            base_conf = min(base_conf, 0.95)
            
            reason = f"Username found on {found_platforms} platform(s)"
            if high_value_count > 0:
                reason += f" including {high_value_count} high-value platform(s)"
            
            candidates.append(
                SmartCandidateProfile(
                    identifier=username,
                    identifier_type="username",
                    data=profile,
                    confidence=base_conf,
                    reason=reason,
                )
            )

        # Email-based candidates with refined scoring
        for email, result in email_results.items():
            # result is a dataclass-like object; access attributes directly
            valid = getattr(result, "valid", False)
            breached = getattr(result, "breached", False)
            reputation = getattr(result, "reputation_score", 0.0)
            online_profiles = getattr(result, "online_profiles", {}) or {}
            disposable = getattr(result, "disposable", False)

            # Base confidence from validation
            base_conf = 0.6 if valid else 0.15
            
            # Boost for online profiles (strong signal)
            if online_profiles:
                profile_count = len(online_profiles)
                base_conf += min(0.15 + 0.05 * min(profile_count, 3), 0.25)
            
            # Boost for breach history (indicates real, active email)
            if breached:
                base_conf += 0.1
            
            # Penalty for disposable emails (lower confidence)
            if disposable:
                base_conf -= 0.15
            
            # Boost for high reputation score
            if reputation >= 70:
                base_conf += 0.05
            
            base_conf = max(0.0, min(base_conf, 0.95))

            reason = "Valid email" if valid else "Email pattern detected"
            if online_profiles:
                reason += f" with {len(online_profiles)} associated profile(s)"
            if breached:
                reason += ", appears in breach databases"
            if disposable:
                reason += " (disposable email service)"

            candidates.append(
                SmartCandidateProfile(
                    identifier=email,
                    identifier_type="email",
                    data=result.__dict__,
                    confidence=base_conf,
                    reason=reason,
                )
            )

        # Phone-based candidates with refined scoring
        for phone, result in phone_results.items():
            valid = getattr(result, "valid", False)
            associated_name = getattr(result, "associated_name", None)
            carrier = getattr(result, "carrier", None)
            line_type = getattr(result, "line_type", None)
            social_platforms = (getattr(result, "metadata", {}) or {}).get(
                "social_platforms"
            )

            # Base confidence from validation
            base_conf = 0.5 if valid else 0.1
            
            # Boost for associated name (strong correlation signal)
            if associated_name:
                base_conf += 0.25
            
            # Boost for social platform associations
            if social_platforms:
                base_conf += min(0.15 + 0.05 * len(social_platforms), 0.2)
            
            # Boost for carrier information (indicates real, active number)
            if carrier and carrier.lower() not in ("unknown", "invalid"):
                base_conf += 0.05
            
            # Boost for mobile vs landline (mobile more likely to be personal)
            if line_type and "mobile" in line_type.lower():
                base_conf += 0.05
            
            base_conf = min(base_conf, 0.95)

            reason = "Valid phone number" if valid else "Phone pattern detected"
            if associated_name:
                reason += f" linked to '{associated_name}'"
            if carrier:
                reason += f" ({carrier})"
            if social_platforms:
                reason += f", found on {len(social_platforms)} social platform(s)"

            candidates.append(
                SmartCandidateProfile(
                    identifier=phone,
                    identifier_type="phone",
                    data=result.__dict__,
                    confidence=base_conf,
                    reason=reason,
                )
            )

        # Person-based candidates with refined scoring
        for full_name, result in person_results.items():
            addresses = getattr(result, "addresses", []) or []
            phones = getattr(result, "phone_numbers", []) or []
            emails = getattr(result, "email_addresses", []) or []
            social = getattr(result, "social_profiles", {}) or {}
            relatives = getattr(result, "relatives", []) or []
            employment = getattr(result, "employment", []) or []

            # Base confidence from attribute count (weighted by importance)
            # Addresses and phones are stronger signals than emails
            attr_score = (
                len(addresses) * 0.3 +
                len(phones) * 0.25 +
                len(emails) * 0.15 +
                len(social.keys()) * 0.2 +
                len(relatives) * 0.05 +
                len(employment) * 0.05
            )
            
            base_conf = min(0.25 + attr_score * 0.15, 0.9)
            
            # Boost for having multiple types of data (more comprehensive record)
            data_types = sum([
                bool(addresses),
                bool(phones),
                bool(emails),
                bool(social),
            ])
            if data_types >= 3:
                base_conf += 0.1
            
            base_conf = min(base_conf, 0.95)
            
            attr_count = len(addresses) + len(phones) + len(emails) + len(social.keys())
            reason = f"Person record with {attr_count} associated attribute(s)"
            if data_types >= 3:
                reason += " (comprehensive profile)"

            candidates.append(
                SmartCandidateProfile(
                    identifier=full_name,
                    identifier_type="name",
                    data=result.__dict__,
                    confidence=base_conf,
                    reason=reason,
                )
            )

        # If we have multiple candidates, use correlation analyzer to identify
        # strongly related pairs and boost their confidence slightly.
        if len(candidates) > 1:
            profile_dicts: List[Dict[str, Any]] = []
            for cand in candidates:
                profile_dicts.append(
                    {
                        "id": cand.identifier,
                        "type": cand.identifier_type,
                        # Surface a few common attributes for similarity:
                        "username": cand.data.get("username") if isinstance(cand.data, dict) else None,
                        "email": cand.data.get("email") if isinstance(cand.data, dict) else None,
                        "phone": cand.data.get("phone") if isinstance(cand.data, dict) else None,
                        "location": cand.data.get("location") if isinstance(cand.data, dict) else None,
                    }
                )

            correlations = self.correlation_analyzer.correlate_profiles(
                profile_dicts
            )

            # Build a quick lookup for boosting
            boost_map: Dict[str, float] = {}
            for corr in correlations:
                if corr.confidence >= 0.6:
                    boost = min(corr.score * 0.2, 0.1)
                    boost_map[corr.entity1] = max(boost_map.get(corr.entity1, 0.0), boost)
                    boost_map[corr.entity2] = max(boost_map.get(corr.entity2, 0.0), boost)

            if boost_map:
                for cand in candidates:
                    boost = boost_map.get(cand.identifier)
                    if boost:
                        cand.confidence = min(1.0, cand.confidence + boost)
                        cand.reason += " (correlated with other matching entities)"

        return candidates

    # ------------------------------------------------------------------
    # Database persistence
    # ------------------------------------------------------------------

    async def _persist_to_database(
        self,
        result: SmartSearchResult,
        start_time: datetime,
    ) -> Optional[int]:
        """Persist Smart search results to database.

        Creates or updates Target, TargetProfile, and SearchHistory records.

        Args:
            result: Smart search result to persist
            start_time: When the search started

        Returns:
            Target ID if successful, None otherwise
        """
        try:
            db_manager = get_database_manager()
        except RuntimeError:
            logger.debug("Database not initialized, skipping persistence")
            return None

        async for session in db_manager.get_session():
            try:
                # Determine target name from best candidate or identifiers
                target_name = self._determine_target_name(result)
                
                # Find or create Target
                stmt = select(Target).where(Target.name == target_name)
                target_result = await session.execute(stmt)
                target = target_result.scalar_one_or_none()
                
                if not target:
                    target = Target(
                        name=target_name,
                        description=result.input.raw_text[:500] if result.input.raw_text else None,
                        category=self._infer_category(result),
                        notes=f"Created from Smart search: {result.input.raw_text[:200]}",
                    )
                    session.add(target)
                    await session.flush()
                
                # Update target search metadata
                target.last_searched = datetime.utcnow()
                target.search_count += 1
                
                # Create SearchHistory entry
                duration = (datetime.utcnow() - start_time).total_seconds()
                search_history = SearchHistory(
                    target_id=target.id,
                    search_query=result.input.raw_text,
                    search_type="smart",
                    platforms_searched=sum(
                        len(result.username_profiles.get(u, {}).get("platforms", {}))
                        for u in result.identifiers.get("usernames", [])
                    ),
                    results_found=len(result.candidates),
                    filters_applied={
                        "region": result.input.region,
                        "identifiers_extracted": result.identifiers,
                    },
                    results_summary={
                        "top_candidates": [
                            {
                                "identifier": c.identifier,
                                "type": c.identifier_type,
                                "confidence": c.confidence,
                            }
                            for c in result.candidates[:5]
                        ],
                        "total_candidates": len(result.candidates),
                    },
                    duration_seconds=duration,
                )
                session.add(search_history)
                
                # Create TargetProfile entries for high-confidence candidates
                profiles_created = 0
                for candidate in result.candidates:
                    if candidate.confidence < 0.5:  # Only persist high-confidence candidates
                        continue
                    
                    if candidate.identifier_type == "username":
                        # Create profiles for each platform where username was found
                        profile_data = candidate.data
                        platforms = profile_data.get("platforms", {})
                        for platform_name, platform_result in platforms.items():
                            if platform_result.get("found"):
                                # Check if profile already exists
                                stmt = select(TargetProfile).where(
                                    TargetProfile.target_id == target.id,
                                    TargetProfile.username == candidate.identifier,
                                    TargetProfile.platform == platform_name,
                                )
                                existing = await session.execute(stmt)
                                if existing.scalar_one_or_none():
                                    continue
                                
                                profile = TargetProfile(
                                    target_id=target.id,
                                    username=candidate.identifier,
                                    platform=platform_name,
                                    profile_url=platform_result.get("url"),
                                    confidence_score=candidate.confidence,
                                    raw_data=platform_result,
                                    profile_metadata={
                                        "source": "smart_search",
                                        "reason": candidate.reason,
                                    },
                                )
                                session.add(profile)
                                profiles_created += 1
                    
                    elif candidate.identifier_type in ("email", "phone"):
                        # Store as metadata in target notes
                        identifier_str = f"{candidate.identifier_type}:{candidate.identifier}"
                        current_notes = target.notes or ""
                        if identifier_str not in current_notes:
                            target.notes = current_notes + (f"\n{identifier_str} (confidence: {candidate.confidence:.2f})" if current_notes else identifier_str + f" (confidence: {candidate.confidence:.2f})")
                
                await session.commit()
                logger.info(
                    f"Persisted Smart search: target_id={target.id}, "
                    f"profiles_created={profiles_created}, candidates={len(result.candidates)}"
                )
                return target.id
                
            except Exception as exc:
                await session.rollback()
                logger.error(f"Failed to persist Smart search to database: {exc}", exc_info=True)
                return None

    def _determine_target_name(self, result: SmartSearchResult) -> str:
        """Determine target name from Smart search result.

        Uses best candidate or first extracted identifier.
        """
        if result.candidates:
            # Use highest confidence candidate
            best = result.candidates[0]
            if best.identifier_type == "name":
                return best.identifier
            elif best.identifier_type == "username":
                return best.identifier
            elif best.identifier_type in ("email", "phone"):
                return best.identifier
        
        # Fallback to first extracted identifier
        identifiers = result.identifiers
        if identifiers.get("names"):
            return identifiers["names"][0]
        elif identifiers.get("usernames"):
            return identifiers["usernames"][0]
        elif identifiers.get("emails"):
            return identifiers["emails"][0]
        elif identifiers.get("phones"):
            return identifiers["phones"][0]
        
        # Last resort
        return result.input.raw_text[:50] or "Unknown Target"

    def _infer_category(self, result: SmartSearchResult) -> str:
        """Infer target category from search results."""
        identifiers = result.identifiers
        
        # If we have person name, likely a person
        if identifiers.get("names"):
            return "person"
        
        # If we have email/phone but no name, might be account
        if identifiers.get("emails") or identifiers.get("phones"):
            return "account"
        
        # If only username, likely account
        if identifiers.get("usernames"):
            return "account"
        
        return "unknown"


__all__ = [
    "SmartSearchInput",
    "SmartCandidateProfile",
    "SmartSearchResult",
    "SmartSearchService",
]


