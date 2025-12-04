"""Tests for cache module."""

import pytest
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from nyx.core.cache import (
    MemoryCacheBackend,
    DiskCacheBackend,
    MultiLevelCache,
    get_cache,
    initialize_cache,
)


class TestMemoryCacheBackend:
    """Test MemoryCacheBackend functionality."""

    @pytest.mark.asyncio
    async def test_get_set(self):
        """Test get and set operations."""
        cache = MemoryCacheBackend(max_size=100, ttl=3600)

        await cache.set("key1", "value1")
        value = await cache.get("key1")

        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Test get with non-existent key."""
        cache = MemoryCacheBackend()

        value = await cache.get("nonexistent")

        assert value is None

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test delete operation."""
        cache = MemoryCacheBackend()

        await cache.set("key1", "value1")
        await cache.delete("key1")
        value = await cache.get("key1")

        assert value is None

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clear operation."""
        cache = MemoryCacheBackend()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = MemoryCacheBackend(max_size=100, ttl=1)  # 1 second TTL

        await cache.set("key1", "value1")
        value1 = await cache.get("key1")
        assert value1 == "value1"

        await asyncio.sleep(1.1)  # Wait for expiration
        value2 = await cache.get("key1")
        assert value2 is None

    @pytest.mark.asyncio
    async def test_max_size(self):
        """Test max size limit."""
        cache = MemoryCacheBackend(max_size=2, ttl=3600)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")  # Should evict oldest

        # At least one should be evicted
        values = [await cache.get("key1"), await cache.get("key2"), await cache.get("key3")]
        assert sum(1 for v in values if v is not None) <= 2


class TestDiskCacheBackend:
    """Test DiskCacheBackend functionality."""

    @pytest.mark.asyncio
    async def test_get_set(self):
        """Test get and set operations."""
        with TemporaryDirectory() as tmpdir:
            cache = DiskCacheBackend(cache_dir=tmpdir, ttl=3600)

            await cache.set("key1", "value1")
            value = await cache.get("key1")

            assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Test get with non-existent key."""
        with TemporaryDirectory() as tmpdir:
            cache = DiskCacheBackend(cache_dir=tmpdir)

            value = await cache.get("nonexistent")

            assert value is None

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test delete operation."""
        with TemporaryDirectory() as tmpdir:
            cache = DiskCacheBackend(cache_dir=tmpdir)

            await cache.set("key1", "value1")
            await cache.delete("key1")
            value = await cache.get("key1")

            assert value is None

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clear operation."""
        with TemporaryDirectory() as tmpdir:
            cache = DiskCacheBackend(cache_dir=tmpdir)

            await cache.set("key1", "value1")
            await cache.set("key2", "value2")
            await cache.clear()

            assert await cache.get("key1") is None
            assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test TTL expiration."""
        with TemporaryDirectory() as tmpdir:
            cache = DiskCacheBackend(cache_dir=tmpdir, ttl=1)  # 1 second TTL

            await cache.set("key1", "value1")
            value1 = await cache.get("key1")
            assert value1 == "value1"

            await asyncio.sleep(1.1)  # Wait for expiration
            value2 = await cache.get("key1")
            assert value2 is None

    @pytest.mark.asyncio
    async def test_cache_path_generation(self):
        """Test cache path generation."""
        with TemporaryDirectory() as tmpdir:
            cache = DiskCacheBackend(cache_dir=tmpdir)

            await cache.set("test key", "value")
            # Should create a file with MD5 hash
            cache_files = list(Path(tmpdir).glob("*.json"))
            assert len(cache_files) == 1


class TestMultiLevelCache:
    """Test MultiLevelCache functionality."""

    @pytest.mark.asyncio
    async def test_get_from_l1(self):
        """Test getting value from L1 cache."""
        with TemporaryDirectory() as tmpdir:
            cache = MultiLevelCache(l2_dir=tmpdir)

            await cache.l1.set("key1", "value1")
            value = await cache.get("key1")

            assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_from_l2_promote(self):
        """Test getting value from L2 and promoting to L1."""
        with TemporaryDirectory() as tmpdir:
            cache = MultiLevelCache(l2_dir=tmpdir)

            await cache.l2.set("key1", "value1")
            value = await cache.get("key1")

            assert value == "value1"
            # Should be promoted to L1
            l1_value = await cache.l1.get("key1")
            assert l1_value == "value1"

    @pytest.mark.asyncio
    async def test_set_both_levels(self):
        """Test setting value in both L1 and L2."""
        with TemporaryDirectory() as tmpdir:
            cache = MultiLevelCache(l2_dir=tmpdir)

            await cache.set("key1", "value1")

            l1_value = await cache.l1.get("key1")
            l2_value = await cache.l2.get("key1")

            assert l1_value == "value1"
            assert l2_value == "value1"

    @pytest.mark.asyncio
    async def test_delete_both_levels(self):
        """Test deleting from both levels."""
        with TemporaryDirectory() as tmpdir:
            cache = MultiLevelCache(l2_dir=tmpdir)

            await cache.set("key1", "value1")
            await cache.delete("key1")

            assert await cache.l1.get("key1") is None
            assert await cache.l2.get("key1") is None

    @pytest.mark.asyncio
    async def test_clear_both_levels(self):
        """Test clearing both levels."""
        with TemporaryDirectory() as tmpdir:
            cache = MultiLevelCache(l2_dir=tmpdir)

            await cache.set("key1", "value1")
            await cache.set("key2", "value2")
            await cache.clear()

            assert await cache.l1.get("key1") is None
            assert await cache.l2.get("key1") is None

    @pytest.mark.asyncio
    async def test_l2_disabled(self):
        """Test cache with L2 disabled."""
        cache = MultiLevelCache(l2_enabled=False)

        assert cache.l2 is None

        await cache.set("key1", "value1")
        value = await cache.get("key1")

        assert value == "value1"

    def test_get_cache_singleton(self):
        """Test that get_cache returns singleton."""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_initialize_cache(self):
        """Test cache initialization."""
        with TemporaryDirectory() as tmpdir:
            cache = initialize_cache(l2_dir=tmpdir, l1_size=500)

            assert cache.l1.cache.maxsize == 500
            assert cache.l2 is not None

