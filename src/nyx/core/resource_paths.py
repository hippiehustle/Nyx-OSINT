"""Resource path resolution for executable and development environments."""

import os
import sys
from pathlib import Path
from typing import Optional


def _is_pyinstaller() -> bool:
    """Check if running from PyInstaller bundle."""
    return hasattr(sys, "_MEIPASS")


def get_base_path() -> Path:
    """Get the base path (executable directory or script directory).
    
    Returns:
        Path to the base directory where the executable or script is located
    """
    if _is_pyinstaller():
        # Running from PyInstaller bundle
        # sys.executable is the path to the .exe file
        return Path(sys.executable).parent
    else:
        # Running from development environment
        # Get the directory containing the main script
        if hasattr(sys, "frozen"):
            return Path(sys.executable).parent
        else:
            # Find the project root (where src/nyx is located)
            # This file is at: src/nyx/core/resource_paths.py
            current_file = Path(__file__).resolve()
            # Go up to project root
            return current_file.parent.parent.parent.parent


def get_data_path() -> Path:
    """Get the data directory path.
    
    Returns:
        Path to the data directory
    """
    base_path = get_base_path()
    
    if _is_pyinstaller():
        # In executable, data should be in executable directory or bundled
        data_path = base_path / "data"
        if data_path.exists():
            return data_path
        # Try bundled resources
        bundled_data = Path(sys._MEIPASS) / "data"
        if bundled_data.exists():
            return bundled_data
        # Fallback: create in executable directory
        return base_path / "data"
    else:
        # In development, use project root data directory
        return base_path / "data"


def get_config_path() -> Path:
    """Get the configuration directory path.
    
    Returns:
        Path to the configuration directory
    """
    base_path = get_base_path()
    
    if _is_pyinstaller():
        # In executable, config should be in executable directory or %APPDATA%
        # Try executable directory first
        config_path = base_path / "config"
        if config_path.exists():
            return config_path
        
        # Try bundled resources
        bundled_config = Path(sys._MEIPASS) / "config"
        if bundled_config.exists():
            return bundled_config
        
        # Fallback: use %APPDATA%/Nyx/config
        appdata = Path(os.getenv("APPDATA", ""))
        if appdata:
            appdata_config = appdata / "Nyx" / "config"
            appdata_config.mkdir(parents=True, exist_ok=True)
            return appdata_config
        
        # Last fallback: create in executable directory
        return base_path / "config"
    else:
        # In development, use project root config directory
        return base_path / "config"


def get_resource_path(relative_path: str) -> Path:
    """Get path to a bundled resource file.
    
    Args:
        relative_path: Relative path from resources directory (e.g., "data/platforms/file.json")
        
    Returns:
        Path to the resource file
    """
    if _is_pyinstaller():
        # In PyInstaller bundle, resources are in sys._MEIPASS
        return Path(sys._MEIPASS) / relative_path
    else:
        # In development, look in project root
        base_path = get_base_path()
        return base_path / relative_path


def get_user_data_path() -> Path:
    """Get the user data directory path (%APPDATA%/Nyx).
    
    Returns:
        Path to user data directory
    """
    appdata = Path(os.getenv("APPDATA", ""))
    if appdata:
        user_data = appdata / "Nyx"
        user_data.mkdir(parents=True, exist_ok=True)
        return user_data
    else:
        # Fallback to executable directory
        return get_base_path() / "user_data"


def get_cache_path() -> Path:
    """Get the cache directory path.
    
    Returns:
        Path to cache directory
    """
    if _is_pyinstaller():
        # Use temp directory or user data directory
        temp_dir = Path(os.getenv("TEMP", ""))
        if temp_dir:
            cache_path = temp_dir / "Nyx" / "cache"
            cache_path.mkdir(parents=True, exist_ok=True)
            return cache_path
        return get_user_data_path() / "cache"
    else:
        # In development, use project root cache
        return get_base_path() / "data" / "cache"


def get_log_path() -> Path:
    """Get the log file directory path.
    
    Returns:
        Path to log directory
    """
    if _is_pyinstaller():
        # Use user data directory for logs
        log_path = get_user_data_path() / "logs"
        log_path.mkdir(parents=True, exist_ok=True)
        return log_path
    else:
        # In development, use project root logs
        return get_base_path() / "logs"


def get_database_path() -> Path:
    """Get the database file path.
    
    Returns:
        Path to database file
    """
    if _is_pyinstaller():
        # Use user data directory for database
        db_path = get_user_data_path() / "nyx.db"
        return db_path
    else:
        # In development, use project root
        return get_base_path() / "nyx.db"

