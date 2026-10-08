#!/usr/bin/python3

# This software under the MIT License
# Unit test for the qsl_generator module

import adif
import logging
import os
import qsl_generator as qslgen
import unittest
import tempfile
import shutil
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

    @patch(
        "sys.argv",
        ["qsl_generator.py", "samples/minimal_1qso.adi", "--quiet", "--verbose"],
    )
    def test_quiet_verbose_together(self):
        with self.assertRaises(ValueError):
            qslgen.main()

    @patch("sys.argv", ["qsl_generator.py", "samples/pippo.adi"])
    def test_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            qslgen.main()

    @patch("os.path.isfile")
    @patch("qsl_generator.adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qsl_generator.py", "samples/test_log.txt"],
    )
    def test_invalid_file_extension(self, mock_parse, mock_isfile):
        mock_parse.return_value = []
        mock_isfile.return_value = True
        with self.assertRaises(ValueError):
            qslgen.main()

    @patch(
        "sys.argv",
        [
            "qsl_generator.py",
            "samples/minimal_1qso.adi",
            "--template",
            "invalid_template.html",
        ],
    )
    def test_nonexistent_template_file(self):
        self.assertTrue(os.path.exists("samples/minimal_1qso.adi"))
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
    def test_invalid_height_raises_1(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen.main()

    @patch("qsl_generator.adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qsl_generator.py", "samples/test_log.adi", "--height", "0"],
    )
    def test_invalid_height_raises_2(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen.main()

    @patch("qsl_generator.adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qsl_generator.py", "samples/test_log.adi", "--height", "9999"],
    )
    def test_height_over_max_raises(self, mock_parse):
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


class TestQSLFilterFormatDate(unittest.TestCase):
    """Test cases for qsl_filter_format_date function"""

    def test_valid_date_default_format(self):
        """Test formatting a valid date with default format"""
        result = qslgen.qsl_filter_format_date("20231225")
        self.assertEqual(result, "25/12/2023")

    def test_valid_date_custom_format(self):
        """Test formatting a valid date with custom format"""
        result = qslgen.qsl_filter_format_date("20231225", fmt="%Y-%m-%d")
        self.assertEqual(result, "2023-12-25")

    def test_valid_date_alternative_format(self):
        """Test formatting a valid date with alternative format"""
        result = qslgen.qsl_filter_format_date("20000101", fmt="%d-%m-%Y")
        self.assertEqual(result, "01-01-2000")

    def test_invalid_date_format(self):
        """Test with invalid date format - should return original value"""
        result = qslgen.qsl_filter_format_date("2023-12-25")
        self.assertEqual(result, "2023-12-25")

    def test_invalid_date_value(self):
        """Test with invalid date value - should return original value"""
        result = qslgen.qsl_filter_format_date("20231332")  # Month 13, day 32
        self.assertEqual(result, "20231332")

    def test_empty_string(self):
        """Test with empty string - should return original value"""
        result = qslgen.qsl_filter_format_date("")
        self.assertEqual(result, "")

    def test_none_value(self):
        """Test with None value - should return original value"""
        result = qslgen.qsl_filter_format_date(None)
        self.assertEqual(result, None)

    def test_partial_date_string(self):
        """Test with partial date string - should return original value"""
        result = qslgen.qsl_filter_format_date("20231")
        self.assertEqual(result, "20231")

    def test_leap_year_date(self):
        """Test formatting a leap year date"""
        result = qslgen.qsl_filter_format_date("20000229")
        self.assertEqual(result, "29/02/2000")

    def test_non_leap_year_date(self):
        """Test with invalid leap year date - should return original value"""
        result = qslgen.qsl_filter_format_date("20010229")  # 2001 is not a leap year
        self.assertEqual(result, "20010229")


