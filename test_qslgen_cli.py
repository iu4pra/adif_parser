#!/usr/bin/python3

# This software under the MIT License
# Unit test for the qslgen_cli module

import unittest
from pathlib import Path
from queue import Queue
from unittest.mock import MagicMock, call, patch

import pytest

import adif
import qsl_generator as qslgen
import qslgen_cli


class QSLGenCLITest(unittest.TestCase):
    def test_main_displays_progress_updates(self):
        progress_bar = MagicMock()

        def generate_with_progress(_qso_list, **kwargs):
            progress_queue = kwargs["progress_queue"]
            progress_queue.put(qslgen.ProgressUpdate("rendering", 0, 1))
            progress_queue.put(qslgen.ProgressUpdate("rendering", 1, 1))
            progress_queue.put(qslgen.ProgressUpdate("done", 1, 1))

        with (
            patch(
                "sys.argv",
                ["qslgen_cli.py", "samples/minimal_1qso.adi"],
            ),
            patch(
                "qsl_generator.generate_qsl_image_pdf",
                side_effect=generate_with_progress,
            ) as mock_generate,
            patch("qslgen_cli.tqdm", return_value=progress_bar) as mock_tqdm,
        ):
            qslgen_cli.main()

        mock_tqdm.assert_called_once_with(desc="Preparing QSLs", unit="QSL")
        self.assertEqual(
            progress_bar.reset.call_args_list,
            [call(total=1), call(total=1)],
        )
        self.assertEqual(
            progress_bar.set_description.call_args_list,
            [
                call("Rendering single QSLs"),
                call("QSL generation complete"),
            ],
        )
        self.assertEqual(progress_bar.refresh.call_count, 3)
        progress_bar.close.assert_called_once()
        self.assertIsInstance(mock_generate.call_args.kwargs["progress_queue"], Queue)

    @patch("sys.argv", ["qslgen_cli.py", ""])
    def test_no_args(self):
        with self.assertRaises(ValueError):
            qslgen_cli.main()

    @patch(
        "sys.argv",
        ["qslgen_cli.py", "samples/minimal_1qso.adi", "--quiet", "--verbose"],
    )
    def test_quiet_verbose_together(self):
        with self.assertRaises(ValueError):
            qslgen_cli.main()

    @patch("sys.argv", ["qslgen_cli.py", "samples/pippo.adi"])
    def test_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            qslgen_cli.main()

    @patch("pathlib.Path.is_file")
    @patch("adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qslgen_cli.py", "samples/test_log.txt"],
    )
    def test_invalid_file_extension(self, mock_parse, mock_isfile):
        mock_parse.return_value = []
        mock_isfile.return_value = True
        with self.assertRaises(ValueError):
            qslgen_cli.main()

    @patch(
        "sys.argv",
        [
            "qslgen_cli.py",
            "samples/minimal_1qso.adi",
            "--template",
            "invalid_template.html",
        ],
    )
    def test_nonexistent_template_file(self):
        self.assertTrue(Path("samples/minimal_1qso.adi").exists())
        with self.assertRaises(FileNotFoundError):
            qslgen_cli.main()


