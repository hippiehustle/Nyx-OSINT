"""Background update service for scheduled checks and notifications."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from nyx.config.updater_config import UpdaterConfig
from nyx.core.logger import get_logger
from nyx.core.updater import UpdateChecker, UpdateScheduler
from nyx.utils.update_utils import add_update_history_entry, get_last_update_check

logger = get_logger(__name__)


class UpdateService:
    """Background service for managing updates."""
    
    def __init__(self, config: UpdaterConfig):
        """Initialize update service.
        
        Args:
            config: Updater configuration
        """
        self.config = config
        self.scheduler = UpdateScheduler(config)
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the update service."""
        if self._running:
            logger.warning("Update service already running")
            return
        
        self._running = True
        logger.info("Update service started")
        
        # Check on startup if configured
        if self.config.should_check_on_startup():
            await self._check_on_startup()
        
        # Start scheduled checks if configured
        if self.config.check_frequency not in ["manual_only", "on_startup"]:
            self._task = asyncio.create_task(self._scheduled_checks())
    
    async def stop(self):
        """Stop the update service."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Update service stopped")
    
    async def _check_on_startup(self):
        """Perform startup update check."""
        try:
            logger.info("Performing startup update check...")
            update_info = await self.scheduler.check_on_startup()
            
            if update_info:
                logger.info(f"Update available: {update_info.get('version')}")
                # TODO: Trigger notification
                add_update_history_entry(
                    update_info.get("version", "unknown"),
                    "check",
                    True,
                    {"update_available": True},
                )
            else:
                logger.info("No updates available")
                add_update_history_entry("current", "check", True, {"update_available": False})
        except Exception as e:
            logger.error(f"Error during startup check: {e}", exc_info=True)
            add_update_history_entry("unknown", "check", False, {"error": str(e)})
    
    async def _scheduled_checks(self):
        """Perform scheduled update checks."""
        while self._running:
            try:
                # Calculate next check time based on frequency
                interval = self._get_check_interval()
                
                # Wait for interval
                await asyncio.sleep(interval.total_seconds())
                
                if not self._running:
                    break
                
                # Check if enough time has passed since last check
                last_check = get_last_update_check()
                if last_check:
                    time_since_check = datetime.now() - last_check
                    if time_since_check < interval:
                        # Not enough time has passed, wait more
                        continue
                
                logger.info("Performing scheduled update check...")
                checker = UpdateChecker(self.config)
                update_info = await checker.check_for_updates()
                
                if update_info:
                    logger.info(f"Update available: {update_info.get('version')}")
                    # TODO: Trigger notification
                    add_update_history_entry(
                        update_info.get("version", "unknown"),
                        "check",
                        True,
                        {"update_available": True},
                    )
                else:
                    add_update_history_entry("current", "check", True, {"update_available": False})
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during scheduled check: {e}", exc_info=True)
                add_update_history_entry("unknown", "check", False, {"error": str(e)})
    
    def _get_check_interval(self) -> timedelta:
        """Get check interval based on frequency setting.
        
        Returns:
            Time interval for checks
        """
        frequency = self.config.check_frequency
        
        if frequency == "daily":
            return timedelta(days=1)
        elif frequency == "weekly":
            return timedelta(weeks=1)
        else:
            # Default to daily
            return timedelta(days=1)
    
    async def check_now(self) -> Optional[dict]:
        """Manually trigger update check.
        
        Returns:
            Update information if available
        """
        logger.info("Manual update check triggered")
        checker = UpdateChecker(self.config)
        update_info = await checker.check_for_updates()
        
        if update_info:
            add_update_history_entry(
                update_info.get("version", "unknown"),
                "check",
                True,
                {"update_available": True, "manual": True},
            )
        else:
            add_update_history_entry("current", "check", True, {"update_available": False, "manual": True})
        
        return update_info

