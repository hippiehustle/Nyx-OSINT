"""Profile building and aggregation from OSINT search results."""

from typing import Dict, List, Optional, Any

from nyx.core.logger import get_logger
from nyx.core.types import Profile
from nyx.models.target import Target, TargetProfile
from nyx.osint.search import SearchService

logger = get_logger(__name__)


class ProfileBuilder:
    """Build comprehensive profiles from search results."""

    def __init__(self, search_service: SearchService):
        """Initialize profile builder.

        Args:
            search_service: Search service instance
        """
        self.search_service = search_service

    async def build_profile(
        self,
        username: str,
        exclude_nsfw: bool = False,
        timeout: Optional[int] = None,
    ) -> Profile:
        """Build profile for username across all platforms.

        Args:
            username: Username to profile
            exclude_nsfw: Whether to exclude NSFW platforms
            timeout: Search timeout in seconds

        Returns:
            Comprehensive profile data
        """
        logger.info(f"Building profile for username: {username}")

        # Search for username across platforms
        search_results = await self.search_service.search_username(
            username,
            exclude_nsfw=exclude_nsfw,
            timeout=timeout,
        )

        # Build profile from results
        profile: Profile = {
            "username": username,
            "found_on_platforms": len(search_results),
            "platforms": search_results,
            "platform_details": {},
            "aggregated_data": {},
        }

        # Aggregate platform information
        for platform_name, result in search_results.items():
            profile["platform_details"][platform_name] = {
                "url": result.get("url"),
                "status_code": result.get("status_code"),
                "response_time": result.get("response_time"),
            }

        return profile

    async def build_target_profile(
        self,
        target: Target,
        usernames: Optional[List[str]] = None,
        exclude_nsfw: bool = False,
    ) -> None:
        """Build target profile with multiple usernames.

        Args:
            target: Target object
            usernames: List of usernames to search (default: target.name)
            exclude_nsfw: Whether to exclude NSFW platforms
        """
        usernames_to_search = usernames or [target.name]

        logger.info(f"Building target profile for: {target.name}")

        all_results = {}
        for username in usernames_to_search:
            results = await self.search_service.search_username(
                username,
                exclude_nsfw=exclude_nsfw,
            )
            all_results.update(results)

        # Create target profiles from results
        for platform_name, result in all_results.items():
            profile = TargetProfile(
                target_id=target.id,
                username=result.get("username"),
                platform=platform_name,
                profile_url=result.get("url"),
            )
            target.profiles.append(profile)

        logger.info(f"Built target profile with {len(all_results)} platform matches")

    def correlate_profiles(self, profiles: Dict[str, Profile]) -> Dict[str, Any]:
        """Correlate multiple profiles to find relationships.

        Args:
            profiles: Dictionary of profiles keyed by identifier

        Returns:
            Correlation analysis
        """
        correlations = {
            "potential_same_person": [],
            "shared_platforms": [],
            "platform_overlap": {},
        }

        profile_keys = list(profiles.keys())
        profile_list = list(profiles.values())

        # Find shared platforms
        for i in range(len(profile_list)):
            for j in range(i + 1, len(profile_list)):
                profile1 = profile_list[i]
                profile2 = profile_list[j]

                platforms1 = set(profile1.get("platforms", {}).keys())
                platforms2 = set(profile2.get("platforms", {}).keys())

                shared = platforms1.intersection(platforms2)
                if shared:
                    correlations["shared_platforms"].append(
                        {
                            "profile1": profile_keys[i],
                            "profile2": profile_keys[j],
                            "shared_platforms": list(shared),
                            "count": len(shared),
                        }
                    )

                    # Check for strong correlation (multiple shared platforms)
                    if len(shared) >= 3:
                        correlations["potential_same_person"].append(
                            {
                                "profile1": profile_keys[i],
                                "profile2": profile_keys[j],
                                "confidence": min(len(shared) / max(len(platforms1), len(platforms2)), 1.0),
                            }
                        )

        return correlations

    def generate_profile_report(self, profile: Profile) -> str:
        """Generate human-readable profile report.

        Args:
            profile: Profile data

        Returns:
            Formatted report string
        """
        report = f"""
=== PROFILE REPORT ===
Username: {profile.get('username')}
Platforms Found: {profile.get('found_on_platforms', 0)}

=== PLATFORMS ===
"""
        for platform_name, details in profile.get("platform_details", {}).items():
            report += f"  {platform_name}:\n"
            report += f"    URL: {details.get('url', 'N/A')}\n"
            if details.get('response_time'):
                report += f"    Response Time: {details['response_time']:.2f}s\n"

        return report
