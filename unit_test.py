#!/usr/bin/python3

# This software under the MIT License
# Unit test for the application

import adif
import logging
import os
import qsl_generator as qslgen
import unittest
import wkhtml
from qso import QSO
from unittest.mock import patch


class WkhtmlTest(unittest.TestCase):
    """Test cases for the wkhtml wrapper"""

    def test_check_exe_exists_image(self):
        with patch.object(
            wkhtml,
            "WKHTMLTOX_BASE_PATH",
            os.path.join(wkhtml.WKHTMLTOX_BASE_PATH, "path/that/doesnt/exist"),
        ):
            with self.assertRaises(AssertionError):
                wkhtml.wkhtmltoimage([])

    def test_check_exe_exists_pdf(self):
        with patch.object(
            wkhtml,
            "WKHTMLTOX_BASE_PATH",
            os.path.join(wkhtml.WKHTMLTOX_BASE_PATH, "path/that/doesnt/exist"),
        ):
            with self.assertRaises(AssertionError):
                wkhtml.wkhtmltopdf([])


class ParsingTest(unittest.TestCase):
    """Test cases for the ADIF parser"""

    def test_empty_string(self):
        """Empty strings return no fields"""
        self.assertEqual(adif.parse_adif_string(""), [])
        self.assertEqual(adif.parse_adif_string("\0"), [])
        self.assertEqual(adif.parse_adif_string("\0" * 3), [])

    def test_newline(self):
        """String with only newlines return no fields"""
        self.assertEqual(adif.parse_adif_string("\n"), [])
        self.assertEqual(adif.parse_adif_string("\n" * 3), [])

    def test_blank_string(self):
        """String with only whitespaces return no fields"""
        self.assertEqual(adif.parse_adif_string(" "), [])
        self.assertEqual(adif.parse_adif_string(" " * 5), [])

    def test_string_without_fields(self):
        """String with no valid fields"""
        _test_string = """QRZLogbook download for iu4pra
    Date: Mon Oct  6 11:30:36 2025
    Bookid: 312206
    Records: 200"""
        self.assertEqual(adif.parse_adif_string(_test_string), [])

    def test_single_field(self):
        """Parse a single, well formatted field"""
        self.assertEqual(
            adif.parse_adif_string("<CALL:6>IK4XYZ"),
            [{"field": "CALL", "len": 6, "type": None, "value": "IK4XYZ"}],
        )

    def test_single_field_with_blanks(self):
        """Parse a single, well formatted field with extra whitespaces"""
        self.assertEqual(
            adif.parse_adif_string("<CALL:6>IK4XYZ  "),
            [{"field": "CALL", "len": 6, "type": None, "value": "IK4XYZ"}],
        )

    def test_single_field_with_extra(self):
        """Parse a single, well formatted field with extra characters"""
        self.assertEqual(
            adif.parse_adif_string("<CALL:6>IK4XYZABC"),
            [{"field": "CALL", "len": 6, "type": None, "value": "IK4XYZ"}],
        )

    def test_single_field_with_type(self):
        """Parse a single, well formatted field with type identifier"""
        self.assertEqual(
            adif.parse_adif_string("<CALL:6:s>IK4XYZ"),
            [{"field": "CALL", "len": 6, "type": "s", "value": "IK4XYZ"}],
        )

    def test_single_field_wrong_type(self):
        self.assertEqual(adif.parse_adif_string("<:6>IK4XYZ"), [])

    def test_single_field_no_len(self):
        """Parse a single, well formatted field without length"""
        self.assertEqual(
            adif.parse_adif_string("<EOR>"),
            [{"field": "EOR", "len": 0, "type": None, "value": None}],
        )

    def test_single_field_wrong_len(self):
        """Parse a single field with a wrong length"""
        for i in range(-5, 1):
            with self.assertRaises(adif.AdifError):
                adif.parse_adif_string(f"<CALL:{i}>IK4XYZ")

    def test_single_field_invalid_len(self):
        """Parse a single field with a non-numeric length"""
        self.assertEqual(adif.parse_adif_string("<CALL:d>IK4XYZ"), [])

    def test_single_field_too_short(self):
        """Single field with insufficient data to fill the value field"""
        with self.assertRaises(adif.AdifError):
            adif.parse_adif_string("<CALL:6>IK4")
        with self.assertRaises(adif.AdifError):
            adif.parse_adif_string("<CALL:6:s>IK4")


class QSOTest(unittest.TestCase):
    """Test cases for the QSO class"""

    def test_blank_qso_not_valid(self):
        """A blank QSO must not be valid"""
        self.assertFalse(QSO({}).is_valid())

    def test_qso_essential_fields(self):
        """A QSO must contain all essential fields"""
        _adif_string = adif.parse_adif_string(
            "<QSO_DATE:8>20251005 <TIME_ON:6>123000 <CALL:6>IW9YZA <BAND:3>12m <MODE:3>FT8 <RST_SENT:2>-- <RST_RCVD:2>-- <EOR>"
        )
        _qso_list = adif.adif_to_qso_list(_adif_string)
        self.assertEqual(len(_qso_list), 1)
        self.assertTrue(_qso_list[0].is_valid())


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
