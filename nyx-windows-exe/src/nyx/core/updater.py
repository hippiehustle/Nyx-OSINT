"""Update manager for checking, downloading, and installing updates."""

import asyncio
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional

from nyx.config.updater_config import UpdaterConfig
from nyx.core.logger import get_logger
from nyx.core.update_client import CustomUpdateClient, GitHubReleasesClient
from nyx.core.version import get_current_version, is_update_available, parse_version

logger = get_logger(__name__)


class UpdateChecker:
    """Check for available updates."""
    
    def __init__(self, config: UpdaterConfig):
        """Initialize update checker.
        
        Args:
            config: Updater configuration
        """
        self.config = config
        self._http_client = None
    
    async def check_for_updates(self) -> Optional[dict]:
        """Check for available updates.
        
        Returns:
            Update information dictionary or None if no update available
        """
        if not self.config.enabled:
            logger.debug("Updater is disabled")
            return None
        
        current_version = str(get_current_version())
        logger.info(f"Checking for updates (current version: {current_version})")
        
        try:
            if self.config.source == "github":
                update_info = await self._check_github()
            elif self.config.source == "custom":
                update_info = await self._check_custom()
            else:
                logger.warning(f"Unknown update source: {self.config.source}")
                return None
            
            if not update_info:
                logger.info("No update information available")
                return None
            
            latest_version = update_info.get("version") or update_info.get("tag_name", "").lstrip("v")
            
            if not latest_version:
                logger.warning("No version found in update info")
                return None
            
            # Check if version should be skipped
            if self.config.is_version_skipped(latest_version):
                logger.info(f"Version {latest_version} is in skip list")
                return None
            
            # Check if update is available
            if not is_update_available(current_version, latest_version):
                logger.info(f"Already on latest version: {latest_version}")
                return None
            
            logger.info(f"Update available: {current_version} -> {latest_version}")
            return {
                "version": latest_version,
                "current_version": current_version,
                "available": True,
                "installer": update_info.get("installer", {}),
                "changelog": update_info.get("changelog", ""),
                "release_notes": update_info.get("release_notes", ""),
                "critical": update_info.get("critical", False),
                "prerelease": update_info.get("prerelease", False),
            }
        except Exception as e:
            logger.error(f"Error checking for updates: {e}", exc_info=True)
            return None
    
    async def _check_github(self) -> Optional[dict]:
        """Check GitHub Releases for updates."""
        if not self.config.github_repo:
            logger.error("GitHub repo not configured")
            return None
        
        client = GitHubReleasesClient(self.config.github_repo)
        release = await client.get_latest_release(self.config.channel)
        
        if not release:
            return None
        
        # Extract installer URL from release assets
        assets = release.get("assets", [])
        installer_asset = None
        for asset in assets:
            if asset.get("name", "").endswith(".exe"):
                installer_asset = asset
                break
        
        if not installer_asset:
            logger.warning("No installer asset found in release")
            return None
        
        return {
            "version": release.get("tag_name", "").lstrip("v"),
            "release_date": release.get("published_at", ""),
            "changelog": release.get("body", ""),
            "release_notes": release.get("html_url", ""),
            "prerelease": release.get("prerelease", False),
            "installer": {
                "url": installer_asset.get("browser_download_url"),
                "size": installer_asset.get("size", 0),
                "filename": installer_asset.get("name", ""),
            },
        }
    
    async def _check_custom(self) -> Optional[dict]:
        """Check custom update server for updates."""
        if not self.config.custom_url:
            logger.error("Custom update URL not configured")
            return None
        
        client = CustomUpdateClient(self.config.custom_url)
        version_info = await client.check_version()
        return version_info


