#!/usr/bin/python3

# This software under the MIT License
# QSL generator
# Generates a printable QSL starting from an HTML template with Jinja2

import argparse
import logging
import math
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from queue import Empty, Queue
from typing import Optional

import pypdf
from jinja2 import Environment, FileSystemLoader, select_autoescape
from tqdm import tqdm

import adif
import playwright_wrapper
from qso import HHMM_LENGTH, HHMMSS_LENGTH, QSO, YYYYMMDD_LENGTH

logger = logging.getLogger(__name__)

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
TEMPLATE_TEMP_FILENAME = Path(TEMP_FOLDER) / "template_out.html"

# Temporary PDF base name
# Usage: the page index is applied with the % operator
PDF_TEMP_BASE_NAME = Path(TEMP_FOLDER) / "qsl_%04d.pdf"

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
        logger.warning(
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
                and qso._d.get("STATION_CALLSIGN", "").upper() == _station
                and qso.is_valid()
            ]
        )
        for _recipient in unique_recipients:
            qso_grouped[_station][_recipient] = [
                qso
                for qso in qso_list
                if isinstance(qso, QSO)
                and qso._d.get("STATION_CALLSIGN", "").upper() == _station
                and qso._d.get("CALL", "").upper() == _recipient
                and qso.is_valid()
            ]
            no_qsos = len(qso_grouped[_station][_recipient])
            logger.info(f"Detected {no_qsos} QSOs from {_station} to {_recipient}")
            yield from split_every(qso_grouped[_station][_recipient], every)


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

    logger.debug(f"\trender_qsl(_i={_i})")

    # Converting all keys into lowercase
    qsos_data_lowercase = [
        {key.casefold(): value for key, value in _qso._d.items()}
        for _qso in _qso_list
        if isinstance(_qso, QSO)
    ]

    if len(qsos_data_lowercase) == 0:
        logger.warning("Empty QSO list, nothing to do")
        return False
    if len(qsos_data_lowercase) == 1:
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

    logger.info(f"\tCompiling QSL {_i + 1} to {qsos_data_lowercase[0]['call']} ")

    if _dry_run is False:
        # Write compiled template to file
        with TEMPLATE_TEMP_FILENAME.open("w", encoding="utf-8") as f:
            f.write(output)

    # Convert template page to image
    if _image:
        out_name = str(Path(_out_folder) / f"{out_base_name}_{_i + 1:04}.{_format}")
        if _dry_run is False:
            renderer.render(
                str(TEMPLATE_TEMP_FILENAME),
                out_name,
                _width,
                _height,
            )
        else:
            logger.info(
                f"Would call: renderer.render {' '.join([str(TEMPLATE_TEMP_FILENAME), out_name, str(_width), str(_height)])}"
            )

    # Convert template page to PDF
    if _pdf:
        if _dry_run is False:
            renderer.render(
                str(TEMPLATE_TEMP_FILENAME),
                str(PDF_TEMP_BASE_NAME) % _i,
                _width,
                _height,
            )
        else:
            logger.info(
                f"Would call: renderer.render {' '.join([str(TEMPLATE_TEMP_FILENAME), str(PDF_TEMP_BASE_NAME) % _i, str(_width), str(_height)])}"
            )

    return True


def unlink_if_exists(path):
    """Utility function to delete a file without throwing an exception if it doesn't exist"""
    if path != "":
        try:
            Path(path).unlink()
        except FileNotFoundError:
            logger.debug(f"unlink_if_exists: {path} not found")
    else:
        raise FileNotFoundError("Invalid empty path")


def rmtree_if_exists(path):
    """Utility function to delete a folder and its subfolders and contents without throwing an exception if it doesn't exist"""
    if path != "":
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            logger.debug(f"rmtree_if_exists: {path} not found")
    else:
        raise FileNotFoundError("Invalid empty path")


