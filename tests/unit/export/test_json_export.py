"""Tests for JSON export module."""

import pytest
import json
import tempfile
from pathlib import Path
from nyx.export.json_export import JSONExporter


class TestJSONExporter:
    """Test JSON export functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.exporter = JSONExporter()
        self.temp_dir = tempfile.mkdtemp()

    def test_export_basic(self):
        """Test basic JSON export."""
        data = {"name": "John", "age": 30, "profiles": [{"platform": "twitter"}]}
        output_path = Path(self.temp_dir) / "test.json"

        self.exporter.export(data, str(output_path))

        assert output_path.exists()

        with open(output_path) as f:
            loaded = json.load(f)
            assert loaded["name"] == "John"
            assert "_metadata" in loaded

    def test_export_without_metadata(self):
        """Test export without metadata."""
        data = {"name": "John"}
        output_path = Path(self.temp_dir) / "test2.json"

        self.exporter.export(data, str(output_path), include_metadata=False)

        with open(output_path) as f:
            loaded = json.load(f)
            assert "_metadata" not in loaded

    def test_export_with_redaction(self):
        """Test export with field redaction."""
        data = {"name": "John", "email": "john@example.com", "ssn": "123-45-6789"}
        output_path = Path(self.temp_dir) / "test3.json"

        self.exporter.export(data, str(output_path), redact_fields=["ssn", "email"])

        with open(output_path) as f:
            loaded = json.load(f)
            assert loaded["ssn"] == "[REDACTED]"
            assert loaded["email"] == "[REDACTED]"
            assert loaded["name"] == "John"