class TestQSLFilterFormatTime(unittest.TestCase):
    """Test cases for qsl_filter_format_time function"""

    def test_valid_time_default_format(self):
        """Test formatting a valid time with default parameters"""
        result = qslgen.qsl_filter_format_time("1430")
        self.assertEqual(result, "14:30")

    def test_valid_time_with_seconds(self):
        """Test formatting a valid time with seconds"""
        result = qslgen.qsl_filter_format_time("143045", include_seconds=True)
        self.assertEqual(result, "14:30:45")

    def test_valid_time_custom_separator(self):
        """Test formatting a valid time with custom separator"""
        result = qslgen.qsl_filter_format_time("1430", separator="-")
        self.assertEqual(result, "14-30")

    def test_valid_time_with_seconds_custom_separator(self):
        """Test formatting a valid time with seconds and custom separator"""
        result = qslgen.qsl_filter_format_time(
            "143045", include_seconds=True, separator=" "
        )
        self.assertEqual(result, "14 30 45")

    def test_time_with_leading_zero(self):
        """Test formatting time with leading zeros"""
        result = qslgen.qsl_filter_format_time("0930")
        self.assertEqual(result, "09:30")

    def test_midnight_time(self):
        """Test formatting midnight time"""
        result = qslgen.qsl_filter_format_time("0000")
        self.assertEqual(result, "00:00")

    def test_end_of_day_time(self):
        """Test formatting end of day time"""
        result = qslgen.qsl_filter_format_time("2359")
        self.assertEqual(result, "23:59")

    def test_empty_string(self):
        """Test with empty string - should return original value"""
        result = qslgen.qsl_filter_format_time("")
        self.assertEqual(result, "")

    def test_none_value(self):
        """Test with None value - should return original value"""
        result = qslgen.qsl_filter_format_time(None)
        self.assertEqual(result, None)

    def test_too_short_string(self):
        """Test with string shorter than 4 characters - should return original value"""
        result = qslgen.qsl_filter_format_time("123")
        self.assertEqual(result, "123")

    def test_three_chars(self):
        """Test with exactly 3 characters - should return original value"""
        result = qslgen.qsl_filter_format_time("143")
        self.assertEqual(result, "143")

    def test_four_chars_exact(self):
        """Test with exactly 4 characters"""
        result = qslgen.qsl_filter_format_time("1430")
        self.assertEqual(result, "14:30")

    def test_six_chars_without_seconds_flag(self):
        """Test with 6 characters but include_seconds=False"""
        result = qslgen.qsl_filter_format_time("143045", include_seconds=False)
        self.assertEqual(result, "14:30")

    def test_six_chars_with_seconds(self):
        """Test with 6 characters and include_seconds=True"""
        result = qslgen.qsl_filter_format_time("143045", include_seconds=True)
        self.assertEqual(result, "14:30:45")

    def test_five_chars_with_seconds_flag(self):
        """Test with 5 characters and include_seconds=True - seconds not included"""
        result = qslgen.qsl_filter_format_time("14304", include_seconds=True)
        self.assertEqual(result, "14:30")

    def test_empty_separator(self):
        """Test with empty separator"""
        result = qslgen.qsl_filter_format_time("1430", separator="")
        self.assertEqual(result, "1430")

    def test_double_char_separator(self):
        """Test with double character separator"""
        result = qslgen.qsl_filter_format_time("1430", separator="::")
        self.assertEqual(result, "14::30")


