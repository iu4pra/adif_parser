#!/usr/bin/python3

# This software under the MIT License
# Unit tests for the Playwright wrapper module

import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

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

    @patch("playwright_wrapper.sync_playwright")
    def test_renderer_handles_exception_in_context(self, mock_playwright):
        """Test that renderer handles exceptions gracefully"""
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_playwright.return_value.start.return_value = mock_pw
        mock_pw.chromium.launch.return_value = mock_browser

        with self.assertRaises(ValueError):
            with playwright_wrapper.QSLRenderer() as renderer:
                raise ValueError("Test exception")

        # Browser should still be closed
        mock_browser.close.assert_called()
        mock_pw.stop.assert_called()


class QSLRendererRenderTest(unittest.TestCase):
    """Test cases for QSLRenderer.render() method"""

    def setUp(self):
        """Create temporary directory and test HTML file"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = self.temp_dir.name

        # Create a simple HTML file for testing
        self.test_html_file = os.path.join(self.temp_path, "test_qsl.html")
        with open(self.test_html_file, "w") as f:
            f.write("""
            <html>
                <head><title>Test QSL Card</title></head>
                <body>
                    <div class="qsl-card">
                        <p>Test QSL Card</p>
                    </div>
                </body>
            </html>
            """)

    def tearDown(self):
        """Clean up temporary files"""
        self.temp_dir.cleanup()

    @patch("playwright_wrapper.sync_playwright")
    def test_render_pdf_output(self, mock_playwright):
        """Test rendering to PDF format"""
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright.return_value.start.return_value = mock_pw
        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        output_pdf = os.path.join(self.temp_path, "output.pdf")

        with playwright_wrapper.QSLRenderer() as renderer:
            renderer.render(self.test_html_file, output_pdf, 10.0, 15.0)

        # Verify PDF method was called
        mock_page.pdf.assert_called_once()
        call_kwargs = mock_page.pdf.call_args[1]
        self.assertEqual(call_kwargs["width"], "10.0cm")
        self.assertEqual(call_kwargs["height"], "15.0cm")
        self.assertTrue(call_kwargs["print_background"])

    @patch("playwright_wrapper.sync_playwright")
    def test_render_image_output(self, mock_playwright):
        """Test rendering to image format"""
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright.return_value.start.return_value = mock_pw
        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        output_png = os.path.join(self.temp_path, "output.png")

        with playwright_wrapper.QSLRenderer() as renderer:
            renderer.render(self.test_html_file, output_png, 10.0, 15.0)

        # Verify screenshot method was called
        mock_page.screenshot.assert_called_once()
        call_kwargs = mock_page.screenshot.call_args[1]
        self.assertIn("clip", call_kwargs)
        self.assertEqual(
            call_kwargs["clip"]["width"], int(10.0 * PLAYWRIGHT_SCREENSHOT_DPI / 2.54)
        )

    @patch("playwright_wrapper.sync_playwright")
    def test_render_jpg_output(self, mock_playwright):
        """Test rendering to JPG format"""
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright.return_value.start.return_value = mock_pw
        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        output_jpg = os.path.join(self.temp_path, "output.jpg")

        with playwright_wrapper.QSLRenderer() as renderer:
            renderer.render(self.test_html_file, output_jpg, 10.0, 15.0)

        # Should use screenshot for non-PDF formats
        mock_page.screenshot.assert_called_once()

    @patch("playwright_wrapper.sync_playwright")
    def test_render_page_closure(self, mock_playwright):
        """Test that pages are properly closed"""
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright.return_value.start.return_value = mock_pw
        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        output_file = os.path.join(self.temp_path, "output.pdf")

        with playwright_wrapper.QSLRenderer() as renderer:
            renderer.render(self.test_html_file, output_file, 10.0, 15.0)

        # Page should be closed after render
        mock_page.close.assert_called_once()

    @patch("playwright_wrapper.sync_playwright")
    def test_render_with_different_dimensions(self, mock_playwright):
        """Test rendering with various width/height combinations"""
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright.return_value.start.return_value = mock_pw
        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        test_cases = [
            (14.0, 9.0),  # Standard QSL size
            (21.0, 29.7),  # A4 size
            (1.0, 1.0),  # Very small
            (100.0, 100.0),  # Very large
        ]

        for width, height in test_cases:
            mock_page.reset_mock()
            output_file = os.path.join(self.temp_path, f"output_{width}x{height}.pdf")

            with playwright_wrapper.QSLRenderer() as renderer:
                renderer.render(self.test_html_file, output_file, width, height)

            # Verify dimensions were passed correctly
            call_kwargs = (
                mock_page.pdf.call_args[1]
                if mock_page.pdf.called
                else mock_page.screenshot.call_args[1]
            )
            if "width" in call_kwargs:  # PDF case
                self.assertEqual(call_kwargs["width"], f"{width}cm")
                self.assertEqual(call_kwargs["height"], f"{height}cm")


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

    @patch("playwright_wrapper.sync_playwright")
    def test_generate_qsl_image_basic(self, mock_playwright):
        """Test basic image generation"""
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright.return_value.__enter__ = MagicMock(return_value=mock_pw)
        mock_playwright.return_value.__exit__ = MagicMock(return_value=False)
        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        output_file = os.path.join(self.temp_path, "output.png")

        playwright_wrapper.generate_qsl_image(self.test_html_file, output_file, 10, 15)

        # Verify screenshot was called
        mock_page.screenshot.assert_called_once()

    @patch("playwright_wrapper.sync_playwright")
    def test_generate_qsl_image_browser_cleanup(self, mock_playwright):
        """Test that browser is cleaned up after image generation"""
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright.return_value.__enter__ = MagicMock(return_value=mock_pw)
        mock_playwright.return_value.__exit__ = MagicMock(return_value=False)
        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        output_file = os.path.join(self.temp_path, "output.png")

        playwright_wrapper.generate_qsl_image(self.test_html_file, output_file, 10, 15)

        # Verify cleanup
        mock_page.close.assert_called_once()
        mock_browser.close.assert_called_once()


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

    @patch("playwright_wrapper.sync_playwright")
    def test_generate_qsl_pdf_basic(self, mock_playwright):
        """Test basic PDF generation"""
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright.return_value.__enter__ = MagicMock(return_value=mock_pw)
        mock_playwright.return_value.__exit__ = MagicMock(return_value=False)
        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        output_file = os.path.join(self.temp_path, "output.pdf")

        playwright_wrapper.generate_qsl_pdf(self.test_html_file, output_file, 10, 15)

        # Verify PDF was called
        mock_page.pdf.assert_called_once()

    @patch("playwright_wrapper.sync_playwright")
    def test_generate_qsl_pdf_parameters(self, mock_playwright):
        """Test that PDF is generated with correct parameters"""
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright.return_value.__enter__ = MagicMock(return_value=mock_pw)
        mock_playwright.return_value.__exit__ = MagicMock(return_value=False)
        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        output_file = os.path.join(self.temp_path, "output.pdf")

        playwright_wrapper.generate_qsl_pdf(
            self.test_html_file, output_file, 10.5, 15.3
        )

        # Verify parameters
        call_kwargs = mock_page.pdf.call_args[1]
        self.assertEqual(call_kwargs["width"], "10.5cm")
        self.assertEqual(call_kwargs["height"], "15.3cm")
        self.assertTrue(call_kwargs["print_background"])
        self.assertEqual(
            call_kwargs["margin"],
            {"top": "0cm", "right": "0cm", "bottom": "0cm", "left": "0cm"},
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
