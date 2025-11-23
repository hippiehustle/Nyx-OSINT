"""Pytest configuration and fixtures."""

import asyncio
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def tmp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config_file(tmp_dir: Path) -> Path:
    """Create temporary config file."""
    config_path = tmp_dir / "config.yaml"
    config_path.write_text("""
debug: true
data_dir: ./data
config_dir: ./config
database:
  url: sqlite:///:memory:
http:
  timeout: 5
  retries: 1
cache:
  enabled: true
  ttl: 60
""")
    return config_path
