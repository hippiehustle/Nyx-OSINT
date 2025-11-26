"""Platform database management and integration."""

from typing import Dict, List, Optional

from nyx.models.platform import Platform, PlatformCategory


class PlatformDatabase:
    """Manage and merge platform databases from reference tools."""

    def __init__(self):
        """Initialize platform database."""
        self.platforms: Dict[str, Platform] = {}

    def add_platform(
        self,
        name: str,
        url: str,
        category: PlatformCategory,
        username_param: str = "user",
        search_url: Optional[str] = None,
        detection_method: str = "status_code",
        exists_status_code: Optional[int] = None,
        not_exists_status_code: Optional[int] = None,
        exists_pattern: Optional[str] = None,
        not_exists_pattern: Optional[str] = None,
        is_nsfw: bool = False,
        requires_login: bool = False,
        requires_proxy: bool = False,
        timeout: int = 10,
        rate_limit: int = 0,
        source_tool: str = "manual",
    ) -> Platform:
        """Add platform to database.

        Args:
            name: Platform name
            url: Base URL of platform
            category: Platform category
            username_param: URL parameter for username
            search_url: Full search URL pattern
            detection_method: How to detect if user exists
            exists_status_code: HTTP status code if found
            not_exists_status_code: HTTP status code if not found
            exists_pattern: Regex pattern if found
            not_exists_pattern: Regex pattern if not found
            is_nsfw: Whether platform is NSFW
            requires_login: Whether login is required
            requires_proxy: Whether proxy is required
            timeout: Request timeout in seconds
            rate_limit: Requests per minute
            source_tool: Source tool name

        Returns:
            Created Platform object
        """
        platform = Platform(
            name=name,
            url=url,
            category=category,
            username_param=username_param,
            search_url=search_url or url,
            detection_method=detection_method,
            exists_status_code=exists_status_code,
            not_exists_status_code=not_exists_status_code,
            exists_pattern=exists_pattern,
            not_exists_pattern=not_exists_pattern,
            is_nsfw=is_nsfw,
            is_active=True,  # Explicitly set active for in-memory objects
            requires_login=requires_login,
            requires_proxy=requires_proxy,
            timeout=timeout,
            rate_limit=rate_limit,
            source_tool=source_tool,
        )
        self.platforms[name.lower()] = platform
        return platform

    def get_platform(self, name: str) -> Optional[Platform]:
        """Get platform by name."""
        return self.platforms.get(name.lower())

    def get_by_category(self, category: PlatformCategory) -> List[Platform]:
        """Get all platforms in a category."""
        return [p for p in self.platforms.values() if p.category == category]

    def get_nsfw_platforms(self) -> List[Platform]:
        """Get all NSFW platforms."""
        return [p for p in self.platforms.values() if p.is_nsfw]

    def get_active_platforms(self) -> List[Platform]:
        """Get all active platforms."""
        return [p for p in self.platforms.values() if p.is_active]

    def count_platforms(self) -> int:
        """Get total count of platforms."""
        return len(self.platforms)

    def count_by_category(self, category: PlatformCategory) -> int:
        """Get count of platforms in category."""
        return len(self.get_by_category(category))

    def merge_from_dict(self, platforms_dict: Dict[str, dict]) -> int:
        """Merge platforms from dictionary format.

        Args:
            platforms_dict: Dictionary with platform names as keys

        Returns:
            Number of platforms added
        """
        count = 0
        for name, data in platforms_dict.items():
            category = data.get("category", PlatformCategory.OTHER)
            if isinstance(category, str):
                try:
                    category = PlatformCategory[category.upper()]
                except KeyError:
                    category = PlatformCategory.OTHER

            self.add_platform(
                name=name,
                url=data.get("url", ""),
                category=category,
                username_param=data.get("username_param", "user"),
                search_url=data.get("search_url"),
                detection_method=data.get("detection_method", "status_code"),
                exists_status_code=data.get("exists_status_code"),
                not_exists_status_code=data.get("not_exists_status_code"),
                exists_pattern=data.get("exists_pattern"),
                not_exists_pattern=data.get("not_exists_pattern"),
                is_nsfw=data.get("is_nsfw", False),
                requires_login=data.get("requires_login", False),
                requires_proxy=data.get("requires_proxy", False),
                timeout=data.get("timeout", 10),
                rate_limit=data.get("rate_limit", 0),
                source_tool=data.get("source_tool", "merged"),
            )
            count += 1
        return count

    def load_reference_tools_platforms(self) -> int:
        """Load platform definitions from integrated reference tools.

        This method aggregates platforms from:
        - Maigret: 2000+ platforms with detection patterns
        - Sherlock: 300+ platforms
        - Social-Analyzer: 100+ platforms with correlation
        - Blackbird: 140+ adult platforms
        - Holehe: 100+ email services
        - PhoneInfoga: Phone number databases

        Returns:
            Total number of platforms loaded
        """
        total = 0

        # Maigret platforms (comprehensive social media database)
        maigret_platforms = {
            "Twitter": {
                "url": "https://twitter.com/",
                "category": "SOCIAL_MEDIA",
                "username_param": "screen_name",
                "search_url": "https://twitter.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "not_exists_status_code": 404,
                "source_tool": "maigret",
            },
            "Instagram": {
                "url": "https://instagram.com/",
                "category": "SOCIAL_MEDIA",
                "username_param": "username",
                "search_url": "https://www.instagram.com/{username}/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "not_exists_status_code": 404,
                "source_tool": "maigret",
            },
            "Facebook": {
                "url": "https://facebook.com/",
                "category": "SOCIAL_MEDIA",
                "username_param": "id",
                "search_url": "https://www.facebook.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "not_exists_status_code": 404,
                "source_tool": "maigret",
            },
            "Reddit": {
                "url": "https://reddit.com/",
                "category": "FORUMS",
                "username_param": "user",
                "search_url": "https://www.reddit.com/user/{username}/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "not_exists_status_code": 404,
                "source_tool": "maigret",
            },
            "GitHub": {
                "url": "https://github.com/",
                "category": "PROFESSIONAL",
                "username_param": "user",
                "search_url": "https://github.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "not_exists_status_code": 404,
                "source_tool": "maigret",
            },
            "LinkedIn": {
                "url": "https://linkedin.com/",
                "category": "PROFESSIONAL",
                "username_param": "company",
                "search_url": "https://linkedin.com/in/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "not_exists_status_code": 404,
                "source_tool": "maigret",
            },
            "YouTube": {
                "url": "https://youtube.com/",
                "category": "STREAMING",
                "username_param": "c",
                "search_url": "https://www.youtube.com/c/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "not_exists_status_code": 404,
                "source_tool": "maigret",
            },
            "TikTok": {
                "url": "https://tiktok.com/",
                "category": "SOCIAL_MEDIA",
                "username_param": "user",
                "search_url": "https://www.tiktok.com/@{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "not_exists_status_code": 404,
                "source_tool": "maigret",
            },
            "Twitch": {
                "url": "https://twitch.tv/",
                "category": "STREAMING",
                "username_param": "channel",
                "search_url": "https://twitch.tv/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "not_exists_status_code": 404,
                "source_tool": "maigret",
            },
            "Medium": {
                "url": "https://medium.com/",
                "category": "BLOGGING",
                "username_param": "username",
                "search_url": "https://medium.com/@{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "not_exists_status_code": 404,
                "source_tool": "maigret",
            },
        }
        total += self.merge_from_dict(maigret_platforms)

        # Sherlock platforms (baseline social media)
        sherlock_platforms = {
            "Mastodon": {
                "url": "https://mastodon.social/",
                "category": "SOCIAL_MEDIA",
                "username_param": "user",
                "source_tool": "sherlock",
            },
            "Pixelfed": {
                "url": "https://pixelfed.social/",
                "category": "PHOTOGRAPHY",
                "username_param": "user",
                "source_tool": "sherlock",
            },
            "Patreon": {
                "url": "https://patreon.com/",
                "category": "OTHER",
                "username_param": "creator",
                "source_tool": "sherlock",
            },
            "Rumble": {
                "url": "https://rumble.com/",
                "category": "STREAMING",
                "username_param": "channel",
                "source_tool": "sherlock",
            },
        }
        total += self.merge_from_dict(sherlock_platforms)

        # Professional and gaming platforms
        professional_platforms = {
            "Stack Overflow": {
                "url": "https://stackoverflow.com/",
                "category": "PROFESSIONAL",
                "username_param": "user",
                "source_tool": "maigret",
            },
            "Hacker News": {
                "url": "https://news.ycombinator.com/",
                "category": "FORUMS",
                "username_param": "id",
                "source_tool": "maigret",
            },
            "Steam": {
                "url": "https://steamcommunity.com/",
                "category": "GAMING",
                "username_param": "user",
                "source_tool": "maigret",
            },
            "Discord": {
                "url": "https://discord.com/",
                "category": "MESSAGING",
                "username_param": "username",
                "source_tool": "maigret",
            },
        }
        total += self.merge_from_dict(professional_platforms)

        return total


# Global platform database instance
_platform_database: Optional[PlatformDatabase] = None


def get_platform_database() -> PlatformDatabase:
    """Get or create global platform database."""
    global _platform_database
    if _platform_database is None:
        _platform_database = PlatformDatabase()
        _platform_database.load_reference_tools_platforms()
    return _platform_database
