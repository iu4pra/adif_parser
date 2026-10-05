#!/usr/bin/python3

# This software under the MIT License
# QSL generator
# Generates a printable QSL starting from an HTML template with Jinja2
# wkhtmltox reference https://wkhtmltopdf.org/downloads.html

from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from qso import QSO
from wkhtml import wkhtmltoimage, wkhtmltopdf, WKHTMLTOX_BASE_DPI
import adif
import argparse
import logging
import os
import pickle
import playwright_wrapper
import pypdf
import shutil

# ==========================================
# EXTERNAL DEPENDENCY WARNING
# ==========================================
# This script relies on the 'wkhtmltox' suite (wkhtmltopdf / wkhtmltoimage)
# to render HTML into PDF or Image formats.
# These are system-level binaries that must be installed separately.
# Download them here: https://wkhtmltopdf.org/downloads.html
# ==========================================

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


def cm_to_px(cm, dpi):
    """Converts centimeters to pixels given a DPI value"""
    return int(cm * dpi / 2.54)


# Default command options for wkhtmltopdf
cmd_options_pdf = {
    "--dpi": str(DPI),
    "--page-width": f"{QSL_WIDTH}cm",
    "--page-height": f"{QSL_HEIGHT}cm",
}

# Default command options for wkhtmltoimage
cmd_options_image = {
    "--zoom": str(DPI / WKHTMLTOX_BASE_DPI),
    "--width": str(cm_to_px(QSL_WIDTH, DPI)),
    "--height": str(cm_to_px(QSL_HEIGHT, DPI)),
}


def generate_options_pdf(_width, _height, _dpi):
    return {
        "--dpi": str(_dpi),
        "--page-width": f"{_width}cm",
        "--page-height": f"{_height}cm",
    }


def generate_options_image(_format, _width, _height, _dpi):
    return {
        "--zoom": str(_dpi / WKHTMLTOX_BASE_DPI),
        "--width": str(cm_to_px(_width, _dpi)),
        "--height": str(cm_to_px(_height, _dpi)),
        "--format": _format,
    }


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


