# Testing Guide

This guide explains how to write and run tests for Nyx-OSINT.

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Writing Tests](#writing-tests)
4. [Running Tests](#running-tests)
5. [Test Fixtures](#test-fixtures)
6. [Mocking](#mocking)
7. [Coverage](#coverage)
8. [Best Practices](#best-practices)

---

## Overview

Nyx-OSINT uses **pytest** for testing. Tests are organized into:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows

### Test Requirements

- Python 3.12+
- pytest
- pytest-asyncio (for async tests)
- pytest-cov (for coverage)
- pytest-mock (for mocking)

---

## Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── intelligence/        # Intelligence module tests
│   ├── osint/               # OSINT module tests
│   ├── core/                # Core module tests
│   ├── export/              # Export module tests
│   ├── filters/             # Filter module tests
│   ├── gui/                  # GUI tests
│   └── test_cli.py          # CLI tests
├── integration/             # Integration tests
│   ├── test_search_pipeline.py
│   ├── test_database.py
│   └── test_export.py
├── conftest.py              # Shared fixtures
└── sanity.py                # Sanity checks
```

---

## Writing Tests

### Basic Test

```python
import pytest
from nyx.osint.search import SearchService

def test_search_service_initialization():
    """Test SearchService initialization."""
    service = SearchService()
    assert service is not None
    assert service.http_client is not None
```

### Async Test

```python
import pytest
from nyx.osint.search import SearchService

@pytest.mark.asyncio
async def test_search_username():
    """Test username search."""
    service = SearchService()
    try:
        results = await service.search_username("testuser")
        assert isinstance(results, dict)
    finally:
        await service.aclose()
```

### Parametrized Test

```python
import pytest
from nyx.core.utils import validate_email

@pytest.mark.parametrize("email,expected", [
    ("test@example.com", True),
    ("invalid-email", False),
    ("user@domain.co.uk", True),
    ("", False),
])
def test_validate_email(email, expected):
    """Test email validation."""
    assert validate_email(email) == expected
```

### Test with Fixtures

```python
import pytest
from nyx.osint.search import SearchService

@pytest.mark.asyncio
async def test_search_with_fixture(search_service):
    """Test search using fixture."""
    results = await search_service.search_username("testuser")
    assert isinstance(results, dict)
```

---

## Running Tests

### Run All Tests

```bash
poetry run pytest
```

### Run Specific Test File

```bash
poetry run pytest tests/unit/test_search.py
```

### Run Specific Test

```bash
poetry run pytest tests/unit/test_search.py::test_search_username
```

### Run with Verbose Output

```bash
poetry run pytest -v
```

### Run with Coverage

```bash
poetry run pytest --cov=src/nyx --cov-report=html
```

### Run Only Failed Tests

```bash
poetry run pytest --lf
```

### Run Tests Matching Pattern

```bash
poetry run pytest -k "test_search"
```

---

## Test Fixtures

### Conftest.py

Shared fixtures are defined in `tests/conftest.py`:

```python
import pytest
from nyx.osint.search import SearchService

@pytest.fixture
async def search_service():
    """Create SearchService instance."""
    service = SearchService()
    yield service
    await service.aclose()

@pytest.fixture
def mock_http_client():
    """Create mock HTTP client."""
    from unittest.mock import AsyncMock
    client = AsyncMock()
    return client
```

### Using Fixtures

```python
@pytest.mark.asyncio
async def test_with_fixture(search_service):
    """Test using search_service fixture."""
    results = await search_service.search_username("test")
    assert results is not None
```

---

## Mocking

### Mock HTTP Requests

```python
import pytest
from unittest.mock import AsyncMock, patch
from nyx.osint.search import SearchService

@pytest.mark.asyncio
async def test_search_with_mock():
    """Test search with mocked HTTP client."""
    service = SearchService()
    
    # Mock HTTP response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = "<html>Profile exists</html>"
    
    with patch.object(service.http_client, 'get', return_value=mock_response):
        results = await service.search_username("testuser")
        assert isinstance(results, dict)
    
    await service.aclose()
```

### Mock External APIs

```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_email_intelligence_with_mock():
    """Test email intelligence with mocked API."""
    from nyx.intelligence.email import EmailIntelligence
    
    email_intel = EmailIntelligence()
    
    # Mock breach check API
    mock_breach_data = {
        "breached": True,
        "breaches": ["Breach1", "Breach2"]
    }
    
    with patch('nyx.intelligence.email.check_breach_api', return_value=mock_breach_data):
        result = await email_intel.investigate("test@example.com")
        assert result.breached is True
        assert len(result.breaches) == 2
```

### Mock Database

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_database_operations():
    """Test database operations with mocked session."""
    from nyx.models.target import Target
    
    mock_session = Mock()
    mock_query = Mock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = Target(id=1, identifier="test")
    
    with patch('nyx.core.database.get_session', return_value=mock_session):
        # Test database operations
        pass
```

---

## Coverage

### Generate Coverage Report

```bash
# Terminal report
poetry run pytest --cov=src/nyx --cov-report=term-missing

# HTML report
poetry run pytest --cov=src/nyx --cov-report=html

# XML report (for CI)
poetry run pytest --cov=src/nyx --cov-report=xml
```

### Coverage Configuration

Create `.coveragerc`:

```ini
[run]
source = src/nyx
omit = 
    */tests/*
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

### Coverage Goals

- **Minimum**: 70% overall coverage
- **Target**: 80% overall coverage
- **Critical Modules**: 90%+ coverage

---

## Best Practices

### 1. Test Isolation

Each test should be independent:

```python
# Good: Each test is independent
def test_a():
    assert func_a() == expected_a

def test_b():
    assert func_b() == expected_b

# Bad: Tests depend on each other
def test_a():
    global_state = "modified"

def test_b():
    assert global_state == "modified"  # Depends on test_a
```

### 2. Descriptive Names

Use descriptive test names:

```python
# Good
def test_search_username_returns_dict():
    pass

def test_search_username_handles_invalid_input():
    pass

# Bad
def test_search():
    pass

def test_1():
    pass
```

### 3. Arrange-Act-Assert

Follow AAA pattern:

```python
def test_example():
    # Arrange: Set up test data
    username = "testuser"
    service = SearchService()
    
    # Act: Execute code under test
    results = await service.search_username(username)
    
    # Assert: Verify results
    assert isinstance(results, dict)
    assert len(results) >= 0
```

### 4. Test Edge Cases

Test boundary conditions:

```python
@pytest.mark.parametrize("username", [
    "",  # Empty string
    "a" * 300,  # Very long
    "user@name",  # Special characters
    "123",  # Numeric
])
def test_search_edge_cases(username):
    # Test edge cases
    pass
```

### 5. Clean Up Resources

Always clean up resources:

```python
@pytest.mark.asyncio
async def test_with_resources():
    service = SearchService()
    try:
        # Test code
        pass
    finally:
        await service.aclose()
```

### 6. Use Fixtures for Setup

```python
@pytest.fixture
async def search_service():
    """Create and clean up SearchService."""
    service = SearchService()
    yield service
    await service.aclose()

@pytest.mark.asyncio
async def test_with_fixture(search_service):
    # Fixture handles cleanup automatically
    results = await search_service.search_username("test")
```

---

## Integration Tests

### Example Integration Test

```python
import pytest
from nyx.intelligence.smart import SmartSearchService, SmartSearchInput

@pytest.mark.asyncio
async def test_smart_search_integration():
    """Test complete Smart search workflow."""
    service = SmartSearchService()
    try:
        input_obj = SmartSearchInput(
            raw_text="John Doe @johndoe john@example.com",
            region="US"
        )
        result = await service.smart_search(input_obj)
        
        assert result is not None
        assert len(result.identifiers) > 0
        assert len(result.candidates) >= 0
    finally:
        await service.aclose()
```

---

## End-to-End Tests

### Example E2E Test

```python
import pytest
from nyx.cli import cli
from click.testing import CliRunner

def test_cli_search_command():
    """Test CLI search command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "-u", "testuser"])
    assert result.exit_code == 0
    assert "testuser" in result.output
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest --cov=src/nyx --cov-report=xml
      - uses: codecov/codecov-action@v2
```

---

## Troubleshooting

### Common Issues

1. **Async test warnings**: Use `@pytest.mark.asyncio`
2. **Fixture not found**: Check `conftest.py` location
3. **Import errors**: Ensure `src/` is in Python path
4. **Resource leaks**: Always clean up async resources

### Debugging Tests

```bash
# Run with debug output
poetry run pytest -v --pdb

# Run with print statements
poetry run pytest -s

# Run specific test with debugger
poetry run pytest tests/unit/test_search.py::test_search_username --pdb
```

---

## Resources

- **pytest Documentation**: https://docs.pytest.org/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **Mocking Guide**: https://docs.python.org/3/library/unittest.mock.html

---

**Version:** 0.1.0  
**Last Updated:** 2025-01-23

