"""Correlation analysis for OSINT data."""

from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib

from nyx.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CorrelationScore:
    """Correlation score between entities."""

    entity1: str
    entity2: str
    score: float
    shared_attributes: List[str]
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class Pattern:
    """Detected pattern."""

    pattern_type: str
    entities: List[str]
    attributes: Dict[str, Any]
    confidence: float
    description: str


class CorrelationAnalyzer:
    """Analyze correlations between OSINT data points."""

    def __init__(self) -> None:
        """Initialize correlation analyzer."""
        pass

    def calculate_similarity(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> float:
        """Calculate similarity score between two data points.

        Args:
            data1: First data point
            data2: Second data point

        Returns:
            Similarity score (0-1)
        """
        if not data1 or not data2:
            return 0.0

        keys1 = set(data1.keys())
        keys2 = set(data2.keys())
        common_keys = keys1.intersection(keys2)

        if not common_keys:
            return 0.0

        matches = 0
        for key in common_keys:
            val1 = data1.get(key)
            val2 = data2.get(key)

            if val1 == val2:
                matches += 1
            elif isinstance(val1, str) and isinstance(val2, str):
                if val1.lower() == val2.lower():
                    matches += 0.9
                elif val1 in val2 or val2 in val1:
                    matches += 0.5

        similarity = matches / len(common_keys) if common_keys else 0.0
        return min(1.0, similarity)

    def find_shared_attributes(
        self, profiles: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Find shared attributes across profiles.

        Args:
            profiles: List of profile data

        Returns:
            Dictionary of shared attributes
        """
        if not profiles:
            return {}

        attribute_map: Dict[str, Set[str]] = {}

        for profile in profiles:
            profile_id = profile.get("id", "")
            for key, value in profile.items():
                if key == "id":
                    continue
                if value:
                    str_value = str(value)
                    if str_value not in attribute_map:
                        attribute_map[str_value] = set()
                    attribute_map[str_value].add(profile_id)

        shared = {}
        for value, profile_ids in attribute_map.items():
            if len(profile_ids) > 1:
                shared[value] = list(profile_ids)

        return shared

    def correlate_profiles(
        self, profiles: List[Dict[str, Any]]
    ) -> List[CorrelationScore]:
        """Correlate multiple profiles.

        Args:
            profiles: List of profiles to correlate

        Returns:
            List of correlation scores
        """
        correlations = []

        for i, profile1 in enumerate(profiles):
            for profile2 in profiles[i + 1 :]:
                similarity = self.calculate_similarity(profile1, profile2)

                if similarity > 0.3:
                    shared = []
                    for key in set(profile1.keys()).intersection(set(profile2.keys())):
                        if profile1.get(key) == profile2.get(key):
                            shared.append(key)

                    confidence = self._calculate_confidence(similarity, len(shared))

                    correlations.append(
                        CorrelationScore(
                            entity1=profile1.get("id", ""),
                            entity2=profile2.get("id", ""),
                            score=similarity,
                            shared_attributes=shared,
                            confidence=confidence,
                            metadata={
                                "profile1": profile1.get("platform", ""),
                                "profile2": profile2.get("platform", ""),
                            },
                        )
                    )

        return sorted(correlations, key=lambda x: x.score, reverse=True)

    def _calculate_confidence(self, similarity: float, shared_count: int) -> float:
        """Calculate confidence score.

        Args:
            similarity: Similarity score
            shared_count: Number of shared attributes

        Returns:
            Confidence score (0-1)
        """
        base_confidence = similarity
        attribute_bonus = min(shared_count * 0.1, 0.3)
        return min(1.0, base_confidence + attribute_bonus)

    def detect_patterns(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """Detect patterns in OSINT data.

        Args:
            data: List of data points

        Returns:
            List of detected patterns
        """
        patterns = []

        username_pattern = self._detect_username_pattern(data)
        if username_pattern:
            patterns.append(username_pattern)

        email_pattern = self._detect_email_pattern(data)
        if email_pattern:
            patterns.append(email_pattern)

        location_pattern = self._detect_location_pattern(data)
        if location_pattern:
            patterns.append(location_pattern)

        return patterns

    def _detect_username_pattern(self, data: List[Dict[str, Any]]) -> Optional[Pattern]:
        """Detect username patterns."""
        usernames = [d.get("username") for d in data if d.get("username")]

        if len(usernames) < 2:
            return None

        common_prefix = self._find_common_prefix(usernames)
        common_suffix = self._find_common_suffix(usernames)

        if len(common_prefix) > 2 or len(common_suffix) > 2:
            return Pattern(
                pattern_type="username_similarity",
                entities=usernames,
                attributes={"prefix": common_prefix, "suffix": common_suffix},
                confidence=0.7,
                description=f"Usernames share common pattern: {common_prefix}*{common_suffix}",
            )

        return None

    def _detect_email_pattern(self, data: List[Dict[str, Any]]) -> Optional[Pattern]:
        """Detect email patterns."""
        emails = [d.get("email") for d in data if d.get("email")]

        if len(emails) < 2:
            return None

        domains = [e.split("@")[-1] for e in emails]
        unique_domains = set(domains)

        if len(unique_domains) == 1:
            return Pattern(
                pattern_type="email_domain",
                entities=emails,
                attributes={"domain": list(unique_domains)[0]},
                confidence=0.8,
                description=f"All emails use same domain: {list(unique_domains)[0]}",
            )

        return None

    def _detect_location_pattern(self, data: List[Dict[str, Any]]) -> Optional[Pattern]:
        """Detect location patterns."""
        locations = [d.get("location") for d in data if d.get("location")]

        if len(locations) < 2:
            return None

        location_counts: Dict[str, int] = {}
        for loc in locations:
            location_counts[loc] = location_counts.get(loc, 0) + 1

        most_common = max(location_counts.items(), key=lambda x: x[1], default=None)

        if most_common and most_common[1] > 1:
            return Pattern(
                pattern_type="location_clustering",
                entities=locations,
                attributes={"common_location": most_common[0], "count": most_common[1]},
                confidence=0.6,
                description=f"Multiple entities in same location: {most_common[0]}",
            )

        return None

    def _find_common_prefix(self, strings: List[str]) -> str:
        """Find common prefix in strings."""
        if not strings:
            return ""

        prefix = strings[0]
        for s in strings[1:]:
            while not s.startswith(prefix):
                prefix = prefix[:-1]
                if not prefix:
                    return ""

        return prefix

    def _find_common_suffix(self, strings: List[str]) -> str:
        """Find common suffix in strings."""
        if not strings:
            return ""

        suffix = strings[0]
        for s in strings[1:]:
            while not s.endswith(suffix):
                suffix = suffix[1:]
                if not suffix:
                    return ""

        return suffix

    def calculate_confidence_score(
        self, data_points: List[Dict[str, Any]], weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate overall confidence score for data.

        Args:
            data_points: Data points to analyze
            weights: Attribute weights

        Returns:
            Confidence score (0-100)
        """
        if not data_points:
            return 0.0

        default_weights = {
            "verified": 1.0,
            "has_email": 0.8,
            "has_phone": 0.8,
            "has_location": 0.6,
            "has_photo": 0.5,
            "has_bio": 0.4,
        }

        weights = weights or default_weights
        total_score = 0.0
        total_weight = 0.0

        for data in data_points:
            for attr, weight in weights.items():
                if data.get(attr):
                    total_score += weight
                total_weight += weight

        confidence = (total_score / total_weight * 100) if total_weight > 0 else 0.0
        return min(100.0, confidence)


from typing import Optional
