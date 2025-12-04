"""Integration tests for database operations."""

import pytest
from datetime import datetime

from nyx.core.database import DatabaseManager, initialize_database
from nyx.models.target import Target, TargetProfile, SearchHistory


class TestDatabaseIntegration:
    """Test database integration."""

    @pytest.mark.asyncio
    async def test_target_creation(self):
        """Test Target creation and persistence."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)
        await db_manager.initialize()

        try:
            async for session in db_manager.get_session():
                target = Target(
                    name="test_target",
                    category="person",
                    description="Test target",
                )
                session.add(target)
                await session.commit()
                await session.refresh(target)

                assert target.id is not None
                assert target.name == "test_target"
                break
        finally:
            await db_manager.close()

    @pytest.mark.asyncio
    async def test_target_profile_creation(self):
        """Test TargetProfile creation."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)
        await db_manager.initialize()

        try:
            async for session in db_manager.get_session():
                target = Target(name="test_target", category="person")
                session.add(target)
                await session.flush()

                profile = TargetProfile(
                    target_id=target.id,
                    username="testuser",
                    platform="Twitter",
                    profile_url="https://twitter.com/testuser",
                    confidence_score=0.8,
                )
                session.add(profile)
                await session.commit()

                assert profile.id is not None
                assert profile.target_id == target.id
                break
        finally:
            await db_manager.close()

    @pytest.mark.asyncio
    async def test_search_history_recording(self):
        """Test SearchHistory recording."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)
        await db_manager.initialize()

        try:
            async for session in db_manager.get_session():
                target = Target(name="test_target", category="person")
                session.add(target)
                await session.flush()

                history = SearchHistory(
                    target_id=target.id,
                    search_query="testuser",
                    search_type="username",
                    platforms_searched=10,
                    results_found=5,
                    duration_seconds=2.5,
                )
                session.add(history)
                await session.commit()

                assert history.id is not None
                assert history.target_id == target.id
                break
        finally:
            await db_manager.close()

    @pytest.mark.asyncio
    async def test_smart_search_persistence(self):
        """Test Smart search persistence."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)
        await db_manager.initialize()

        try:
            async for session in db_manager.get_session():
                target = Target(name="test_target", category="person")
                session.add(target)
                await session.flush()

                history = SearchHistory(
                    target_id=target.id,
                    search_query="test query",
                    search_type="smart",
                    platforms_searched=5,
                    results_found=3,
                    filters_applied={"region": "US"},
                    results_summary={"candidates": 3},
                    duration_seconds=5.0,
                )
                session.add(history)
                await session.commit()

                assert history.search_type == "smart"
                assert history.filters_applied["region"] == "US"
                break
        finally:
            await db_manager.close()

    @pytest.mark.asyncio
    async def test_target_profile_relationship(self):
        """Test Target-Profile relationship."""
        db_manager = DatabaseManager("sqlite:///:memory:", echo=False)
        await db_manager.initialize()

        try:
            async for session in db_manager.get_session():
                target = Target(name="test_target", category="person")
                session.add(target)
                await session.flush()

                profile1 = TargetProfile(
                    target_id=target.id,
                    username="testuser",
                    platform="Twitter",
                    profile_url="https://twitter.com/testuser",
                )
                profile2 = TargetProfile(
                    target_id=target.id,
                    username="testuser",
                    platform="GitHub",
                    profile_url="https://github.com/testuser",
                )
                session.add_all([profile1, profile2])
                await session.commit()

                # Query profiles for target
                from sqlalchemy import select

                stmt = select(TargetProfile).where(TargetProfile.target_id == target.id)
                result = await session.execute(stmt)
                profiles = result.scalars().all()

                assert len(profiles) == 2
                break
        finally:
            await db_manager.close()

