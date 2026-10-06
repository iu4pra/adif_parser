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

    @patch("sys.argv", ["qsl_generator.py", ""])
    def test_no_args(self):
        with self.assertRaises(Exception):
            qslgen.main()

    @patch("sys.argv", ["qsl_generator.py", "samples/pippo.adi"])
    def test_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            qslgen.main()

    @patch("sys.argv", ["qsl_generator.py", "samples/minimal_1qso.adi","--template","invalid_template.html"])
    def test_nonexistent_template_file(self):
        self.assertTrue(os.path.exists("samples/minimal_1qso.adi"))
        with self.assertRaises(FileNotFoundError):
             qslgen.main()

class QSLGeneratorValidationTest(unittest.TestCase):

    @patch("qsl_generator.generate_qsl_image_pdf")
    @patch("sys.argv", ["qsl_generator.py", "samples/minimal_1qso.adi"])
    def test_default_pdf_image_args(self, mock_generate):
        qslgen.main()
        _, kwargs = mock_generate.call_args
        self.assertTrue(kwargs["_pdf"])
        self.assertFalse(kwargs["_image"])

    @patch("qsl_generator.generate_qsl_image_pdf")
    @patch("sys.argv", ["qsl_generator.py", "samples/minimal_1qso.adi", "--image"])
    def test_custom_pdf_image_args_1(self, mock_generate):
        qslgen.main()
        _, kwargs = mock_generate.call_args
        self.assertTrue(kwargs["_image"])
        self.assertFalse(kwargs["_pdf"])

    @patch("qsl_generator.generate_qsl_image_pdf")
    @patch("sys.argv", ["qsl_generator.py", "samples/minimal_1qso.adi", "--pdf"])
    def test_custom_pdf_image_args_2(self, mock_generate):
        qslgen.main()
        _, kwargs = mock_generate.call_args
        self.assertTrue(kwargs["_pdf"])
        self.assertFalse(kwargs["_image"])

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
        ["qsl_generator.py", "samples/test_log.adi", "--height", "-1"],
    )
    def test_invalid_height_raises(self, mock_parse):
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
