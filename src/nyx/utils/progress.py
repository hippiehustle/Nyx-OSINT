"""Animated progress bar system with visual effects.

This module provides a sophisticated animated progress bar that displays live
download/processing progress with smooth visual animation effects. The progress
bar supports:
- Sequential character animation using customizable sequences
- Dynamic terminal width auto-fitting
- ANSI color support for rich terminal output
- Concurrent multiple progress bars
- Configurable styling and timing
"""

import shutil
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable
from datetime import datetime


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for styled terminal output."""

    # Reset
    RESET = "\033[0m"

    # Standard colors (8-bit)
    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        """Convert RGB to ANSI escape code."""
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def bg_rgb(r: int, g: int, b: int) -> str:
        """Convert RGB to ANSI background escape code."""
        return f"\033[48;2;{r};{g};{b}m"

    @staticmethod
    def from_hex(hex_color: str) -> str:
        """Convert hex color to ANSI escape code.

        Args:
            hex_color: Hex color string (e.g., '#ededed' or 'ededed')

        Returns:
            ANSI escape code for the color
        """
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return Colors.rgb(r, g, b)


@dataclass
class ProgressBarConfig:
    """Configuration for progress bar appearance and behavior."""

    # Animation settings
    animation_sequence: str = "░▒▓█▓▒"
    fill_char: str = "█"
    empty_char: str = "░"
    bracket_start: str = "["
    bracket_end: str = "]"

    # Layout settings
    label_width: int = 25
    size_width: int = 10
    separator: str = "|"
    bar_length: int = 50  # Default, will auto-fit if enabled
    auto_fit: bool = True
    min_bar_length: int = 20
    max_bar_length: int = 150

    # Color scheme (hex colors)
    text_color: str = "#ededed"
    bar_color: str = "#e0ff70"
    background_color: str = "#ffffff"
    percentage_color: str = "#80000d"
    separator_color: str = "#00ffff"
    complete_color: str = "#58fe58"

    # Timing (milliseconds)
    animation_speed: int = 100
    progress_update_interval: int = 500

    # Display settings
    show_percentage: bool = True
    show_fraction: bool = False
    progress_direction: str = "ltr"  # left to right

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.progress_direction not in ["ltr", "rtl"]:
            raise ValueError("progress_direction must be 'ltr' or 'rtl'")


@dataclass
class ProgressItem:
    """Represents a single progress item/bar."""

    label: str
    size: str = ""
    progress: float = 0.0  # 0-100
    target_progress: float = 0.0  # For smooth transitions
    animation_frame: int = 0
    status: str = "active"  # active, complete, error
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def update_progress(self, value: float):
        """Update target progress value.

        Args:
            value: Progress value (0-100)
        """
        self.target_progress = min(100.0, max(0.0, value))
        if self.target_progress >= 100.0:
            self.status = "complete"

    def increment_progress(self, amount: float):
        """Increment progress by amount.

        Args:
            amount: Amount to increment (can be negative)
        """
        self.update_progress(self.target_progress + amount)


class AnimatedProgressBar:
    """Animated progress bar with smooth visual effects.

    This class manages multiple concurrent progress bars with animated effects.
    Each bar shows a label, size, animated progress indicator, and percentage.

    Example:
        >>> config = ProgressBarConfig()
        >>> progress = AnimatedProgressBar(config)
        >>> progress.add_item("downloading", "pytorch-2.3.0", "1.37 GB")
        >>> progress.start()
        >>> progress.update("downloading", 50.0)
        >>> progress.stop()
    """

    def __init__(self, config: Optional[ProgressBarConfig] = None):
        """Initialize animated progress bar.

        Args:
            config: Progress bar configuration
        """
        self.config = config or ProgressBarConfig()
        self.items: Dict[str, ProgressItem] = {}
        self.running = False
        self.animation_thread: Optional[threading.Thread] = None
        self.update_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self._stop_event = threading.Event()

        # Cache terminal size
        self._terminal_width = self._get_terminal_width()
        self._last_size_check = time.time()

        # Pre-convert colors
        self._colors = {
            'text': Colors.from_hex(self.config.text_color),
            'bar': Colors.from_hex(self.config.bar_color),
            'percentage': Colors.from_hex(self.config.percentage_color),
            'separator': Colors.from_hex(self.config.separator_color),
            'complete': Colors.from_hex(self.config.complete_color),
            'reset': Colors.RESET,
        }

    def _get_terminal_width(self) -> int:
        """Get current terminal width.

        Returns:
            Terminal width in characters
        """
        try:
            size = shutil.get_terminal_size()
            return size.columns
        except Exception:
            return 80  # Fallback

    def _calculate_bar_length(self) -> int:
        """Calculate optimal bar length based on terminal width.

        Returns:
            Calculated bar length
        """
        if not self.config.auto_fit:
            return self.config.bar_length

        # Check if we need to update terminal size (every 2 seconds)
        if time.time() - self._last_size_check > 2.0:
            self._terminal_width = self._get_terminal_width()
            self._last_size_check = time.time()

        # Calculate used width
        used_width = (
            self.config.label_width +
            self.config.size_width +
            len(self.config.separator) * 3 +  # 3 separators
            len(self.config.bracket_start) +
            len(self.config.bracket_end) +
            (7 if self.config.show_percentage else 0) +  # " | 100%"
            10  # Padding and spacing
        )

        available_width = self._terminal_width - used_width
        bar_length = max(
            self.config.min_bar_length,
            min(self.config.max_bar_length, available_width)
        )

        return bar_length

    def add_item(
        self,
        item_id: str,
        label: str,
        size: str = "",
        initial_progress: float = 0.0
    ) -> None:
        """Add a new progress item.

        Args:
            item_id: Unique identifier for this item
            label: Display label (will be padded/truncated to label_width)
            size: Size string (e.g., "1.37 GB")
            initial_progress: Initial progress value (0-100)
        """
        with self.lock:
            self.items[item_id] = ProgressItem(
                label=label,
                size=size,
                progress=initial_progress,
                target_progress=initial_progress,
            )

    def update(self, item_id: str, progress: float) -> None:
        """Update progress for an item.

        Args:
            item_id: Item identifier
            progress: New progress value (0-100)
        """
        with self.lock:
            if item_id in self.items:
                self.items[item_id].update_progress(progress)

    def increment(self, item_id: str, amount: float) -> None:
        """Increment progress for an item.

        Args:
            item_id: Item identifier
            amount: Amount to increment
        """
        with self.lock:
            if item_id in self.items:
                self.items[item_id].increment_progress(amount)

    def remove_item(self, item_id: str) -> None:
        """Remove a progress item.

        Args:
            item_id: Item identifier
        """
        with self.lock:
            self.items.pop(item_id, None)

    def _render_bar(self, item: ProgressItem, bar_length: int) -> str:
        """Render a single progress bar.

        Args:
            item: Progress item to render
            bar_length: Length of the progress bar

        Returns:
            Formatted progress bar string with ANSI colors
        """
        # Format label (pad or truncate)
        label = item.label[:self.config.label_width].ljust(self.config.label_width)

        # Format size (right-aligned)
        size = item.size[:self.config.size_width].rjust(self.config.size_width)

        # Calculate filled positions based on current progress
        filled_positions = int((item.progress / 100.0) * bar_length)
        current_position = int((item.progress / 100.0) * bar_length)

        # Build the progress bar with animation
        bar_chars = []
        seq_len = len(self.config.animation_sequence)

        for pos in range(bar_length):
            if pos < filled_positions:
                # Completed section
                bar_chars.append(self.config.fill_char)
            elif pos == current_position and item.status == "active":
                # Current position - show animation sequence
                char_index = item.animation_frame % seq_len
                bar_chars.append(self.config.animation_sequence[char_index])
            else:
                # Empty section
                bar_chars.append(self.config.empty_char)

        bar_content = ''.join(bar_chars)

        # Format percentage
        percentage = f"{int(item.progress)}%"

        # Choose colors based on status
        bar_color = (
            self._colors['complete'] if item.status == "complete"
            else self._colors['bar']
        )
        percentage_color = (
            self._colors['complete'] if item.status == "complete"
            else self._colors['percentage']
        )

        # Assemble the complete line with colors
        parts = [
            self._colors['text'],
            label,
            self._colors['reset'],
            " ",
            self._colors['separator'],
            self.config.separator,
            self._colors['reset'],
            " ",
            self._colors['text'],
            size,
            self._colors['reset'],
            " ",
            self._colors['separator'],
            self.config.separator,
            self._colors['reset'],
            " ",
            bar_color,
            self.config.bracket_start,
            bar_content,
            self.config.bracket_end,
            self._colors['reset'],
            " ",
            self._colors['separator'],
            self.config.separator,
            self._colors['reset'],
            " ",
            percentage_color,
            percentage,
            self._colors['reset'],
        ]

        return ''.join(parts)

    def _render_all(self) -> str:
        """Render all progress bars.

        Returns:
            Complete output string with all progress bars
        """
        with self.lock:
            if not self.items:
                return ""

            bar_length = self._calculate_bar_length()
            lines = []

            for item_id in sorted(self.items.keys()):
                item = self.items[item_id]
                lines.append(self._render_bar(item, bar_length))

            return '\n'.join(lines)

    def _animation_loop(self):
        """Animation loop that updates animation frames."""
        while not self._stop_event.is_set():
            with self.lock:
                for item in self.items.values():
                    if item.status == "active":
                        item.animation_frame += 1

            # Sleep for animation speed (converted from ms to seconds)
            self._stop_event.wait(self.config.animation_speed / 1000.0)

    def _progress_update_loop(self):
        """Progress update loop that smoothly transitions progress values."""
        while not self._stop_event.is_set():
            with self.lock:
                for item in self.items.values():
                    # Smoothly increment progress towards target
                    if item.progress < item.target_progress:
                        diff = item.target_progress - item.progress
                        # Move 20% of the way each update for smooth transition
                        item.progress = min(
                            item.target_progress,
                            item.progress + max(0.5, diff * 0.2)
                        )
                    elif item.progress > item.target_progress:
                        # Should rarely happen, but handle it
                        item.progress = item.target_progress

            # Sleep for progress update interval (converted from ms to seconds)
            self._stop_event.wait(self.config.progress_update_interval / 1000.0)

    def _display_loop(self):
        """Main display loop that renders progress bars."""
        num_lines = 0

        while not self._stop_event.is_set():
            output = self._render_all()

            if output:
                # Clear previous lines
                if num_lines > 0:
                    # Move cursor up and clear lines
                    sys.stdout.write(f'\033[{num_lines}A')
                    sys.stdout.write('\033[J')

                # Write new output
                sys.stdout.write(output + '\n')
                sys.stdout.flush()

                num_lines = len(self.items)

            # Refresh rate (50ms for smooth display)
            time.sleep(0.05)

        # Final render after stop
        output = self._render_all()
        if output and num_lines > 0:
            sys.stdout.write(f'\033[{num_lines}A')
            sys.stdout.write('\033[J')
            sys.stdout.write(output + '\n')
            sys.stdout.flush()

    def start(self):
        """Start the animated progress bar display."""
        if self.running:
            return

        self.running = True
        self._stop_event.clear()

        # Start animation thread
        self.animation_thread = threading.Thread(
            target=self._animation_loop,
            daemon=True
        )
        self.animation_thread.start()

        # Start progress update thread
        self.update_thread = threading.Thread(
            target=self._progress_update_loop,
            daemon=True
        )
        self.update_thread.start()

        # Start display thread
        self.display_thread = threading.Thread(
            target=self._display_loop,
            daemon=True
        )
        self.display_thread.start()

    def stop(self):
        """Stop the animated progress bar display."""
        if not self.running:
            return

        self.running = False
        self._stop_event.set()

        # Wait for threads to finish
        if self.animation_thread:
            self.animation_thread.join(timeout=1.0)
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
        if hasattr(self, 'display_thread') and self.display_thread:
            self.display_thread.join(timeout=1.0)

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class SimpleProgressBar:
    """Simplified single-line progress bar for simple use cases.

    Example:
        >>> bar = SimpleProgressBar("Downloading", total=100)
        >>> bar.start()
        >>> for i in range(100):
        ...     bar.update(i + 1)
        ...     time.sleep(0.1)
        >>> bar.stop()
    """

    def __init__(
        self,
        label: str,
        total: int = 100,
        size: str = "",
        config: Optional[ProgressBarConfig] = None
    ):
        """Initialize simple progress bar.

        Args:
            label: Progress bar label
            total: Total value for completion
            size: Size string to display
            config: Optional configuration
        """
        self.label = label
        self.total = total
        self.size = size
        self.current = 0

        self._progress_bar = AnimatedProgressBar(config)
        self._progress_bar.add_item("main", label, size, 0.0)

    def update(self, value: int):
        """Update progress value.

        Args:
            value: Current progress value
        """
        self.current = value
        percentage = (value / self.total) * 100.0 if self.total > 0 else 0.0
        self._progress_bar.update("main", percentage)

    def increment(self, amount: int = 1):
        """Increment progress by amount.

        Args:
            amount: Amount to increment
        """
        self.update(self.current + amount)

    def start(self):
        """Start progress bar display."""
        self._progress_bar.start()

    def stop(self):
        """Stop progress bar display."""
        self._progress_bar.stop()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
