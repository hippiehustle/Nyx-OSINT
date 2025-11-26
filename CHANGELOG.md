# Changelog

All notable changes to the Nyx OSINT Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-11-26

### Added

#### Major Search Enhancements
- **Phone Search Auto-Detection**: Phone numbers now automatically detect region from format
- **Phone Name Lookup**: Added associated name discovery for phone numbers
- **Phone Address Lookup**: Find addresses linked to phone numbers
- **Email Profile Search**: New `--profiles` flag for extensive online profile discovery
- **Person Lookup (WHOIS)**: Complete new search type `-w/--whois` for person investigations
  - Find addresses, phone numbers, emails, relatives, associates
  - Social profile discovery across 2000+ platforms
  - Employment and education history
  - State filtering support
- **Deep Investigation**: New `-d/--deep` search type with intelligent query detection
  - Automatically detects if query is email, phone, username, or person name
  - Runs all applicable searches concurrently
  - Unified comprehensive reporting

#### GUI Overhaul
- **Complete Redesign**: Professional dark theme with modern interface
- **Multi-Type Search**: Radio buttons for Username, Email, Phone, Person, Deep searches
- **Real-Time Progress**: Live progress bar and status updates during searches
- **Async Execution**: All searches run in background without freezing UI
- **Results View**: Dedicated results display with export functionality
- **Settings Panel**: Appearance controls and about information
- **Error Handling**: Comprehensive error handling with user-friendly messages

#### CLI Improvements
- **Animated Progress Tracker**: Live updating spinner showing checked/found counts
- **Enhanced Help**: Comprehensive examples and documentation
- **Better Validation**: Clear error messages and input validation
- **Verbose Mode**: Debug logging with `-v/--verbose` flag

### Changed
- **Search Timeout**: Increased default from 30s to 120s for large searches
- **Platform Loading**: Fixed path resolution for JSON platform files
- **Progress Tracking**: Progress callback now properly passed through search service

### Fixed
- **False Positives**: Enhanced validation to reduce false positive matches
- **Username Detection**: Improved URL validation to reject root domain redirects
- **Progress Updates**: Progress tracker now shows real-time statistics
- **Platform JSON Loading**: Fixed Windows path issues for loading 1300+ additional platforms
- **Logger Import**: Fixed missing logger import in platforms.py

### Technical
- **New Modules**: 
  - `src/nyx/intelligence/person.py` - Person investigation engine
  - Enhanced `email.py` with profile search
  - Enhanced `phone.py` with auto-detection
- **Code Quality**: Comprehensive error handling and logging throughout
- **Documentation**: Updated README with all new features and examples
- **Testing**: All core functionality validated and production-ready

## [0.0.1] - 2024-11-23

### Added
- Initial release with core OSINT functionality
- Username search across 2000+ platforms
- Email and phone intelligence gathering
- Basic GUI and CLI interfaces
- Export functionality (HTML, PDF, JSON, CSV)
- Advanced filtering and search capabilities
- Data correlation and analysis tools

---

[0.1.0]: https://github.com/hippiehustle/Nyx-OSINT/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/hippiehustle/Nyx-OSINT/releases/tag/v0.0.1
