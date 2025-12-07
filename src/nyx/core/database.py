"""Database connection and session management."""

from typing import AsyncIterator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from nyx.models.platform import Base as PlatformBase
from nyx.models.target import Base as TargetBase


class DatabaseManager:
    """Manage database connections and sessions."""

    def __init__(self, database_url: str, echo: bool = False):
        """Initialize database manager.

        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL statements
        """
        self.database_url = database_url
        self.echo = echo
        self.engine = None
        self.async_session_maker = None

    async def initialize(self) -> None:
        """Initialize database connection and create tables."""
        # Use NullPool for SQLite to avoid threading issues
        if "sqlite" in self.database_url:
            self.engine = create_async_engine(
                self.database_url,
                echo=self.echo,
                poolclass=NullPool,
                connect_args={"check_same_thread": False},
            )
        else:
            self.engine = create_async_engine(
                self.database_url,
                echo=self.echo,
            )

        self.async_session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables
        async with self.engine.begin() as conn:
            # Create all tables from both base classes
            await conn.run_sync(PlatformBase.metadata.create_all)
            await conn.run_sync(TargetBase.metadata.create_all)

    async def get_session(self) -> AsyncIterator[AsyncSession]:
        """Get async database session."""
        if not self.async_session_maker:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        async with self.async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    async def close(self) -> None:
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()

    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            if not self.engine:
                return False
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Database health check failed: {e}", exc_info=False)
            return False


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get global database manager.
    
    Note: Database must be initialized first using initialize_database() or ensure_database_initialized().
    For async contexts, use get_database_manager_async() instead.
    """
    global _db_manager
    if _db_manager is None:
        raise RuntimeError(
            "Database manager not initialized. "
            "Call initialize_database() or ensure_database_initialized() first."
        )
    return _db_manager


async def get_database_manager_async(config=None) -> DatabaseManager:
    """Get database manager, initializing if necessary (async-safe).
    
    Args:
        config: Optional Config object
        
    Returns:
        DatabaseManager instance
    """
    return await ensure_database_initialized(config)


async def initialize_database(database_url: str, echo: bool = False) -> DatabaseManager:
    """Initialize and return global database manager."""
    global _db_manager
    
    # Resolve database URL if it's SQLite and resource paths are available
    if "sqlite" in database_url:
        try:
            from nyx.core.resource_paths import get_database_path
            db_path = get_database_path()
            # Convert to absolute path for SQLite
            database_url = f"sqlite:///{db_path.absolute()}"
        except ImportError:
            # Resource paths not available, use original URL
            pass
    
    _db_manager = DatabaseManager(database_url, echo=echo)
    await _db_manager.initialize()
    return _db_manager


async def ensure_database_initialized(config=None) -> DatabaseManager:
    """Ensure database is initialized, initializing if necessary.
    
    Args:
        config: Optional Config object. If provided, uses config.database settings.
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    
    if _db_manager is not None:
        return _db_manager
    
    # Initialize from config if provided
    if config:
        database_url = config.database.get_resolved_url()
        echo = config.database.echo
    else:
        # Use default
        try:
            from nyx.core.resource_paths import get_database_path
            db_path = get_database_path()
            database_url = f"sqlite:///{db_path.absolute()}"
        except ImportError:
            database_url = "sqlite:///./nyx.db"
        echo = False
    
    return await initialize_database(database_url, echo=echo)
