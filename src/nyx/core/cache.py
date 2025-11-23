"""Multi-level caching system for Nyx."""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from cachetools import TTLCache


class CacheBackend(ABC):
    """Abstract cache backend."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache."""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory LRU cache backend."""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """Initialize memory cache.

        Args:
            max_size: Maximum cache entries
            ttl: Time to live in seconds
        """
        self.cache = TTLCache(maxsize=max_size, ttl=ttl)
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        async with self.lock:
            return self.cache.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in memory cache."""
        async with self.lock:
            self.cache[key] = value

    async def delete(self, key: str) -> None:
        """Delete value from memory cache."""
        async with self.lock:
            self.cache.pop(key, None)

    async def clear(self) -> None:
        """Clear memory cache."""
        async with self.lock:
            self.cache.clear()


class DiskCacheBackend(CacheBackend):
    """Disk-based cache backend using JSON."""

    def __init__(self, cache_dir: str = "./data/cache", ttl: int = 86400):
        """Initialize disk cache.

        Args:
            cache_dir: Cache directory path
            ttl: Time to live in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        self.lock = asyncio.Lock()

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        # Use hash of key to create valid filename
        import hashlib

        hashed = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hashed}.json"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache."""
        async with self.lock:
            cache_path = self._get_cache_path(key)
            if not cache_path.exists():
                return None

            try:
                with open(cache_path, "r") as f:
                    data = json.load(f)

                # Check if expired
                if time.time() - data["timestamp"] > self.ttl:
                    cache_path.unlink()
                    return None

                return data["value"]
            except Exception:
                return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in disk cache."""
        async with self.lock:
            cache_path = self._get_cache_path(key)
            try:
                with open(cache_path, "w") as f:
                    json.dump(
                        {
                            "key": key,
                            "value": value,
                            "timestamp": time.time(),
                            "ttl": ttl or self.ttl,
                        },
                        f,
                    )
            except Exception:
                pass

    async def delete(self, key: str) -> None:
        """Delete value from disk cache."""
        async with self.lock:
            cache_path = self._get_cache_path(key)
            try:
                cache_path.unlink()
            except Exception:
                pass

    async def clear(self) -> None:
        """Clear disk cache."""
        async with self.lock:
            import shutil

            try:
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass


class MultiLevelCache:
    """Multi-level caching system with L1 (memory) and L2 (disk)."""

    def __init__(
        self,
        l1_size: int = 1000,
        l1_ttl: int = 3600,
        l2_enabled: bool = True,
        l2_dir: str = "./data/cache",
        l2_ttl: int = 86400,
    ):
        """Initialize multi-level cache.

        Args:
            l1_size: L1 cache max size
            l1_ttl: L1 cache TTL in seconds
            l2_enabled: Whether to enable L2 disk cache
            l2_dir: L2 cache directory
            l2_ttl: L2 cache TTL in seconds
        """
        self.l1 = MemoryCacheBackend(max_size=l1_size, ttl=l1_ttl)
        self.l2 = DiskCacheBackend(cache_dir=l2_dir, ttl=l2_ttl) if l2_enabled else None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Tries L1 first, then L2 if available.
        """
        # Try L1
        value = await self.l1.get(key)
        if value is not None:
            return value

        # Try L2
        if self.l2:
            value = await self.l2.get(key)
            if value is not None:
                # Promote to L1
                await self.l1.set(key, value)
                return value

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.

        Sets in both L1 and L2.
        """
        await self.l1.set(key, value, ttl)
        if self.l2:
            await self.l2.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        await self.l1.delete(key)
        if self.l2:
            await self.l2.delete(key)

    async def clear(self) -> None:
        """Clear all cache levels."""
        await self.l1.clear()
        if self.l2:
            await self.l2.clear()


# Global cache instance
_cache: Optional[MultiLevelCache] = None


def get_cache() -> MultiLevelCache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = MultiLevelCache()
    return _cache


def initialize_cache(
    l1_size: int = 1000,
    l1_ttl: int = 3600,
    l2_enabled: bool = True,
    l2_dir: str = "./data/cache",
    l2_ttl: int = 86400,
) -> MultiLevelCache:
    """Initialize and return global cache."""
    global _cache
    _cache = MultiLevelCache(
        l1_size=l1_size,
        l1_ttl=l1_ttl,
        l2_enabled=l2_enabled,
        l2_dir=l2_dir,
        l2_ttl=l2_ttl,
    )
    return _cache
