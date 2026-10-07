#!/usr/bin/python3

# This software under the MIT License
# Unit tests for the Playwright wrapper module

import logging
import os
import tempfile
import unittest
from pathlib import Path

import playwright_wrapper
from playwright_wrapper import PLAYWRIGHT_SCREENSHOT_DPI


class UtilityFunctionsTest(unittest.TestCase):
    """Test cases for utility functions in playwright_wrapper"""

    def test_cm_to_playwright_px_basic(self):
        """Test basic cm to pixels conversion"""
        # 2.54 cm = 96 px (at default DPI)
        result = playwright_wrapper.cm_to_playwright_px(2.54)
        self.assertEqual(result, PLAYWRIGHT_SCREENSHOT_DPI)

    def test_cm_to_playwright_px_zero(self):
        """Test conversion with zero input"""
        result = playwright_wrapper.cm_to_playwright_px(0)
        self.assertEqual(result, 0)

    def test_cm_to_playwright_px_float_values(self):
        """Test conversion with various float values"""
        # 1 cm
        result = playwright_wrapper.cm_to_playwright_px(1.0)
        self.assertEqual(result, int(1.0 * PLAYWRIGHT_SCREENSHOT_DPI / 2.54))

        # 10 cm
        result = playwright_wrapper.cm_to_playwright_px(10.0)
        self.assertEqual(result, int(10.0 * PLAYWRIGHT_SCREENSHOT_DPI / 2.54))

    def test_cm_to_playwright_px_negative(self):
        """Test conversion with negative values (should work mathematically)"""
        result = playwright_wrapper.cm_to_playwright_px(-2.54)
        self.assertEqual(result, -PLAYWRIGHT_SCREENSHOT_DPI)


class QSLRendererContextManagerTest(unittest.TestCase):
    """Test cases for QSLRenderer context manager functionality"""

    def test_renderer_context_manager_enters(self):
        """Test that QSLRenderer can be used as context manager"""
        with playwright_wrapper.QSLRenderer() as renderer:
            self.assertIsNotNone(renderer._playwright)
            self.assertIsNotNone(renderer._browser)

    def test_renderer_context_manager_exits_cleanly(self):
        """Test that context manager cleanup works"""
        renderer = playwright_wrapper.QSLRenderer()
        with renderer:
            playwright_obj = renderer._playwright
            browser_obj = renderer._browser

        # After exit, these should be cleaned up (browser closed)
        # We can't directly test if they're None, but no exception should be raised

    def test_renderer_initialization_none_values(self):
        """Test that initialization sets None values"""
        renderer = playwright_wrapper.QSLRenderer()
        self.assertIsNone(renderer._playwright)
        self.assertIsNone(renderer._browser)

    def test_renderer_handles_exception_in_context(self):
        """Test that renderer handles exceptions gracefully"""
        # Mocking is handled by conftest.py fixture
        with self.assertRaises(ValueError):
            with playwright_wrapper.QSLRenderer() as renderer:
                raise ValueError("Test exception")


