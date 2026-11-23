#!/usr/bin/python3

# This software under the MIT License
# Unit test for the qslgen_cli module

import logging
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


SAMPLE_LOG = "samples/minimal_1qso.adi"


def parse_args(*options):
    """Parse the given options with the real CLI parser"""
    return qslgen_cli.build_parser().parse_args([SAMPLE_LOG, *options])


class BuildParserTest(unittest.TestCase):
    def test_defaults(self):
        args = parse_args()
        self.assertEqual(args.filename, SAMPLE_LOG)
        self.assertEqual(args.outfile, qslgen.PDF_OUTPUT)
        self.assertEqual(args.template, qslgen.TEMPLATE_DEFAULT_FILE)
        self.assertEqual(args.output_dir, qslgen.OUT_FOLDER)
        self.assertEqual(args.image_format, qslgen.IMG_OUT_EXTENSION)
        self.assertEqual(args.width, qslgen.QSL_WIDTH)
        self.assertEqual(args.height, qslgen.QSL_HEIGHT)
        self.assertEqual(args.max_qso, 3)
        for flag in ("pdf", "image", "quiet", "verbose", "dry_run", "only_valid"):
            self.assertFalse(getattr(args, flag), flag)

    def test_all_options(self):
        args = qslgen_cli.build_parser().parse_args(
            [
                SAMPLE_LOG,
                "custom_name",
                "--pdf",
                "--image",
                "--template",
                "my_card.html",
                "--output-dir",
                "out",
                "--image-format",
                "png",
                "--width",
                "10.5",
                "--height",
                "7",
                "--quiet",
                "--verbose",
                "--dry-run",
                "--only-valid",
                "--max-qso",
                "5",
            ]
        )
        self.assertEqual(args.outfile, "custom_name")
        self.assertTrue(args.pdf)
        self.assertTrue(args.image)
        self.assertEqual(args.template, "my_card.html")
        self.assertEqual(args.output_dir, "out")
        self.assertEqual(args.image_format, "png")
        self.assertEqual(args.width, 10.5)
        self.assertEqual(args.height, 7.0)
        self.assertTrue(args.quiet)
        self.assertTrue(args.verbose)
        self.assertTrue(args.dry_run)
        self.assertTrue(args.only_valid)
        self.assertEqual(args.max_qso, 5)

    def test_missing_input_file_exits(self):
        with self.assertRaises(SystemExit):
            qslgen_cli.build_parser().parse_args([])

    def test_non_numeric_width_exits(self):
        with self.assertRaises(SystemExit):
            qslgen_cli.build_parser().parse_args([SAMPLE_LOG, "--width", "wide"])


class CheckCardSizeTest(unittest.TestCase):
    def test_valid_values_return_none(self):
        self.assertIsNone(qslgen_cli.check_card_size("--width", 14, 700))
        self.assertIsNone(qslgen_cli.check_card_size("--width", 700, 700))
        self.assertIsNone(qslgen_cli.check_card_size("--width", 0.1, 700))

    def test_zero_is_rejected_with_option_name(self):
        with self.assertRaisesRegex(ValueError, "--width must be positive"):
            qslgen_cli.check_card_size("--width", 0, 700)

    def test_negative_is_rejected_with_option_name(self):
        with self.assertRaisesRegex(ValueError, "--height must be positive"):
            qslgen_cli.check_card_size("--height", -3, 180)

    def test_over_maximum_is_rejected_with_option_name(self):
        with self.assertRaisesRegex(ValueError, "--height must be <= 180"):
            qslgen_cli.check_card_size("--height", 180.1, 180)


