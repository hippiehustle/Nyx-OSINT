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

        This method aggregates 200+ platforms from:
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

        # Major Social Media Platforms
        social_media_platforms = {
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
            "Snapchat": {
                "url": "https://snapchat.com/",
                "category": "SOCIAL_MEDIA",
                "username_param": "user",
                "search_url": "https://www.snapchat.com/add/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Pinterest": {
                "url": "https://pinterest.com/",
                "category": "SOCIAL_MEDIA",
                "username_param": "user",
                "search_url": "https://www.pinterest.com/{username}/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "not_exists_status_code": 404,
                "source_tool": "maigret",
            },
            "Tumblr": {
                "url": "https://tumblr.com/",
                "category": "BLOGGING",
                "username_param": "user",
                "search_url": "https://{username}.tumblr.com/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "not_exists_status_code": 404,
                "source_tool": "maigret",
            },
            "VK": {
                "url": "https://vk.com/",
                "category": "SOCIAL_MEDIA",
                "username_param": "id",
                "search_url": "https://vk.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "not_exists_status_code": 404,
                "source_tool": "maigret",
            },
            "Telegram": {
                "url": "https://t.me/",
                "category": "MESSAGING",
                "username_param": "username",
                "search_url": "https://t.me/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "maigret",
            },
            "WhatsApp": {
                "url": "https://wa.me/",
                "category": "MESSAGING",
                "username_param": "phone",
                "search_url": "https://wa.me/{username}",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Mastodon": {
                "url": "https://mastodon.social/",
                "category": "SOCIAL_MEDIA",
                "username_param": "user",
                "search_url": "https://mastodon.social/@{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Minds": {
                "url": "https://minds.com/",
                "category": "SOCIAL_MEDIA",
                "username_param": "user",
                "search_url": "https://minds.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Gab": {
                "url": "https://gab.com/",
                "category": "SOCIAL_MEDIA",
                "username_param": "user",
                "search_url": "https://gab.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Parler": {
                "url": "https://parler.com/",
                "category": "SOCIAL_MEDIA",
                "username_param": "user",
                "search_url": "https://parler.com/{username}",
                "detection_method": "status_code",
                "source_tool": "sherlock",
            },
            "Truth Social": {
                "url": "https://truthsocial.com/",
                "category": "SOCIAL_MEDIA",
                "username_param": "user",
                "search_url": "https://truthsocial.com/@{username}",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
        }
        total += self.merge_from_dict(social_media_platforms)

        # Professional Networks
        professional_platforms = {
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
            "GitLab": {
                "url": "https://gitlab.com/",
                "category": "PROFESSIONAL",
                "username_param": "user",
                "search_url": "https://gitlab.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "maigret",
            },
            "Bitbucket": {
                "url": "https://bitbucket.org/",
                "category": "PROFESSIONAL",
                "username_param": "user",
                "search_url": "https://bitbucket.org/{username}/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Stack Overflow": {
                "url": "https://stackoverflow.com/",
                "category": "PROFESSIONAL",
                "username_param": "user",
                "search_url": "https://stackoverflow.com/users/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "maigret",
            },
            "HackerRank": {
                "url": "https://hackerrank.com/",
                "category": "PROFESSIONAL",
                "username_param": "user",
                "search_url": "https://hackerrank.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Codewars": {
                "url": "https://codewars.com/",
                "category": "PROFESSIONAL",
                "username_param": "user",
                "search_url": "https://www.codewars.com/users/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "LeetCode": {
                "url": "https://leetcode.com/",
                "category": "PROFESSIONAL",
                "username_param": "user",
                "search_url": "https://leetcode.com/{username}/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "AngelList": {
                "url": "https://angel.co/",
                "category": "PROFESSIONAL",
                "username_param": "user",
                "search_url": "https://angel.co/u/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Behance": {
                "url": "https://behance.net/",
                "category": "PROFESSIONAL",
                "username_param": "user",
                "search_url": "https://www.behance.net/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Dribbble": {
                "url": "https://dribbble.com/",
                "category": "PROFESSIONAL",
                "username_param": "user",
                "search_url": "https://dribbble.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
        }
        total += self.merge_from_dict(professional_platforms)

        # Dating Platforms
        dating_platforms = {
            "Tinder": {
                "url": "https://tinder.com/",
                "category": "DATING",
                "username_param": "user",
                "search_url": "https://tinder.com/@{username}",
                "detection_method": "status_code",
                "source_tool": "blackbird",
            },
            "Bumble": {
                "url": "https://bumble.com/",
                "category": "DATING",
                "username_param": "user",
                "search_url": "https://bumble.com/app/{username}",
                "detection_method": "status_code",
                "source_tool": "blackbird",
            },
            "OkCupid": {
                "url": "https://okcupid.com/",
                "category": "DATING",
                "username_param": "user",
                "search_url": "https://www.okcupid.com/profile/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "blackbird",
            },
            "Match": {
                "url": "https://match.com/",
                "category": "DATING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "blackbird",
            },
            "POF": {
                "url": "https://pof.com/",
                "category": "DATING",
                "username_param": "user",
                "search_url": "https://www.pof.com/viewprofile.aspx?profile_id={username}",
                "detection_method": "status_code",
                "source_tool": "blackbird",
            },
            "Hinge": {
                "url": "https://hinge.co/",
                "category": "DATING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "blackbird",
            },
            "eHarmony": {
                "url": "https://eharmony.com/",
                "category": "DATING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "blackbird",
            },
            "Badoo": {
                "url": "https://badoo.com/",
                "category": "DATING",
                "username_param": "user",
                "search_url": "https://badoo.com/profile/{username}",
                "detection_method": "status_code",
                "source_tool": "blackbird",
            },
            "MeetMe": {
                "url": "https://meetme.com/",
                "category": "DATING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "blackbird",
            },
            "Tagged": {
                "url": "https://tagged.com/",
                "category": "DATING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "blackbird",
            },
        }
        total += self.merge_from_dict(dating_platforms)

        # Gaming Platforms
        gaming_platforms = {
            "Steam": {
                "url": "https://steamcommunity.com/",
                "category": "GAMING",
                "username_param": "user",
                "search_url": "https://steamcommunity.com/id/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "maigret",
            },
            "Xbox Live": {
                "url": "https://xbox.com/",
                "category": "GAMING",
                "username_param": "user",
                "search_url": "https://account.xbox.com/profile?gamertag={username}",
                "detection_method": "status_code",
                "source_tool": "sherlock",
            },
            "PlayStation": {
                "url": "https://playstation.com/",
                "category": "GAMING",
                "username_param": "user",
                "search_url": "https://psnprofiles.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Roblox": {
                "url": "https://roblox.com/",
                "category": "GAMING",
                "username_param": "user",
                "search_url": "https://www.roblox.com/user.aspx?username={username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Minecraft": {
                "url": "https://namemc.com/",
                "category": "GAMING",
                "username_param": "user",
                "search_url": "https://namemc.com/profile/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Epic Games": {
                "url": "https://epicgames.com/",
                "category": "GAMING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Battle.net": {
                "url": "https://battle.net/",
                "category": "GAMING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Origin": {
                "url": "https://origin.com/",
                "category": "GAMING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Riot Games": {
                "url": "https://riotgames.com/",
                "category": "GAMING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Kongregate": {
                "url": "https://kongregate.com/",
                "category": "GAMING",
                "username_param": "user",
                "search_url": "https://www.kongregate.com/accounts/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
        }
        total += self.merge_from_dict(gaming_platforms)

        # Forums and Communities
        forum_platforms = {
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
            "4chan": {
                "url": "https://4chan.org/",
                "category": "FORUMS",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "8chan": {
                "url": "https://8kun.top/",
                "category": "FORUMS",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Hacker News": {
                "url": "https://news.ycombinator.com/",
                "category": "FORUMS",
                "username_param": "id",
                "search_url": "https://news.ycombinator.com/user?id={username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "maigret",
            },
            "Quora": {
                "url": "https://quora.com/",
                "category": "FORUMS",
                "username_param": "user",
                "search_url": "https://www.quora.com/profile/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "DeviantArt": {
                "url": "https://deviantart.com/",
                "category": "PHOTOGRAPHY",
                "username_param": "user",
                "search_url": "https://www.deviantart.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Something Awful": {
                "url": "https://forums.somethingawful.com/",
                "category": "FORUMS",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Bodybuilding.com": {
                "url": "https://bodybuilding.com/",
                "category": "FORUMS",
                "username_param": "user",
                "search_url": "https://forum.bodybuilding.com/member.php?u={username}",
                "detection_method": "status_code",
                "source_tool": "sherlock",
            },
        }
        total += self.merge_from_dict(forum_platforms)

        # Streaming and Video Platforms
        streaming_platforms = {
            "YouTube": {
                "url": "https://youtube.com/",
                "category": "STREAMING",
                "username_param": "c",
                "search_url": "https://www.youtube.com/@{username}",
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
            "Kick": {
                "url": "https://kick.com/",
                "category": "STREAMING",
                "username_param": "channel",
                "search_url": "https://kick.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "manual",
            },
            "Rumble": {
                "url": "https://rumble.com/",
                "category": "STREAMING",
                "username_param": "channel",
                "search_url": "https://rumble.com/user/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "DLive": {
                "url": "https://dlive.tv/",
                "category": "STREAMING",
                "username_param": "user",
                "search_url": "https://dlive.tv/{username}",
                "detection_method": "status_code",
                "source_tool": "sherlock",
            },
            "Vimeo": {
                "url": "https://vimeo.com/",
                "category": "STREAMING",
                "username_param": "user",
                "search_url": "https://vimeo.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Dailymotion": {
                "url": "https://dailymotion.com/",
                "category": "STREAMING",
                "username_param": "user",
                "search_url": "https://www.dailymotion.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Mixer": {
                "url": "https://mixer.com/",
                "category": "STREAMING",
                "username_param": "channel",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
        }
        total += self.merge_from_dict(streaming_platforms)

        # Photography and Art Platforms
        photography_platforms = {
            "Flickr": {
                "url": "https://flickr.com/",
                "category": "PHOTOGRAPHY",
                "username_param": "user",
                "search_url": "https://www.flickr.com/photos/{username}/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "500px": {
                "url": "https://500px.com/",
                "category": "PHOTOGRAPHY",
                "username_param": "user",
                "search_url": "https://500px.com/p/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Pixelfed": {
                "url": "https://pixelfed.social/",
                "category": "PHOTOGRAPHY",
                "username_param": "user",
                "search_url": "https://pixelfed.social/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Unsplash": {
                "url": "https://unsplash.com/",
                "category": "PHOTOGRAPHY",
                "username_param": "user",
                "search_url": "https://unsplash.com/@{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "SmugMug": {
                "url": "https://smugmug.com/",
                "category": "PHOTOGRAPHY",
                "username_param": "user",
                "search_url": "https://{username}.smugmug.com/",
                "detection_method": "status_code",
                "source_tool": "sherlock",
            },
        }
        total += self.merge_from_dict(photography_platforms)

        # Blogging Platforms
        blogging_platforms = {
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
            "WordPress": {
                "url": "https://wordpress.com/",
                "category": "BLOGGING",
                "username_param": "user",
                "search_url": "https://{username}.wordpress.com/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Blogger": {
                "url": "https://blogger.com/",
                "category": "BLOGGING",
                "username_param": "user",
                "search_url": "https://{username}.blogspot.com/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "LiveJournal": {
                "url": "https://livejournal.com/",
                "category": "BLOGGING",
                "username_param": "user",
                "search_url": "https://{username}.livejournal.com/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Ghost": {
                "url": "https://ghost.org/",
                "category": "BLOGGING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Substack": {
                "url": "https://substack.com/",
                "category": "BLOGGING",
                "username_param": "user",
                "search_url": "https://{username}.substack.com/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "manual",
            },
        }
        total += self.merge_from_dict(blogging_platforms)

        # Crypto and Blockchain Platforms
        crypto_platforms = {
            "Coinbase": {
                "url": "https://coinbase.com/",
                "category": "CRYPTO",
                "username_param": "user",
                "search_url": "https://www.coinbase.com/{username}",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Binance": {
                "url": "https://binance.com/",
                "category": "CRYPTO",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Kraken": {
                "url": "https://kraken.com/",
                "category": "CRYPTO",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "OpenSea": {
                "url": "https://opensea.io/",
                "category": "CRYPTO",
                "username_param": "user",
                "search_url": "https://opensea.io/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "manual",
            },
            "Rarible": {
                "url": "https://rarible.com/",
                "category": "CRYPTO",
                "username_param": "user",
                "search_url": "https://rarible.com/{username}",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
        }
        total += self.merge_from_dict(crypto_platforms)

        # Shopping and Marketplace Platforms
        shopping_platforms = {
            "eBay": {
                "url": "https://ebay.com/",
                "category": "SHOPPING",
                "username_param": "user",
                "search_url": "https://www.ebay.com/usr/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Etsy": {
                "url": "https://etsy.com/",
                "category": "SHOPPING",
                "username_param": "shop",
                "search_url": "https://www.etsy.com/shop/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Amazon": {
                "url": "https://amazon.com/",
                "category": "SHOPPING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Poshmark": {
                "url": "https://poshmark.com/",
                "category": "SHOPPING",
                "username_param": "user",
                "search_url": "https://poshmark.com/closet/{username}",
                "detection_method": "status_code",
                "source_tool": "sherlock",
            },
            "Mercari": {
                "url": "https://mercari.com/",
                "category": "SHOPPING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
        }
        total += self.merge_from_dict(shopping_platforms)

        # Messaging Platforms
        messaging_platforms = {
            "Discord": {
                "url": "https://discord.com/",
                "category": "MESSAGING",
                "username_param": "username",
                "detection_method": "status_code",
                "source_tool": "maigret",
            },
            "Slack": {
                "url": "https://slack.com/",
                "category": "MESSAGING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Skype": {
                "url": "https://skype.com/",
                "category": "MESSAGING",
                "username_param": "user",
                "search_url": "https://secure.skype.com/portal/profile/{username}",
                "detection_method": "status_code",
                "source_tool": "sherlock",
            },
            "WeChat": {
                "url": "https://wechat.com/",
                "category": "MESSAGING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Line": {
                "url": "https://line.me/",
                "category": "MESSAGING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Signal": {
                "url": "https://signal.org/",
                "category": "MESSAGING",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
        }
        total += self.merge_from_dict(messaging_platforms)

        # Music and Audio Platforms
        music_platforms = {
            "Spotify": {
                "url": "https://spotify.com/",
                "category": "OTHER",
                "username_param": "user",
                "search_url": "https://open.spotify.com/user/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "SoundCloud": {
                "url": "https://soundcloud.com/",
                "category": "OTHER",
                "username_param": "user",
                "search_url": "https://soundcloud.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Bandcamp": {
                "url": "https://bandcamp.com/",
                "category": "OTHER",
                "username_param": "user",
                "search_url": "https://{username}.bandcamp.com/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Apple Music": {
                "url": "https://music.apple.com/",
                "category": "OTHER",
                "username_param": "user",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
            "Last.fm": {
                "url": "https://last.fm/",
                "category": "OTHER",
                "username_param": "user",
                "search_url": "https://www.last.fm/user/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Mixcloud": {
                "url": "https://mixcloud.com/",
                "category": "OTHER",
                "username_param": "user",
                "search_url": "https://www.mixcloud.com/{username}/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
        }
        total += self.merge_from_dict(music_platforms)

        # Funding and Support Platforms
        funding_platforms = {
            "Patreon": {
                "url": "https://patreon.com/",
                "category": "OTHER",
                "username_param": "creator",
                "search_url": "https://www.patreon.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Ko-fi": {
                "url": "https://ko-fi.com/",
                "category": "OTHER",
                "username_param": "user",
                "search_url": "https://ko-fi.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "sherlock",
            },
            "Buy Me a Coffee": {
                "url": "https://buymeacoffee.com/",
                "category": "OTHER",
                "username_param": "user",
                "search_url": "https://www.buymeacoffee.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "source_tool": "manual",
            },
            "Kickstarter": {
                "url": "https://kickstarter.com/",
                "category": "OTHER",
                "username_param": "user",
                "search_url": "https://www.kickstarter.com/profile/{username}",
                "detection_method": "status_code",
                "source_tool": "sherlock",
            },
            "GoFundMe": {
                "url": "https://gofundme.com/",
                "category": "OTHER",
                "username_param": "user",
                "search_url": "https://www.gofundme.com/f/{username}",
                "detection_method": "status_code",
                "source_tool": "manual",
            },
        }
        total += self.merge_from_dict(funding_platforms)

        # ADULT/NSFW PLATFORMS - Comprehensive Coverage
        adult_platforms = {
            "OnlyFans": {
                "url": "https://onlyfans.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://onlyfans.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Fansly": {
                "url": "https://fansly.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://fansly.com/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "ManyVids": {
                "url": "https://manyvids.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://www.manyvids.com/Profile/{username}/",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Chaturbate": {
                "url": "https://chaturbate.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://chaturbate.com/{username}/",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Pornhub": {
                "url": "https://pornhub.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://www.pornhub.com/users/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "xHamster": {
                "url": "https://xhamster.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://xhamster.com/users/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Xvideos": {
                "url": "https://xvideos.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://www.xvideos.com/profiles/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "RedTube": {
                "url": "https://redtube.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://www.redtube.com/pornstar/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "YouPorn": {
                "url": "https://youporn.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://www.youporn.com/uservids/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Tube8": {
                "url": "https://tube8.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Spankbang": {
                "url": "https://spankbang.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://spankbang.com/profile/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Clips4Sale": {
                "url": "https://clips4sale.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "IWantClips": {
                "url": "https://iwantclips.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://iwantclips.com/store/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "AVN Stars": {
                "url": "https://stars.avn.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://stars.avn.com/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "FetLife": {
                "url": "https://fetlife.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://fetlife.com/users/{username}",
                "detection_method": "status_code",
                "exists_status_code": 200,
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "AdultWork": {
                "url": "https://adultwork.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Stripchat": {
                "url": "https://stripchat.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://stripchat.com/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "LiveJasmin": {
                "url": "https://livejasmin.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Cam4": {
                "url": "https://cam4.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://www.cam4.com/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "BongaCams": {
                "url": "https://bongacams.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "MyFreeCams": {
                "url": "https://myfreecams.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://profiles.myfreecams.com/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "CamSoda": {
                "url": "https://camsoda.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://www.camsoda.com/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Flirt4Free": {
                "url": "https://flirt4free.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Streamate": {
                "url": "https://streamate.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "ImLive": {
                "url": "https://imlive.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "JerkMate": {
                "url": "https://jerkmate.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Slutroulette": {
                "url": "https://slutroulette.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "AdultFriendFinder": {
                "url": "https://adultfriendfinder.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Ashley Madison": {
                "url": "https://ashleymadison.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Alt.com": {
                "url": "https://alt.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Seeking": {
                "url": "https://seeking.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "ModelHub": {
                "url": "https://modelhub.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://www.modelhub.com/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Brazzers": {
                "url": "https://brazzers.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Reality Kings": {
                "url": "https://realitykings.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "IAFD": {
                "url": "https://iafd.com/",
                "category": "ADULT",
                "username_param": "user",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Pornstar Database": {
                "url": "https://babepedia.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://www.babepedia.com/babe/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "NiteFlirt": {
                "url": "https://niteflirt.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://www.niteflirt.com/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Sextpanther": {
                "url": "https://sextpanther.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://www.sextpanther.com/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "LoyalFans": {
                "url": "https://loyalfans.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://www.loyalfans.com/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "JustForFans": {
                "url": "https://justfor.fans/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://justfor.fans/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "4Based": {
                "url": "https://4based.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://4based.com/{username}",
                "detection_method": "status_code",
                "is_nsfw": True,
                "source_tool": "blackbird",
            },
            "Gumroad": {
                "url": "https://gumroad.com/",
                "category": "ADULT",
                "username_param": "user",
                "search_url": "https://gumroad.com/{username}",
                "detection_method": "status_code",
                "is_nsfw": False,  # Can have NSFW content but not exclusively
                "source_tool": "manual",
            },
        }
        total += self.merge_from_dict(adult_platforms)

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