def dict_to_cmd_list(_cmd_options: dict):
    """Converts a dict of options to a list to pass to subprocess.run"""
    cmd_list = []
    for k, v in _cmd_options.items():
        cmd_list.append(k)
        if v is not None:
            cmd_list.append(v)
    return cmd_list


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
    _dpi: int = DPI,
    _wkhtml_image_args=None,
    _wkhtml_pdf_args=None,
    _dry_run: bool = False,
):
    """Generates either, one QSL image per QSO in the given list,
    a PDF file qith the QSLs contained in the given QSO list, or both"""

    if _dry_run:
        logging.warning("Running app in dry-run mode")

    if not _image and not _pdf:
        logging.error("No output specified!")
        return

    assert isinstance(qso_list, list)

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

    # Generate each QSL
    for i, _qso in enumerate(qso_list):
        assert isinstance(_qso, QSO)

        # ---------------------------------------------------------------------
        # DATA FLOW: Python -> Jinja -> HTML
        # 1. We extract the raw dictionary from the QSO object (_qso._d).
        # 2. We convert all keys to lowercase (e.g., 'CALL' -> 'call').
        #    This is done because Jinja templates usually prefer lowercase variables.
        # 3. We pass this dictionary to the template context as 'qso'.
        #    This allows the HTML template to access variables like {{ qso.call }}
        #    or {{ qso.band }}.
        # ---------------------------------------------------------------------

        qso_data_lowercase = {}

        with playwright_wrapper.QSLRenderer() as renderer:
            for key, value in _qso._d.items():
                # Converting all keys into lowercase
                qso_data_lowercase[key.casefold()] = value
            output = template.render(qso=qso_data_lowercase)

            logging.info(f"\tCompiling QSL {i+1} to {qso_data_lowercase['call']} ")

            if _dry_run is False:
                # Write compiled template to file
                with open(TEMPLATE_TEMP_FILENAME, "wt", encoding="utf-8") as f:
                    f.write(output)

            # Remove any extension in the passed out filename, will be added later
            out_base_name = _out_filename.rsplit(".", 1)[0]
            logging.debug(
                f"Passed output filename : {_out_filename}\nBase name without extension: {out_base_name}"
            )

            # Convert template page to image
            if _image:
                out_name = os.path.join(
                    _out_folder, (out_base_name + "_%04d." % (i + 1) + _format)
                )
                image_cmd_list = dict_to_cmd_list(
                    generate_options_image(_format, _width, _height, _dpi)
                )
                if _wkhtml_image_args:
                    image_cmd_list.extend(_wkhtml_image_args.split())
                if _dry_run is False:
                    ret = wkhtmltoimage(
                        image_cmd_list + [TEMPLATE_TEMP_FILENAME, out_name]
                    )
                    renderer.render(
                        TEMPLATE_TEMP_FILENAME,
                        out_name.rsplit(".", 1)[0] + "_playwright." + _format,
                        _width,
                        _height,
                    )
                    if ret.returncode != 0:
                        logging.warning(f"wkhtmltoimage returned {ret.returncode}")
                else:
                    logging.info(
                        f"Would call: wkhtmltoimage {' '.join(image_cmd_list + [TEMPLATE_TEMP_FILENAME, out_name])}"
                    )

            # Convert template page to PDF
            if _pdf:
                pdf_cmd_list = dict_to_cmd_list(
                    generate_options_pdf(_width, _height, _dpi)
                )
                if _wkhtml_pdf_args:
                    pdf_cmd_list.extend(_wkhtml_pdf_args.split())
                if _dry_run is False:
                    ret = wkhtmltopdf(
                        pdf_cmd_list
                        + [TEMPLATE_TEMP_FILENAME, (PDF_TEMP_BASE_NAME % i)]
                    )
                    renderer.render(
                        TEMPLATE_TEMP_FILENAME,
                        (PDF_TEMP_BASE_NAME % i),
                        _width,
                        _height,
                    )
                    if ret.returncode != 0:
                        logging.warning(f"wkhtmltopdf returned {ret.returncode}")
                else:
                    logging.info(
                        f"Would call: wkhtmltopdf {' '.join(pdf_cmd_list + [TEMPLATE_TEMP_FILENAME, (PDF_TEMP_BASE_NAME % i)])}"
                    )

    if _pdf:
        # Concatenate all files to create a single PDF to print
        out_name = os.path.join(_out_folder, out_base_name + ".pdf")
        if not _dry_run:
            writer = pypdf.PdfWriter()
            for pdf in [(PDF_TEMP_BASE_NAME % i) for i in range(len(qso_list))]:
                if os.path.isfile(pdf):
                    writer.append(pdf)
                else:
                    logging.error(
                        f"Error: file {pdf} not found! Check wkhtmltopdf output!"
                    )
            writer.write(out_name)
            writer.close()
        else:
            logging.info(f"Would create output file {out_name}")

    if _dry_run is False:
        # Delete temporary folder and its content
        rmtree_if_exists(TEMP_FOLDER)


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

    # Remove ecisting handlers
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
        description="Generate a .pdf file from a QSO list in .adi or .dump format"
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
        "--dpi",
        metavar="dpi",
        type=int,
        default=DPI,
        help=f"Tentative DPI value (default {DPI})",
    )

    parser.add_argument(
        "--wkhtml-image-args",
        metavar="wkhtml_image_args",
        type=str,
        default="",
        help="Extra arguments for wkhtmltoimage",
    )

    parser.add_argument(
        "--wkhtml-pdf-args",
        metavar="wkhtml_pdf_args",
        type=str,
        default="",
        help="Extra arguments for wkhtmltopdf",
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

    # Parse arguments
    args = parser.parse_args()

    # Logger bust me setup BEFORE any call!
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

    # TODO to be removed, test code for .dump files
    elif ext.casefold() in [
        "dump",
    ]:
        logging.warning("TEST ONLY dump file, not for production!")
        # Unpickle data
        with open(args.filename, "rb", encoding="utf-8") as f:
            qso_list = pickle.load(f)
    else:
        raise Exception("Unrecognized file extension")

    # Optional parameters validation
    if args.width <= 0:
        raise ValueError("--width must be positive")
    elif args.width > QSL_WIDTH_MAX:
        raise ValueError(f"--width must be <= {QSL_WIDTH_MAX}")

    if args.height <= 0:
        raise ValueError("--height must be positive")
    elif args.height > QSL_HEIGHT_MAX:
        raise ValueError(f"--height must be <= {QSL_HEIGHT_MAX}")

    if args.dpi <= 0:
        raise ValueError("--dpi must be positive")
    elif args.dpi > DPI_MAX:
        raise ValueError(f"--dpi must be <= {DPI_MAX}")

    if args.wkhtml_image_args:
        logging.info(f"wkhtml_image_args: {args.wkhtml_image_args.split()}")

    if args.wkhtml_pdf_args:
        logging.info(f"wkhtml_pdf_args: {args.wkhtml_pdf_args.split()}")

    # All OK, generate QSLs
    generate_qsl_image_pdf(
        qso_list,
        _image=args.image,
        _pdf=args.pdf,
        _template=args.template,
        _out_filename=args.outfile,
        _out_folder=args.output_dir,
        _format=args.image_format,
        _width=args.width,
        _height=args.height,
        _dpi=args.dpi,
        _wkhtml_image_args=args.wkhtml_image_args,
        _wkhtml_pdf_args=args.wkhtml_pdf_args,
        _dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
