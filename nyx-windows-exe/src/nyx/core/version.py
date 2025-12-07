"""Version management and comparison utilities."""

import re
from dataclasses import dataclass
from typing import Optional, Tuple

from nyx import __version__, VERSION_INFO


@dataclass
class Version:
    """Semantic version representation."""
    
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None
    
    def __str__(self) -> str:
        """Convert to string representation."""
        version_str = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version_str += f"-{self.prerelease}"
        if self.build:
            version_str += f"+{self.build}"
        return version_str
    
    def __lt__(self, other: "Version") -> bool:
        """Compare versions (less than)."""
        if not isinstance(other, Version):
            return NotImplemented
        
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        
        # Prerelease versions are considered less than release versions
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        if self.prerelease and other.prerelease:
            return self.prerelease < other.prerelease
        
        return False
    
    def __le__(self, other: "Version") -> bool:
        """Compare versions (less than or equal)."""
        return self < other or self == other
    
    def __eq__(self, other: object) -> bool:
        """Compare versions (equal)."""
        if not isinstance(other, Version):
            return NotImplemented
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
            and self.build == other.build
        )
    
    def __ne__(self, other: object) -> bool:
        """Compare versions (not equal)."""
        return not self == other
    
    def __gt__(self, other: "Version") -> bool:
        """Compare versions (greater than)."""
        return not self <= other
    
    def __ge__(self, other: "Version") -> bool:
        """Compare versions (greater than or equal)."""
        return not self < other


def parse_version(version_str: str) -> Version:
    """Parse a version string into a Version object.
    
    Args:
        version_str: Version string (e.g., "1.2.3", "1.2.3-alpha", "1.2.3+build")
        
    Returns:
        Version object
        
    Raises:
        ValueError: If version string is invalid
    """
    # Pattern: major.minor.patch[-prerelease][+build]
    pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([\w\.-]+))?(?:\+([\w\.-]+))?$"
    match = re.match(pattern, version_str)
    
    if not match:
        raise ValueError(f"Invalid version string: {version_str}")
    
    major, minor, patch, prerelease, build = match.groups()
    
    return Version(
        major=int(major),
        minor=int(minor),
        patch=int(patch),
        prerelease=prerelease,
        build=build,
    )


def get_current_version() -> Version:
    """Get the current application version.
    
    Returns:
        Current version as Version object
    """
    try:
        return parse_version(__version__)
    except ValueError:
        # Fallback to VERSION_INFO tuple
        major, minor, patch, *rest = VERSION_INFO
        prerelease = rest[0] if rest and isinstance(rest[0], str) else None
        return Version(major, minor, patch, prerelease=prerelease)


def compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings.
    
    Args:
        version1: First version string
        version2: Second version string
        
    Returns:
        -1 if version1 < version2, 0 if equal, 1 if version1 > version2
    """
    v1 = parse_version(version1)
    v2 = parse_version(version2)
    
    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0


def is_update_available(current_version: str, latest_version: str) -> bool:
    """Check if an update is available.
    
    Args:
        current_version: Current version string
        latest_version: Latest available version string
        
    Returns:
        True if latest_version > current_version
    """
    return compare_versions(latest_version, current_version) > 0


def check_min_version_requirement(current_version: str, min_version: str) -> bool:
    """Check if current version meets minimum version requirement.
    
    Args:
        current_version: Current version string
        min_version: Minimum required version string
        
    Returns:
        True if current_version >= min_version
    """
    return compare_versions(current_version, min_version) >= 0


def get_version_info() -> dict:
    """Get comprehensive version information.
    
    Returns:
        Dictionary with version information
    """
    version = get_current_version()
    
    return {
        "version": str(version),
        "major": version.major,
        "minor": version.minor,
        "patch": version.patch,
        "prerelease": version.prerelease,
        "build": version.build,
        "version_info": VERSION_INFO,
    }

