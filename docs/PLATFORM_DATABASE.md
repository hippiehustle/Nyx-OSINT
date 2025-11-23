# Nyx Expanded Platform Database

## Overview

The Nyx platform database has been expanded to include **150+ searchable websites** organized by search type and category. The database ensures comprehensive coverage for username, email, and phone number searches with intelligent filtering and categorization.

## Architecture

### Platform Categories

The database uses 20+ categories to organize platforms:

#### Username Search Categories
- **SOCIAL_MEDIA**: Twitter/X, Instagram, Facebook, TikTok, Snapchat, Pinterest, Mastodon, Bluesky, Threads, etc.
- **STREAMING**: YouTube, Twitch, Rumble, Kick, Odysee, Dailymotion, Vimeo, BitChute, LBRY
- **GAMING**: Steam, PlayStation Network, Xbox Live, Nintendo Network, Epic Games, Roblox, Discord, Minecraft, Fortnite, etc.
- **PROFESSIONAL**: LinkedIn, Stack Overflow, AngelList, Crunchbase
- **DEVELOPER**: GitHub, GitLab, Bitbucket, SourceForge, CodePen, Observable, Replit, Glitch
- **DATING**: Match, OKCupid, Tinder, Bumble, Hinge, Grindr, Badoo, Plenty of Fish, eHarmony, Zoosk
- **PHOTOGRAPHY**: Flickr, 500px, SmugMug, Pixelfed, Imgur, DeviantArt, ArtStation
- **MUSIC**: Spotify, SoundCloud, Bandcamp, YouTube Music, Last.fm, Discogs, MixCloud, Tidal, Apple Music
- **FORUMS**: Reddit, 4chan, 8kun, Voat, Stack Exchange, Hacker News, Slashdot, Digg, Quora
- **BLOGGING**: Medium, Substack, Tumblr, WordPress.com, Blogger
- **PORTFOLIO**: ArtStation, CodePen, Personal Portfolios
- **COMMUNITY**: Discord, Nextdoor, Meetup, Patreon, Kickstarter, Indiegogo
- **NEWS**: Substack, Medium, News Sites
- **CRYPTO**: Bitcoin Talk, Coinbase, Kraken, Binance, Bitfinex, Poloniex
- **TRADING**: StockTwits, Seeking Alpha
- **SHOPPING**: eBay, Amazon, Etsy, Aliexpress, Shopify, MercadoLibre, OLX, Craigslist
- **ANIME**: MyAnimeList, AniList, Kitsu, MangaDex
- **MESSAGING**: Telegram, WhatsApp, Viber, Signal
- **VIDEO**: YouTube, Twitch, Dailymotion, Vimeo, BitChute, LBRY

#### Email Search Categories
- **EMAIL_SERVICE**: Gmail, Outlook, Yahoo Mail, ProtonMail, Tutanota, Thunderbird, Mail.ru, Yandex Mail, AOL, Mail.com, Fastmail, Zoho Mail, iCloud
- **EMAIL_VERIFICATION**: HaveIBeenPwned, Breach Alert, Data.com, RocketReach, Hunter.io, Clearbit, Truecaller, Spokeo, PeopleFinder, BeenVerified, White Pages, ZoomInfo

#### Phone Search Categories
- **PHONE_LOOKUP**: Truecaller, PhoneInfoga, Spokeo, Whitepages, ReversePhoneFile, CallerIDTest, Sync.me, BeenVerified, FastPeopleSearch, TrueLookup
- **PHONE_DATABASE**: NumVerify, ZoomInfo, Apollo.io, RocketReach

## Platform Structure

Each platform in the database contains:

```python
{
    "name": "Platform Name",
    "url": "https://platform.com/",
    "category": "SOCIAL_MEDIA",  # or other category
    "username_param": "user",     # URL parameter for username
    "search_url": "https://platform.com/{username}",
    "supports_username": True,    # Whether it supports username search
    "supports_email": False,      # Whether it supports email search
    "supports_phone": False,      # Whether it supports phone search
    "is_nsfw": False,             # Content rating
    "requires_login": False,      # If login needed
    "requires_proxy": False,      # If proxy needed
    "timeout": 10,                # Request timeout in seconds
    "rate_limit": 0,              # Requests per minute (0 = unlimited)
}
```

## Search Types & Coverage

### Username Search (150+ platforms)
Searches all platforms that support username queries. By default, Nyx searches **ALL active username-supporting platforms** unless filtered by:
- Specific platform names
- Categories
- NSFW exclusion
- Custom filters

