#!/usr/bin/python3

# This software under the MIT License
# Simple Playwright wrapper

import logging
import os.path
from pathlib import Path
from playwright.sync_api import sync_playwright

# DPI used by page.screenshot()
# Found empyrically to match page.pdf() output
PLAYWRIGHT_SCREENSHOT_DPI = 96

# TEMPORARY TO AVOID CIRCULAR IMPORT
def cm_to_px(cm, dpi):
    """Converts centimeters to pixels given a DPI value"""
    return int(cm * dpi / 2.54)


def generate_qsl_image(_input_html: str, _output_name: str, _width: int, _height: int):
    """Simple wrapper to generate a single image, very inefficient because the browser is launched once per QSO"""
    with sync_playwright() as p:
        # Map URI to local file
        file_url = Path(_input_html).resolve().as_uri()

        browser = p.chromium.launch()

        page = browser.new_page()
        page.goto(file_url)
        # screenshot() only works at fixed DPI!
        page.screenshot(
            path=_output_name,
            clip={
                "x": 0,
                "y": 0,
                "width": _width * PLAYWRIGHT_SCREENSHOT_DPI / 2.54,
                "height": _height * PLAYWRIGHT_SCREENSHOT_DPI / 2.54,
            },
        )
        page.close()
        browser.close()


def generate_qsl_pdf(_input_html: str, _output_name: str, _width: int, _height: int):
    """Simple wrapper to generate a single PDF, very inefficient because the browser is launched once per QSO"""
    with sync_playwright() as p:
        # Map URI to local file
        file_url = Path(_input_html).resolve().as_uri()

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()
        page.goto(file_url)
        page.pdf(
            path=_output_name,
            width=f"{_width}cm",  # Works with px (it's even more accurate)
            height=f"{_height}cm",  # Works with px (it's even more accurate)
            print_background=True,
            margin={"top": "0cm", "right": "0cm", "bottom": "0cm", "left": "0cm"},
        )
        page.close()
        browser.close()


class QSLRenderer:
    """Class for QSL generation within a single Playwright browser instance"""

    def __init__(self):
        # For safer __exit__ handling
        self._playwright = None
        self._browser = None

    # To use the object in a with context
    def __enter__(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch()
        return self

    # To use the object in a with context, guaranteed to run even if exceptions are raised
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logging.error(f"Error: {exc_type}: {exc_val}")
        try:
            if self._browser:
                self._browser.close()
        finally:
            if self._playwright:
                self._playwright.stop()

    def render(
        self, _input_html: str, _output_name: str, _width: float, _height: float
    ):
        """Generate QSL card as image or PDF"""
        logging.info("QSLRenderer.render() start")
        file_url = Path(_input_html).resolve().as_uri()
        page = self._browser.new_page()

        try:
            logging.info("QSLRenderer.render() goto")
            page.goto(file_url, wait_until="load")

            # Check if PDF output is requested
            logging.info("QSLRenderer.render() generate")
            if Path(_output_name).suffix.lower() == ".pdf":
                page.pdf(
                    path=_output_name,
                    width=f"{_width}cm",  # Works with px (it's even more accurate)
                    height=f"{_height}cm",  # Works with px (it's even more accurate)
                    print_background=True,
                    margin={
                        "top": "0cm",
                        "right": "0cm",
                        "bottom": "0cm",
                        "left": "0cm",
                    },
                )
            else:
                # Otherwise fallback to image at the moment
                page.screenshot(
                    path=_output_name,
                    clip={
                        "x": 0,
                        "y": 0,
                        "width": int(_width * PLAYWRIGHT_SCREENSHOT_DPI / 2.54),
                        "height": int(_height * PLAYWRIGHT_SCREENSHOT_DPI / 2.54),
                    },
                )
        finally:
            page.close()
        logging.info("QSLRenderer.render() end")
