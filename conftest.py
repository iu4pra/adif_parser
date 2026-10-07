#!/usr/bin/python3
# This software under the MIT License
# Pytest configuration - Global mocks for Playwright tests

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_playwright_globally():
    """
    Auto-mock Playwright for ALL tests.
    This fixture runs for every test without needing explicit decorators.
    Avoids the need for @patch on every test and speeds up CI by skipping
    playwright install --with-deps
    """
    with patch("playwright_wrapper.sync_playwright") as mock_sync_playwright:
        # Setup the mock structure
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        # Configure return values for context manager

        # Covers pattern:
        # with sync_playwright() as p:
        mock_sync_playwright.return_value.__enter__.return_value = mock_pw
        mock_sync_playwright.return_value.__exit__.return_value = None

        # Covers pattern:
        # sync_playwright().start()
        mock_sync_playwright.return_value.start.return_value = mock_pw

        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        yield {
            "playwright": mock_pw,
            "browser": mock_browser,
            "page": mock_page,
        }


@pytest.fixture
def mock_playwright_components():
    """
    Provides individual mock components for tests that need fine-grained control.
    Use this when you need to inspect or modify specific mock behavior.
    """
    mock_pw = MagicMock()
    mock_browser = MagicMock()
    mock_page = MagicMock()

    return {
        "pw": mock_pw,
        "browser": mock_browser,
        "page": mock_page,
    }