### Email Search (25+ platforms)
Searches email verification services and email-based detection platforms including:
- Email services (Gmail, Outlook, Yahoo, etc.)
- Breach databases (HaveIBeenPwned)
- People search databases (Spokeo, BeenVerified, etc.)

### Phone Search (14+ platforms)
Searches phone lookup and reverse phone databases including:
- Phone lookup services (Truecaller, NumVerify)
- People search databases (Spokeo, BeenVerified, etc.)
- Business phone databases (ZoomInfo, Apollo.io, RocketReach)

## Default Behavior

### Username Search
```python
# By default, searches ALL active platforms
results = await search_service.search_username("username")

# With filtering
results = await search_service.search_username(
    "username",
    categories=["SOCIAL_MEDIA", "GAMING"],  # Only these categories
    exclude_nsfw=True                        # Exclude adult platforms
)

# With specific platforms
results = await search_service.search_username(
    "username",
    platforms=["Twitter/X", "GitHub", "Reddit"]  # Only these
)
```

### Email Search
```python
# Searches ALL email-supporting platforms by default
results = await search_service.search_email("email@example.com")
```

### Phone Search
```python
# Searches ALL phone-supporting platforms by default
results = await search_service.search_phone("+1-555-0123")
```

## Usage Examples

### Basic Username Search
```python
from nyx.osint.search import SearchService

service = SearchService()

# Search across ALL platforms (150+)
results = await service.search_username("john_doe")

# Results will include matches from:
# - All social media platforms
# - Developer platforms (GitHub, etc.)
# - Gaming platforms (Steam, etc.)
# - Professional networks (LinkedIn, etc.)
# - Forums (Reddit, etc.)
# - And many more...
```

### Category-Specific Search
```python
# Search only developer/tech platforms
results = await service.search_username(
    "username",
    categories=["DEVELOPER", "PROFESSIONAL"]
)

# Returns matches from: GitHub, GitLab, LinkedIn, Stack Overflow, etc.
```

### NSFW Exclusion
```python
# Search all platforms except adult platforms
results = await service.search_username(
    "username",
    exclude_nsfw=True
)
```

### Email Search
```python
# Searches 25+ email verification/lookup platforms
results = await service.search_email("user@example.com")

# Checks:
# - Email services (Gmail, Outlook, etc.)
# - Breach databases (HaveIBeenPwned, etc.)
# - People search services (Spokeo, BeenVerified, etc.)
```

### Phone Search
```python
# Searches 14+ phone lookup platforms
results = await service.search_phone("+1-555-0123")

# Checks:
# - Phone lookup services (Truecaller, etc.)
# - People finders (Spokeo, BeenVerified, etc.)
# - Business databases (ZoomInfo, etc.)
```

## Platform Statistics

### Total Platforms: 150+

| Search Type | Count | Example Platforms |
|-------------|-------|-------------------|
| Username | 135+ | Twitter/X, GitHub, Reddit, Steam, Instagram, TikTok, Twitch, etc. |
| Email | 25+ | Gmail, Outlook, HaveIBeenPwned, Spokeo, etc. |
| Phone | 14+ | Truecaller, NumVerify, Spokeo, BeenVerified, etc. |

### By Category

| Category | Count |
|----------|-------|
| Social Media | 20+ |
| Gaming | 11+ |
| Streaming | 10+ |
| Developer | 9+ |
| Email Service/Verification | 25+ |
| Phone Lookup/Database | 14+ |
| Professional | 6+ |
| Dating | 10+ |
| Photography | 10+ |
| Music | 9+ |
| Forums | 10+ |
| Shopping | 8+ |
| Other | 20+ |

## Key Features

### 1. Automatic Search Type Detection
```python
# The system automatically filters platforms based on search type
# Username searches ONLY use username-supporting platforms
# Email searches ONLY use email-supporting platforms
# Phone searches ONLY use phone-supporting platforms
```

### 2. Comprehensive Coverage by Default
```python
# When no filters specified, searches use ALL appropriate platforms
# "ALL platforms by default" is the key principle
# Users can narrow down with optional filters
```

### 3. Flexible Filtering
Users can filter by:
- **Specific platforms**: `platforms=["GitHub", "Reddit"]`
- **Categories**: `categories=["SOCIAL_MEDIA", "GAMING"]`
- **NSFW**: `exclude_nsfw=True`
- **Custom combinations**: Mix and match filters

