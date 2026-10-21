#!/usr/bin/python3

# This software under the MIT License
# QSL generator
# Generates a printable QSL starting from an HTML template with Jinja2

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from qso import QSO
from queue import Empty, Queue
from tqdm import tqdm
from typing import Optional
import adif
import argparse
import logging
import math
import os
import pickle
import playwright_wrapper
import pypdf
import shutil

# QSL standard size in centimeters
QSL_WIDTH = 14.0
QSL_HEIGHT = 9.0
# Maximum size
QSL_WIDTH_MAX = 700.0
QSL_HEIGHT_MAX = 180.0

# Default DPI
DPI = 150
# Maximum DPI
DPI_MAX = 1500

# Default template filename
TEMPLATE_DEFAULT_FILE = "template.html"
# Template folder
TEMPLATE_FOLDER = "./templates"

# Temporary folder
TEMP_FOLDER = "./tmp/"
# Compiled template temporary filename
TEMPLATE_TEMP_FILENAME = os.path.join(TEMP_FOLDER, "template_out.html")

# Temporary PDF base name
# Usage: filename = PDF_TEMP_BASE_NAME % index
PDF_TEMP_BASE_NAME = os.path.join(TEMP_FOLDER, "./qsl_%04d.pdf")

# Output folder
OUT_FOLDER = "./out/"

# Output image extension
IMG_OUT_EXTENSION = "jpg"
# Output image base name
IMG_OUT_BASE_NAME = "./qsl_%04d."
# Final PDF filename
PDF_OUTPUT = "./qsl.pdf"


@dataclass(frozen=True)
class ProgressUpdate:
    """Class to provide progress updates for QSL generation to the caller"""

    stage: str
    completed: int
    total: int


def split_every(items, every):
    """Transform a list in sublists, each one with at most 'every' elements"""
    for i in range(math.ceil((len(items)) / every)):
        _from = i * every
        _to = min(_from + every, len(items))
        yield items[_from:_to]


def qso_list_generator(qso_list, every):
    qso_grouped = {}

    # Get any unique sending station callsign (typically should be only one)
    unique_send_stations = set(
        [
            qso._d.get("STATION_CALLSIGN", "").upper()
            for qso in qso_list
            if isinstance(qso, QSO)
        ]
    )
    if len(unique_send_stations) > 1:
        logging.warning(
            f"Found {len(unique_send_stations)} unique sending stations, everything should work as expected anyway"
        )

    for _station in unique_send_stations:
        qso_grouped[_station] = {}
        # Get all unique recipients for each sending station
        unique_recipients = set(
            [
                qso._d.get("CALL", "").upper()
                for qso in qso_list
                if isinstance(qso, QSO)
                and qso._d.get("STATION_CALLSIGN") == _station
                and qso.is_valid()
            ]
        )
        for _recipient in unique_recipients:
            qso_grouped[_station][_recipient] = [
                qso
                for qso in qso_list
                if isinstance(qso, QSO)
                and qso._d.get("STATION_CALLSIGN") == _station
                and qso._d.get("CALL") == _recipient
                and qso.is_valid()
            ]
            no_qsos = len(qso_grouped[_station][_recipient])
            logging.info(f"Detected {no_qsos} QSOs from {_station} to {_recipient}")
            for _qso_list in split_every(qso_grouped[_station][_recipient], every):
                yield _qso_list


