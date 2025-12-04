"""Tests for GUI main window."""

import pytest
from unittest.mock import MagicMock, patch

from nyx.gui.main_window import MainWindow, create_app


class TestMainWindow:
    """Test MainWindow functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        with patch("nyx.gui.main_window.ctk.CTk"), patch(
            "nyx.gui.main_window.load_config"
        ):
            self.config = MagicMock()
            self.window = MainWindow(self.config)

    def test_initialization(self):
        """Test window initialization."""
        assert self.window.config == self.config
        assert self.window.main_content is not None

    def test_create_sidebar(self):
        """Test sidebar creation."""
        assert hasattr(self.window, "sidebar")

    def test_create_content_area(self):
        """Test content area creation."""
        assert hasattr(self.window, "main_content")
        assert hasattr(self.window, "search_entry")
        assert hasattr(self.window, "search_type")

    def test_search_type_selection(self):
        """Test search type selection."""
        assert self.window.search_type.get() == "username"

    def test_perform_search_empty_query(self):
        """Test search with empty query."""
        self.window.search_entry.delete(0, "end")
        self.window.status_label = MagicMock()

        self.window.perform_search()

        # Should update status with error message
        self.window.status_label.configure.assert_called()

    @patch("nyx.gui.main_window.threading.Thread")
    def test_perform_search(self, mock_thread):
        """Test search execution."""
        self.window.search_entry.insert(0, "testuser")
        self.window.status_label = MagicMock()
        self.window.results_text = MagicMock()

        self.window.perform_search()

        mock_thread.assert_called_once()

    def test_update_results_thread_safe(self):
        """Test thread-safe results update."""
        self.window.results_text = MagicMock()
        self.window.after = MagicMock()

        self.window._update_results("test")

        self.window.after.assert_called_once()

    def test_update_summary_thread_safe(self):
        """Test thread-safe summary update."""
        self.window.summary_text = MagicMock()
        self.window.after = MagicMock()

        self.window._update_summary("test")

        self.window.after.assert_called_once()

    def test_update_status_thread_safe(self):
        """Test thread-safe status update."""
        self.window.status_label = MagicMock()
        self.window.after = MagicMock()

        self.window._update_status("test")

        self.window.after.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_username(self):
        """Test username search method."""
        with patch("nyx.gui.main_window.SearchService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.search_username = AsyncMock(
                return_value={"Twitter": {"found": True, "url": "https://twitter.com/test"}}
            )
            mock_service.aclose = AsyncMock()

            self.window._update_results = MagicMock()
            self.window._update_summary = MagicMock()
            self.window._update_status = MagicMock()

            await self.window._search_username("testuser")

            mock_service.search_username.assert_called_once()
            mock_service.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_email(self):
        """Test email search method."""
        with patch("nyx.gui.main_window.EmailIntelligence") as mock_class:
            mock_intel = MagicMock()
            mock_class.return_value = mock_intel
            mock_intel.investigate = AsyncMock(return_value=MagicMock(
                valid=True,
                breached=False,
                disposable=False,
                provider="Gmail",
                reputation_score=80.0,
                online_profiles={},
            ))

            self.window._update_results = MagicMock()
            self.window._update_summary = MagicMock()
            self.window._update_status = MagicMock()

            await self.window._search_email("test@example.com")

            mock_intel.investigate.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_phone(self):
        """Test phone search method."""
        with patch("nyx.gui.main_window.PhoneIntelligence") as mock_class:
            mock_intel = MagicMock()
            mock_class.return_value = mock_intel
            mock_intel.investigate = AsyncMock(return_value=MagicMock(
                valid=True,
                country_name="United States",
                country_code="US",
                carrier="AT&T",
                line_type="mobile",
                timezone=None,
                associated_name=None,
            ))

            self.window._update_results = MagicMock()
            self.window._update_summary = MagicMock()
            self.window._update_status = MagicMock()

            await self.window._search_phone("+14155551234", "US")

            mock_intel.investigate.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_person(self):
        """Test person search method."""
        with patch("nyx.gui.main_window.PersonIntelligence") as mock_class:
            mock_intel = MagicMock()
            mock_class.return_value = mock_intel
            mock_intel.investigate = AsyncMock(return_value=MagicMock(
                addresses=[],
                phone_numbers=[],
                email_addresses=[],
                social_profiles={},
            ))

            self.window._update_results = MagicMock()
            self.window._update_summary = MagicMock()
            self.window._update_status = MagicMock()

            await self.window._search_person("John Doe", "CA")

            mock_intel.investigate.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_smart(self):
        """Test Smart search method."""
        with patch("nyx.gui.main_window.SmartSearchService") as mock_class:
            mock_service = AsyncMock()
            mock_class.return_value = mock_service
            mock_service.smart_search = AsyncMock(return_value=MagicMock(
                identifiers={"usernames": [], "emails": [], "phones": [], "names": []},
                candidates=[],
            ))
            mock_service.aclose = AsyncMock()

            self.window._update_results = MagicMock()
            self.window._update_summary = MagicMock()
            self.window._update_status = MagicMock()

            await self.window._search_smart("test query", None)

            mock_service.smart_search.assert_called_once()
            mock_service.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_deep(self):
        """Test deep search method."""
        with patch("nyx.gui.main_window.SearchService") as mock_search_class, patch(
            "nyx.gui.main_window.EmailIntelligence"
        ) as mock_email_class, patch(
            "nyx.gui.main_window.PhoneIntelligence"
        ) as mock_phone_class:

            mock_search = AsyncMock()
            mock_search_class.return_value = mock_search
            mock_search.search_username = AsyncMock(return_value={})
            mock_search.aclose = AsyncMock()

            mock_email = MagicMock()
            mock_email_class.return_value = mock_email
            mock_email.investigate = AsyncMock()

            mock_phone = MagicMock()
            mock_phone_class.return_value = mock_phone
            mock_phone.investigate = AsyncMock()

            self.window._update_results = MagicMock()
            self.window._update_status = MagicMock()

            await self.window._search_deep("test", None)

            mock_search.aclose.assert_called_once()

    def test_on_search_click(self):
        """Test search menu click handler."""
        self.window.on_search_click()

        # Should not raise

    def test_on_targets_click(self):
        """Test targets menu click handler."""
        self.window.on_targets_click()

        # Should not raise

    def test_on_results_click(self):
        """Test results menu click handler."""
        self.window.on_results_click()

        # Should not raise

    def test_on_settings_click(self):
        """Test settings menu click handler."""
        self.window.on_settings_click()

        # Should not raise


class TestCreateApp:
    """Test create_app function."""

    @patch("nyx.gui.main_window.MainWindow")
    @patch("nyx.gui.main_window.load_config")
    def test_create_app_with_config(self, mock_config, mock_window_class):
        """Test app creation with config."""
        mock_config.return_value = MagicMock()
        mock_window = MagicMock()
        mock_window_class.return_value = mock_window

        app = create_app()

        assert app == mock_window
        mock_window_class.assert_called_once()

    @patch("nyx.gui.main_window.MainWindow")
    @patch("nyx.gui.main_window.load_config")
    def test_create_app_without_config(self, mock_config, mock_window_class):
        """Test app creation without config."""
        mock_config.return_value = MagicMock()
        mock_window = MagicMock()
        mock_window_class.return_value = mock_window

        app = create_app(config=None)

        assert app == mock_window

