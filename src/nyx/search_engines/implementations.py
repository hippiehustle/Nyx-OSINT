"""Search engine implementations."""

import re
from typing import Optional
from urllib.parse import quote

from bs4 import BeautifulSoup

from nyx.core.logger import get_logger
from nyx.core.types import SearchResults
from nyx.search_engines.base import BaseSearchEngine, SearchResult

logger = get_logger(__name__)


class GoogleSearchEngine(BaseSearchEngine):
    """Google search engine integration."""

    def __init__(self, use_ssl: bool = True, **kwargs):
        """Initialize Google search engine.

        Args:
            use_ssl: Whether to use HTTPS
            **kwargs: Additional arguments for BaseSearchEngine
        """
        super().__init__(name="Google", **kwargs)
        self.protocol = "https" if use_ssl else "http"
        self.base_url = f"{self.protocol}://www.google.com/search"

    async def search(
        self,
        query: str,
        num_results: int = 10,
        lang: str = "en",
    ) -> SearchResults:
        """Execute Google search.

        Args:
            query: Search query
            num_results: Number of results
            lang: Language code

        Returns:
            Search results
        """
        params = {
            "q": query,
            "num": num_results,
            "hl": lang,
        }

        async with self.http_client:
            response = await self.http_client.get(
                self.base_url,
                params=params,
            )

        if not response:
            logger.error(f"Google search failed for query: {query}")
            return []

        results = self._parse_google_results(response.text, num_results)
        return [result.to_dict() for result in results]

    def _parse_google_results(self, html: str, limit: int) -> list[SearchResult]:
        """Parse Google search results from HTML.

        Args:
            html: HTML content
            limit: Maximum results to parse

        Returns:
            List of search results
        """
        results = []
        soup = BeautifulSoup(html, "html.parser")

        # Find all search results (div with class 'g')
        for i, result_div in enumerate(soup.find_all("div", class_="g"), 1):
            if i > limit:
                break

            try:
                # Extract title and URL
                link = result_div.find("a", href=True)
                if not link:
                    continue

                title = link.get_text(strip=True)
                url = link["href"]

                # Skip Google's own pages
                if not url.startswith("http"):
                    continue

                # Extract snippet
                snippet_div = result_div.find("div", class_="VwiC3b")
                snippet = snippet_div.get_text(strip=True) if snippet_div else ""

                result = SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    rank=i,
                )
                results.append(result)
            except Exception as e:
                logger.debug(f"Error parsing Google result: {e}")
                continue

        return results


class BingSearchEngine(BaseSearchEngine):
    """Bing search engine integration."""

    def __init__(self, **kwargs):
        """Initialize Bing search engine.

        Args:
            **kwargs: Arguments for BaseSearchEngine
        """
        super().__init__(name="Bing", **kwargs)
        self.base_url = "https://www.bing.com/search"

    async def search(
        self,
        query: str,
        num_results: int = 10,
        lang: str = "en",
    ) -> SearchResults:
        """Execute Bing search.

        Args:
            query: Search query
            num_results: Number of results
            lang: Language code

        Returns:
            Search results
        """
        params = {
            "q": query,
            "count": num_results,
            "setLang": lang,
        }

        async with self.http_client:
            response = await self.http_client.get(
                self.base_url,
                params=params,
            )

        if not response:
            logger.error(f"Bing search failed for query: {query}")
            return []

        results = self._parse_bing_results(response.text, num_results)
        return [result.to_dict() for result in results]

    def _parse_bing_results(self, html: str, limit: int) -> list[SearchResult]:
        """Parse Bing search results from HTML.

        Args:
            html: HTML content
            limit: Maximum results to parse

        Returns:
            List of search results
        """
        results = []
        soup = BeautifulSoup(html, "html.parser")

        # Find all search results (li with class 'b_algo')
        for i, result_li in enumerate(soup.find_all("li", class_="b_algo"), 1):
            if i > limit:
                break

            try:
                # Extract title and URL
                link = result_li.find("a", href=True)
                if not link:
                    continue

                title = link.get_text(strip=True)
                url = link["href"]

                # Extract snippet
                snippet_div = result_li.find("p", class_="b_algoSlug")
                snippet = snippet_div.get_text(strip=True) if snippet_div else ""

                result = SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    rank=i,
                )
                results.append(result)
            except Exception as e:
                logger.debug(f"Error parsing Bing result: {e}")
                continue

        return results


