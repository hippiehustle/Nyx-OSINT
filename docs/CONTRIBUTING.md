# Contributing to Nyx-OSINT

Thank you for your interest in contributing to Nyx-OSINT! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Contributing Process](#contributing-process)
5. [Coding Standards](#coding-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Documentation](#documentation)
8. [Submitting Changes](#submitting-changes)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior

- Be respectful and considerate
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or inflammatory comments
- Personal attacks
- Publishing others' private information

---

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)
- Git
- Basic understanding of OSINT principles

### First Contribution

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/Nyx-OSINT.git
   cd Nyx-OSINT
   ```
3. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Setup

### 1. Install Dependencies

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Install development dependencies
poetry install --with dev
```

### 2. Set Up Pre-commit Hooks

```bash
# Install pre-commit
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

### 3. Configure Environment

```bash
# Copy example configuration
cp .env.example .env.local

# Edit configuration
nano .env.local
```

### 4. Run Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/nyx --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_specific.py
```

---

## Contributing Process

### Types of Contributions

1. **Bug Fixes**: Fix issues reported in GitHub Issues
2. **Features**: Implement new functionality
3. **Documentation**: Improve or add documentation
4. **Tests**: Add or improve test coverage
5. **Performance**: Optimize existing code
6. **Platforms**: Add new platform checkers

### Workflow

1. **Check Issues**: Look for existing issues or create a new one
2. **Plan**: Discuss your approach in the issue
3. **Implement**: Write code following our standards
4. **Test**: Ensure all tests pass
5. **Document**: Update relevant documentation
6. **Submit**: Create a pull request

---

## Coding Standards

### Python Style

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line Length**: 100 characters (soft limit)
- **Type Hints**: Required for all public functions
- **Docstrings**: Google-style docstrings for all public APIs

### Code Formatting

We use **Ruff** for linting and formatting:

```bash
# Check code style
poetry run ruff check src tests

# Auto-fix issues
poetry run ruff check --fix src tests

# Format code
poetry run ruff format src tests
```

### Type Hints

Always include type hints for function parameters and return types:

```python
from typing import Optional, Dict, List

def search_username(
    username: str,
    exclude_nsfw: bool = False,
) -> Dict[str, Profile]:
    """Search for username across platforms.
    
    Args:
        username: Username to search
        exclude_nsfw: Whether to exclude NSFW platforms
        
    Returns:
        Dictionary mapping platform names to Profile objects
    """
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def process_data(data: List[str], threshold: int = 10) -> Dict[str, int]:
    """Process data and return statistics.
    
    Args:
        data: List of data items to process
        threshold: Minimum count threshold
        
    Returns:
        Dictionary with statistics
        
    Raises:
        ValueError: If data is empty
    """
    if not data:
        raise ValueError("Data cannot be empty")
    # ...
```

### Naming Conventions

- **Functions/Methods**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Prefix with `_`

### Async/Await

Use `async`/`await` for I/O operations:

```python
async def fetch_data(url: str) -> Dict[str, Any]:
    async with HTTPClient() as client:
        response = await client.get(url)
        return response.json()
```

---

## Testing Guidelines

### Test Structure

Tests are organized in `tests/` directory:

```
tests/
├── unit/          # Unit tests
├── integration/   # Integration tests
└── conftest.py    # Shared fixtures
```

### Writing Tests

Use `pytest` for testing:

```python
import pytest
from nyx.osint.search import SearchService

@pytest.mark.asyncio
async def test_search_username():
    service = SearchService()
    results = await service.search_username("testuser")
    assert isinstance(results, dict)
    await service.aclose()
```

### Test Coverage

- Aim for >80% coverage
- Test edge cases and error conditions
- Mock external dependencies

### Running Tests

```bash
# All tests
poetry run pytest

# Specific test
poetry run pytest tests/unit/test_search.py::test_search_username

# With coverage
poetry run pytest --cov=src/nyx --cov-report=term-missing
```

---

## Documentation

### Code Documentation

- Document all public APIs
- Include examples in docstrings
- Explain complex logic

### User Documentation

- Update `docs/USER_MANUAL.md` for user-facing changes
- Update `docs/API.md` for API changes
- Add examples where helpful

### Developer Documentation

- Update `docs/ARCHITECTURE.md` for architectural changes
- Update `docs/CONTRIBUTING.md` for process changes
- Document new extension points

---

## Submitting Changes

### Pull Request Process

1. **Update your branch**:
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-branch
   git rebase main
   ```

2. **Ensure tests pass**:
   ```bash
   poetry run pytest
   poetry run ruff check src tests
   ```

3. **Write a clear PR description**:
   - What changes were made
   - Why they were made
   - How to test
   - Related issues

4. **Create Pull Request**:
   - Use descriptive title
   - Link related issues
   - Request review from maintainers

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Changelog updated (if applicable)

### Review Process

1. Maintainers review your PR
2. Address feedback and suggestions
3. Make requested changes
4. PR is merged when approved

---

## Adding New Platforms

### Platform Checker Plugin

Create a new plugin:

```python
from nyx.osint.plugin import PlatformCheckerPlugin
from nyx.osint.profile import Profile

class MyPlatformChecker(PlatformCheckerPlugin):
    async def check(self, username: str) -> Optional[Profile]:
        # Implementation
        pass
    
    def get_platform_name(self) -> str:
        return "myplatform"
```

### Platform Database Entry

Add platform to `data/platforms.json`:

```json
{
  "name": "MyPlatform",
  "url": "https://myplatform.com/{username}",
  "check_type": "status_code",
  "category": "social_media",
  "nsfw": false
}
```

### Testing

Add tests:

```python
@pytest.mark.asyncio
async def test_my_platform_checker():
    checker = MyPlatformChecker()
    profile = await checker.check("testuser")
    assert profile is not None
```

---

## Performance Considerations

### Optimization Guidelines

- Profile before optimizing
- Use async/await for I/O
- Cache expensive operations
- Batch operations when possible

### Benchmarking

```bash
# Run benchmarks
poetry run pytest tests/benchmarks/ -v
```

---

## Security Considerations

### Security Best Practices

- Never commit API keys or secrets
- Validate and sanitize all inputs
- Use parameterized queries for database
- Follow principle of least privilege

### Reporting Security Issues

**Do NOT** create public issues for security vulnerabilities.

Instead:
1. Email security concerns privately
2. Provide detailed description
3. Allow time for fix before disclosure

---

## Getting Help

### Resources

- **Documentation**: `docs/` directory
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Architecture**: `docs/ARCHITECTURE.md`

### Questions?

- Open a GitHub Discussion
- Ask in an existing issue
- Contact maintainers

---

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in release notes
- Acknowledged in documentation

---

Thank you for contributing to Nyx-OSINT! 🎉

**Version:** 0.1.0  
**Last Updated:** 2025-01-23

