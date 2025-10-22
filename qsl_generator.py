#!/usr/bin/python3

# This software under the MIT License
# QSL generator
# Generates a printable QSL starting from an HTML template with Jinja2
# wkhtmltox reference https://wkhtmltopdf.org/downloads.html

from jinja2 import Environment, FileSystemLoader
from qso import QSO
import adif
import argparse
import os
import pickle
import pypdf
import shutil
import subprocess

# Default template filename
TEMPLATE_DEFAULT_FILE = 'template.html'
TEMPLATE_FOLDER = './templates'
# Temporary folder
TEMP_FOLDER = './tmp/'
# Compiled template filename
TEMPLATE_TEMP_FILENAME = os.path.join(TEMP_FOLDER, 'template_out.html')
# Temporary PDF base name
# Usage: filename = PDF_TEMP_BASE_NAME % index
PDF_TEMP_BASE_NAME = os.path.join(TEMP_FOLDER, './qsl_%04d.pdf')
# Output image base name
IMG_TEMP_BASE_NAME = os.path.join(TEMP_FOLDER, './qsl_%04d.jpg')
# Final PDF_filename
PDF_OUTPUT = './out.pdf'


def cm_to_px(cm, dpi):
    """Converts centimeters to pixels given a DPI value"""
    return int(cm*dpi/2.54)


# Command options for wkhtmltopdf
cmd_options_pdf = {"--page-width": "14cm", "--page-height": "9cm"}

# Command options for wkhtmltoimage
cmd_options_image = {
    "--width": str(cm_to_px(14, 75)), "--height": str(cm_to_px(9, 75))}


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


def generate_qsl_pdf(qso_list: list[QSO], _template: str = TEMPLATE_DEFAULT_FILE):
    """Generates a PDF file qith the QSLs contained in the given QSO list"""
    assert isinstance(qso_list, list)

    # Template file full path
    template_path = os.path.join(TEMPLATE_FOLDER, _template)
    if not os.path.isfile(template_path):
        raise FileNotFoundError(f"Template file {template_path} not found")

    # Create temporary folder if not present
    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)
    else:
        if not os.path.isdir(TEMP_FOLDER):
            os.unlink(TEMP_FOLDER)
            os.makedirs(TEMP_FOLDER)

    # Delete previous output file(s)
    # TODO create out/ folder
    unlink_if_exists(PDF_OUTPUT)

    # Loading Jinja environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_FOLDER))

    # Loading HTML template
    template = env.get_template(_template)

    for i, _qso in enumerate(qso_list):
        assert isinstance(_qso, QSO)

        # Rendering the template and storing the resulting text in variable output
        qso_data_lowercase = {}
        for key, value in _qso._d.items():
            # Converting all keys into lowercase
            qso_data_lowercase[key.casefold()] = value
        output = template.render(qso=qso_data_lowercase)

        print(f"\tCompiling QSL {i+1} to {qso_data_lowercase['call']} ")

        # Write compiled template to file
        with open(TEMPLATE_TEMP_FILENAME, 'wt', encoding='utf-8') as f:
            f.write(output)

        # Convert template page to PDF
        subprocess.run(["./wkhtmltopdf"] + dict_to_cmd_list(cmd_options_pdf) +
                       [TEMPLATE_TEMP_FILENAME, (PDF_TEMP_BASE_NAME % i)])

    # Concatenate all files to create a single PDF to print
    writer = pypdf.PdfWriter()
    for pdf in [(PDF_TEMP_BASE_NAME % i) for i in range(len(qso_list))]:
        writer.append(pdf)
    writer.write(PDF_OUTPUT)
    writer.close()

    # Delete temporary folder and its content
    if os.path.exists(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER)


def generate_qsl_image(qso_list: list[QSO], _template: str = TEMPLATE_DEFAULT_FILE):
    """Generates one QSL image per QSO in the given list"""
    assert isinstance(qso_list, list)

    # Template file full path
    template_path = os.path.join(TEMPLATE_FOLDER, _template)
    if not os.path.isfile(template_path):
        raise FileNotFoundError(f"Template file {template_path} not found")

    # Delete previous output file(s)
    # TODO create out/ folder
    if os.path.exists(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER)

    # Create temporary folder if not present
    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)
    else:
        if not os.path.isdir(TEMP_FOLDER):
            os.unlink(TEMP_FOLDER)
            os.makedirs(TEMP_FOLDER)

    # Loading Jinja environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_FOLDER))

    # Loading HTML template
    template = env.get_template(_template)

    for i, _qso in enumerate(qso_list):
        assert isinstance(_qso, QSO)

        # Rendering the template and storing the resulting text in variable output
        qso_data_lowercase = {}
        for key, value in _qso._d.items():
            # Converting all keys into lowercase
            qso_data_lowercase[key.casefold()] = value
        output = template.render(qso=qso_data_lowercase)

        print(f"\tCompiling QSL {i+1} to {qso_data_lowercase['call']} ")

        # Write compiled template to file
        with open(TEMPLATE_TEMP_FILENAME, 'wt', encoding='utf-8') as f:
            f.write(output)

        # Convert template page to PDF
        subprocess.run(["./wkhtmltoimage"] + dict_to_cmd_list(cmd_options_image) +
                       [TEMPLATE_TEMP_FILENAME, (IMG_TEMP_BASE_NAME % i)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Generate a .pdf file from a QSO list in .adi o .dump format")
    parser.add_argument('filename', metavar='input_file',
                        type=str, help='Log file to process (ADIF format)')
    parser.add_argument('outname', metavar='output_file',
                        nargs='?', default='out.pdf', type=str, help='Output file name')
    parser.add_argument('--pdf', action='store_true',
                        help='Output as multipage PDF')
    parser.add_argument('--image', default=False,
                        action='store_true', help='Output as images')
    parser.add_argument('--template', metavar='template_file', type=str,
                        default=TEMPLATE_DEFAULT_FILE, help='Template file to use')

    # parser.add_argument(
    #    '--log', default=sys.stdout, type=argparse.FileType('w'),
    #    help='the file where the sum should be written')
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
    ext = filename.split('.')[-1]

    if ext.casefold() in ['adi', 'adif']:
        print(f"Proceeding to parse ADIF file {args.filename}")
        qso_list = adif.qso_list_from_file(filename)

    elif ext.casefold() in ['dump',]:
        print("TEST ONLY dump file")
        # Unpickle data
        with open(args.filename, 'rb') as f:
            qso_list = pickle.load(f)
    else:
        raise Exception("Unrecognized file extension")

    if args.pdf:
        generate_qsl_pdf(qso_list, args.template)

    if args.image:
        generate_qsl_image(qso_list, args.template)
