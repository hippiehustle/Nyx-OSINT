# Nyx - Professional OSINT Investigation Platform

**Nyx (Net Yield Xtractor)** is a comprehensive open-source intelligence (OSINT) gathering and profile building tool designed for law enforcement, security professionals, journalists, and authorized investigators.

## Features

### Core Capabilities
- **2500+ Platform Search**: Username search across social media, professional, dating, gaming, forums, and adult platforms
- **Email Intelligence**: Full email validation, breach checking (HIBP), service detection, reputation scoring, optional online profile discovery
- **Phone Intelligence**: Auto-region detection, phone number parsing, validation, carrier lookup, location inference, line type detection, name/address association
- **Person Lookup (WHOIS)**: Comprehensive person investigation by name and state - find addresses, phone numbers, relatives, associates, social profiles, and employment history
- **Deep Investigation**: Unified comprehensive search that automatically detects query type and runs all applicable searches (username, email, phone, person)
- **Advanced Filtering**: 9 filter operators, query language, saved searches, batch processing
- **Data Analysis**: Correlation analysis, relationship graphs, timeline analysis, pattern detection
- **Profile Correlation**: Relationship analysis and profile linking with confidence scoring
- **Export & Reporting**: HTML, PDF, JSON, CSV exports with professional templates and redaction

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

**✅ ALL PHASES COMPLETE - Production Ready**

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed information.

### Completed Phases ✓ (12/12 - 100%)
- **PHASE 1**: Project Infrastructure & Setup
- **PHASE 2**: Reference Tools Analysis & Database Merging
- **PHASE 3**: Core Infrastructure & Utilities
- **PHASE 4**: Platform Checking Implementation
- **PHASE 5**: Search Engine Integration
- **PHASE 6**: GUI & CLI Implementation
- **PHASE 7**: Email & Phone Intelligence ✅ NEW
  - Email validation, breach checking, service detection
  - Phone number parsing, validation, carrier lookup
  - Reputation scoring and intelligence gathering
- **PHASE 8**: Advanced Search & Filtering ✅ NEW
  - Advanced filtering with 9 operators
  - Saved search management
  - Batch processing for multiple targets
- **PHASE 9**: Data Analysis & Correlation ✅ NEW
  - Correlation analysis and pattern detection
  - Relationship graph generation
  - Timeline analysis and temporal patterns
- **PHASE 10**: Export & Reporting ✅ NEW
  - HTML, PDF, JSON, CSV export formats
  - Professional report templates
  - Field redaction support
- **PHASE 11**: Testing & Quality Assurance ✅ NEW
  - Comprehensive unit tests (50+ test cases)
  - Integration test structure
  - Code coverage tracking
- **PHASE 12**: Documentation & Deployment ✅ NEW
  - Complete API documentation
  - User manual and guides
  - Docker containerization

## Installation

### 🚀 Quick Start (Recommended)

**Automated guided setup wizard handles everything for you!**

#### Linux / macOS / WSL
```bash
# Make executable and run
chmod +x setup.sh
./setup.sh
```

#### Windows (PowerShell)
```powershell
# Run as Administrator (recommended)
.\setup.ps1
```

The setup wizard will:
- ✅ Detect and install Python 3.12+
- ✅ Install Poetry dependency manager
- ✅ Configure environment variables
- ✅ Install all dependencies (including Playwright browsers)
- ✅ Initialize database
- ✅ Verify installation
- ✅ Provide detailed setup logs

**See [QUICKSTART.md](QUICKSTART.md) for a quick reference or [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for detailed instructions.**

---

### Manual Installation

If you prefer manual setup:

#### Prerequisites
- Python 3.12+
- Poetry (dependency management)
- Tesseract-OCR (optional, for image text recognition)

#### Steps

```bash
# Clone or download the project
cd Nyx-OSINT

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies with Poetry
poetry install

# Copy configuration template
cp .env.example .env
cp config/settings.yaml config/settings.local.yaml

# Initialize database
poetry run python -c "from nyx.core.database import initialize_database; import asyncio; asyncio.run(initialize_database())"

# Verify installation
poetry run nyx-cli --version
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
# Username search
poetry run nyx-cli search -u john_doe

# Username search with NSFW exclusion
poetry run nyx-cli search -u john_doe --no-nsfw

# Email intelligence
poetry run nyx-cli search -e user@example.com

# Email with online profile discovery (slower but more thorough)
poetry run nyx-cli search -e user@example.com --profiles

# Phone intelligence (auto-detects region from number format)
poetry run nyx-cli search -p +14155552671

# Phone with explicit region
poetry run nyx-cli search -p 4155552671 --region US

# Person lookup (WHOIS)
poetry run nyx-cli search -w "John Doe" --region CA

# Person lookup with middle name/initial
poetry run nyx-cli search -w "John M Doe" --region NY

# Deep investigation (comprehensive search using all methods)
poetry run nyx-cli search -d "john.doe@email.com"
poetry run nyx-cli search -d "+14155552671"
poetry run nyx-cli search -d "John Doe"

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

## Docker Deployment

### Quick Start with Docker

```bash
# Build and run CLI
docker-compose up nyx-cli

# Build and run GUI (requires X11 forwarding)
docker-compose up nyx-gui

# Run with PostgreSQL and Tor
docker-compose up nyx-postgres tor-proxy
```

## Development

### Running Tests

```bash
poetry run pytest tests/

# With coverage
poetry run pytest tests/ --cov=src/nyx --cov-report=html
```

### Documentation

- **API Documentation**: [docs/API.md](docs/API.md)
- **User Manual**: [docs/USER_MANUAL.md](docs/USER_MANUAL.md)
- **Project Status**: [PROJECT_STATUS.md](PROJECT_STATUS.md)

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
