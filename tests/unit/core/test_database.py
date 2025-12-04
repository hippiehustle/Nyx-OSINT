"""Tests for database module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nyx.core.database import DatabaseManager, get_database_manager, initialize_database


class TestDatabaseManager:
    """Test DatabaseManager functionality."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test database manager initialization."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)
        await db_manager.initialize()

        assert db_manager.engine is not None
        assert db_manager.async_session_maker is not None

    @pytest.mark.asyncio
    async def test_get_session(self):
        """Test getting database session."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)
        await db_manager.initialize()

        async for session in db_manager.get_session():
            assert session is not None
            break

    @pytest.mark.asyncio
    async def test_get_session_not_initialized(self):
        """Test getting session when not initialized."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)

        with pytest.raises(RuntimeError):
            async for session in db_manager.get_session():
                pass

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test database health check."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)
        await db_manager.initialize()

        health = await db_manager.health_check()

        assert health is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self):
        """Test health check when not initialized."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)

        health = await db_manager.health_check()

        assert health is False

    @pytest.mark.asyncio
    async def test_close(self):
        """Test database closing."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)
        await db_manager.initialize()

        db_manager.engine.dispose = AsyncMock()

        await db_manager.close()

        db_manager.engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_no_engine(self):
        """Test closing when engine not initialized."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)

        await db_manager.close()

        # Should not raise

    @pytest.mark.asyncio
    async def test_session_context_manager(self):
        """Test session as context manager."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)
        await db_manager.initialize()

        async for session in db_manager.get_session():
            assert session is not None
            # Session should be closed after context exit
            break

    @pytest.mark.asyncio
    async def test_sqlite_nullpool(self):
        """Test SQLite uses NullPool."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)
        await db_manager.initialize()

        assert db_manager.engine is not None

    @pytest.mark.asyncio
    async def test_postgresql_pool(self):
        """Test PostgreSQL uses default pool."""
        db_manager = DatabaseManager("postgresql+asyncpg://user:pass@localhost/db", echo=False)
        await db_manager.initialize()

        assert db_manager.engine is not None


class TestGlobalDatabaseFunctions:
    """Test global database functions."""

    def test_get_database_manager_not_initialized(self):
        """Test getting database manager when not initialized."""
        # Clear global state
        import nyx.core.database as db_module
        db_module._db_manager = None

        with pytest.raises(RuntimeError):
            get_database_manager()

    @pytest.mark.asyncio
    async def test_initialize_database(self):
        """Test database initialization function."""
        db_manager = await initialize_database("sqlite:///:memory:", echo=False)

        assert db_manager is not None
        assert db_manager.engine is not None

        await db_manager.close()