class UpdateDownloader:
    """Download update files."""
    
    def __init__(self, config: UpdaterConfig):
        """Initialize update downloader.
        
        Args:
            config: Updater configuration
        """
        self.config = config
        self._http_client = None
        self._progress_callback: Optional[Callable[[int, int], None]] = None
    
    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """Set progress callback for download updates.
        
        Args:
            callback: Function(bytes_downloaded, total_bytes)
        """
        self._progress_callback = callback
    
    async def download_update(self, update_info: dict, destination: Optional[Path] = None) -> Optional[Path]:
        """Download update installer.
        
        Args:
            update_info: Update information dictionary
            destination: Optional destination path (defaults to temp directory)
            
        Returns:
            Path to downloaded file or None if failed
        """
        installer_info = update_info.get("installer", {})
        installer_url = installer_info.get("url")
        
        if not installer_url:
            logger.error("No installer URL in update info")
            return None
        
        if destination is None:
            temp_dir = Path(tempfile.gettempdir()) / "Nyx" / "updates"
            temp_dir.mkdir(parents=True, exist_ok=True)
            filename = installer_info.get("filename", "update.exe")
            destination = temp_dir / filename
        
        logger.info(f"Downloading update from {installer_url} to {destination}")
        
        try:
            # Determine client type
            if "github.com" in installer_url:
                # GitHub asset download
                repo = self.config.github_repo
                if repo:
                    client = GitHubReleasesClient(repo)
                    success = await client.download_asset(installer_url, str(destination))
                else:
                    logger.error("GitHub repo not configured")
                    return None
            else:
                # Custom server download
                if not self.config.custom_url:
                    logger.error("Custom update URL not configured")
                    return None
                client = CustomUpdateClient(self.config.custom_url)
                version = update_info.get("version", "")
                success = await client.download_update(version, str(destination))
            
            if not success:
                logger.error("Download failed")
                return None
            
            # Verify checksum if provided
            expected_checksum = installer_info.get("checksum", "")
            if expected_checksum:
                if not self._verify_checksum(destination, expected_checksum):
                    logger.error("Checksum verification failed")
                    destination.unlink()
                    return None
            
            logger.info(f"Update downloaded successfully: {destination}")
            return destination
        except Exception as e:
            logger.error(f"Error downloading update: {e}", exc_info=True)
            return None
    
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify file checksum.
        
        Args:
            file_path: Path to file
            expected_checksum: Expected checksum (format: "sha256:hexdigest")
            
        Returns:
            True if checksum matches
        """
        try:
            if expected_checksum.startswith("sha256:"):
                algorithm = hashlib.sha256()
                expected = expected_checksum[7:]
            else:
                logger.warning(f"Unknown checksum format: {expected_checksum}")
                return True  # Skip verification if format unknown
            
            # Calculate file checksum
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    algorithm.update(chunk)
            
            actual = algorithm.hexdigest()
            return actual.lower() == expected.lower()
        except Exception as e:
            logger.error(f"Error verifying checksum: {e}", exc_info=True)
            return False


class UpdateInstaller:
    """Install downloaded updates."""
    
    def __init__(self, config: UpdaterConfig):
        """Initialize update installer.
        
        Args:
            config: Updater configuration
        """
        self.config = config
    
    async def install_update(self, installer_path: Path, silent: bool = True) -> bool:
        """Install update from installer file.
        
        Args:
            installer_path: Path to installer executable
            silent: Run installer in silent mode
            
        Returns:
            True if installation successful
        """
        if not installer_path.exists():
            logger.error(f"Installer not found: {installer_path}")
            return False
        
        logger.info(f"Installing update from {installer_path}")
        
        try:
            # Run installer
            cmd = [str(installer_path)]
            if silent:
                cmd.append("/S")  # Silent mode for NSIS installer
                # Add other silent flags for different installer types if needed
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Update installed successfully")
                return True
            else:
                logger.error(f"Installer failed with code {process.returncode}")
                logger.error(f"Stderr: {stderr.decode()}")
                return False
        except Exception as e:
            logger.error(f"Error installing update: {e}", exc_info=True)
            return False


class UpdateScheduler:
    """Schedule and manage update checks."""
    
    def __init__(self, config: UpdaterConfig):
        """Initialize update scheduler.
        
        Args:
            config: Updater configuration
        """
        self.config = config
        self._checker = UpdateChecker(config)
        self._downloader = UpdateDownloader(config)
        self._installer = UpdateInstaller(config)
    
    async def check_on_startup(self) -> Optional[dict]:
        """Check for updates on startup if configured.
        
        Returns:
            Update information if available, None otherwise
        """
        if not self.config.should_check_on_startup():
            return None
        
        return await self._checker.check_for_updates()
    
    def should_check_now(self) -> bool:
        """Check if update check should run now based on frequency.
        
        Returns:
            True if check should run
        """
        if self.config.check_frequency == "manual_only":
            return False
        
        if self.config.check_frequency == "on_startup":
            # Only check on startup, not scheduled
            return False
        
        # For daily/weekly, check if enough time has passed
        if not self.config.last_check:
            return True
        
        # TODO: Implement time-based checking
        # For now, always return True if not manual_only
        return True

