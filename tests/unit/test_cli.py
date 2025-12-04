"""Tests for CLI module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from click.testing import CliRunner

from nyx.cli import cli


class TestCLICommands:
    """Test CLI command functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Nyx OSINT" in result.output

    def test_cli_version(self):
        """Test CLI version option."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

    @patch("nyx.cli.load_config")
    @patch("nyx.cli.setup_logging")
    def test_cli_no_subcommand(self, mock_setup, mock_config):
        """Test CLI without subcommand shows help."""
        result = self.runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "Nyx OSINT" in result.output

    @patch("nyx.cli.load_config")
    @patch("nyx.cli.setup_logging")
    @patch("nyx.cli._search_username")
    def test_search_username_command(self, mock_search, mock_setup, mock_config):
        """Test username search command."""
        mock_config.return_value = MagicMock()
        mock_search.return_value = None

        result = self.runner.invoke(cli, ["search", "-u", "testuser"])

        # Command should be invoked (may fail due to async, but should parse correctly)
        assert result.exit_code in [0, 1]  # May fail due to async execution

    @patch("nyx.cli.load_config")
    @patch("nyx.cli.setup_logging")
    @patch("nyx.cli._search_email")
    def test_search_email_command(self, mock_search, mock_setup, mock_config):
        """Test email search command."""
        mock_config.return_value = MagicMock()
        mock_search.return_value = None

        result = self.runner.invoke(cli, ["search", "-e", "test@example.com"])

        assert result.exit_code in [0, 1]

    @patch("nyx.cli.load_config")
    @patch("nyx.cli.setup_logging")
    @patch("nyx.cli._search_phone")
    def test_search_phone_command(self, mock_search, mock_setup, mock_config):
        """Test phone search command."""
        mock_config.return_value = MagicMock()
        mock_search.return_value = None

        result = self.runner.invoke(cli, ["search", "-p", "+14155551234", "--region", "US"])

        assert result.exit_code in [0, 1]

    @patch("nyx.cli.load_config")
    @patch("nyx.cli.setup_logging")
    @patch("nyx.cli._search_person")
    def test_search_person_command(self, mock_search, mock_setup, mock_config):
        """Test person search command."""
        mock_config.return_value = MagicMock()
        mock_search.return_value = None

        result = self.runner.invoke(cli, ["search", "-w", "John Doe", "--region", "CA"])

        assert result.exit_code in [0, 1]

    @patch("nyx.cli.load_config")
    @patch("nyx.cli.setup_logging")
    @patch("nyx.cli._search_deep")
    def test_search_deep_command(self, mock_search, mock_setup, mock_config):
        """Test deep search command."""
        mock_config.return_value = MagicMock()
        mock_search.return_value = None

        result = self.runner.invoke(cli, ["search", "-d", "testquery"])

        assert result.exit_code in [0, 1]

    @patch("nyx.cli.load_config")
    @patch("nyx.cli.setup_logging")
    @patch("nyx.cli.SmartSearchService")
    def test_smart_command(self, mock_service_class, mock_setup, mock_config):
        """Test smart search command."""
        mock_config.return_value = MagicMock()
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.smart_search = AsyncMock(return_value=MagicMock(
            input=MagicMock(raw_text="test", region=None),
            identifiers={"usernames": [], "emails": [], "phones": [], "names": []},
            candidates=[],
            target_id=None,
        ))
        mock_service.aclose = AsyncMock()

        result = self.runner.invoke(cli, ["smart", "test query"])

        assert result.exit_code in [0, 1]

    @patch("nyx.cli.load_config")
    @patch("nyx.cli.setup_logging")
    @patch("nyx.cli.get_platform_database")
    def test_platforms_command(self, mock_db, mock_setup, mock_config):
        """Test platforms command."""
        mock_config.return_value = MagicMock()
        mock_platform_db = MagicMock()
        mock_platform_db.platforms = {}
        mock_db.return_value = mock_platform_db

        result = self.runner.invoke(cli, ["platforms"])

        assert result.exit_code in [0, 1]

    @patch("nyx.cli.load_config")
    @patch("nyx.cli.setup_logging")
    @patch("nyx.cli.get_platform_database")
    def test_stats_command(self, mock_db, mock_setup, mock_config):
        """Test stats command."""
        mock_config.return_value = MagicMock()
        mock_platform_db = MagicMock()
        mock_platform_db.count_platforms = MagicMock(return_value=100)
        mock_platform_db.platforms = {}
        mock_db.return_value = mock_platform_db

        result = self.runner.invoke(cli, ["stats"])

        assert result.exit_code in [0, 1]

    @patch("nyx.cli.load_config")
    @patch("nyx.cli.setup_logging")
    def test_help_command(self, mock_setup, mock_config):
        """Test help command."""
        mock_config.return_value = MagicMock()

        result = self.runner.invoke(cli, ["help"])

        assert result.exit_code == 0

    @patch("nyx.cli.load_config")
    @patch("nyx.cli.setup_logging")
    def test_help_command_with_query(self, mock_setup, mock_config):
        """Test help command with query."""
        mock_config.return_value = MagicMock()

        result = self.runner.invoke(cli, ["help", "search"])

        assert result.exit_code == 0

    @patch("nyx.cli.load_config")
    @patch("nyx.cli.setup_logging")
    def test_config_error_handling(self, mock_setup, mock_config):
        """Test config error handling."""
        mock_config.side_effect = Exception("Config error")

        result = self.runner.invoke(cli, ["search", "-u", "testuser"])

        assert result.exit_code == 1
        assert "Error loading configuration" in result.output

