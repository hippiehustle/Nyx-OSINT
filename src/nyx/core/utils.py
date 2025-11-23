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
