"""Advanced filtering system for search results."""

import re
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum

from nyx.core.logger import get_logger

logger = get_logger(__name__)


class FilterOperator(Enum):
    """Filter operators."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX = "regex"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


@dataclass
class FilterRule:
    """Single filter rule."""

    field: str
    operator: FilterOperator
    value: Any
    case_sensitive: bool = False


class AdvancedFilter:
    """Advanced filtering for search results."""

    def __init__(self) -> None:
        """Initialize advanced filter."""
        self.operator_map: Dict[FilterOperator, Callable] = {
            FilterOperator.EQUALS: self._equals,
            FilterOperator.NOT_EQUALS: self._not_equals,
            FilterOperator.CONTAINS: self._contains,
            FilterOperator.NOT_CONTAINS: self._not_contains,
            FilterOperator.REGEX: self._regex,
            FilterOperator.GREATER_THAN: self._greater_than,
            FilterOperator.LESS_THAN: self._less_than,
            FilterOperator.IN_LIST: self._in_list,
            FilterOperator.NOT_IN_LIST: self._not_in_list,
        }

    def apply_rule(self, item: Dict[str, Any], rule: FilterRule) -> bool:
        """Apply single filter rule to item.

        Args:
            item: Item to filter
            rule: Filter rule

        Returns:
            True if item matches rule, False otherwise
        """
        if rule.field not in item:
            return False

        value = item[rule.field]
        operator_func = self.operator_map.get(rule.operator)

        if not operator_func:
            logger.warning(f"Unknown operator: {rule.operator}")
            return False

        return operator_func(value, rule.value, rule.case_sensitive)

    def _equals(self, value: Any, target: Any, case_sensitive: bool) -> bool:
        """Check equality."""
        if isinstance(value, str) and isinstance(target, str) and not case_sensitive:
            return value.lower() == target.lower()
        return value == target

    def _not_equals(self, value: Any, target: Any, case_sensitive: bool) -> bool:
        """Check inequality."""
        return not self._equals(value, target, case_sensitive)

    def _contains(self, value: Any, target: Any, case_sensitive: bool) -> bool:
        """Check if value contains target."""
        if not isinstance(value, str) or not isinstance(target, str):
            return False
        if not case_sensitive:
            return target.lower() in value.lower()
        return target in value

    def _not_contains(self, value: Any, target: Any, case_sensitive: bool) -> bool:
        """Check if value does not contain target."""
        return not self._contains(value, target, case_sensitive)

    def _regex(self, value: Any, pattern: str, case_sensitive: bool) -> bool:
        """Check regex match."""
        if not isinstance(value, str):
            return False
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            return bool(re.search(pattern, value, flags))
        except re.error:
            logger.warning(f"Invalid regex pattern: {pattern}")
            return False

    def _greater_than(self, value: Any, target: Any, case_sensitive: bool) -> bool:
        """Check if value is greater than target."""
        try:
            return float(value) > float(target)
        except (ValueError, TypeError):
            return False

    def _less_than(self, value: Any, target: Any, case_sensitive: bool) -> bool:
        """Check if value is less than target."""
        try:
            return float(value) < float(target)
        except (ValueError, TypeError):
            return False

    def _in_list(self, value: Any, target_list: List[Any], case_sensitive: bool) -> bool:
        """Check if value is in list."""
        if not isinstance(target_list, list):
            return False
        if isinstance(value, str) and not case_sensitive:
            return value.lower() in [str(t).lower() for t in target_list]
        return value in target_list

    def _not_in_list(self, value: Any, target_list: List[Any], case_sensitive: bool) -> bool:
        """Check if value is not in list."""
        return not self._in_list(value, target_list, case_sensitive)

    def filter_items(
        self, items: List[Dict[str, Any]], rules: List[FilterRule], match_all: bool = True
    ) -> List[Dict[str, Any]]:
        """Filter items using multiple rules.

        Args:
            items: Items to filter
            rules: Filter rules
            match_all: True to require all rules match (AND), False for any (OR)

        Returns:
            Filtered items
        """
        if not rules:
            return items

        filtered = []
        for item in items:
            if match_all:
                if all(self.apply_rule(item, rule) for rule in rules):
                    filtered.append(item)
            else:
                if any(self.apply_rule(item, rule) for rule in rules):
                    filtered.append(item)

        return filtered


class FilterChain:
    """Chain multiple filters together."""

    def __init__(self) -> None:
        """Initialize filter chain."""
        self.filters: List[AdvancedFilter] = []
        self.rules: List[List[FilterRule]] = []

    def add_filter(self, rules: List[FilterRule]) -> "FilterChain":
        """Add filter to chain.

        Args:
            rules: Filter rules

        Returns:
            Self for chaining
        """
        self.filters.append(AdvancedFilter())
        self.rules.append(rules)
        return self

    def apply(self, items: List[Dict[str, Any]], match_all: bool = True) -> List[Dict[str, Any]]:
        """Apply filter chain to items.

        Args:
            items: Items to filter
            match_all: True to require all rules match (AND), False for any (OR)

        Returns:
            Filtered items
        """
        result = items
        for filter_obj, rules in zip(self.filters, self.rules):
            result = filter_obj.filter_items(result, rules, match_all)
        return result

    def clear(self) -> None:
        """Clear all filters."""
        self.filters = []
        self.rules = []


class QueryParser:
    """Parse advanced query syntax."""

    def __init__(self) -> None:
        """Initialize query parser."""
        pass

    def parse(self, query: str) -> List[FilterRule]:
        """Parse query string into filter rules.

        Query syntax:
            field:value - equals
            field!=value - not equals
            field~value - contains
            field!~value - not contains
            field>value - greater than
            field<value - less than
            field=/regex/ - regex match

        Args:
            query: Query string

        Returns:
            List of filter rules
        """
        rules = []
        parts = query.split()

        for part in parts:
            if "!=" in part:
                field, value = part.split("!=", 1)
                rules.append(FilterRule(field, FilterOperator.NOT_EQUALS, value))
            elif "!~" in part:
                field, value = part.split("!~", 1)
                rules.append(FilterRule(field, FilterOperator.NOT_CONTAINS, value))
            elif "~" in part:
                field, value = part.split("~", 1)
                rules.append(FilterRule(field, FilterOperator.CONTAINS, value))
            elif ">=" in part:
                field, value = part.split(">=", 1)
                rules.append(FilterRule(field, FilterOperator.GREATER_THAN, value))
            elif "<=" in part:
                field, value = part.split("<=", 1)
                rules.append(FilterRule(field, FilterOperator.LESS_THAN, value))
            elif ">" in part:
                field, value = part.split(">", 1)
                rules.append(FilterRule(field, FilterOperator.GREATER_THAN, value))
            elif "<" in part:
                field, value = part.split("<", 1)
                rules.append(FilterRule(field, FilterOperator.LESS_THAN, value))
            elif "=" in part and part.count("=") == 1:
                if "/" in part and part.endswith("/"):
                    field, pattern = part.split("=/", 1)
                    pattern = pattern.rstrip("/")
                    rules.append(FilterRule(field, FilterOperator.REGEX, pattern))
                else:
                    field, value = part.split("=", 1)
                    rules.append(FilterRule(field, FilterOperator.EQUALS, value))
            elif ":" in part:
                field, value = part.split(":", 1)
                rules.append(FilterRule(field, FilterOperator.EQUALS, value))

        return rules
