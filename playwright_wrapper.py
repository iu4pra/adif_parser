#!/usr/bin/python3

# This software under the MIT License
# Simple Playwright wrapper

import os.path
from pathlib import Path
from playwright.sync_api import sync_playwright

def generate_qsl_image(_input_html: str, _output_name: str, _width: int, _height: int):
    with sync_playwright() as p:
        # Map URI to local file
        file_url = Path(_input_html).resolve().as_uri()

        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': _width, 'height': _height})
        page.goto(file_url)
        page.screenshot(path=_output_name, clip={'x': 0, 'y': 0, 'width': _width, 'height': _height})
        browser.close()

def generate_qsl_pdf(_input_html: str, _output_name: str, _width: int, _height: int):
    with sync_playwright() as p:
        # Map URI to local file
        file_url = Path(_input_html).resolve().as_uri()

        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(file_url)
        page.pdf(path=_output_name,
        width=f"{_width}cm",
        height=f"{_height}cm",
        print_background=True,
        margin={
        "top": "0cm",
        "right": "0cm",
        "bottom": "0cm",
        "left": "0cm"
        }
        )
        browser.close()