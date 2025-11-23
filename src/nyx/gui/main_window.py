"""Main application window for Nyx GUI."""

import customtkinter as ctk
from typing import Optional

from nyx.config.base import Config
from nyx.core.logger import get_logger

logger = get_logger(__name__)


class MainWindow(ctk.CTk):
    """Main application window."""

    def __init__(
        self,
        config: Optional[Config] = None,
        title: str = "Nyx - OSINT Investigation Platform",
        width: int = 1400,
        height: int = 900,
    ):
        """Initialize main window.

        Args:
            config: Application configuration
            title: Window title
            width: Window width
            height: Window height
        """
        super().__init__()

        self.config = config
        self.title(title)
        self.geometry(f"{width}x{height}")

        # Configure colors
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Create main layout
        self._create_layout()

    def _create_layout(self) -> None:
        """Create main window layout."""
        # Create sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Create main content area
        self.main_content = ctk.CTkFrame(self)
        self.main_content.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Add logo/title to sidebar
        title_label = ctk.CTkLabel(
            self.sidebar,
            text="NYX",
            font=("Helvetica", 24, "bold"),
        )
        title_label.pack(pady=20)

        version_label = ctk.CTkLabel(
            self.sidebar,
            text="v0.1.0",
            font=("Helvetica", 10),
        )
        version_label.pack()

        # Add menu buttons to sidebar
        self._create_menu_buttons()

        # Add main content
        self._create_content_area()

    def _create_menu_buttons(self) -> None:
        """Create sidebar menu buttons."""
        buttons = [
            ("Search", self.on_search_click),
            ("Targets", self.on_targets_click),
            ("Results", self.on_results_click),
            ("Settings", self.on_settings_click),
        ]

        for button_text, command in buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=button_text,
                command=command,
                width=180,
                height=40,
            )
            btn.pack(pady=5, padx=10)

    def _create_content_area(self) -> None:
        """Create main content area."""
        # Header
        header = ctk.CTkLabel(
            self.main_content,
            text="OSINT Investigation Platform",
            font=("Helvetica", 20, "bold"),
        )
        header.pack(pady=10)

        # Search frame
        search_frame = ctk.CTkFrame(self.main_content)
        search_frame.pack(fill="x", padx=10, pady=10)

        search_label = ctk.CTkLabel(
            search_frame,
            text="Search Query:",
            font=("Helvetica", 12),
        )
        search_label.pack(side="left", padx=5)

        self.search_entry = ctk.CTkEntry(search_frame, width=400)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)

        search_button = ctk.CTkButton(
            search_frame,
            text="Search",
            command=self.perform_search,
        )
        search_button.pack(side="left", padx=5)

        # Results frame
        self.results_frame = ctk.CTkFrame(self.main_content)
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.results_text = ctk.CTkTextbox(self.results_frame)
        self.results_text.pack(fill="both", expand=True)

        # Status bar
        self.status_label = ctk.CTkLabel(
            self.main_content,
            text="Ready",
            font=("Helvetica", 10),
        )
        self.status_label.pack(pady=5)

    def perform_search(self) -> None:
        """Perform search operation."""
        query = self.search_entry.get()
        if not query:
            self.status_label.configure(text="Please enter a search query")
            return

        self.status_label.configure(text=f"Searching for: {query}...")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("end", f"Searching for: {query}\n\nThis is where search results will appear.")

        logger.info(f"User initiated search for: {query}")

    def on_search_click(self) -> None:
        """Handle search button click."""
        logger.debug("Search menu clicked")

    def on_targets_click(self) -> None:
        """Handle targets button click."""
        logger.debug("Targets menu clicked")

    def on_results_click(self) -> None:
        """Handle results button click."""
        logger.debug("Results menu clicked")

    def on_settings_click(self) -> None:
        """Handle settings button click."""
        logger.debug("Settings menu clicked")


def create_app(config: Optional[Config] = None) -> MainWindow:
    """Create and return main application window.

    Args:
        config: Application configuration

    Returns:
        Main window instance
    """
    return MainWindow(config=config)
