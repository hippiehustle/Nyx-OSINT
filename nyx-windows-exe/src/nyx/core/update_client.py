"""HTTP client for update operations."""

import json
from typing import Dict, Optional
from urllib.parse import urljoin

from nyx.core.http_client import HTTPClient
from nyx.core.logger import get_logger

logger = get_logger(__name__)


class GitHubReleasesClient:
    """Client for GitHub Releases API."""
    
    def __init__(self, repo: str, http_client: Optional[HTTPClient] = None):
        """Initialize GitHub Releases client.
        
        Args:
            repo: Repository in format "owner/repo"
            http_client: Optional HTTP client instance
        """
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{repo}"
        self.http_client = http_client or HTTPClient()
    
    async def get_latest_release(self, channel: str = "stable") -> Optional[Dict]:
        """Get the latest release information.
        
        Args:
            channel: Release channel (stable, beta, alpha)
            
        Returns:
            Release information dictionary or None
        """
        try:
            # For stable channel, get latest release
            # For beta/alpha, get latest prerelease
            if channel == "stable":
                url = f"{self.base_url}/releases/latest"
            else:
                url = f"{self.base_url}/releases"
            
            async with self.http_client:
                response = await self.http_client.get(url)
            
            if not response:
                logger.error("Failed to fetch release information")
                return None
            
            if channel != "stable":
                # Filter for prereleases matching channel
                releases = response.json() if isinstance(response.json(), list) else [response.json()]
                for release in releases:
                    if release.get("prerelease") and channel in release.get("tag_name", "").lower():
                        return release
                return None
            
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching latest release: {e}", exc_info=True)
            return None
    
    async def download_asset(self, asset_url: str, destination: str) -> bool:
        """Download a release asset.
        
        Args:
            asset_url: URL to the asset
            destination: Local file path to save to
            
        Returns:
            True if download successful
        """
        try:
            async with self.http_client:
                # GitHub requires Accept header for asset downloads
                headers = {"Accept": "application/octet-stream"}
                response = await self.http_client.get(asset_url, headers=headers, stream=True)
                
                if not response:
                    return False
                
                # Save to file
                with open(destination, "wb") as f:
                    async for chunk in response.iter_bytes():
                        f.write(chunk)
                
                return True
        except Exception as e:
            logger.error(f"Error downloading asset: {e}", exc_info=True)
            return False


class CustomUpdateClient:
    """Client for custom update server."""
    
    def __init__(self, base_url: str, http_client: Optional[HTTPClient] = None):
        """Initialize custom update client.
        
        Args:
            base_url: Base URL of update server
            http_client: Optional HTTP client instance
        """
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client or HTTPClient()
    
    async def check_version(self) -> Optional[Dict]:
        """Check for available updates.
        
        Returns:
            Version information dictionary or None
        """
        try:
            url = urljoin(self.base_url, "/api/version")
            async with self.http_client:
                response = await self.http_client.get(url)
            
            if not response:
                return None
            
            return response.json()
        except Exception as e:
            logger.error(f"Error checking version: {e}", exc_info=True)
            return None
    
    async def get_update_info(self, version: str) -> Optional[Dict]:
        """Get update information for a specific version.
        
        Args:
            version: Version string
            
        Returns:
            Update information dictionary or None
        """
        try:
            url = urljoin(self.base_url, f"/api/update/{version}")
            async with self.http_client:
                response = await self.http_client.get(url)
            
            if not response:
                return None
            
            return response.json()
        except Exception as e:
            logger.error(f"Error getting update info: {e}", exc_info=True)
            return None
    
    async def download_update(self, version: str, destination: str) -> bool:
        """Download update installer.
        
        Args:
            version: Version to download
            destination: Local file path to save to
            
        Returns:
            True if download successful
        """
        try:
            url = urljoin(self.base_url, f"/api/download/{version}")
            async with self.http_client:
                response = await self.http_client.get(url, stream=True)
                
                if not response:
                    return False
                
                with open(destination, "wb") as f:
                    async for chunk in response.iter_bytes():
                        f.write(chunk)
                
                return True
        except Exception as e:
            logger.error(f"Error downloading update: {e}", exc_info=True)
            return False