### 4. Intelligent Tagging
Each platform is tagged with:
- **Search type support**: Clearly marked which search types each platform supports
- **Category**: For grouped filtering
- **Metadata**: NSFW flag, login requirements, proxy requirements, etc.

### 5. Extensible Database
Easy to add new platforms:
```python
db.add_platform(
    name="NewPlatform",
    url="https://newplatform.com/",
    category=PlatformCategory.SOCIAL_MEDIA,
    search_url="https://newplatform.com/{username}",
    supports_username=True,
    supports_email=False,
    supports_phone=False,
)
```

## Database Methods

### Get Platforms by Type

```python
from nyx.osint.platforms import get_platform_database

db = get_platform_database()

# Get all username-searchable platforms
username_platforms = db.get_username_platforms()

# Get all email-searchable platforms
email_platforms = db.get_email_platforms()

# Get all phone-searchable platforms
phone_platforms = db.get_phone_platforms()

# Get by category
social_media = db.get_by_category(PlatformCategory.SOCIAL_MEDIA)

# Get NSFW platforms
adult_platforms = db.get_nsfw_platforms()

# Get active platforms
active = db.get_active_platforms()

# Count statistics
total = db.count_platforms()
social_count = db.count_by_category(PlatformCategory.SOCIAL_MEDIA)
```

## Performance Considerations

### Concurrent Searches
- Default: 100 concurrent platform checks
- Configurable: `SearchService(max_concurrent_searches=50)`
- Uses asyncio for efficient concurrent HTTP requests

### Caching
- Results cached with TTL (Time To Live)
- Multi-level cache (L1 in-memory, L2 persistent)
- Reduces redundant API calls

### Rate Limiting
- Per-platform rate limits supported
- Respects platform rate limits
- Exponential backoff on rate limit hits

## Adding New Platforms

### Manual Addition
```python
db.add_platform(
    name="Reddit",
    url="https://reddit.com/",
    category=PlatformCategory.FORUMS,
    username_param="user",
    search_url="https://www.reddit.com/user/{username}/",
    supports_username=True,
    supports_email=False,
    supports_phone=False,
)
```

### Bulk Addition from Dictionary
```python
platforms_dict = {
    "GitHub": {
        "url": "https://github.com/",
        "category": "DEVELOPER",
        "username_param": "user",
        "supports_username": True,
    },
    # ... more platforms
}

db.merge_from_dict(platforms_dict)
```

## Query Capabilities

The database supports queries like:

```python
# All username platforms (135+)
db.get_username_platforms()

# All email platforms (25+)
db.get_email_platforms()

# All phone platforms (14+)
db.get_phone_platforms()

# By category
db.get_by_category(PlatformCategory.SOCIAL_MEDIA)

# Active platforms only
db.get_active_platforms()

# NSFW platforms
db.get_nsfw_platforms()

# Single platform
db.get_platform("GitHub")

# Statistics
db.count_platforms()
db.count_by_category(PlatformCategory.GAMING)
```

## Future Expansion

The database is designed for easy expansion:

### Planned Additions
- Regional social networks
- Industry-specific platforms
- Specialized databases
- More email services
- More phone lookup services
- Government databases (where public)
- Academic repositories

### Contributing New Platforms
To add platforms:
1. Research platform structure and URL format
2. Verify username/email/phone detection method
3. Test detection method
4. Add to appropriate category
5. Document any special requirements

## Legal & Ethical Considerations

### Platform Terms of Service
- All searches respect platform Terms of Service
- No scraping where prohibited
- Rate limits and timeouts enforced
- User agents properly configured

### Privacy
- Results cached securely
- No data stored longer than necessary
- Encrypted storage for sensitive data
- GDPR/CCPA compliant design

### Ethical Use
Nyx is designed for:
- Law enforcement investigations
- Security research
- Bug bounty programs
- Authorized background checks
- Journalistic investigations

### Responsible Disclosure
- Never publish personal data found
- Report security issues responsibly
- Follow platform policies
- Respect privacy laws

## Troubleshooting

### No results found
- Verify platform is active
- Check platform's current status
- Verify username/email/phone format
- Check rate limiting isn't blocking
- Verify internet connectivity

### Too many concurrent searches
- Reduce `max_concurrent_searches` parameter
- Implement queue/batch processing
- Add delays between searches

### Rate limited
- Increase timeouts
- Reduce concurrent searches
- Add retry with exponential backoff
- Use proxy rotation

---

**Database Version**: 1.0
**Last Updated**: 2025-11-23
**Total Platforms**: 150+
**Categories**: 20+
**Search Types**: 3 (username, email, phone)
