#!/usr/bin/python3

# This software under the MIT License
# QSL generator
# Generates a printable QSL starting from an HTML template with Jinja2
# wkhtmltox reference https://wkhtmltopdf.org/downloads.html

from jinja2 import Environment, FileSystemLoader, select_autoescape
from qso import QSO
from wkhtml import wkhtmltoimage, wkhtmltopdf, WKHTMLTOX_BASE_DPI
import adif
import argparse
import logging
import os
import pickle
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
QSL_WIDTH = 14
QSL_HEIGHT = 9

# Default DPI
DPI = 150

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
IMG_OUT_EXTENSION = 'jpg'
# Output image base name
IMG_OUT_BASE_NAME = "./qsl_%04d."
# Final PDF_filename
PDF_OUTPUT = "./out.pdf"


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
    "--zoom": str(DPI/WKHTMLTOX_BASE_DPI),
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
        "--zoom": str(_dpi/WKHTMLTOX_BASE_DPI),
        "--width": str(cm_to_px(_width, _dpi)),
        "--height": str(cm_to_px(_height, _dpi)),
        "--format": _format,
    }

def unlink_if_exists(path):
    """Utility function to delete a file without throwing an exception if it doesn't exist"""
    try:
        os.unlink(path)
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
    _out_folder: str = OUT_FOLDER,
    _format: str = IMG_OUT_EXTENSION,
    _width: float = QSL_WIDTH,
    _height: float = QSL_HEIGHT,
    _dpi: int = DPI,
):
    """Generates either, one QSL image per QSO in the given list,
    a PDF file qith the QSLs contained in the given QSO list, or both"""

    if not _image and not _pdf:
        logging.error("No output specified!")
        return

    assert isinstance(qso_list, list)

    # Template file full path
    template_path = os.path.join(TEMPLATE_FOLDER, _template)
    if not os.path.isfile(template_path):
        raise FileNotFoundError(f"Template file {template_path} not found")

    # Delete previous output file(s) if present
    if os.path.exists(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER)

    # Re-create temporary folder
    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)
    else:
        if not os.path.isdir(TEMP_FOLDER):
            os.unlink(TEMP_FOLDER)
            os.makedirs(TEMP_FOLDER)

    if _pdf:
        # Delete previous output file(s)
        unlink_if_exists(PDF_OUTPUT)


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
        
        for key, value in _qso._d.items():
            # Converting all keys into lowercase
            qso_data_lowercase[key.casefold()] = value
        output = template.render(qso=qso_data_lowercase)

        logging.info(f"\tCompiling QSL {i+1} to {qso_data_lowercase['call']} ")

        # Write compiled template to file
        with open(TEMPLATE_TEMP_FILENAME, "wt", encoding="utf-8") as f:
            f.write(output)

        # Convert template page to image
        if _image:
            out_name = os.path.join(_out_folder, (IMG_OUT_BASE_NAME % i + _format))
            ret = wkhtmltoimage(
                dict_to_cmd_list(generate_options_image(_format,_width,_height,_dpi)) + [TEMPLATE_TEMP_FILENAME, out_name]
            )
            logging.info(f"wkhtmltoimage returned {ret.returncode}")

        # Convert template page to PDF
        if _pdf:
            ret = wkhtmltopdf(
                dict_to_cmd_list(generate_options_pdf(_width,_height,_dpi))
                + [TEMPLATE_TEMP_FILENAME, (PDF_TEMP_BASE_NAME % i)]
            )
    if _pdf:
        # Concatenate all files to create a single PDF to print
        out_name = os.path.join(_out_folder, PDF_OUTPUT)
        writer = pypdf.PdfWriter()
        for pdf in [(PDF_TEMP_BASE_NAME % i) for i in range(len(qso_list))]:
            writer.append(pdf)
        writer.write(out_name)
        writer.close()

    # Delete temporary folder and its content
    if os.path.exists(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER)

if __name__ == "__main__":
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
        "outname",
        metavar="output_file",
        nargs="?",
        default="out.pdf",
        type=str,
        help="Output file name",
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
        "--image_format",
        metavar="image_format",
        type=str,
        default=IMG_OUT_EXTENSION,
        help=f"Output image format (default {IMG_OUT_EXTENSION})",
    )
    parser.add_argument(
        "--dpi",
        metavar="dpi",
        type=int,
        default=DPI,
        help=f"Tentative DPI value (default {DPI})",
    )

    args = parser.parse_args()

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
        raise Exception("At least one output option must be specified")
    # File extension
    ext = filename.split(".")[-1]

    if ext.casefold() in ["adi", "adif"]:
        logging.info(f"Proceeding to parse ADIF file {args.filename}")
        qso_list = adif.qso_list_from_file(filename)

    elif ext.casefold() in [
        "dump",
    ]:
        logging.warning("TEST ONLY dump file, not for production!")
        # Unpickle data
        with open(args.filename, "rb") as f:
            qso_list = pickle.load(f)
    else:
        raise Exception("Unrecognized file extension")

    generate_qsl_image_pdf(
        qso_list,
        _image=args.image,
        _pdf=args.pdf,
        _template=args.template,
        _out_folder=args.output_dir,
        _format=args.image_format,
        _dpi=args.dpi)
