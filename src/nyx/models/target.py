"""Target and profile models for OSINT database."""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Integer,
    LargeBinary,
    String,
    Table,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

Base = declarative_base()

# Association table for profile-to-profile relationships (links)
profile_links = Table(
    "profile_links",
    Base.metadata,
    Column("source_profile_id", Integer, ForeignKey("target_profiles.id"), primary_key=True),
    Column("target_profile_id", Integer, ForeignKey("target_profiles.id"), primary_key=True),
    Column("relationship_type", String(50)),  # "same_person", "related_account", "verified", etc.
)


class Target(Base):
    """Investigation target/subject."""

    __tablename__ = "targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="unknown")  # person, account, organization, etc.

    # Investigation metadata
    priority: Mapped[int] = mapped_column(Integer, default=5)  # 1-10, 10=highest
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, closed, archived
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Search history
    last_searched: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    search_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profiles: Mapped[list["TargetProfile"]] = relationship("TargetProfile", back_populates="target", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Target(id={self.id}, name={self.name}, category={self.category})>"


class TargetProfile(Base):
    """Profile of a target across platforms."""

    __tablename__ = "target_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_id: Mapped[int] = mapped_column(Integer, ForeignKey("targets.id"), index=True)

    username: Mapped[str] = mapped_column(String(255), index=True)
    platform: Mapped[str] = mapped_column(String(100), index=True)
    profile_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Profile data
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Account metadata
    followers_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    following_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    posts_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    account_created: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Profile picture
    profile_pic_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    profile_pic_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    # Raw and extended data
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    profile_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Verification and confidence
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[float] = mapped_column(Integer, default=0.0)  # 0.0-1.0
    is_nsfw: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    target: Mapped[Target] = relationship("Target", back_populates="profiles")
    linked_profiles: Mapped[list["TargetProfile"]] = relationship(
        "TargetProfile",
        secondary=profile_links,
        primaryjoin=id == profile_links.c.source_profile_id,
        secondaryjoin=id == profile_links.c.target_profile_id,
        viewonly=True,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<TargetProfile(username={self.username}, platform={self.platform})>"


class SearchHistory(Base):
    """History of searches performed."""

    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_id: Mapped[int] = mapped_column(Integer, ForeignKey("targets.id"), index=True)

    search_query: Mapped[str] = mapped_column(String(255))
    search_type: Mapped[str] = mapped_column(String(50))  # username, email, phone, etc.
    platforms_searched: Mapped[int] = mapped_column(Integer, default=0)
    results_found: Mapped[int] = mapped_column(Integer, default=0)

    filters_applied: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    results_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    duration_seconds: Mapped[float] = mapped_column(Integer, default=0.0)

    target: Mapped[Target] = relationship("Target", foreign_keys=[target_id])

    def __repr__(self) -> str:
        """String representation."""
        return f"<SearchHistory(target_id={self.target_id}, query={self.search_query})>"
