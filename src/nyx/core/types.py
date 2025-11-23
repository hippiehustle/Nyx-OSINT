"""Common type definitions and protocols for Nyx."""

from typing import Any, Awaitable, Callable, Dict, List, Optional, Protocol, TypeVar, Union

# Generic type variables
T = TypeVar("T")
P = TypeVar("P")

# Common type aliases
JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JSONValue]

# Search result type
SearchResult = Dict[str, Any]
SearchResults = List[SearchResult]

# Profile type
Profile = Dict[str, Any]
Profiles = List[Profile]

# Platform detection result
PlatformMatch = Dict[str, Union[str, bool, int]]
PlatformMatches = List[PlatformMatch]


class AsyncCallable(Protocol):
    """Protocol for async callable."""

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute async call."""
        ...


class CacheBackend(Protocol):
    """Protocol for cache backends."""

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ...

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        ...

    async def clear(self) -> None:
        """Clear all cache."""
        ...


class SearchEngine(Protocol):
    """Protocol for search engine implementations."""

    async def search(self, query: str) -> SearchResults:
        """Execute search query."""
        ...

    async def get_info(self) -> JSONDict:
        """Get search engine information."""
        ...


class PlatformChecker(Protocol):
    """Protocol for platform checking implementations."""

    async def check(self, username: str) -> Optional[PlatformMatch]:
        """Check if username exists on platform."""
        ...

    async def get_info(self) -> JSONDict:
        """Get platform information."""
        ...
