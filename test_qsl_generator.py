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

    @patch("sys.argv", ["qsl_generator.py", "pippo.txt"])
    def test_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            qslgen.main()


class QSLGeneratorArgsTest(unittest.TestCase):
    @patch("qsl_generator.adif.qso_list_from_file")
    @patch("qsl_generator.generate_qsl_image_pdf")
    @patch(
        "sys.argv",
        [
            "qsl_generator.py",
            "samples/test_log.adi",
            "--pdf",
            "--wkhtml-pdf-args",
            "--disable-smart-shrinking --lowquality",
        ],
    )
    def test_main_passes_pdf_custom_args(self, mock_generate, mock_parse):
        mock_parse.return_value = []
        qslgen.main()
        _, kwargs = mock_generate.call_args
        self.assertEqual(
            kwargs["_wkhtml_pdf_args"], "--disable-smart-shrinking --lowquality"
        )

    @patch("qsl_generator.adif.qso_list_from_file")
    @patch("qsl_generator.generate_qsl_image_pdf")
    @patch(
        "sys.argv",
        [
            "qsl_generator.py",
            "samples/test_log.adi",
            "--image",
            "--wkhtml-image-args",
            "--disable-smart-shrinking --enable-javascript",
        ],
    )
    def test_main_passes_image_custom_args(self, mock_generate, mock_parse):
        mock_parse.return_value = []
        qslgen.main()
        _, kwargs = mock_generate.call_args
        self.assertEqual(
            kwargs["_wkhtml_image_args"],
            "--disable-smart-shrinking --enable-javascript",
        )


class QSLGeneratorValidationTest(unittest.TestCase):
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
    @patch("sys.argv", ["qsl_generator.py", "samples/test_log.adi", "--dpi", "0"])
    def test_invalid_dpi_raises(self, mock_parse):
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


class QSLGeneratorCommandTest(unittest.TestCase):
    @patch("qsl_generator.wkhtmltoimage")
    def test_image_command_includes_custom_args(self, mock_wkhtmltoimage):
        mock_wkhtmltoimage.return_value = type("Result", (), {"returncode": 0})()

        qso_list = adif.qso_list_from_file("samples/test_log.adi")
        qslgen.generate_qsl_image_pdf(
            qso_list,
            _image=True,
            _pdf=False,
            _format="jpg",
            _wkhtml_image_args="--disable-smart-shrinking --enable-javascript",
            _out_filename="out",
            _out_folder="./tmp_out",
        )

        cmd = mock_wkhtmltoimage.call_args[0][0]
        self.assertIn("--disable-smart-shrinking", cmd)
        self.assertIn("--enable-javascript", cmd)
        self.assertIn(os.path.join(qslgen.TEMP_FOLDER, "template_out.html"), cmd)

    @patch("qsl_generator.wkhtmltopdf")
    def test_pdf_command_includes_custom_args(self, mock_wkhtmltopdf):
        mock_wkhtmltopdf.return_value = type("Result", (), {"returncode": 0})()

        qso_list = adif.qso_list_from_file("samples/test_log.adi")

        qslgen.generate_qsl_image_pdf(
            qso_list,
            _image=False,
            _pdf=True,
            _wkhtml_pdf_args="--lowquality --disable-smart-shrinking",
            _out_filename="out.pdf",
            _out_folder="./tmp_out",
        )

        cmd = mock_wkhtmltopdf.call_args[0][0]
        self.assertIn("--lowquality", cmd)
        self.assertIn("--disable-smart-shrinking", cmd)


class QSLGeneratorOutputNameTest(unittest.TestCase):
    @patch("qsl_generator.adif.qso_list_from_file")
    @patch("qsl_generator.generate_qsl_image_pdf")
    @patch("sys.argv", ["qsl_generator.py", "samples/test_log.adi", "custom_name"])
    def test_main_uses_output_filename_argument(self, mock_generate, mock_parse):
        mock_parse.return_value = []
        qslgen.main()
        _, kwargs = mock_generate.call_args
        self.assertEqual(kwargs["_out_filename"], "custom_name")


class ImageFormatTest(unittest.TestCase):
    @patch("qsl_generator.wkhtmltoimage")
    def test_image_format_is_applied_to_output_name(self, mock_wkhtmltoimage):
        mock_wkhtmltoimage.return_value = type("Result", (), {"returncode": 0})()

        qslgen.generate_qsl_image_pdf(
            qso_list=adif.qso_list_from_file("samples/test_log.adi"),
            _image=True,
            _pdf=False,
            _format="png",
            _out_filename="out",
            _out_folder="./tmp_out",
        )

        output_path = mock_wkhtmltoimage.call_args[0][0][-1]
        self.assertTrue(output_path.endswith(".png"))


class QSLGeneratorWarningTest(unittest.TestCase):
    @patch("qsl_generator.wkhtmltoimage")
    @patch("qsl_generator.logging.warning")
    def test_nonzero_image_return_logs_warning(self, mock_warning, mock_wkhtmltoimage):
        mock_wkhtmltoimage.return_value = type("Result", (), {"returncode": 1})()

        qslgen.generate_qsl_image_pdf(
            qso_list=adif.qso_list_from_file("samples/test_log.adi"),
            _image=True,
            _pdf=False,
            _out_filename="out",
            _out_folder="./tmp_out",
        )

        mock_warning.assert_called()

if __name__ == "__main__":
    unittest.main()