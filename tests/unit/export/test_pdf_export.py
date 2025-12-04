"""Tests for PDF export module."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from nyx.export.pdf import PDFExporter


class TestPDFExporter:
    """Test PDFExporter functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.exporter = PDFExporter()

    def test_initialization_default(self):
        """Test PDFExporter initialization with defaults."""
        assert self.exporter.page_size is not None
        assert self.exporter.styles is not None

    def test_initialization_letter_size(self):
        """Test PDFExporter initialization with letter size."""
        exporter = PDFExporter(page_size="letter")
        assert exporter.page_size is not None

    def test_initialization_a4_size(self):
        """Test PDFExporter initialization with A4 size."""
        exporter = PDFExporter(page_size="a4")
        assert exporter.page_size is not None

    def test_export_basic(self):
        """Test basic PDF export."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"
            data = {
                "profiles": [
                    {"platform": "Twitter", "username": "testuser", "url": "https://twitter.com/testuser"}
                ],
                "data": [],
            }

            self.exporter.export(data, str(output_path), title="Test Report")

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_export_with_description(self):
        """Test PDF export with description."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"
            data = {"profiles": [], "data": []}

            self.exporter.export(
                data,
                str(output_path),
                title="Test Report",
                description="Test description",
            )

            assert output_path.exists()

    def test_export_with_profiles(self):
        """Test PDF export with multiple profiles."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"
            data = {
                "profiles": [
                    {"platform": "Twitter", "username": "user1", "url": "https://twitter.com/user1"},
                    {"platform": "GitHub", "username": "user2", "url": "https://github.com/user2"},
                ],
                "data": [],
            }

            self.exporter.export(data, str(output_path))

            assert output_path.exists()

    def test_export_with_data_table(self):
        """Test PDF export with data table."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"
            data = {
                "profiles": [],
                "data": [
                    {"name": "John", "age": 30, "city": "NYC"},
                    {"name": "Jane", "age": 25, "city": "LA"},
                ],
            }

            self.exporter.export(data, str(output_path))

            assert output_path.exists()

    def test_export_redact_fields(self):
        """Test PDF export with field redaction."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"
            data = {
                "profiles": [
                    {"platform": "Twitter", "username": "testuser", "email": "test@example.com"}
                ],
                "data": [],
            }

            self.exporter.export(
                data, str(output_path), redact_fields=["email"]
            )

            assert output_path.exists()

    def test_export_redact_nested_fields(self):
        """Test PDF export with nested field redaction."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"
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

            assert output_path.exists()

    def test_export_creates_directory(self):
        """Test that export creates parent directory if needed."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "test.pdf"
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

    def test_export_empty_data(self):
        """Test PDF export with empty data."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"
            data = {"profiles": [], "data": []}

            self.exporter.export(data, str(output_path))

            assert output_path.exists()

    def test_export_multiple_pages(self):
        """Test PDF export with multiple pages."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"
            # Create enough profiles to potentially span multiple pages
            data = {
                "profiles": [
                    {"platform": f"Platform{i}", "username": f"user{i}"}
                    for i in range(20)
                ],
                "data": [],
            }

            self.exporter.export(data, str(output_path))

            assert output_path.exists()