def render_qsl(
    _qso_list: list[QSO],
    _i: int,
    _image: bool,
    _pdf: bool,
    _width: float,
    _height: float,
    _format: str,
    _dry_run: bool,
    _out_folder: str,
    out_base_name: str,
    template,
    renderer: playwright_wrapper.QSLRenderer,
):

    logging.debug(f"\trender_qsl(_i={_i})")

    # Converting all keys into lowercase
    qsos_data_lowercase = [
        {key.casefold(): value for key, value in _qso._d.items()}
        for _qso in _qso_list
        if isinstance(_qso, QSO)
    ]

    if len(qsos_data_lowercase) == 0:
        logging.warning("Empty QSO list, nothing to do")
        return False
    elif len(qsos_data_lowercase) == 1:
        # Render template in single QSO mode
        output = template.render(qso=qsos_data_lowercase[0])
    else:
        # Render template in multiple QSO mode
        output = template.render(qsos=qsos_data_lowercase)

    # ---------------------------------------------------------------------
    # DATA FLOW: Python -> Jinja -> HTML
    # 1. We extract the raw dictionary from the QSO object (_qso._d).
    # 2. We convert all keys to lowercase (e.g., 'CALL' -> 'call').
    #    This is done because Jinja templates usually prefer lowercase variables.
    # 3. We pass this dictionary to the template context as 'qso'.
    #    This allows the HTML template to access variables like {{ qso.call }}
    #    or {{ qso.band }}.
    # ---------------------------------------------------------------------

    logging.info(f"\tCompiling QSL {_i+1} to {qsos_data_lowercase[0]['call']} ")

    if _dry_run is False:
        # Write compiled template to file
        with open(TEMPLATE_TEMP_FILENAME, "wt", encoding="utf-8") as f:
            f.write(output)

    # Convert template page to image
    if _image:
        out_name = os.path.join(
            _out_folder,
            (out_base_name + "_%04d." % (_i + 1) + _format),
        )
        if _dry_run is False:
            renderer.render(
                TEMPLATE_TEMP_FILENAME,
                out_name,
                _width,
                _height,
            )
        else:
            logging.info(
                f"Would call: renderer.render {' '.join([TEMPLATE_TEMP_FILENAME, out_name,str(_width),str(_height)])}"
            )

    # Convert template page to PDF
    if _pdf:
        if _dry_run is False:
            renderer.render(
                TEMPLATE_TEMP_FILENAME,
                (PDF_TEMP_BASE_NAME % _i),
                _width,
                _height,
            )
        else:
            logging.info(
                f"Would call: renderer.render {' '.join([TEMPLATE_TEMP_FILENAME, (PDF_TEMP_BASE_NAME % _i), str(_width),str(_height)])}"
            )

    return True


def unlink_if_exists(path):
    """Utility function to delete a file without throwing an exception if it doesn't exist"""
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def rmtree_if_exists(path):
    """Utility function to delete a folder and its subfolders and contents without throwing an exception if it doesn't exist"""
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass


def qsl_filter_format_date(value, fmt="%d/%m/%Y"):
    try:
        dt = datetime.strptime(value, "%Y%m%d")
        return dt.strftime(fmt)
    except (ValueError, TypeError) as e:
        logging.error(f"qsl_filter_format_date(value={value}): {e}")
        return value


def qsl_filter_format_time(value, include_seconds=False, separator=":"):
    if not value or len(value) < 4:
        return value

    parts = [value[:2], value[2:4]]

    if include_seconds and len(value) >= 6:
        parts.append(value[4:6])

    return separator.join(parts)