class QSLGenCLIValidationTest(unittest.TestCase):
    @patch("adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qslgen_cli.py", "samples/test_log.adi", "--width", "-1"],
    )
    def test_invalid_width_negative_raises(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen_cli.main()

    @patch("qsl_generator.generate_qsl_image_pdf")
    @patch("sys.argv", ["qslgen_cli.py", "samples/minimal_1qso.adi"])
    def test_default_pdf_image_args(self, mock_generate):
        qslgen_cli.main()
        _, kwargs = mock_generate.call_args
        self.assertTrue(kwargs["_pdf"])
        self.assertFalse(kwargs["_image"])

    @patch("qsl_generator.generate_qsl_image_pdf")
    @patch("sys.argv", ["qslgen_cli.py", "samples/minimal_1qso.adi", "--image"])
    def test_custom_pdf_image_args_1(self, mock_generate):
        qslgen_cli.main()
        _, kwargs = mock_generate.call_args
        self.assertTrue(kwargs["_image"])
        self.assertFalse(kwargs["_pdf"])

    @patch("qsl_generator.generate_qsl_image_pdf")
    @patch("sys.argv", ["qslgen_cli.py", "samples/minimal_1qso.adi", "--pdf"])
    def test_custom_pdf_image_args_2(self, mock_generate):
        qslgen_cli.main()
        _, kwargs = mock_generate.call_args
        self.assertTrue(kwargs["_pdf"])
        self.assertFalse(kwargs["_image"])

    @patch("adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qslgen_cli.py", "samples/test_log.adi", "--width", "0"],
    )
    def test_invalid_width_zero_raises(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen_cli.main()

    @patch("adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qslgen_cli.py", "samples/test_log.adi", "--width", "99999"],
    )
    def test_width_over_max_raises(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen_cli.main()

    @patch("adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qslgen_cli.py", "samples/test_log.adi", "--height", "-1"],
    )
    def test_invalid_height_raises_1(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen_cli.main()

    @patch("adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qslgen_cli.py", "samples/test_log.adi", "--height", "0"],
    )
    def test_invalid_height_raises_2(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen_cli.main()

    @patch("adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qslgen_cli.py", "samples/test_log.adi", "--height", "9999"],
    )
    def test_height_over_max_raises(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen_cli.main()

    @patch("adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qslgen_cli.py", "samples/test_log.adi", "--max-qso", "-1"],
    )
    def test_max_qso_negative(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen_cli.main()

    @patch("adif.qso_list_from_file")
    @patch(
        "sys.argv",
        ["qslgen_cli.py", "samples/test_log.adi", "--max-qso", "0"],
    )
    def test_max_qso_zero(self, mock_parse):
        mock_parse.return_value = []
        with self.assertRaises(ValueError):
            qslgen_cli.main()


class QSLGenCLIOutputNameTest(unittest.TestCase):
    @patch("adif.qso_list_from_file")
    @patch("qsl_generator.generate_qsl_image_pdf")
    @patch("sys.argv", ["qslgen_cli.py", "samples/test_log.adi", "custom_name"])
    def test_main_uses_output_filename_argument(self, mock_generate, mock_parse):
        mock_parse.return_value = []
        qslgen_cli.main()
        _, kwargs = mock_generate.call_args
        self.assertEqual(kwargs["_out_filename"], "custom_name")


@pytest.mark.parametrize(
    "argv,expected_pdf,expected_image",
    [
        (["qslgen_cli.py", "samples/minimal_1qso.adi"], True, False),
        (["qslgen_cli.py", "samples/minimal_1qso.adi", "--image"], False, True),
        (["qslgen_cli.py", "samples/minimal_1qso.adi", "--pdf"], True, False),
    ],
)
def test_output_selection(
    argv,
    expected_pdf,
    expected_image,
):
    qso_list = ["dummy_qso"]

    with (
        patch("sys.argv", argv),
        patch("adif.qso_list_from_file", return_value=qso_list),
        patch("qsl_generator.generate_qsl_image_pdf") as mock_generate,
    ):
        qslgen_cli.main()

        mock_generate.assert_called_once()

        args, kwargs = mock_generate.call_args

        assert args[0] == qso_list
        assert kwargs["_pdf"] is expected_pdf
        assert kwargs["_image"] is expected_image


@pytest.mark.parametrize(
    "options,expected_limit",
    [([], 3), (["--max-qso", "1"], 1), (["--max-qso", "5"], 5)],
)
def test_cli_grouping_limit(options, expected_limit):
    qsos = adif.qso_list_from_file("samples/multi_qso_same_station.adi")
    with (
        patch(
            "sys.argv",
            ["qslgen_cli.py", "samples/multi_qso_same_station.adi", *options],
        ),
        patch("qsl_generator.generate_qsl_image_pdf") as generate,
    ):
        qslgen_cli.main()
    limit = generate.call_args.kwargs["_max_qso"]
    groups = list(qslgen.qso_list_generator(qsos, limit))
    assert limit == expected_limit
    assert sum(map(len, groups)) == len(qsos)
    assert max(map(len, groups)) <= expected_limit
    if expected_limit == 1:
        assert all(len(group) == 1 for group in groups)


if __name__ == "__main__":
    unittest.main()
