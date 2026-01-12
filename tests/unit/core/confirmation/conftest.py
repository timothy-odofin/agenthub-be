"""
Pytest configuration for confirmation tests.
"""

import pytest

# Configure pytest-asyncio to use function-scoped event loops
pytest_plugins = ('pytest_asyncio',)


def pytest_configure(config):
    """Configure pytest settings."""
    config.option.asyncio_mode = "auto"