class ValidateArgsTest(unittest.TestCase):
    def test_returns_none_for_valid_args(self):
        self.assertIsNone(qslgen_cli.validate_args(parse_args()))

    def test_no_output_option_falls_back_to_pdf(self):
        args = parse_args()
        qslgen_cli.validate_args(args)
        self.assertTrue(args.pdf)
        self.assertFalse(args.image)

    def test_image_only_does_not_enable_pdf(self):
        args = parse_args("--image")
        qslgen_cli.validate_args(args)
        self.assertTrue(args.image)
        self.assertFalse(args.pdf)

    def test_pdf_and_image_are_both_kept(self):
        args = parse_args("--pdf", "--image")
        qslgen_cli.validate_args(args)
        self.assertTrue(args.pdf)
        self.assertTrue(args.image)

    def test_quiet_and_verbose_are_exclusive(self):
        with self.assertRaisesRegex(ValueError, "--quiet and --verbose"):
            qslgen_cli.validate_args(parse_args("--quiet", "--verbose"))

    def test_missing_file_raises(self):
        args = qslgen_cli.build_parser().parse_args(["samples/does_not_exist.adi"])
        with self.assertRaises(FileNotFoundError):
            qslgen_cli.validate_args(args)

    def test_invalid_sizes_raise_with_option_name(self):
        for option, value, message in (
            ("--width", "0", "--width must be positive"),
            ("--width", str(qslgen.QSL_WIDTH_MAX + 1), "--width must be <="),
            ("--height", "-1", "--height must be positive"),
            ("--height", str(qslgen.QSL_HEIGHT_MAX + 1), "--height must be <="),
        ):
            with (
                self.subTest(option=option, value=value),
                self.assertRaisesRegex(ValueError, message),
            ):
                qslgen_cli.validate_args(parse_args(option, value))

    def test_boundary_sizes_are_accepted(self):
        args = parse_args(
            "--width",
            str(qslgen.QSL_WIDTH_MAX),
            "--height",
            str(qslgen.QSL_HEIGHT_MAX),
        )
        self.assertIsNone(qslgen_cli.validate_args(args))

    def test_max_qso_must_be_positive(self):
        for value in ("0", "-2"):
            with (
                self.subTest(value=value),
                self.assertRaisesRegex(ValueError, "--max-qso must be positive"),
            ):
                qslgen_cli.validate_args(parse_args("--max-qso", value))

    def test_does_not_configure_logging(self):
        root = logging.getLogger()
        handlers, level = root.handlers[:], root.level
        qslgen_cli.validate_args(parse_args("--quiet"))
        self.assertEqual(root.handlers, handlers)
        self.assertEqual(root.level, level)


class SetupLoggingTest(unittest.TestCase):
    def setUp(self):
        root = logging.getLogger()
        saved_handlers, saved_level = root.handlers[:], root.level

        def restore():
            for handler in root.handlers[:]:
                root.removeHandler(handler)
            for handler in saved_handlers:
                root.addHandler(handler)
            root.setLevel(saved_level)

        self.addCleanup(restore)

    def test_sets_level_and_single_console_handler(self):
        qslgen_cli.setup_logging(logging.DEBUG)
        root = logging.getLogger()
        self.assertEqual(root.level, logging.DEBUG)
        self.assertEqual(len(root.handlers), 1)
        self.assertIsInstance(root.handlers[0], logging.StreamHandler)

    def test_default_level_is_info(self):
        qslgen_cli.setup_logging()
        self.assertEqual(logging.getLogger().level, logging.INFO)

    def test_replaces_existing_handlers(self):
        root = logging.getLogger()
        root.addHandler(logging.NullHandler())
        root.addHandler(logging.NullHandler())
        qslgen_cli.setup_logging(logging.WARNING)
        self.assertEqual(len(root.handlers), 1)
        self.assertNotIsInstance(root.handlers[0], logging.NullHandler)

    def test_formatter_includes_timestamp_name_and_level(self):
        qslgen_cli.setup_logging(logging.INFO)
        fmt = logging.getLogger().handlers[0].formatter._fmt
        self.assertEqual(fmt, "%(asctime)s %(name)s %(levelname)s: %(message)s")


