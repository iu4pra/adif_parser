#!/usr/bin/python3

# This software under the MIT License
# Simple Playwright wrapper

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
        browser.close()


def generate_qsl_pdf(_input_html: str, _output_name: str, _width: int, _height: int):
    """Simple wrapper to generate a single PDF, very inefficient because the browser is launched once per QSO"""
    with sync_playwright() as p:
        # Map URI to local file
        file_url = Path(_input_html).resolve().as_uri()

        browser = p.chromium.launch()

        page = browser.new_page()
        page.goto(file_url)
        page.pdf(
            path=_output_name,
            width=f"{_width}cm",  # Works with px (it's even more accurate)
            height=f"{_height}cm",  # Works with px (it's even more accurate)
            print_background=True,
            margin={"top": "0cm", "right": "0cm", "bottom": "0cm", "left": "0cm"},
        )
        browser.close()
