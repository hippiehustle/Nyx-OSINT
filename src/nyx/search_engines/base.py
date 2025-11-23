"""Base class for search engine implementations."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from nyx.core.http_client import HTTPClient
from nyx.core.logger import get_logger
from nyx.core.types import SearchResults

logger = get_logger(__name__)


class SearchResult:
    """Single search result."""

    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
        rank: int = 0,
    ):
        """Initialize search result.

        Args:
            title: Result title
            url: Result URL
            snippet: Result snippet/description
            rank: Result rank (1-based)
        """
        self.title = title
        self.url = url
        self.snippet = snippet
        self.rank = rank

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "rank": self.rank,
        }


class BaseSearchEngine(ABC):
    """Base class for search engine implementations."""

    def __init__(
        self,
        name: str,
        timeout: int = 10,
        rate_limit: float = 5.0,
        user_agent: Optional[str] = None,
    ):
        """Initialize search engine.

        Args:
            name: Search engine name
            timeout: Request timeout in seconds
            rate_limit: Requests per second
            user_agent: Custom user agent
        """
        self.name = name
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Nyx/0.1.0"
        self.http_client = HTTPClient(
            timeout=timeout,
            rate_limit=rate_limit,
            user_agent=self.user_agent,
        )

    @abstractmethod
    async def search(
        self,
        query: str,
        num_results: int = 10,
        lang: str = "en",
    ) -> SearchResults:
        """Execute search query.

        Args:
            query: Search query
            num_results: Number of results to return
            lang: Language code

        Returns:
            List of search results
        """
        pass

    async def search_name(
        self,
        name: str,
        num_results: int = 10,
    ) -> SearchResults:
        """Search for a person by name.

        Args:
            name: Person's name
            num_results: Number of results

        Returns:
            Search results
        """
        query = f'"{name}"'
        return await self.search(query, num_results=num_results)

    async def search_email(
        self,
        email: str,
        num_results: int = 10,
    ) -> SearchResults:
        """Search for email address.

        Args:
            email: Email address
            num_results: Number of results

        Returns:
            Search results
        """
        query = f'"{email}"'
        return await self.search(query, num_results=num_results)

    async def search_username(
        self,
        username: str,
        num_results: int = 10,
    ) -> SearchResults:
        """Search for username mentions.

        Args:
            username: Username to search for
            num_results: Number of results

        Returns:
            Search results
        """
        query = f'"{username}"'
        return await self.search(query, num_results=num_results)

    async def search_phone(
        self,
        phone: str,
        num_results: int = 10,
    ) -> SearchResults:
        """Search for phone number.

        Args:
            phone: Phone number
            num_results: Number of results

        Returns:
            Search results
        """
        query = f'"{phone}"'
        return await self.search(query, num_results=num_results)

    async def search_url(
        self,
        url: str,
        num_results: int = 10,
    ) -> SearchResults:
        """Search for mentions of a URL.

        Args:
            url: URL to search for
            num_results: Number of results

        Returns:
            Search results
        """
        return await self.search(url, num_results=num_results)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.close()

    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__}(name={self.name})>"
