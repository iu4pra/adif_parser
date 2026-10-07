#!/usr/bin/python3
# pytest configuration
# Mocks Playwright to avoid installation during tests

import sys
from unittest.mock import MagicMock


# Provide expected functions
def mock_sync_playwright():
    """Factory che ritorna il mock structure per sync_playwright"""
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=MagicMock())
    mock.__exit__ = MagicMock(return_value=False)
    return mock


# Mock playwright before any test imports it
# This prevents the need to install playwright during CI
sys.modules["playwright"] = MagicMock()
sys.modules["playwright.sync_api"] = MagicMock()
# Expose factory in mocked module
sys.modules["playwright.sync_api"].sync_playwright = mock_sync_playwright