class TestUnlinkIfExists(unittest.TestCase):
    """Test cases for unlink_if_exists function"""

    def setUp(self):
        """Create temporary directory for tests"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_delete_existing_file(self):
        """Test deleting an existing file"""
        # Create a test file
        test_file = os.path.join(self.test_dir, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        # Verify file exists
        self.assertTrue(os.path.exists(test_file))

        # Delete the file
        qslgen.unlink_if_exists(test_file)

        # Verify file is deleted
        self.assertFalse(os.path.exists(test_file))

    def test_delete_non_existing_file(self):
        """Test deleting a non-existing file - should not raise exception"""
        non_existing_file = os.path.join(self.test_dir, "non_existing.txt")

        # Should not raise an exception
        try:
            qslgen.unlink_if_exists(non_existing_file)
        except FileNotFoundError:
            self.fail("unlink_if_exists raised FileNotFoundError unexpectedly!")

    def test_delete_file_with_special_characters(self):
        """Test deleting a file with special characters in name"""
        test_file = os.path.join(self.test_dir, "test file (special).txt")
        with open(test_file, "w") as f:
            f.write("test content")

        self.assertTrue(os.path.exists(test_file))

        qslgen.unlink_if_exists(test_file)

        self.assertFalse(os.path.exists(test_file))

    def test_delete_file_with_long_path(self):
        """Test deleting a file with a long path"""
        # Create nested directories
        nested_dir = os.path.join(self.test_dir, "level1", "level2", "level3")
        os.makedirs(nested_dir, exist_ok=True)

        test_file = os.path.join(nested_dir, "deep_file.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        self.assertTrue(os.path.exists(test_file))

        qslgen.unlink_if_exists(test_file)

        self.assertFalse(os.path.exists(test_file))

    def test_unlink_empty_string_path(self):
        """Test unlink_if_exists with empty string path"""
        try:
            qslgen.unlink_if_exists("")
        except (FileNotFoundError, OSError):
            pass  # Both exceptions are acceptable


class TestRmtreeIfExists(unittest.TestCase):
    """Test cases for rmtree_if_exists function"""

    def setUp(self):
        """Create temporary directory for tests"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_delete_existing_directory(self):
        """Test deleting an existing directory"""
        # Create a test directory
        test_dir_path = os.path.join(self.test_dir, "test_dir")
        os.makedirs(test_dir_path)

        # Verify directory exists
        self.assertTrue(os.path.exists(test_dir_path))

        # Delete the directory
        qslgen.rmtree_if_exists(test_dir_path)

        # Verify directory is deleted
        self.assertFalse(os.path.exists(test_dir_path))

    def test_delete_directory_with_files(self):
        """Test deleting a directory containing files"""
        # Create a test directory with files
        test_dir_path = os.path.join(self.test_dir, "test_dir_with_files")
        os.makedirs(test_dir_path)

        # Add files to the directory
        for i in range(3):
            test_file = os.path.join(test_dir_path, f"file_{i}.txt")
            with open(test_file, "w") as f:
                f.write(f"content {i}")

        # Verify directory and files exist
        self.assertTrue(os.path.exists(test_dir_path))
        self.assertEqual(len(os.listdir(test_dir_path)), 3)

        # Delete the directory
        qslgen.rmtree_if_exists(test_dir_path)

        # Verify directory and files are deleted
        self.assertFalse(os.path.exists(test_dir_path))

    def test_delete_nested_directories(self):
        """Test deleting nested directories with files"""
        # Create nested directories
        test_dir_path = os.path.join(self.test_dir, "parent")
        os.makedirs(os.path.join(test_dir_path, "child1", "grandchild"), exist_ok=True)
        os.makedirs(os.path.join(test_dir_path, "child2"), exist_ok=True)

        # Add files at different levels
        with open(os.path.join(test_dir_path, "root_file.txt"), "w") as f:
            f.write("root")
        with open(os.path.join(test_dir_path, "child1", "child_file.txt"), "w") as f:
            f.write("child")
        with open(
            os.path.join(test_dir_path, "child1", "grandchild", "deep_file.txt"), "w"
        ) as f:
            f.write("deep")

        # Verify directory structure exists
        self.assertTrue(os.path.exists(test_dir_path))

        # Delete the directory
        qslgen.rmtree_if_exists(test_dir_path)

        # Verify directory and all contents are deleted
        self.assertFalse(os.path.exists(test_dir_path))

    def test_delete_non_existing_directory(self):
        """Test deleting a non-existing directory - should not raise exception"""
        non_existing_dir = os.path.join(self.test_dir, "non_existing_dir")

        # Should not raise an exception
        try:
            qslgen.rmtree_if_exists(non_existing_dir)
        except FileNotFoundError:
            self.fail("rmtree_if_exists raised FileNotFoundError unexpectedly!")

    def test_delete_directory_with_special_characters(self):
        """Test deleting a directory with special characters in name"""
        test_dir_path = os.path.join(self.test_dir, "dir (special) [test]")
        os.makedirs(test_dir_path)

        with open(os.path.join(test_dir_path, "file.txt"), "w") as f:
            f.write("test")

        self.assertTrue(os.path.exists(test_dir_path))

        qslgen.rmtree_if_exists(test_dir_path)

        self.assertFalse(os.path.exists(test_dir_path))

    def test_delete_empty_directory(self):
        """Test deleting an empty directory"""
        test_dir_path = os.path.join(self.test_dir, "empty_dir")
        os.makedirs(test_dir_path)

        self.assertTrue(os.path.exists(test_dir_path))

        qslgen.rmtree_if_exists(test_dir_path)

        self.assertFalse(os.path.exists(test_dir_path))

    def test_rmtree_empty_string_path(self):
        """Test rmtree_if_exists with empty string path"""
        try:
            qslgen.rmtree_if_exists("")
        except (FileNotFoundError, OSError):
            pass  # Both exceptions are acceptabl


if __name__ == "__main__":
    unittest.main()
