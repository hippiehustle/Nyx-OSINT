"""Utility functions for update operations."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from nyx.core.logger import get_logger
from nyx.core.resource_paths import get_user_data_path

logger = get_logger(__name__)


def calculate_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate checksum of a file.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (sha256, md5, etc.)
        
    Returns:
        Hex digest of file checksum
    """
    if algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "md5":
        hasher = hashlib.md5()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum.
    
    Args:
        file_path: Path to file
        expected_checksum: Expected checksum (format: "sha256:hexdigest" or "md5:hexdigest")
        
    Returns:
        True if checksum matches
    """
    try:
        if ":" in expected_checksum:
            algorithm, expected = expected_checksum.split(":", 1)
        else:
            # Default to sha256 if no algorithm specified
            algorithm = "sha256"
            expected = expected_checksum
        
        actual = calculate_file_checksum(file_path, algorithm)
        return actual.lower() == expected.lower()
    except Exception as e:
        logger.error(f"Error verifying checksum: {e}", exc_info=True)
        return False


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def calculate_download_progress(downloaded: int, total: int) -> float:
    """Calculate download progress percentage.
    
    Args:
        downloaded: Bytes downloaded
        total: Total bytes to download
        
    Returns:
        Progress percentage (0-100)
    """
    if total == 0:
        return 0.0
    return min(100.0, (downloaded / total) * 100.0)


def get_update_history_path() -> Path:
    """Get path to update history file.
    
    Returns:
        Path to update history JSON file
    """
    user_data = get_user_data_path()
    return user_data / "update_history.json"


def load_update_history() -> List[Dict]:
    """Load update history.
    
    Returns:
        List of update history entries
    """
    history_path = get_update_history_path()
    if not history_path.exists():
        return []
    
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading update history: {e}", exc_info=True)
        return []


def save_update_history(history: List[Dict]):
    """Save update history.
    
    Args:
        history: List of update history entries
    """
    history_path = get_update_history_path()
    history_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving update history: {e}", exc_info=True)


def add_update_history_entry(version: str, action: str, success: bool, details: Optional[Dict] = None):
    """Add entry to update history.
    
    Args:
        version: Version string
        action: Action performed (check, download, install)
        success: Whether action was successful
        details: Additional details
    """
    history = load_update_history()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "version": version,
        "action": action,
        "success": success,
        "details": details or {},
    }
    
    history.append(entry)
    
    # Keep only last 100 entries
    if len(history) > 100:
        history = history[-100:]
    
    save_update_history(history)


def get_last_update_check() -> Optional[datetime]:
    """Get timestamp of last update check.
    
    Returns:
        Last check timestamp or None
    """
    history = load_update_history()
    
    for entry in reversed(history):
        if entry.get("action") == "check" and entry.get("success"):
            try:
                return datetime.fromisoformat(entry["timestamp"])
            except (ValueError, KeyError):
                continue
    
    return None


def get_last_installed_version() -> Optional[str]:
    """Get last successfully installed version.
    
    Returns:
        Version string or None
    """
    history = load_update_history()
    
    for entry in reversed(history):
        if entry.get("action") == "install" and entry.get("success"):
            return entry.get("version")
    
    return None

