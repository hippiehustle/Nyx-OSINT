# Plugin Development Guide

This guide explains how to create custom platform checkers and extend Nyx-OSINT functionality.

## Table of Contents

1. [Overview](#overview)
2. [Creating a Plugin](#creating-a-plugin)
3. [Plugin Interface](#plugin-interface)
4. [Examples](#examples)
5. [Best Practices](#best-practices)
6. [Testing Plugins](#testing-plugins)
7. [Advanced Topics](#advanced-topics)

---

## Overview

Nyx-OSINT uses a plugin system to allow custom platform checkers. Plugins can:

- Add support for new platforms
- Implement custom checking logic
- Integrate with external APIs
- Extend existing functionality

### Plugin Types

1. **Platform Checker Plugins**: Check if a username exists on a platform
2. **Intelligence Plugins**: Add new intelligence gathering capabilities
3. **Export Plugins**: Add new export formats

---

## Creating a Plugin

### Basic Structure

```python
from nyx.osint.plugin import PlatformCheckerPlugin
from nyx.osint.profile import Profile
from typing import Optional

class MyPlatformChecker(PlatformCheckerPlugin):
    """Custom platform checker for MyPlatform."""
    
    async def check(self, username: str) -> Optional[Profile]:
        """Check if username exists on MyPlatform.
        
        Args:
            username: Username to check
            
        Returns:
            Profile if found, None otherwise
        """
        # Implementation here
        pass
    
    def get_platform_name(self) -> str:
        """Return the platform name."""
        return "myplatform"
```

### Required Methods

#### `check(username: str) -> Optional[Profile]`

This method performs the actual check. It should:

- Return a `Profile` object if the username exists
- Return `None` if the username doesn't exist
- Raise exceptions for errors (not for "not found")

#### `get_platform_name() -> str`

Returns the platform identifier (used for registration).

---

## Plugin Interface

### PlatformCheckerPlugin

Base class for platform checker plugins:

```python
from abc import ABC, abstractmethod
from typing import Optional
from nyx.osint.profile import Profile

class PlatformCheckerPlugin(ABC):
    """Abstract base class for platform checker plugins."""
    
    @abstractmethod
    async def check(self, username: str) -> Optional[Profile]:
        """Check if username exists on platform.
        
        Args:
            username: Username to check
            
        Returns:
            Profile if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return platform identifier."""
        pass
    
    def get_platform_url(self, username: str) -> str:
        """Generate platform URL for username.
        
        Args:
            username: Username
            
        Returns:
            Platform URL
        """
        # Default implementation
        return f"https://{self.get_platform_name()}.com/{username}"
```

---

## Examples

### Example 1: Simple Status Code Checker

```python
from nyx.osint.plugin import PlatformCheckerPlugin
from nyx.osint.profile import Profile
from nyx.core.http_client import HTTPClient
from typing import Optional

class SimplePlatformChecker(PlatformCheckerPlugin):
    """Simple checker using HTTP status codes."""
    
    def __init__(self):
        self.base_url = "https://example.com"
        self.http_client = HTTPClient()
    
    async def check(self, username: str) -> Optional[Profile]:
        """Check username using status code."""
        url = f"{self.base_url}/{username}"
        
        try:
            response = await self.http_client.get(url)
            
            if response.status_code == 200:
                return Profile(
                    platform=self.get_platform_name(),
                    username=username,
                    url=url,
                    exists=True,
                )
            return None
        except Exception:
            return None
    
    def get_platform_name(self) -> str:
        return "example"
    
    async def aclose(self):
        """Clean up resources."""
        await self.http_client.aclose()
```

### Example 2: JSON API Checker

```python
from nyx.osint.plugin import PlatformCheckerPlugin
from nyx.osint.profile import Profile
from nyx.core.http_client import HTTPClient
from typing import Optional, Dict, Any
import json

class JSONAPIChecker(PlatformCheckerPlugin):
    """Checker using JSON API responses."""
    
    def __init__(self):
        self.api_url = "https://api.example.com/users"
        self.http_client = HTTPClient()
    
    async def check(self, username: str) -> Optional[Profile]:
        """Check username via JSON API."""
        url = f"{self.api_url}/{username}"
        
        try:
            response = await self.http_client.get(url)
            
            if response.status_code == 200:
                data: Dict[str, Any] = response.json()
                
                return Profile(
                    platform=self.get_platform_name(),
                    username=username,
                    url=f"https://example.com/{username}",
                    exists=True,
                    metadata={
                        "display_name": data.get("name"),
                        "bio": data.get("bio"),
                        "followers": data.get("followers_count"),
                    },
                )
            return None
        except Exception:
            return None
    
    def get_platform_name(self) -> str:
        return "example_api"
    
    async def aclose(self):
        await self.http_client.aclose()
```

### Example 3: Regex-Based Checker

```python
from nyx.osint.plugin import PlatformCheckerPlugin
from nyx.osint.profile import Profile
from nyx.core.http_client import HTTPClient
from typing import Optional
import re

class RegexChecker(PlatformCheckerPlugin):
    """Checker using regex pattern matching."""
    
    def __init__(self):
        self.base_url = "https://example.com"
        self.http_client = HTTPClient()
        self.pattern = re.compile(r'<h1 class="username">(.+?)</h1>')
    
    async def check(self, username: str) -> Optional[Profile]:
        """Check username using regex pattern."""
        url = f"{self.base_url}/{username}"
        
        try:
            response = await self.http_client.get(url)
            
            if response.status_code == 200:
                content = response.text
                match = self.pattern.search(content)
                
                if match:
                    return Profile(
                        platform=self.get_platform_name(),
                        username=username,
                        url=url,
                        exists=True,
                        metadata={"display_name": match.group(1)},
                    )
            return None
        except Exception:
            return None
    
    def get_platform_name(self) -> str:
        return "example_regex"
    
    async def aclose(self):
        await self.http_client.aclose()
```

---

## Best Practices

### 1. Error Handling

Handle errors gracefully:

```python
async def check(self, username: str) -> Optional[Profile]:
    try:
        # Check logic
        pass
    except httpx.HTTPError:
        # Network errors - return None (not found)
        return None
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in {self.get_platform_name()}: {e}")
        return None
```

### 2. Resource Management

Always clean up resources:

```python
class MyChecker(PlatformCheckerPlugin):
    def __init__(self):
        self.http_client = HTTPClient()
    
    async def aclose(self):
        """Clean up resources."""
        await self.http_client.aclose()
```

### 3. Rate Limiting

Respect platform rate limits:

```python
from nyx.core.http_client import HTTPClient

class RateLimitedChecker(PlatformCheckerPlugin):
    def __init__(self):
        # Use shared HTTP client with rate limiting
        self.http_client = HTTPClient(rate_limit=5.0)  # 5 req/sec
```

### 4. Caching

Let the SearchService handle caching - don't implement your own.

### 5. User-Agent

Use appropriate user-agent:

```python
self.http_client = HTTPClient(
    user_agent="Nyx-OSINT/0.1.0 (https://github.com/your-org/nyx-osint)"
)
```

---

## Testing Plugins

### Unit Tests

```python
import pytest
from nyx.osint.plugin import MyPlatformChecker

@pytest.mark.asyncio
async def test_my_checker_exists():
    checker = MyPlatformChecker()
    try:
        profile = await checker.check("existing_user")
        assert profile is not None
        assert profile.exists is True
        assert profile.platform == "myplatform"
    finally:
        await checker.aclose()

@pytest.mark.asyncio
async def test_my_checker_not_found():
    checker = MyPlatformChecker()
    try:
        profile = await checker.check("nonexistent_user")
        assert profile is None
    finally:
        await checker.aclose()
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_plugin_registration():
    from nyx.osint.plugin import PluginRegistry
    
    registry = PluginRegistry()
    checker = MyPlatformChecker()
    registry.register(checker)
    
    found = registry.get_plugin("myplatform")
    assert found is not None
    assert isinstance(found, MyPlatformChecker)
```

---

## Advanced Topics

### Using Shared HTTP Client

For better resource management, use a shared HTTP client:

```python
from nyx.osint.search import SearchService

# SearchService provides a shared HTTP client
search_service = SearchService()
checker = MyPlatformChecker(http_client=search_service.http_client)
```

### Custom Metadata

Add custom metadata to profiles:

```python
profile = Profile(
    platform=self.get_platform_name(),
    username=username,
    url=url,
    exists=True,
    metadata={
        "custom_field": "value",
        "another_field": 123,
    },
)
```

### Async Context Managers

Implement async context manager support:

```python
class MyChecker(PlatformCheckerPlugin):
    async def __aenter__(self):
        await self.http_client.open()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
```

Usage:

```python
async with MyChecker() as checker:
    profile = await checker.check("username")
```

---

## Registering Plugins

### Manual Registration

```python
from nyx.osint.plugin import PluginRegistry
from nyx.osint.search import SearchService

# Create registry
registry = PluginRegistry()

# Register plugin
checker = MyPlatformChecker()
registry.register(checker)

# Use in SearchService
search_service = SearchService(plugin_registry=registry)
```

### Auto-Discovery

Plugins can be auto-discovered if placed in `nyx/plugins/`:

```python
# nyx/plugins/my_checker.py
from nyx.osint.plugin import PlatformCheckerPlugin

class MyChecker(PlatformCheckerPlugin):
    # ...
```

---

## Troubleshooting

### Common Issues

1. **Plugin not found**: Ensure `get_platform_name()` returns correct name
2. **Resource leaks**: Always call `aclose()` or use context managers
3. **Rate limiting**: Use shared HTTP client with rate limiting
4. **False positives**: Implement proper validation logic

### Debugging

Enable debug logging:

```python
import logging

logger = logging.getLogger("nyx.plugins")
logger.setLevel(logging.DEBUG)
```

---

## Resources

- **API Documentation**: `docs/API.md`
- **Architecture Guide**: `docs/ARCHITECTURE.md`
- **Example Plugins**: `src/nyx/osint/checker.py`

---

**Version:** 0.1.0  
**Last Updated:** 2025-01-23

