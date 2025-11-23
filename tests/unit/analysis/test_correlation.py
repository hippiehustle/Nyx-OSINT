"""Tests for correlation analysis module."""

import pytest
from nyx.analysis.correlation import CorrelationAnalyzer


class TestCorrelationAnalyzer:
    """Test correlation analysis functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = CorrelationAnalyzer()

    def test_calculate_similarity_identical(self):
        """Test similarity of identical data."""
        data1 = {"name": "John", "age": 30, "city": "NYC"}
        data2 = {"name": "John", "age": 30, "city": "NYC"}
        similarity = self.analyzer.calculate_similarity(data1, data2)
        assert similarity == 1.0

    def test_calculate_similarity_different(self):
        """Test similarity of different data."""
        data1 = {"name": "John", "age": 30}
        data2 = {"name": "Jane", "age": 25}
        similarity = self.analyzer.calculate_similarity(data1, data2)
        assert 0 <= similarity < 1.0

    def test_calculate_similarity_no_common(self):
        """Test similarity with no common keys."""
        data1 = {"name": "John"}
        data2 = {"age": 30}
        similarity = self.analyzer.calculate_similarity(data1, data2)
        assert similarity == 0.0

    def test_find_shared_attributes(self):
        """Test finding shared attributes."""
        profiles = [
            {"id": "1", "email": "test@example.com", "location": "NYC"},
            {"id": "2", "email": "test@example.com", "location": "LA"},
            {"id": "3", "email": "other@example.com", "location": "NYC"},
        ]
        shared = self.analyzer.find_shared_attributes(profiles)
        assert "test@example.com" in shared
        assert "NYC" in shared

    def test_correlate_profiles(self):
        """Test profile correlation."""
        profiles = [
            {"id": "1", "username": "john_doe", "email": "john@example.com"},
            {"id": "2", "username": "john_doe", "email": "john@example.com"},
            {"id": "3", "username": "jane_smith", "email": "jane@example.com"},
        ]
        correlations = self.analyzer.correlate_profiles(profiles)
        assert len(correlations) > 0
        assert correlations[0].score > 0.3

    def test_calculate_confidence_score(self):
        """Test confidence score calculation."""
        data_points = [
            {"verified": True, "has_email": True, "has_phone": True},
            {"verified": False, "has_email": True, "has_phone": False},
        ]
        score = self.analyzer.calculate_confidence_score(data_points)
        assert 0 <= score <= 100
