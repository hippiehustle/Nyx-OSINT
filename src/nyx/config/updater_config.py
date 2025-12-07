"""Update configuration management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UpdaterConfig(BaseModel):
    """Configuration for the auto-updater."""
    
    enabled: bool = Field(default=True, description="Enable auto-updater")
    source: str = Field(default="github", description="Update source: github, custom, disabled")
    github_repo: Optional[str] = Field(default=None, description="GitHub repository (owner/repo)")
    custom_url: Optional[str] = Field(default=None, description="Custom update server URL")
    check_on_startup: bool = Field(default=True, description="Check for updates on startup")
    check_frequency: str = Field(
        default="daily",
        description="Check frequency: on_startup, daily, weekly, manual_only"
    )
    auto_download: bool = Field(default=False, description="Automatically download updates")
    auto_install: bool = Field(default=False, description="Automatically install updates (requires confirmation)")
    channel: str = Field(default="stable", description="Update channel: stable, beta, alpha")
    skip_versions: List[str] = Field(default_factory=list, description="Versions to skip")
    last_check: Optional[datetime] = Field(default=None, description="Last update check timestamp")
    last_update: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    def should_check_on_startup(self) -> bool:
        """Check if updates should be checked on startup."""
        return self.enabled and self.check_on_startup
    
    def should_auto_download(self) -> bool:
        """Check if updates should be auto-downloaded."""
        return self.enabled and self.auto_download
    
    def should_auto_install(self) -> bool:
        """Check if updates should be auto-installed."""
        return self.enabled and self.auto_install
    
    def is_version_skipped(self, version: str) -> bool:
        """Check if a version is in the skip list."""
        return version in self.skip_versions
    
    def get_update_source_url(self) -> Optional[str]:
        """Get the update source URL based on configuration."""
        if not self.enabled or self.source == "disabled":
            return None
        
        if self.source == "github" and self.github_repo:
            return f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        
        if self.source == "custom" and self.custom_url:
            return self.custom_url
        
        return None

