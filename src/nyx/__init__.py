"""
Nyx (Net Yield Xtractor) - Professional OSINT Investigation Platform

A comprehensive open-source intelligence gathering and profile building tool
designed for law enforcement, security professionals, journalists, and
authorized investigators.

Features:
- 2500+ platform username search
- Email enumeration and breach database checking
- Phone number intelligence gathering
- Location intelligence from multiple sources
- Profile correlation and relationship analysis
- Comprehensive target profile management
- NSFW/adult platform detection
- Multiple export formats (HTML, PDF, JSON, CSV)
- Professional dark-themed GUI
- Tor and proxy support
- Complete privacy controls
"""

__version__ = "0.1.0"
__author__ = "OSINT Development Team"
__email__ = "nyx@osint.dev"
__license__ = "MIT"
__copyright__ = "Copyright 2025 OSINT Development Team"

# Core version info
VERSION_INFO = (0, 1, 0, "alpha")
VERSION = __version__

# Module imports
from nyx.config import Config, load_config, EncryptionManager
from nyx.core.logger import get_logger, setup_logging

__all__ = [
    "Config",
    "load_config",
    "EncryptionManager",
    "get_logger",
    "setup_logging",
    "__version__",
    "__author__",
    "__license__",
]

# Initialize logger
logger = get_logger(__name__)

logger.debug(f"Nyx v{__version__} initialized")
