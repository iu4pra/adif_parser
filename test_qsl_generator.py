#!/usr/bin/python3

# This software under the MIT License
# Unit test for the qsl_generator module

import adif
import logging
import os
import qsl_generator as qslgen
import unittest
from unittest.mock import patch


class QSLGeneratorBasicTest(unittest.TestCase):

    def test_cm_to_px_basic(self):
        """Test basic cm to pixels conversion"""
        # 2.54 cm = 96 px (at default DPI)
        result = qslgen.cm_to_px(2.54, 96)
        self.assertEqual(result, 96)

    def test_cm_to_px_zero(self):
        """Test conversion with zero input"""
        result = qslgen.cm_to_px(0, 96)
        self.assertEqual(result, 0)

    def test_cm_to_px_float_values(self):
        """Test conversion with various float values"""
        # 1 cm
        result = qslgen.cm_to_px(1.0, 96)
        self.assertEqual(result, int(1.0 * 96 / 2.54))

        # 10 cm
        result = qslgen.cm_to_px(10.0, 96)
        self.assertEqual(result, int(10.0 * 96 / 2.54))

    def test_cm_to_px_negative(self):
        """Test conversion with negative values (should work mathematically)"""
        result = qslgen.cm_to_px(-2.54, 96)
        self.assertEqual(result, -96)

    @patch("sys.argv", ["qsl_generator.py", ""])
    def test_no_args(self):
        with self.assertRaises(Exception):
            qslgen.main()

    @patch("sys.argv", ["qsl_generator.py", "samples/pippo.adi"])
    def test_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            qslgen.main()


class QSLGeneratorValidationTest(unittest.TestCase):

    @patch("qsl_generator.adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qsl_generator.py", "samples/test_log.adi", "--width", "-1"],
    )
    def test_invalid_width_raises(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen.main()

    @patch("qsl_generator.adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qsl_generator.py", "samples/test_log.adi", "--width", "0"],
    )
    def test_invalid_width_raises(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen.main()

    @patch("qsl_generator.adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qsl_generator.py", "samples/test_log.adi", "--width", "99999"],
    )
    def test_width_over_max_raises(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen.main()

    @patch("qsl_generator.adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qsl_generator.py", "samples/test_log.adi", "--height", "-1"],
    )
    def test_invalid_height_raises(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen.main()

    @patch("qsl_generator.adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qsl_generator.py", "samples/test_log.adi", "--height", "0"],
    )
    def test_invalid_height_raises(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen.main()

    @patch("qsl_generator.adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qsl_generator.py", "samples/test_log.adi", "--height", "9999"],
    )
    def test_invalid_height_raises(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen.main()


class QSLGeneratorOutputNameTest(unittest.TestCase):
    @patch("qsl_generator.adif.qso_list_from_file")
    @patch("qsl_generator.generate_qsl_image_pdf")
    @patch("sys.argv", ["qsl_generator.py", "samples/test_log.adi", "custom_name"])
    def test_main_uses_output_filename_argument(self, mock_generate, mock_parse):
        mock_parse.return_value = []
        qslgen.main()
        _, kwargs = mock_generate.call_args
        self.assertEqual(kwargs["_out_filename"], "custom_name")


if __name__ == "__main__":
    unittest.main()
