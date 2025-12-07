"""Update notification system for GUI."""

import threading
from typing import Optional

from nyx.core.logger import get_logger

logger = get_logger(__name__)


class UpdateNotificationManager:
    """Manage update notifications in GUI."""
    
    def __init__(self, parent_window):
        """Initialize notification manager.
        
        Args:
            parent_window: Parent GUI window (MainWindow)
        """
        self.parent = parent_window
        self._notification_window: Optional = None
    
    def show_update_available(self, update_info: dict):
        """Show notification that update is available.
        
        Args:
            update_info: Update information dictionary
        """
        try:
            import customtkinter as ctk
            
            # Create notification window
            if self._notification_window:
                self._notification_window.destroy()
            
            self._notification_window = ctk.CTkToplevel(self.parent)
            self._notification_window.title("Update Available")
            self._notification_window.geometry("500x400")
            self._notification_window.transient(self.parent)
            self._notification_window.grab_set()
            
            # Version info
            version_label = ctk.CTkLabel(
                self._notification_window,
                text=f"Update Available: {update_info.get('version', 'Unknown')}",
                font=("Helvetica", 16, "bold"),
            )
            version_label.pack(pady=10)
            
            current_label = ctk.CTkLabel(
                self._notification_window,
                text=f"Current: {update_info.get('current_version', 'Unknown')}",
                font=("Helvetica", 12),
            )
            current_label.pack(pady=5)
            
            # Changelog
            changelog_text = ctk.CTkTextbox(self._notification_window, height=150)
            changelog_text.pack(fill="both", expand=True, padx=10, pady=10)
            changelog_text.insert("1.0", update_info.get("changelog", "No changelog available."))
            changelog_text.configure(state="disabled")
            
            # Buttons
            button_frame = ctk.CTkFrame(self._notification_window)
            button_frame.pack(pady=10)
            
            def download_update():
                # Trigger download via parent window if available
                if hasattr(self.parent, '_check_for_updates'):
                    # Store update info for download
                    self.parent._pending_update = update_info
                    logger.info("Download update requested")
                self._notification_window.destroy()
            
            def later():
                self._notification_window.destroy()
            
            download_btn = ctk.CTkButton(
                button_frame,
                text="Download Update",
                command=download_update,
                width=150,
            )
            download_btn.pack(side="left", padx=5)
            
            later_btn = ctk.CTkButton(
                button_frame,
                text="Later",
                command=later,
                width=150,
            )
            later_btn.pack(side="left", padx=5)
            
        except Exception as e:
            logger.error(f"Error showing update notification: {e}", exc_info=True)
    
    def show_update_progress(self, progress: float, message: str = "Downloading update..."):
        """Show update download/install progress.
        
        Args:
            progress: Progress percentage (0-100)
            message: Progress message
        """
        try:
            import customtkinter as ctk
            
            if not self._notification_window:
                self._notification_window = ctk.CTkToplevel(self.parent)
                self._notification_window.title("Update Progress")
                self._notification_window.geometry("400x150")
                self._notification_window.transient(self.parent)
            
            # Clear existing widgets
            for widget in self._notification_window.winfo_children():
                widget.destroy()
            
            # Progress label
            progress_label = ctk.CTkLabel(
                self._notification_window,
                text=message,
                font=("Helvetica", 12),
            )
            progress_label.pack(pady=10)
            
            # Progress bar
            progress_bar = ctk.CTkProgressBar(self._notification_window, width=300)
            progress_bar.pack(pady=10)
            progress_bar.set(progress / 100.0)
            
            # Percentage label
            percent_label = ctk.CTkLabel(
                self._notification_window,
                text=f"{progress:.1f}%",
                font=("Helvetica", 11),
            )
            percent_label.pack(pady=5)
            
        except Exception as e:
            logger.error(f"Error showing progress: {e}", exc_info=True)
    
    def show_update_complete(self, version: str):
        """Show notification that update is complete.
        
        Args:
            version: Installed version
        """
        try:
            import customtkinter as ctk
            
            if self._notification_window:
                self._notification_window.destroy()
            
            self._notification_window = ctk.CTkToplevel(self.parent)
            self._notification_window.title("Update Complete")
            self._notification_window.geometry("350x150")
            self._notification_window.transient(self.parent)
            self._notification_window.grab_set()
            
            success_label = ctk.CTkLabel(
                self._notification_window,
                text="✅ Update Installed Successfully!",
                font=("Helvetica", 14, "bold"),
            )
            success_label.pack(pady=20)
            
            version_label = ctk.CTkLabel(
                self._notification_window,
                text=f"Version {version} is now installed.",
                font=("Helvetica", 11),
            )
            version_label.pack(pady=5)
            
            def close():
                self._notification_window.destroy()
            
            ok_btn = ctk.CTkButton(
                self._notification_window,
                text="OK",
                command=close,
                width=100,
            )
            ok_btn.pack(pady=10)
            
        except Exception as e:
            logger.error(f"Error showing completion notification: {e}", exc_info=True)
    
    def close(self):
        """Close any open notification windows."""
        if self._notification_window:
            try:
                self._notification_window.destroy()
            except Exception:
                pass
            self._notification_window = None


# Global notification function for use by update service
def show_update_notification(update_info: dict):
    """Show update notification (called from update service).
    
    Args:
        update_info: Update information dictionary
    """
    # This will be called from update service
    # If GUI is available, it should register a handler
    logger.info(f"Update available: {update_info.get('version')}")
    # GUI integration will be handled by MainWindow if available

