"""Integration tests for export functionality."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from nyx.export.html import HTMLExporter
from nyx.export.pdf import PDFExporter
from nyx.export.json_export import JSONExporter
from nyx.export.csv_export import CSVExporter


class TestExportIntegration:
    """Test export integration with real search results."""

    def test_html_export_from_search_results(self):
        """Test HTML export from search results."""
        with TemporaryDirectory() as tmpdir:
            exporter = HTMLExporter()
            output_path = Path(tmpdir) / "report.html"

            data = {
                "profiles": [
                    {
                        "platform": "Twitter",
                        "username": "testuser",
                        "url": "https://twitter.com/testuser",
                        "found": True,
                    },
                    {
                        "platform": "GitHub",
                        "username": "testuser",
                        "url": "https://github.com/testuser",
                        "found": True,
                    },
                ],
                "data": [],
            }

            exporter.export(data, str(output_path), title="Test Report")

            assert output_path.exists()
            content = output_path.read_text(encoding="utf-8")
            assert "Twitter" in content
            assert "GitHub" in content

    def test_pdf_export_from_search_results(self):
        """Test PDF export from search results."""
        with TemporaryDirectory() as tmpdir:
            exporter = PDFExporter()
            output_path = Path(tmpdir) / "report.pdf"

            data = {
                "profiles": [
                    {
                        "platform": "Twitter",
                        "username": "testuser",
                        "url": "https://twitter.com/testuser",
                    }
                ],
                "data": [],
            }

            exporter.export(data, str(output_path), title="Test Report")

            assert output_path.exists()

    def test_json_export_from_search_results(self):
        """Test JSON export from search results."""
        with TemporaryDirectory() as tmpdir:
            exporter = JSONExporter()
            output_path = Path(tmpdir) / "report.json"

            data = {
                "profiles": [
                    {
                        "platform": "Twitter",
                        "username": "testuser",
                        "url": "https://twitter.com/testuser",
                    }
                ],
                "metadata": {"generated_at": "2024-01-01"},
            }

            exporter.export(data, str(output_path))

            assert output_path.exists()
            import json

            loaded = json.loads(output_path.read_text(encoding="utf-8"))
            assert "profiles" in loaded

    def test_csv_export_from_search_results(self):
        """Test CSV export from search results."""
        with TemporaryDirectory() as tmpdir:
            exporter = CSVExporter()
            output_path = Path(tmpdir) / "report.csv"

            data = [
                {"platform": "Twitter", "username": "testuser", "url": "https://twitter.com/testuser"},
                {"platform": "GitHub", "username": "testuser", "url": "https://github.com/testuser"},
            ]

            exporter.export(data, str(output_path))

            assert output_path.exists()
            content = output_path.read_text(encoding="utf-8")
            assert "Twitter" in content
            assert "GitHub" in content

    def test_export_with_redaction(self):
        """Test export with field redaction."""
        with TemporaryDirectory() as tmpdir:
            exporter = HTMLExporter()
            output_path = Path(tmpdir) / "report.html"

            data = {
                "profiles": [
                    {
                        "platform": "Twitter",
                        "username": "testuser",
                        "email": "test@example.com",
                        "phone": "1234567890",
                    }
                ],
                "data": [],
            }

            exporter.export(
                data,
                str(output_path),
                redact_fields=["email", "phone"],
            )

            content = output_path.read_text(encoding="utf-8")
            assert "[REDACTED]" in content
            assert "test@example.com" not in content

