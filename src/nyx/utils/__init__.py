"""Utility modules for Nyx OSINT."""

from nyx.utils.progress import (
    AnimatedProgressBar,
    SimpleProgressBar,
    ProgressBarConfig,
    ProgressItem,
    Colors,
)

# Try to import update utilities (may not be available in all builds)
try:
    from nyx.utils.update_utils import (
        add_update_history_entry,
        calculate_download_progress,
        calculate_file_checksum,
        format_file_size,
        get_last_installed_version,
        get_last_update_check,
        load_update_history,
        save_update_history,
        verify_checksum,
    )
    __all__ = [
        "AnimatedProgressBar",
        "SimpleProgressBar",
        "ProgressBarConfig",
        "ProgressItem",
        "Colors",
        "calculate_file_checksum",
        "verify_checksum",
        "format_file_size",
        "calculate_download_progress",
        "load_update_history",
        "save_update_history",
        "add_update_history_entry",
        "get_last_update_check",
        "get_last_installed_version",
    ]
except ImportError:
    __all__ = [
        "AnimatedProgressBar",
        "SimpleProgressBar",
        "ProgressBarConfig",
        "ProgressItem",
        "Colors",
    ]
