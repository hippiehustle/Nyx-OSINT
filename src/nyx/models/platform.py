"""Platform models for OSINT database."""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
import enum

Base = declarative_base()


class PlatformCategory(str, enum.Enum):
    """Platform category enumeration."""

    SOCIAL_MEDIA = "social_media"
    PROFESSIONAL = "professional"
    DATING = "dating"
    GAMING = "gaming"
    FORUMS = "forums"
    ADULT = "adult"
    BLOGGING = "blogging"
    PHOTOGRAPHY = "photography"
    MESSAGING = "messaging"
    STREAMING = "streaming"
    CRYPTO = "crypto"
    SHOPPING = "shopping"
    OTHER = "other"


class Platform(Base):
    """Platform definition for username/profile searching."""

    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    url: Mapped[str] = mapped_column(String(2048))
    category: Mapped[PlatformCategory] = mapped_column(
        Enum(PlatformCategory), default=PlatformCategory.OTHER
    )

    # Platform detection
    username_param: Mapped[str] = mapped_column(String(255), nullable=True)  # e.g., "user", "id"
    search_url: Mapped[str] = mapped_column(String(2048), nullable=True)  # URL pattern for username search
    detection_method: Mapped[str] = mapped_column(String(50), default="status_code")  # status_code, regex, json
    
    # Email/Phone search support
    email_search_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)  # URL pattern for email search
    phone_search_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)  # URL pattern for phone search
    email_param: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # URL parameter name for email (e.g., "email", "q")
    phone_param: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # URL parameter name for phone (e.g., "phone", "tel")

    # Detection patterns
    exists_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Expected code if found
    not_exists_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    exists_pattern: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Regex pattern if found
    not_exists_pattern: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Platform metadata
    is_nsfw: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_login: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_proxy: Mapped[bool] = mapped_column(Boolean, default=False)
    timeout: Mapped[int] = mapped_column(Integer, default=10)  # Request timeout in seconds
    rate_limit: Mapped[int] = mapped_column(Integer, default=0)  # Requests per minute (0 = unlimited)
    headers: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Source information
    source_tool: Mapped[str] = mapped_column(String(100), nullable=True)  # maigret, sherlock, etc.
    last_verified: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Platform(name={self.name}, category={self.category})>"


class PlatformStats(Base):
    """Statistics about platform search attempts."""

    __tablename__ = "platform_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform_id: Mapped[int] = mapped_column(Integer, ForeignKey("platforms.id"), index=True)

    total_searches: Mapped[int] = mapped_column(Integer, default=0)
    successful_finds: Mapped[int] = mapped_column(Integer, default=0)
    failed_searches: Mapped[int] = mapped_column(Integer, default=0)
    average_response_time: Mapped[float] = mapped_column(Float, default=0.0)
    last_search_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    platform: Mapped[Platform] = relationship("Platform", foreign_keys=[platform_id])

    def __repr__(self) -> str:
        """String representation."""
        return f"<PlatformStats(platform_id={self.platform_id}, searches={self.total_searches})>"


class PlatformResult(Base):
    """Result of searching a platform for a username."""

    __tablename__ = "platform_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform_id: Mapped[int] = mapped_column(Integer, ForeignKey("platforms.id"), index=True)
    username: Mapped[str] = mapped_column(String(255), index=True)

    found: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    profile_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    response_status: Mapped[int] = mapped_column(Integer, nullable=True)
    response_time: Mapped[float] = mapped_column(Float, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    platform: Mapped[Platform] = relationship("Platform", foreign_keys=[platform_id])

    def __repr__(self) -> str:
        """String representation."""
        return f"<PlatformResult(platform={self.platform_id}, username={self.username}, found={self.found})>"