def qsl_filter_format_date(value, fmt="%d/%m/%Y"):
    try:
        if len(value) != YYYYMMDD_LENGTH:
            raise ValueError("Date must use YYYYMMDD format")
        dt = date.fromisoformat(f"{value[:4]}-{value[4:6]}-{value[6:8]}")
        return dt.strftime(fmt)
    except (ValueError, TypeError):
        logger.exception(f"qsl_filter_format_date(value={value})")
        return value


def qsl_filter_format_time(value, include_seconds=False, separator=":"):
    if not value or len(value) < HHMM_LENGTH:
        return value

    parts = [value[:2], value[2:HHMM_LENGTH]]

    if include_seconds and len(value) >= HHMMSS_LENGTH:
        parts.append(value[HHMM_LENGTH:HHMMSS_LENGTH])

    return separator.join(parts)


# TODO (power-of-10): split into smaller functions
def generate_qsl_image_pdf(  # noqa: C901, PLR0912, PLR0915
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
        logger.warning("Running app in dry-run mode")

    if not _image and not _pdf:
        logger.error("No output specified!")
        return

    assert isinstance(qso_list, list)

    # Removed QSOs counter initialized to list length before pruning
    removed_qsos = len(qso_list)  # Counter for debugging

    # Build a list with only valid QSOs
    qso_list = [qso for qso in qso_list if qso.is_valid()]

    # The list lenght after pruning is subtraced to get how many QSOs were removed
    removed_qsos -= len(qso_list)

    for qso in qso_list:
        assert qso.is_valid()

    if removed_qsos > 0:
        logger.warning(
            f"Removed {removed_qsos} invalid QSOs from the list, which now contains {len(qso_list)} QSOs"
        )

    if len(qso_list) == 0:
        logger.warning("No QSO found")
        report_progress("done", 0, 0)
        return

    # Sort the list by timestamp
    qso_list.sort(key=QSO.timestamp_on)

    # Remove any extension in the passed out filename, will be added later
    out_base_name = _out_filename.rsplit(".", 1)[0]
    logger.debug(
        f"Passed output filename : {_out_filename}\nBase name without extension: {out_base_name}"
    )

    # Template file full path
    template_path = Path(TEMPLATE_FOLDER) / _template
    if not template_path.is_file():
        raise FileNotFoundError(f"Template file {template_path} not found")

    if _dry_run is False:
        # Delete previous output file(s) if present
        rmtree_if_exists(TEMP_FOLDER)

        # Re-create temporary folder
        if not Path(TEMP_FOLDER).exists():
            Path(TEMP_FOLDER).mkdir(parents=True)
        elif not Path(TEMP_FOLDER).is_dir():
            Path(TEMP_FOLDER).unlink()
            Path(TEMP_FOLDER).mkdir(parents=True)

        if _pdf:
            # Delete previous output file(s)
            unlink_if_exists(_out_filename)

        # Create output folder
        if not Path(_out_folder).exists():
            Path(_out_folder).mkdir(parents=True)
        elif not Path(_out_folder).is_dir():
            Path(_out_folder).unlink()
            Path(_out_folder).mkdir(parents=True)

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
                logger.warning("Empty QSO list! Skipping to next one")
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
                logger.warning("Didn't render anything")
            report_progress("rendering", _i, total_batches)

    if _pdf:
        report_progress("assembling_pdf", 0, 1)
        # Concatenate all files to create a single PDF to print
        out_name = str(Path(_out_folder) / (out_base_name + ".pdf"))
        if not _dry_run:
            writer = pypdf.PdfWriter()
            for pdf in [str(PDF_TEMP_BASE_NAME) % i for i in range(_i)]:
                if Path(pdf).is_file():
                    writer.append(pdf)
                else:
                    logger.error(
                        f"Error: file {pdf} not found! Check Playwright output!"
                    )
            writer.write(out_name)
            writer.close()
        else:
            logger.info(f"Would create output file {out_name}")
        report_progress("assembling_pdf", 1, 1)

    if _dry_run is False:
        # Delete temporary folder and its content
        rmtree_if_exists(TEMP_FOLDER)
    report_progress("done", total_batches, total_batches)


if __name__ == "__main__":
    main()