def generate_qsl_image_pdf(
    qso_list: list[QSO],
    _image: bool = False,
    _pdf: bool = False,
    _template: str = TEMPLATE_DEFAULT_FILE,
    _out_filename: str = PDF_OUTPUT,
    _out_folder: str = OUT_FOLDER,
    _format: str = IMG_OUT_EXTENSION,
    _width: float = QSL_WIDTH,
    _height: float = QSL_HEIGHT,
    _dry_run: bool = False,
    _max_qso: int = 3,
    progress_queue: Optional[Queue] = None,
):
    """Generate QSL output and optionally send progress updates to a thread-safe queue."""

    def report_progress(stage: str, completed: int, total: int) -> None:
        if progress_queue is not None:
            progress_queue.put(ProgressUpdate(stage, completed, total))

    if _dry_run:
        logging.warning("Running app in dry-run mode")

    if not _image and not _pdf:
        logging.error("No output specified!")
        return

    assert isinstance(qso_list, list)

    # NOTE the most Pythonic way would be a list comprehension: [ qso for qso in qso_list if qso.is_valid() ]
    removed_qsos = 0  # Counter for debugging
    for qso in qso_list[:]:
        if not qso.is_valid():
            logging.warning(
                f"Invalid QSO found: {qso._d.get('CALL','<no_call>')} on {qso._d.get('QSO_DATE','<no_date>')}"
            )
            qso_list.remove(qso)
            removed_qsos += 1
    if removed_qsos > 0:
        logging.warning(
            f"Removed {removed_qsos} invalid QSOs from the list, which now contains {len(qso_list)} QSOs"
        )

    if len(qso_list) == 0:
        logging.warning("No QSO found")
        report_progress("done", 0, 0)
        return

    # Sort the list by timestamp
    qso_list.sort(key=QSO.timestamp_on)

    # Remove any extension in the passed out filename, will be added later
    out_base_name = _out_filename.rsplit(".", 1)[0]
    logging.debug(
        f"Passed output filename : {_out_filename}\nBase name without extension: {out_base_name}"
    )

    # Template file full path
    template_path = os.path.join(TEMPLATE_FOLDER, _template)
    if not os.path.isfile(template_path):
        raise FileNotFoundError(f"Template file {template_path} not found")

    if _dry_run is False:
        # Delete previous output file(s) if present
        rmtree_if_exists(TEMP_FOLDER)

        # Re-create temporary folder
        if not os.path.exists(TEMP_FOLDER):
            os.makedirs(TEMP_FOLDER)
        else:
            if not os.path.isdir(TEMP_FOLDER):
                os.unlink(TEMP_FOLDER)
                os.makedirs(TEMP_FOLDER)

        if _pdf:
            # Delete previous output file(s)
            unlink_if_exists(_out_filename)

        # Create output folder
        if not os.path.exists(_out_folder):
            os.makedirs(_out_folder)
        else:
            if not os.path.isdir(_out_folder):
                os.unlink(_out_folder)
                os.makedirs(_out_folder)

    # Loading Jinja environment
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_FOLDER),
        autoescape=select_autoescape(["html", "htm", "xml"]),
    )
    # Loading filters
    env.filters["format_date"] = qsl_filter_format_date
    env.filters["format_time"] = qsl_filter_format_time

    # Loading HTML template
    template = env.get_template(_template)

    qso_batches = list(qso_list_generator(qso_list, _max_qso))
    total_batches = len(qso_batches)
    report_progress("rendering", 0, total_batches)

    with playwright_wrapper.QSLRenderer() as renderer:

        # Initialize counter
        _i = 0

        # Generate each QSL
        for _qso_list in qso_batches:
            if len(_qso_list) == 0:
                logging.warning("Empty QSO list! Skipping to next one")
                continue

            if render_qsl(
                _qso_list,
                _i,
                _image,
                _pdf,
                _width,
                _height,
                _format,
                _dry_run,
                _out_folder,
                out_base_name,
                template,
                renderer,
            ):
                _i += 1
            else:
                logging.warning("Didn't render anything")
            report_progress("rendering", _i, total_batches)

    if _pdf:
        report_progress("assembling_pdf", 0, 1)
        # Concatenate all files to create a single PDF to print
        out_name = os.path.join(_out_folder, out_base_name + ".pdf")
        if not _dry_run:
            writer = pypdf.PdfWriter()
            for pdf in [(PDF_TEMP_BASE_NAME % i) for i in range(_i)]:
                if os.path.isfile(pdf):
                    writer.append(pdf)
                else:
                    logging.error(
                        f"Error: file {pdf} not found! Check Playwright output!"
                    )
            writer.write(out_name)
            writer.close()
        else:
            logging.info(f"Would create output file {out_name}")
        report_progress("assembling_pdf", 1, 1)

    if _dry_run is False:
        # Delete temporary folder and its content
        rmtree_if_exists(TEMP_FOLDER)
    report_progress("done", total_batches, total_batches)


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
def main():
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
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"File {filename} doesn't exist")

    # If no output is specified fallback to PDF
    if not args.image and not args.pdf:
        args.pdf = True

    # If only --image is specified do not generate PDF
    if args.image and not args.pdf:
        args.pdf = False

    if not args.pdf and args.pdf is not None and args.image == False:
        raise ValueError("At least one output option must be specified")

    # File extension
    ext = filename.split(".")[-1]

    if ext.casefold() in ["adi", "adif"]:
        logging.info(
            f"Proceeding to parse ADIF file {args.filename}, only valid QSO: {args.only_valid}"
        )
        qso_list = adif.qso_list_from_file(filename, args.only_valid)

    else:
        raise ValueError("Unrecognized file extension")

    # Optional parameters validation
    if args.width <= 0:
        raise ValueError("--width must be positive")
    elif args.width > QSL_WIDTH_MAX:
        raise ValueError(f"--width must be <= {QSL_WIDTH_MAX}")

    if args.height <= 0:
        raise ValueError("--height must be positive")
    elif args.height > QSL_HEIGHT_MAX:
        raise ValueError(f"--height must be <= {QSL_HEIGHT_MAX}")

    if args.max_qso <= 0:
        raise ValueError("--max-qso must be positive (1 to disable multi-QSO cards)")

    # All OK, generate QSLs
    with ThreadPoolExecutor() as executor:
        progress_queue = Queue() # To display progress

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
