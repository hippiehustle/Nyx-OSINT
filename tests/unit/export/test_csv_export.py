"""Tests for CSV export module."""

import pytest
import csv
import tempfile
from pathlib import Path
from nyx.export.csv_export import CSVExporter


class TestCSVExporter:
    """Test CSV export functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.exporter = CSVExporter()
        self.temp_dir = tempfile.mkdtemp()

    def test_export_basic(self):
        """Test basic CSV export."""
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
        ]
        output_path = Path(self.temp_dir) / "test.csv"

        self.exporter.export(data, str(output_path))

        assert output_path.exists()

        with open(output_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["name"] == "John"

    def test_export_with_fieldnames(self):
        """Test export with specific field names."""
        data = [
            {"name": "John", "age": 30, "email": "john@example.com"},
            {"name": "Jane", "age": 25, "email": "jane@example.com"},
        ]
        output_path = Path(self.temp_dir) / "test2.csv"

        self.exporter.export(data, str(output_path), fieldnames=["name", "age"])

        with open(output_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert "email" not in rows[0]

    def test_export_with_redaction(self):
        """Test export with field redaction."""
        data = [
            {"name": "John", "ssn": "123-45-6789"},
            {"name": "Jane", "ssn": "987-65-4321"},
        ]
        output_path = Path(self.temp_dir) / "test3.csv"

        self.exporter.export(data, str(output_path), redact_fields=["ssn"])

        with open(output_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert rows[0]["ssn"] == "[REDACTED]"
