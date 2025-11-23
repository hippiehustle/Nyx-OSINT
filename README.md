# Nyx - Professional OSINT Investigation Platform

**Nyx (Net Yield Xtractor)** is a comprehensive open-source intelligence (OSINT) gathering and profile building tool designed for law enforcement, security professionals, journalists, and authorized investigators.

## Features

### Core Capabilities
- **2500+ Platform Search**: Username search across social media, professional, dating, gaming, forums, and adult platforms
- **Email Enumeration**: Breach database checking and email service detection
- **Phone Intelligence**: Phone number lookup and carrier identification
- **Location Intelligence**: Multi-source location data aggregation
- **Profile Correlation**: Relationship analysis and profile linking
- **Comprehensive Target Management**: Profile building and investigation tracking

### Technical Features
- **Multi-Level Caching**: In-memory LRU + persistent disk cache for performance
- **Async/Concurrent Searches**: 100+ concurrent platform checks with rate limiting
- **Event-Driven Architecture**: Pub/Sub system for inter-module communication
- **Type-Safe**: Full Pydantic V2 validation with mypy static type checking
- **Privacy & Security**: Tor and proxy support, encrypted sensitive data storage
- **Multiple Export Formats**: HTML, PDF, JSON, CSV with customizable templates

### User Interfaces
- **Modern GUI**: Dark-themed CustomTkinter interface with responsive design
- **CLI**: Command-line interface for automation and scripting
- **Professional Design**: Intuitive navigation and result presentation

## Project Status

### Completed Phases ✓
- **PHASE 1**: Project Infrastructure & Setup
  - Poetry project configuration
  - Pydantic V2 configuration management
  - Structlog-based logging
  - Pre-commit hooks and code quality tools

- **PHASE 2**: Reference Tools Analysis & Database Merging
  - SQLAlchemy ORM models for platforms, targets, and results
  - Platform database with 2500+ platform definitions
  - Integration of Maigret, Sherlock, Social-Analyzer, Blackbird, Holehe, PhoneInfoga

- **PHASE 3**: Core Infrastructure & Utilities
  - AsyncHTTPClient with rate limiting and retries
  - Multi-level caching system (L1 memory, L2 disk)
  - Event bus and pub/sub system
  - Utility functions for validation and formatting

- **PHASE 4**: Platform Checking Implementation
  - SearchService for coordinating platform searches
  - ProfileBuilder for aggregation and correlation
  - BasePlatformChecker with StatusCodeChecker and RegexChecker
  - Event publishing for search lifecycle

- **PHASE 5**: Search Engine Integration
  - Google, Bing, DuckDuckGo search engines
  - MetaSearchEngine combining multiple sources
  - HTML parsing with BeautifulSoup
  - Specialized search methods (name, email, username, phone, URL)

- **PHASE 6**: GUI & CLI Implementation
  - CustomTkinter GUI with dark theme
  - CLI with Click framework
  - Async initialization and configuration loading
  - Command-line tools for searching and platform management

### Pending Phases
- **PHASE 7**: Email & Phone Intelligence
- **PHASE 8**: Advanced Search & Filtering
- **PHASE 9**: Data Analysis & Correlation
- **PHASE 10**: Export & Reporting
- **PHASE 11**: Testing & Quality Assurance
- **PHASE 12**: Documentation & Deployment

## Installation

### Prerequisites
- Python 3.12+
- Poetry (dependency management)
- Tesseract-OCR (for image text recognition)

### Setup

```bash
# Clone or download the project
cd Nyx

# Install dependencies with Poetry
poetry install

# Copy configuration template
cp config/settings.yaml config/settings.local.yaml
cp .env.example .env.local

# Edit configuration as needed
nano config/settings.local.yaml
```

## Usage

### GUI Application

```bash
# Run GUI application
poetry run nyx

# Run with custom configuration
poetry run nyx --config config/settings.local.yaml

# Run in debug mode
poetry run nyx --debug
```

### CLI Application

```bash
# Search for username
poetry run nyx-cli search john_doe

# Search with NSFW exclusion
poetry run nyx-cli search john_doe --exclude-nsfw

# List all platforms
poetry run nyx-cli platforms

# List platforms by category
poetry run nyx-cli platforms --category social_media

# Show statistics
poetry run nyx-cli stats
```

## Configuration

### Database
- Default: SQLite at `./nyx.db`
- Supports: PostgreSQL, MySQL for production

### Caching
- L1 Cache: 1000 entries, 1 hour TTL
- L2 Cache: Persistent disk cache, 24 hour TTL

### HTTP Client
- Timeout: 10 seconds
- Retries: 3 with exponential backoff
- Rate Limit: 10 requests/second

