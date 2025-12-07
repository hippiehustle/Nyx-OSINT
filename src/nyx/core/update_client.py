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
            
            if not response or response.status_code != 200:
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
    
    async def download_asset(self, asset_url: str, destination: str, progress_callback=None) -> bool:
        """Download a release asset.
        
        Args:
            asset_url: URL to the asset
            destination: Local file path to save to
            progress_callback: Optional callback(bytes_downloaded, total_bytes)
            
        Returns:
            True if download successful
        """
        try:
            import httpx
            
            # Use httpx directly for streaming downloads
            headers = {"Accept": "application/octet-stream", "User-Agent": "Nyx/0.1.0"}
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("GET", asset_url, headers=headers) as response:
                    if response.status_code != 200:
                        return False
                    
                    # Get content length if available
                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0
                    
                    # Save to file with progress tracking
                    with open(destination, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback:
                                progress_callback(downloaded, total_size if total_size > 0 else downloaded)
                
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
            
            if not response or response.status_code != 200:
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
            
            if not response or response.status_code != 200:
                return None
            
            return response.json()
        except Exception as e:
            logger.error(f"Error getting update info: {e}", exc_info=True)
            return None
    
    async def download_update(self, version: str, destination: str, progress_callback=None) -> bool:
        """Download update installer.
        
        Args:
            version: Version to download
            destination: Local file path to save to
            progress_callback: Optional callback(bytes_downloaded, total_bytes)
            
        Returns:
            True if download successful
        """
        try:
            import httpx
            
            url = urljoin(self.base_url, f"/api/download/{version}")
            headers = {"User-Agent": "Nyx/0.1.0"}
            
            # Use httpx directly for streaming downloads
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("GET", url, headers=headers) as response:
                    if response.status_code != 200:
                        return False
                    
                    # Get content length if available
                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0
                    
                    # Save to file with progress tracking
                    with open(destination, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback:
                                progress_callback(downloaded, total_size if total_size > 0 else downloaded)
                
                return True
        except Exception as e:
            logger.error(f"Error downloading update: {e}", exc_info=True)
            return False

