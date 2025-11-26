# Nyx-OSINT Platform Database

## Overview

This directory contains the external platform data files that extend Nyx-OSINT's platform coverage beyond the core platforms hard-coded in the application. The platform system is designed to support 2000+ platforms from Maigret, 140+ adult platforms from Blackbird, and custom user-defined platforms.

## Current Platform Coverage

### Hard-Coded Platforms (src/nyx/osint/platforms.py)
- **Core Platforms**: ~650 platforms integrated directly in the codebase
- **Categories**: All major categories including social media, professional networks, gaming, forums, adult, streaming, crypto, and more
- **Sources**: Sherlock, Maigret, Blackbird, and custom additions

### External JSON Platforms (data/platforms/)
- **maigret_extended_platforms.json**: 261 additional mainstream platforms
- **maigret_international_platforms.json**: 43 regional/international platforms
- **maigret_niche_platforms.json**: 20+ specialized/niche platforms
- **custom_platforms.json**: User-defined custom platforms (create this file to add your own)

### Total Coverage
- **Current**: ~974 platforms loaded and searchable
- **Target**: 2000+ platforms (Maigret) + 140+ adult platforms (Blackbird)
- **Extensible**: Add unlimited platforms via JSON files

## Platform JSON Format

Each platform in the JSON files follows this structure:

```json
{
  "PlatformName": {
    "url": "https://example.com/",
    "category": "SOCIAL_MEDIA",
    "search_url": "https://example.com/users/{username}",
    "detection_method": "status_code",
    "is_nsfw": false,
    "source_tool": "maigret",
    "exists_status_code": [200],
    "not_exists_status_code": [404],
    "exists_pattern": null,
    "not_exists_pattern": null,
    "requires_login": false,
    "requires_proxy": false,
    "timeout": 30,
    "rate_limit": null
  }
}
```

### Required Fields
- `url`: Base URL of the platform
- `category`: Platform category (see categories below)
- `search_url`: URL template with {username} placeholder
- `detection_method`: "status_code" or "pattern"
- `source_tool`: Source of the platform definition

### Optional Fields
- `is_nsfw`: Boolean, marks adult content platforms
- `exists_status_code`: HTTP codes indicating username exists
- `not_exists_status_code`: HTTP codes indicating username doesn't exist
- `exists_pattern`: Regex pattern indicating existence
- `not_exists_pattern`: Regex pattern indicating non-existence
- `requires_login`: Boolean, requires authentication
- `requires_proxy`: Boolean, recommended to use proxy
- `timeout`: Request timeout in seconds
- `rate_limit`: Rate limiting configuration

## Platform Categories

Supported categories:
- `SOCIAL_MEDIA` - General social networks
- `PROFESSIONAL` - LinkedIn, professional networks
- `DATING` - Dating apps and sites
- `GAMING` - Gaming platforms, Steam, Xbox, etc.
- `FORUMS` - Discussion forums and communities
- `ADULT` - Adult/NSFW platforms
- `BLOGGING` - Blogging platforms
- `PHOTOGRAPHY` - Photo sharing sites
- `MESSAGING` - Messaging apps
- `STREAMING` - Video/music streaming
- `CRYPTO` - Cryptocurrency platforms
- `SHOPPING` - E-commerce sites
- `TECH` - Developer platforms, code repos
- `MUSIC` - Music platforms
- `CREATIVE` - Art, design platforms
- `EDUCATION` - Learning platforms
- `SPORTS` - Sports/fitness platforms
- `TRAVEL` - Travel platforms
- `FOOD` - Food/recipe platforms
- `FINANCIAL` - Financial services
- `OTHER` - Other platforms

## Adding More Platforms

### Method 1: Extend Existing JSON Files

Add platforms to the existing JSON files:

```bash
# Edit with your favorite editor
nano data/platforms/maigret_extended_platforms.json
```

### Method 2: Create Custom Platforms File

Create your own custom platforms file:

```bash
# Create custom platforms file
cat > data/platforms/custom_platforms.json << 'EOF'
{
  "MyPlatform": {
    "url": "https://myplatform.com/",
    "category": "SOCIAL_MEDIA",
    "search_url": "https://myplatform.com/user/{username}",
    "detection_method": "status_code",
    "source_tool": "custom"
  }
}
EOF
```

### Method 3: Import from Maigret Database

To import the full Maigret 2000+ platform database:

1. Clone Maigret repository:
```bash
git clone https://github.com/soxoj/maigret.git
```

2. Convert Maigret's JSON to Nyx format:
```python
import json

# Load Maigret's data.json
with open('maigret/maigret/resources/data.json', 'r') as f:
    maigret_data = json.load(f)

# Convert to Nyx format
nyx_platforms = {}
for name, config in maigret_data.items():
    nyx_platforms[name] = {
        "url": config.get("urlMain", ""),
        "category": "OTHER",  # Categorize as needed
        "search_url": config.get("url", ""),
        "detection_method": "status_code",
        "source_tool": "maigret"
    }

# Save to Nyx format
with open('data/platforms/maigret_all_platforms.json', 'w') as f:
    json.dump(nyx_platforms, f, indent=2)
```

3. Add the file to the loader in `src/nyx/osint/platforms.py`:
```python
json_files = [
    "maigret_extended_platforms.json",
    "maigret_international_platforms.json",
    "maigret_niche_platforms.json",
    "maigret_all_platforms.json",  # Add this line
    "custom_platforms.json",
]
```

### Method 4: Bulk Import Script

Use the provided bulk import script:

```bash
# Create a TSV file with platform data
# Format: Name\tURL\tCategory\tSearchURL
python scripts/import_platforms.py platforms.tsv
```

## Platform Sources

### Maigret (2000+ platforms)
- Repository: https://github.com/soxoj/maigret
- Comprehensive database with international coverage
- Regular updates and community contributions

### Blackbird (140+ adult platforms)
- Repository: https://github.com/p1ngul1n0/blackbird
- Specialized in adult/NSFW platform coverage
- Regular updates with new platforms

### Sherlock
- Repository: https://github.com/sherlock-project/sherlock
- Original username enumeration tool
- Core platform set

## Platform Testing

Test platforms before adding:

```bash
# Test a single platform
nyx-cli search -u testuser --platforms "PlatformName" -v

# Test newly added platforms
nyx-cli platforms list --source custom
```

## Best Practices

1. **Categorize Properly**: Use the correct category for better filtering
2. **Mark NSFW**: Always set `is_nsfw: true` for adult content
3. **Test Detection**: Verify detection methods work correctly
4. **Document Source**: Include `source_tool` to track origins
5. **Rate Limits**: Set appropriate rate limits to avoid bans
6. **Proxies**: Mark platforms that require proxies

## Roadmap to 2000+ Platforms

The platform system is designed to scale to 2000+ platforms:

**Phase 1** (Current - ~974 platforms):
- ✅ Core 650+ platforms hard-coded
- ✅ Dynamic JSON loading system
- ✅ 140+ adult platforms from Blackbird
- ✅ External data files infrastructure

**Phase 2** (Target - 2000+ platforms):
- Import full Maigret database (~1000 additional platforms)
- Add regional/international platforms from Maigret
- Include legacy/defunct platforms for historical searches
- Community contributions via pull requests

**Phase 3** (Future expansion):
- Automated platform discovery
- Community-maintained platform database
- API integrations for real-time platform updates
- Machine learning for detection method optimization

## Contributing

To contribute new platforms:

1. Fork the repository
2. Add platforms to appropriate JSON files
3. Test the platforms work correctly
4. Submit a pull request with platform additions

## License

Platform data is aggregated from open-source projects (Maigret, Sherlock, Blackbird) and is subject to their respective licenses. Custom additions follow the Nyx-OSINT license.