class MainBehaviorTest(unittest.TestCase):
    def run_main(self, *options, **patches):
        """Run main() with the generator mocked; return the generator mock"""
        with (
            patch("sys.argv", ["qslgen_cli.py", SAMPLE_LOG, *options]),
            patch("qslgen_cli.setup_logging") as mock_logging,
            patch("qsl_generator.generate_qsl_image_pdf") as mock_generate,
            patch("qslgen_cli.tqdm"),
        ):
            qslgen_cli.main()
        return mock_generate, mock_logging

    def test_logging_level_selection(self):
        for options, level in (
            ((), logging.INFO),
            ((("--quiet",)), logging.CRITICAL),
            ((("--verbose",)), logging.DEBUG),
        ):
            with self.subTest(options=options):
                _, mock_logging = self.run_main(*options)
                mock_logging.assert_called_once_with(level)

    def test_options_are_forwarded_to_generator(self):
        mock_generate, _ = self.run_main(
            "custom_name",
            "--image",
            "--template",
            "my_card.html",
            "--output-dir",
            "out",
            "--image-format",
            "png",
            "--width",
            "10",
            "--height",
            "6",
            "--dry-run",
            "--max-qso",
            "2",
        )
        kwargs = mock_generate.call_args.kwargs
        self.assertEqual(kwargs["_out_filename"], "custom_name")
        self.assertEqual(kwargs["_template"], "my_card.html")
        self.assertEqual(kwargs["_out_folder"], "out")
        self.assertEqual(kwargs["_format"], "png")
        self.assertEqual(kwargs["_width"], 10)
        self.assertEqual(kwargs["_height"], 6)
        self.assertTrue(kwargs["_dry_run"])
        self.assertEqual(kwargs["_max_qso"], 2)

    def test_only_valid_is_forwarded_to_parser(self):
        for options, expected in (((), False), ((("--only-valid",)), True)):
            with self.subTest(options=options):
                with (
                    patch("sys.argv", ["qslgen_cli.py", SAMPLE_LOG, *options]),
                    patch("qslgen_cli.setup_logging"),
                    patch("qslgen_cli.tqdm"),
                    patch("qsl_generator.generate_qsl_image_pdf"),
                    patch("adif.qso_list_from_file", return_value=[]) as mock_parse,
                ):
                    qslgen_cli.main()
                mock_parse.assert_called_once_with(str(Path(SAMPLE_LOG)), expected)

    def test_validation_runs_before_parsing(self):
        with (
            patch(
                "sys.argv",
                ["qslgen_cli.py", SAMPLE_LOG, "--width", "0"],
            ),
            patch("adif.qso_list_from_file") as mock_parse,
            self.assertRaises(ValueError),
        ):
            qslgen_cli.main()
        mock_parse.assert_not_called()

    def test_extension_check_is_case_insensitive(self):
        with (
            patch("sys.argv", ["qslgen_cli.py", "samples/UPPER.ADIF"]),
            patch("pathlib.Path.is_file", return_value=True),
            patch("qslgen_cli.setup_logging"),
            patch("qslgen_cli.tqdm"),
            patch("adif.qso_list_from_file", return_value=[]) as mock_parse,
            patch("qsl_generator.generate_qsl_image_pdf"),
        ):
            qslgen_cli.main()
        mock_parse.assert_called_once()

    def test_unknown_progress_stage_uses_stage_name(self):
        progress_bar = MagicMock()

        def generate(_qso_list, **kwargs):
            kwargs["progress_queue"].put(qslgen.ProgressUpdate("custom_stage", 2, 4))

        with (
            patch("sys.argv", ["qslgen_cli.py", SAMPLE_LOG]),
            patch("qslgen_cli.setup_logging"),
            patch("qsl_generator.generate_qsl_image_pdf", side_effect=generate),
            patch("qslgen_cli.tqdm", return_value=progress_bar),
        ):
            qslgen_cli.main()
        progress_bar.reset.assert_called_once_with(total=4)
        progress_bar.set_description.assert_called_once_with("custom_stage")
        self.assertEqual(progress_bar.n, 2)

    def test_same_stage_does_not_reset_progress_bar(self):
        progress_bar = MagicMock()

        def generate(_qso_list, **kwargs):
            for done in (0, 1, 2):
                kwargs["progress_queue"].put(
                    qslgen.ProgressUpdate("assembling_pdf", done, 2)
                )

        with (
            patch("sys.argv", ["qslgen_cli.py", SAMPLE_LOG]),
            patch("qslgen_cli.setup_logging"),
            patch("qsl_generator.generate_qsl_image_pdf", side_effect=generate),
            patch("qslgen_cli.tqdm", return_value=progress_bar),
        ):
            qslgen_cli.main()
        progress_bar.reset.assert_called_once_with(total=2)
        progress_bar.set_description.assert_called_once_with("Assembling final PDF")
        self.assertEqual(progress_bar.refresh.call_count, 3)

    def test_worker_exception_is_propagated_and_bar_closed(self):
        progress_bar = MagicMock()
        with (
            patch("sys.argv", ["qslgen_cli.py", SAMPLE_LOG]),
            patch("qslgen_cli.setup_logging"),
            patch(
                "qsl_generator.generate_qsl_image_pdf",
                side_effect=RuntimeError("render failed"),
            ),
            patch("qslgen_cli.tqdm", return_value=progress_bar),
            self.assertRaisesRegex(RuntimeError, "render failed"),
        ):
            qslgen_cli.main()
        progress_bar.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