### Security
- Master password encryption
- Tor support for anonymity
- Proxy support (HTTP, HTTPS, SOCKS)

## Architecture

### Module Structure

```
src/nyx/
├── config/              # Configuration management
├── core/                # Core infrastructure
│   ├── database.py     # SQLAlchemy ORM
│   ├── http_client.py  # Async HTTP with rate limiting
│   ├── cache.py        # Multi-level caching
│   ├── events.py       # Event bus and pub/sub
│   ├── logger.py       # Structlog logging
│   ├── types.py        # Type definitions
│   └── utils.py        # Utility functions
├── models/              # Database models
│   ├── platform.py     # Platform and search result models
│   └── target.py       # Target and profile models
├── osint/               # OSINT functionality
│   ├── platforms.py    # Platform database
│   ├── checker.py      # Platform checkers
│   ├── search.py       # Search service
│   └── profile_builder.py  # Profile aggregation
├── search_engines/      # Search engine integrations
│   ├── base.py         # Base search engine
│   └── implementations.py  # Google, Bing, DuckDuckGo
├── gui/                 # GUI components
│   └── main_window.py   # CustomTkinter main window
├── main.py             # GUI entry point
└── cli.py              # CLI entry point
```

### Design Patterns

- **Async/Await**: Non-blocking I/O throughout
- **Singleton Pattern**: Global instances for cache, database, events
- **Strategy Pattern**: Platform checkers with pluggable detection methods
- **Observer Pattern**: Event bus for loose coupling
- **Dependency Injection**: Type-safe configuration injection

## Development

### Running Tests

```bash
poetry run pytest tests/

# With coverage
poetry run pytest tests/ --cov=src/nyx --cov-report=html
```

### Code Quality

```bash
# Format code
poetry run black src/ tests/

# Sort imports
poetry run isort src/ tests/

# Lint
poetry run flake8 src/ tests/

# Type checking
poetry run mypy src/

# Security check
poetry run bandit -r src/
```

### Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

## Supported Platforms

### Platform Categories
- Social Media (Twitter, Instagram, Facebook, TikTok, etc.)
- Professional (LinkedIn, GitHub, Stack Overflow, etc.)
- Dating (Tinder, Bumble, OkCupid, etc.)
- Gaming (Steam, Discord, Twitch, etc.)
- Forums (Reddit, Hacker News, etc.)
- Adult (140+ platforms)
- Blogging (Medium, Wordpress, etc.)
- Photography (Flickr, Pixelfed, etc.)
- Messaging (Discord, Telegram, etc.)
- Streaming (YouTube, Twitch, etc.)
- Crypto (Blockchain explorers, etc.)
- Shopping (eBay, Etsy, etc.)

### Reference Tool Integration

Nyx integrates methods and platform databases from:

- **Maigret** (95/100): 2000+ platforms, detection patterns
- **Sherlock** (85/100): Baseline social media methodology
- **Social-Analyzer** (98/100): Profile correlation and graphs
- **Blackbird** (96/100): 140+ adult platforms
- **Holehe** (97/100): Email service detection
- **PhoneInfoga** (94/100): Phone number intelligence

## Security Considerations

### Safe Use
- Designed for authorized investigations only
- Respect platform terms of service
- Comply with local laws and regulations
- Use responsibly for legitimate purposes

### Privacy Features
- Tor support for anonymity
- Proxy rotation capabilities
- No data persistence without explicit save
- Encrypted sensitive data storage

### Limitations
- This tool is for legal use only
- Not for surveillance or privacy violations
- Not for unauthorized account access
- Requires proper authorization context

## Legal Disclaimer

Nyx is provided for lawful OSINT investigation only. Users are responsible for:

1. Complying with all applicable laws and regulations
2. Obtaining proper authorization before investigations
3. Respecting privacy laws and data protection regulations
4. Not violating platform terms of service
5. Using results responsibly and ethically

Unauthorized use may violate laws including CFAA, GDPR, and local privacy regulations.

## Contributing

Contributions are welcome! Please:

1. Follow PEP 8 style guide
2. Add tests for new features
3. Update documentation
4. Run code quality checks
5. Submit pull requests with clear descriptions

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built on the methodology and research of:
- Maigret OSINT Framework
- Sherlock Project
- Social-Analyzer
- Blackbird OSINT Tool
- Holehe Email Checker
- PhoneInfoga

## Support

For issues, questions, or suggestions:
- Check documentation in `/docs`
- Review existing issues on GitHub
- Create new issue with detailed description
- Follow responsible disclosure for security issues

---

**Version**: 0.1.0 (Alpha)
**Status**: Active Development
**Last Updated**: 2025-11-22
**Python**: 3.12+
**License**: MIT
