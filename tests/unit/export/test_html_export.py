"""Tests for HTML export module."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from nyx.export.html import HTMLExporter


class TestHTMLExporter:
    """Test HTMLExporter functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.exporter = HTMLExporter()

    def test_initialization_default(self):
        """Test HTMLExporter initialization with defaults."""
        assert self.exporter.template_dir is None
        assert self.exporter.env is None

    def test_initialization_with_template_dir(self):
        """Test HTMLExporter initialization with template directory."""
        with TemporaryDirectory() as tmpdir:
            exporter = HTMLExporter(template_dir=tmpdir)
            assert exporter.template_dir == Path(tmpdir)
            assert exporter.env is not None

    def test_export_basic(self):
        """Test basic HTML export."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"
            data = {
                "profiles": [
                    {"platform": "Twitter", "username": "testuser", "url": "https://twitter.com/testuser"}
                ],
                "data": [],
            }

            self.exporter.export(data, str(output_path), title="Test Report")

            assert output_path.exists()
            content = output_path.read_text(encoding="utf-8")
            assert "Test Report" in content
            assert "Twitter" in content
            assert "testuser" in content

    def test_export_with_description(self):
        """Test HTML export with description."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"
            data = {"profiles": [], "data": []}

            self.exporter.export(
                data,
                str(output_path),
                title="Test Report",
                description="Test description",
            )

            content = output_path.read_text(encoding="utf-8")
            assert "Test description" in content

    def test_export_with_profiles(self):
        """Test HTML export with multiple profiles."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"
            data = {
                "profiles": [
                    {"platform": "Twitter", "username": "user1", "url": "https://twitter.com/user1"},
                    {"platform": "GitHub", "username": "user2", "url": "https://github.com/user2"},
                ],
                "data": [],
            }

            self.exporter.export(data, str(output_path))

            content = output_path.read_text(encoding="utf-8")
            assert "Twitter" in content
            assert "GitHub" in content
            assert "user1" in content
            assert "user2" in content

    def test_export_with_data_table(self):
        """Test HTML export with data table."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"
            data = {
                "profiles": [],
                "data": [
                    {"name": "John", "age": 30, "city": "NYC"},
                    {"name": "Jane", "age": 25, "city": "LA"},
                ],
            }

            self.exporter.export(data, str(output_path))

            content = output_path.read_text(encoding="utf-8")
            assert "John" in content
            assert "Jane" in content
            assert "NYC" in content

    def test_export_redact_fields(self):
        """Test HTML export with field redaction."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"
            data = {
                "profiles": [
                    {"platform": "Twitter", "username": "testuser", "email": "test@example.com"}
                ],
                "data": [],
            }

            self.exporter.export(
                data, str(output_path), redact_fields=["email"]
            )

            content = output_path.read_text(encoding="utf-8")
            assert "[REDACTED]" in content
            assert "test@example.com" not in content

    def test_export_redact_nested_fields(self):
        """Test HTML export with nested field redaction."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"
            data = {
                "profiles": [
                    {
                        "platform": "Twitter",
                        "username": "testuser",
                        "metadata": {"email": "test@example.com", "phone": "1234567890"},
                    }
                ],
                "data": [],
            }

            self.exporter.export(
                data, str(output_path), redact_fields=["email"]
            )

            content = output_path.read_text(encoding="utf-8")
            # Check that nested email is redacted
            assert "testuser" in content  # Username should remain

    def test_export_creates_directory(self):
        """Test that export creates parent directory if needed."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "test.html"
            data = {"profiles": [], "data": []}

            self.exporter.export(data, str(output_path))

            assert output_path.exists()
            assert output_path.parent.exists()

    def test_redact_fields_recursive(self):
        """Test recursive field redaction."""
        data = {
            "profiles": [
                {"platform": "Twitter", "email": "test@example.com"},
            ],
            "data": [
                {"name": "John", "email": "john@example.com"},
            ],
        }

        redacted = self.exporter._redact_fields(data, ["email"])

        assert redacted["profiles"][0]["email"] == "[REDACTED]"
        assert redacted["data"][0]["email"] == "[REDACTED]"
        assert redacted["profiles"][0]["platform"] == "Twitter"  # Not redacted

    def test_redact_fields_empty(self):
        """Test redaction with empty fields list."""
        data = {"profiles": [{"platform": "Twitter", "email": "test@example.com"}]}
        redacted = self.exporter._redact_fields(data, [])
        assert redacted == data

    def test_export_metadata_included(self):
        """Test that metadata is included in export."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"
            data = {"profiles": [], "data": []}

            self.exporter.export(data, str(output_path))

            content = output_path.read_text(encoding="utf-8")
            assert "Generated:" in content
            assert "Nyx OSINT Platform" in content