class DuckDuckGoSearchEngine(BaseSearchEngine):
    """DuckDuckGo search engine integration (privacy-focused)."""

    def __init__(self, **kwargs):
        """Initialize DuckDuckGo search engine.

        Args:
            **kwargs: Arguments for BaseSearchEngine
        """
        super().__init__(name="DuckDuckGo", **kwargs)
        self.base_url = "https://duckduckgo.com/html"

    async def search(
        self,
        query: str,
        num_results: int = 10,
        lang: str = "en-us",
    ) -> SearchResults:
        """Execute DuckDuckGo search.

        Args:
            query: Search query
            num_results: Number of results
            lang: Language code

        Returns:
            Search results
        """
        params = {
            "q": query,
            "kl": lang,
        }

        async with self.http_client:
            response = await self.http_client.get(
                self.base_url,
                params=params,
            )

        if not response:
            logger.error(f"DuckDuckGo search failed for query: {query}")
            return []

        results = self._parse_duckduckgo_results(response.text, num_results)
        return [result.to_dict() for result in results]

    def _parse_duckduckgo_results(self, html: str, limit: int) -> list[SearchResult]:
        """Parse DuckDuckGo search results from HTML.

        Args:
            html: HTML content
            limit: Maximum results to parse

        Returns:
            List of search results
        """
        results = []
        soup = BeautifulSoup(html, "html.parser")

        # Find all search results
        for i, result_div in enumerate(soup.find_all("div", class_="result"), 1):
            if i > limit:
                break

            try:
                # Extract title and URL
                link = result_div.find("a", class_="result__a", href=True)
                if not link:
                    continue

                title = link.get_text(strip=True)
                url = link.get("href", "")

                # Extract snippet
                snippet_div = result_div.find("a", class_="result__snippet")
                snippet = snippet_div.get_text(strip=True) if snippet_div else ""

                result = SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    rank=i,
                )
                results.append(result)
            except Exception as e:
                logger.debug(f"Error parsing DuckDuckGo result: {e}")
                continue

        return results


class MetaSearchEngine(BaseSearchEngine):
    """Meta search engine that queries multiple engines."""

    def __init__(self, engines: Optional[list] = None, **kwargs):
        """Initialize meta search engine.

        Args:
            engines: List of search engine instances
            **kwargs: Arguments for BaseSearchEngine
        """
        super().__init__(name="MetaSearch", **kwargs)
        self.engines = engines or [
            GoogleSearchEngine(**kwargs),
            BingSearchEngine(**kwargs),
            DuckDuckGoSearchEngine(**kwargs),
        ]

    async def search(
        self,
        query: str,
        num_results: int = 10,
        lang: str = "en",
    ) -> SearchResults:
        """Execute meta search across multiple engines.

        Args:
            query: Search query
            num_results: Number of results per engine
            lang: Language code

        Returns:
            Aggregated search results
        """
        import asyncio

        # Search all engines in parallel
        tasks = [
            engine.search(query, num_results=num_results, lang=lang)
            for engine in self.engines
        ]

        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate and deduplicate results
        seen_urls = set()
        aggregated_results = []

        for results in results_lists:
            if isinstance(results, Exception):
                continue

            for result in results:
                url = result.get("url")
                if url not in seen_urls:
                    seen_urls.add(url)
                    aggregated_results.append(result)

                if len(aggregated_results) >= num_results:
                    return aggregated_results[:num_results]

        return aggregated_results
