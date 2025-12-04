"""Utility functions for Nyx."""

import re
from typing import List, Optional
from urllib.parse import quote, urljoin, urlunsplit


def sanitize_username(username: str, min_length: int = 1, max_length: int = 255) -> Optional[str]:
    """Sanitize and validate username.

    Args:
        username: Username to sanitize
        min_length: Minimum username length
        max_length: Maximum username length

    Returns:
        Sanitized username or None if invalid
    """
    if not username or not isinstance(username, str):
        return None

    # Strip whitespace
    username = username.strip()

    # Check length
    if len(username) < min_length or len(username) > max_length:
        return None

    # Remove special characters (keep alphanumeric, dash, underscore, dot)
    username = re.sub(r"[^\w\-\.]", "", username)

    return username if username else None


def format_url(base_url: str, username: str, param_name: str = "user") -> str:
    """Format URL with username parameter.

    Args:
        base_url: Base URL or URL pattern
        username: Username to insert
        param_name: Parameter name for username

    Returns:
        Formatted URL
    """
    # Escape username for URL
    escaped = quote(username, safe="")

    # Try different formatting approaches
    if "{username}" in base_url:
        return base_url.format(username=escaped)
    elif "{" + param_name + "}" in base_url:
        return base_url.format(**{param_name: escaped})
    else:
        # Assume it's a base URL and append username
        separator = "/" if not base_url.endswith("/") else ""
        return f"{base_url}{separator}{escaped}"


def validate_email(email: str) -> bool:
    """Validate email address format.

    Args:
        email: Email to validate

    Returns:
        Whether email is valid format
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format.

    Args:
        phone: Phone number to validate

    Returns:
        Whether phone number looks valid
    """
    # Simple check for digits and common separators
    cleaned = re.sub(r"[\s\-\(\)\.+]", "", phone)
    return bool(re.match(r"^\d{7,15}$", cleaned))


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL.

    Args:
        url: URL to extract from

    Returns:
        Domain or None if invalid
    """
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url if "://" in url else f"https://{url}")
        domain = parsed.netloc
        return domain if domain else None
    except Exception:
        return None


def is_url(text: str) -> bool:
    """Check if text is a valid URL.

    Args:
        text: Text to check

    Returns:
        Whether text is URL-like
    """
    url_pattern = r"https?://[^\s]+"
    return bool(re.match(url_pattern, text))


def split_text_into_chunks(text: str, chunk_size: int = 1000) -> List[str]:
    """Split text into chunks of specified size.

    Args:
        text: Text to split
        chunk_size: Size of each chunk

    Returns:
        List of text chunks
    """
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i : i + chunk_size])
    return chunks


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text.

    Args:
        text: Text to normalize

    Returns:
        Text with normalized whitespace
    """
    return " ".join(text.split())


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data showing only first few characters.

    Args:
        data: Data to mask
        visible_chars: Number of characters to show

    Returns:
        Masked data
    """
    if len(data) <= visible_chars:
        return "*" * len(data)
    return data[:visible_chars] + "*" * (len(data) - visible_chars)


def sanitize_file_path(file_path: str, base_dir: Optional[str] = None) -> Optional[str]:
    """Sanitize file path to prevent directory traversal attacks.

    Args:
        file_path: File path to sanitize
        base_dir: Base directory to restrict paths to (optional)

    Returns:
        Sanitized file path or None if invalid
    """
    if not file_path or not isinstance(file_path, str):
        return None

    # Remove any path traversal attempts
    file_path = file_path.replace("..", "").replace("~", "")
    file_path = file_path.strip()

    # Remove leading slashes
    file_path = file_path.lstrip("/\\")

    # If base_dir is provided, ensure path is within it
    if base_dir:
        from pathlib import Path
        try:
            resolved = Path(base_dir) / file_path
            resolved = resolved.resolve()
            base_resolved = Path(base_dir).resolve()
            if not str(resolved).startswith(str(base_resolved)):
                return None
            return str(resolved)
        except Exception:
            return None

    return file_path if file_path else None


def sanitize_url(url: str) -> Optional[str]:
    """Sanitize and validate URL.

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL or None if invalid
    """
    if not url or not isinstance(url, str):
        return None

    url = url.strip()

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.netloc:
            return None
        return url
    except Exception:
        return None


def validate_name(name: str, min_length: int = 1, max_length: int = 100) -> bool:
    """Validate person name format.

    Args:
        name: Name to validate
        min_length: Minimum name length
        max_length: Maximum name length

    Returns:
        Whether name is valid
    """
    if not name or not isinstance(name, str):
        return False

    name = name.strip()

    if len(name) < min_length or len(name) > max_length:
        return False

    # Allow letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        return False

    return True


def sanitize_query(query: str, max_length: int = 1000) -> Optional[str]:
    """Sanitize search query.

    Args:
        query: Query to sanitize
        max_length: Maximum query length

    Returns:
        Sanitized query or None if invalid
    """
    if not query or not isinstance(query, str):
        return None

    query = query.strip()

    if len(query) > max_length:
        query = query[:max_length]

    # Remove control characters
    query = "".join(char for char in query if ord(char) >= 32 or char in "\n\r\t")

    return query if query else None