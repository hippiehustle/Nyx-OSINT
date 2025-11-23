"""Tests for advanced filtering module."""

import pytest
from nyx.filters.advanced import AdvancedFilter, FilterRule, FilterOperator, QueryParser


class TestAdvancedFilter:
    """Test advanced filtering functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.filter = AdvancedFilter()

    def test_filter_equals(self):
        """Test equals filter."""
        items = [{"name": "John"}, {"name": "Jane"}, {"name": "john"}]
        rule = FilterRule("name", FilterOperator.EQUALS, "John", case_sensitive=True)
        result = self.filter.filter_items(items, [rule])
        assert len(result) == 1
        assert result[0]["name"] == "John"

    def test_filter_contains(self):
        """Test contains filter."""
        items = [{"text": "Hello World"}, {"text": "Goodbye"}, {"text": "hello"}]
        rule = FilterRule("text", FilterOperator.CONTAINS, "hello", case_sensitive=False)
        result = self.filter.filter_items(items, [rule])
        assert len(result) == 2

    def test_filter_regex(self):
        """Test regex filter."""
        items = [{"email": "test@gmail.com"}, {"email": "user@yahoo.com"}, {"email": "admin@gmail.com"}]
        rule = FilterRule("email", FilterOperator.REGEX, r"@gmail\.com$")
        result = self.filter.filter_items(items, [rule])
        assert len(result) == 2

    def test_filter_greater_than(self):
        """Test greater than filter."""
        items = [{"age": 25}, {"age": 30}, {"age": 20}]
        rule = FilterRule("age", FilterOperator.GREATER_THAN, 22)
        result = self.filter.filter_items(items, [rule])
        assert len(result) == 2

    def test_filter_in_list(self):
        """Test in list filter."""
        items = [{"status": "active"}, {"status": "pending"}, {"status": "inactive"}]
        rule = FilterRule("status", FilterOperator.IN_LIST, ["active", "pending"])
        result = self.filter.filter_items(items, [rule])
        assert len(result) == 2

    def test_filter_multiple_rules_and(self):
        """Test multiple rules with AND logic."""
        items = [
            {"name": "John", "age": 25},
            {"name": "Jane", "age": 30},
            {"name": "Bob", "age": 20},
        ]
        rules = [
            FilterRule("age", FilterOperator.GREATER_THAN, 22),
            FilterRule("name", FilterOperator.CONTAINS, "J"),
        ]
        result = self.filter.filter_items(items, rules, match_all=True)
        assert len(result) == 2

    def test_filter_multiple_rules_or(self):
        """Test multiple rules with OR logic."""
        items = [
            {"name": "John", "age": 25},
            {"name": "Jane", "age": 30},
            {"name": "Bob", "age": 35},
        ]
        rules = [
            FilterRule("name", FilterOperator.EQUALS, "Bob"),
            FilterRule("age", FilterOperator.LESS_THAN, 26),
        ]
        result = self.filter.filter_items(items, rules, match_all=False)
        assert len(result) == 2


class TestQueryParser:
    """Test query parser."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = QueryParser()

    def test_parse_equals(self):
        """Test parsing equals operator."""
        rules = self.parser.parse("name:John")
        assert len(rules) == 1
        assert rules[0].field == "name"
        assert rules[0].operator == FilterOperator.EQUALS
        assert rules[0].value == "John"

    def test_parse_not_equals(self):
        """Test parsing not equals operator."""
        rules = self.parser.parse("status!=inactive")
        assert len(rules) == 1
        assert rules[0].operator == FilterOperator.NOT_EQUALS

    def test_parse_contains(self):
        """Test parsing contains operator."""
        rules = self.parser.parse("text~hello")
        assert len(rules) == 1
        assert rules[0].operator == FilterOperator.CONTAINS

    def test_parse_regex(self):
        """Test parsing regex operator."""
        rules = self.parser.parse("email=/.*@gmail.com/")
        assert len(rules) == 1
        assert rules[0].operator == FilterOperator.REGEX

    def test_parse_multiple(self):
        """Test parsing multiple conditions."""
        rules = self.parser.parse("name:John age>25 status!=inactive")
        assert len(rules) == 3