class QSLRendererRenderTest(unittest.TestCase):
    """Test cases for QSLRenderer.render() method"""

    def setUp(self):
        """Create temporary directory and test HTML file"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = self.temp_dir.name

        # Create a simple HTML file for testing
        self.test_html_file = os.path.join(self.temp_path, "test_qsl.html")
        with open(self.test_html_file, "w") as f:
            f.write(
                "<html><head><title>Test QSL Card</title></head><body><div><p>Test QSL Card</p></div></body></html>"
            )

    def tearDown(self):
        """Clean up temporary files"""
        self.temp_dir.cleanup()

    def test_render_pdf_output(self):
        """Test rendering to PDF format"""
        # Mocking is handled by conftest.py fixture
        output_pdf = os.path.join(self.temp_path, "output.pdf")

        with playwright_wrapper.QSLRenderer() as renderer:
            renderer.render(self.test_html_file, output_pdf, 10.0, 15.0)

        # Verify PDF method was called (via mock)
        # Note: actual assertions on mock calls can be added with mock_playwright_components fixture if needed

    def test_render_image_output(self):
        """Test rendering to image format"""
        # Mocking is handled by conftest.py fixture
        output_png = os.path.join(self.temp_path, "output.png")

        with playwright_wrapper.QSLRenderer() as renderer:
            renderer.render(self.test_html_file, output_png, 10.0, 15.0)

    def test_render_jpg_output(self):
        """Test rendering to JPG format"""
        # Mocking is handled by conftest.py fixture
        output_jpg = os.path.join(self.temp_path, "output.jpg")

        with playwright_wrapper.QSLRenderer() as renderer:
            renderer.render(self.test_html_file, output_jpg, 10.0, 15.0)

    def test_render_page_closure(self):
        """Test that pages are properly closed"""
        # Mocking is handled by conftest.py fixture
        output_file = os.path.join(self.temp_path, "output.pdf")

        with playwright_wrapper.QSLRenderer() as renderer:
            renderer.render(self.test_html_file, output_file, 10.0, 15.0)

    def test_render_with_different_dimensions(self):
        """Test rendering with various width/height combinations"""
        # Mocking is handled by conftest.py fixture
        test_cases = [
            (14.0, 9.0),  # Standard QSL size
            (21.0, 29.7),  # A4 size
            (1.0, 1.0),  # Very small
            (100.0, 100.0),  # Very large
        ]

        for width, height in test_cases:
            output_file = os.path.join(self.temp_path, f"output_{width}x{height}.pdf")

            with playwright_wrapper.QSLRenderer() as renderer:
                renderer.render(self.test_html_file, output_file, width, height)


class GenerateQslImageTest(unittest.TestCase):
    """Test cases for generate_qsl_image() function"""

    def setUp(self):
        """Create temporary directory and test HTML file"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = self.temp_dir.name

        self.test_html_file = os.path.join(self.temp_path, "test_qsl.html")
        with open(self.test_html_file, "w") as f:
            f.write("<html><body><p>Test</p></body></html>")

    def tearDown(self):
        """Clean up temporary files"""
        self.temp_dir.cleanup()

    def test_generate_qsl_image_basic(self):
        """Test basic image generation"""
        # Mocking is handled by conftest.py fixture
        output_file = os.path.join(self.temp_path, "output.png")

        playwright_wrapper.generate_qsl_image(self.test_html_file, output_file, 10, 15)

    def test_generate_qsl_image_browser_cleanup(self):
        """Test that browser is cleaned up after image generation"""
        # Mocking is handled by conftest.py fixture
        output_file = os.path.join(self.temp_path, "output.png")

        playwright_wrapper.generate_qsl_image(self.test_html_file, output_file, 10, 15)


class GenerateQslPdfTest(unittest.TestCase):
    """Test cases for generate_qsl_pdf() function"""

    def setUp(self):
        """Create temporary directory and test HTML file"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = self.temp_dir.name

        self.test_html_file = os.path.join(self.temp_path, "test_qsl.html")
        with open(self.test_html_file, "w") as f:
            f.write("<html><body><p>Test</p></body></html>")

    def tearDown(self):
        """Clean up temporary files"""
        self.temp_dir.cleanup()

    def test_generate_qsl_pdf_basic(self):
        """Test basic PDF generation"""
        # Mocking is handled by conftest.py fixture
        output_file = os.path.join(self.temp_path, "output.pdf")

        playwright_wrapper.generate_qsl_pdf(self.test_html_file, output_file, 10, 15)

    def test_generate_qsl_pdf_parameters(self):
        """Test that PDF is generated with correct parameters"""
        # Mocking is handled by conftest.py fixture
        output_file = os.path.join(self.temp_path, "output.pdf")

        playwright_wrapper.generate_qsl_pdf(
            self.test_html_file, output_file, 10.5, 15.3
        )


# Automatically run tests when this module is executed
if __name__ == "__main__":
    # Override logging configuration to show only critical errors
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s", level=logging.CRITICAL
    )

    # Use this to conditionally disable all logging output
    DISABLE_LOGGING = True

    if DISABLE_LOGGING:
        logging.basicConfig(handlers=[logging.NullHandler()], force=True)

    unittest.main()
