#!/usr/bin/python3

# This software under the MIT License
# Command line interface for QSL generator written in Tkinter

import argparse

import adif
import os.path
from qsl_generator import *

def setup_logging(level=logging.INFO):
    """
    Logging configuration for all app modules
    """
    # Detailed format with timestamp
    log_format = "%(asctime)s %(name)s %(levelname)s: %(message)s"

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Root logger configuration (every module will inherit)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

# Main module function
# TODO (power-of-10): split into smaller functions + separate logic
def main():  # noqa: C901, PLR0912, PLR0915
    # Define parser and its arguments
    parser = argparse.ArgumentParser(
        description="Generate a .pdf file from a QSO list in .adi format"
    )

    parser.add_argument(
        "filename",
        metavar="input_file",
        type=str,
        help="Log file to process (ADIF format)",
    )

    parser.add_argument(
        "outfile",
        metavar="output_file",
        nargs="?",
        type=str,
        default=PDF_OUTPUT,
        help="Output file name (base name for images)",
    )

    parser.add_argument("--pdf", action="store_true", help="Output as multi-page PDF")

    parser.add_argument(
        "--image", default=False, action="store_true", help="Output as images"
    )

    parser.add_argument(
        "--template",
        metavar="template_file",
        type=str,
        default=TEMPLATE_DEFAULT_FILE,
        help=f"Template to use from {TEMPLATE_FOLDER} folder (default {TEMPLATE_DEFAULT_FILE})",
    )

    parser.add_argument(
        "--output-dir",
        metavar="output_folder",
        type=str,
        default=OUT_FOLDER,
        help=f"Output folder (default {OUT_FOLDER})",
    )

    parser.add_argument(
        "--image-format",
        metavar="image_format",
        type=str,
        default=IMG_OUT_EXTENSION,
        help=f"Output image format (default {IMG_OUT_EXTENSION})",
    )

    parser.add_argument(
        "--width",
        metavar="width",
        type=float,
        default=QSL_WIDTH,
        help=f"QSL width in centimeters (default {QSL_WIDTH})",
    )

    parser.add_argument(
        "--height",
        metavar="height",
        type=float,
        default=QSL_HEIGHT,
        help=f"QSL height in centimeters (default {QSL_HEIGHT})",
    )

    parser.add_argument(
        "--quiet", default=False, action="store_true", help="Suppress output"
    )

    parser.add_argument(
        "--verbose", default=False, action="store_true", help="More debug info"
    )

    parser.add_argument(
        "--dry-run",
        default=False,
        action="store_true",
        help="Do not create/alter/remove files",
    )

    parser.add_argument(
        "--only-valid",
        default=False,
        action="store_true",
        help="Process only valid QSOs",
    )

    parser.add_argument(
        "--max-qso",
        metavar="max_qso",
        type=int,
        default=3,
        help="Maximum QSOs per multiple QSL card (default 3, 1 to disable multi-QSO cards)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Logger must be set up BEFORE any call!
    if args.quiet and args.verbose:
        raise ValueError("Cannot use --quiet and --verbose together")

    if args.quiet:
        setup_logging(logging.CRITICAL)
    elif args.verbose:
        setup_logging(logging.DEBUG)
    else:
        setup_logging(logging.INFO)

    # Filename to be processed
    filename = os.path.relpath(args.filename)

    # Arguments check
    if not Path(filename).is_file():
        raise FileNotFoundError(f"File {filename} doesn't exist")

    # If no output is specified fallback to PDF
    if not args.image and not args.pdf:
        args.pdf = True

    # If only --image is specified do not generate PDF
    if args.image and not args.pdf:
        args.pdf = False

    if not args.pdf and args.pdf is not None and not args.image:
        raise ValueError("At least one output option must be specified")

    # File extension
    ext = filename.split(".")[-1]

    if ext.casefold() in ["adi", "adif"]:
        logger.info(
            f"Proceeding to parse ADIF file {args.filename}, only valid QSO: {args.only_valid}"
        )
        qso_list = adif.qso_list_from_file(filename, args.only_valid)

    else:
        raise ValueError("Unrecognized file extension")

    # Optional parameters validation
    if args.width <= 0:
        raise ValueError("--width must be positive")
    if args.width > QSL_WIDTH_MAX:
        raise ValueError(f"--width must be <= {QSL_WIDTH_MAX}")

    if args.height <= 0:
        raise ValueError("--height must be positive")
    if args.height > QSL_HEIGHT_MAX:
        raise ValueError(f"--height must be <= {QSL_HEIGHT_MAX}")

    if args.max_qso <= 0:
        raise ValueError("--max-qso must be positive (1 to disable multi-QSO cards)")

    # All OK, generate QSLs
    with ThreadPoolExecutor() as executor:
        progress_queue = Queue()  # To display progress

        future = executor.submit(
            generate_qsl_image_pdf,
            qso_list,
            _image=args.image,
            _pdf=args.pdf,
            _template=args.template,
            _out_filename=args.outfile,
            _out_folder=args.output_dir,
            _format=args.image_format,
            _width=args.width,
            _height=args.height,
            _dry_run=args.dry_run,
            _max_qso=args.max_qso,
            progress_queue=progress_queue,
        )

        # Display progress bar in the main thread
        progress_bar = tqdm(desc="Preparing QSLs", unit="QSL")
        # Current progress bar stage to track when to reset the bar and change its description
        current_stage = None
        stage_descriptions = {
            "rendering": "Rendering single QSLs",
            "assembling_pdf": "Assembling final PDF",
            "done": "QSL generation complete",
        }
        while True:
            try:
                progress_update = progress_queue.get(timeout=0.1)
            except Empty:
                if future.done():
                    break
                continue

            if progress_update.stage != current_stage:
                progress_bar.reset(total=progress_update.total)
                progress_bar.set_description(
                    stage_descriptions.get(progress_update.stage, progress_update.stage)
                )
                current_stage = progress_update.stage
            progress_bar.n = progress_update.completed
            progress_bar.refresh()

        try:
            future.result()  # Forward exceptions from the worker to the main thread
        finally:
            progress_bar.close()

if __name__ == "__main__":
    main()