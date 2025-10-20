#!/usr/bin/python3

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

# Temporary folder
TEMP_FOLDER = './tmp/'
# Compiled template filename
TEMPLATE_TEMP_FILENAME = os.path.join(TEMP_FOLDER, 'template_out.html')
# Temporary PDF base name
# Usage: filename = PDF_TEMP_BASE_NAME % index
PDF_TEMP_BASE_NAME = os.path.join(TEMP_FOLDER, './qsl_%04d.pdf')
# Final PDF_filename
PDF_OUTPUT = './out.pdf'

# Command options for wkhtmltopdf
cmd_options = {"--page-width": "14cm", "--page-height": "9cm"}


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


def generate_qsl_pdf(qso_list: list[QSO]):
    """Generates a PDF file qith the QSLs contained in the given QSO list"""
    assert isinstance(qso_list, list)

    # Create temporary folder if not present
    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)
    else:
        if not os.path.isdir(TEMP_FOLDER):
            os.unlink(TEMP_FOLDER)

    # Delete previous output file(s)
    unlink_if_exists(PDF_OUTPUT)

    # Loading Jinja environment
    # TODO separate folder for templates
    env = Environment(loader=FileSystemLoader('./templates/'))

    # Loading HTML template
    template = env.get_template('template.html')

    for i, _qso in enumerate(qso_list):
        assert isinstance(_qso, QSO)
        # Rendering the template and storing the resulting text in variable output
        qso_data_lowercase = {}
        for key, value in _qso._d.items():
            qso_data_lowercase[key.casefold()] = value
        output = template.render(qso=qso_data_lowercase)

        # Write compiled template to file
        with open(TEMPLATE_TEMP_FILENAME, 'wt', encoding='utf-8') as f:
            f.write(output)

        # Convert template page to PDF
        subprocess.run(["./wkhtmltopdf"] + dict_to_cmd_list(cmd_options) +
                       [TEMPLATE_TEMP_FILENAME, (PDF_TEMP_BASE_NAME % i)])

    writer = pypdf.PdfWriter()
    for pdf in [(PDF_TEMP_BASE_NAME % i) for i in range(len(qso_list))]:
        writer.append(pdf)
    writer.write(PDF_OUTPUT)
    writer.close()

    # Delete temporary folder and its content
    if os.path.exists(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Generate a .pdf file from a QSO list in .adi o .dump format")
    parser.add_argument('filename', metavar='input_file',
                        type=str, help='Log file to process')
    parser.add_argument('outname', metavar='output_file',
                        nargs='?', default='out.pdf', type=str, help='Output file name')
    # parser.add_argument(
    #    '--log', default=sys.stdout, type=argparse.FileType('w'),
    #    help='the file where the sum should be written')
    args = parser.parse_args()

    # Filename to be processed
    filename = os.path.relpath(args.filename)
    ext = filename.split('.')[-1]
    if ext.casefold() in ['adi', 'adif']:
        print("ADIF file")
        qso_list = adif.adif_to_qso_list(adif.parse_adif_file(
            filename))  # TODO create single function!

    elif ext.casefold() in ['dump',]:
        print("TEST ONLY dump file")
        # Unpickle data
        with open(args.filename, 'rb') as f:
            qso_list = pickle.load(f)
    else:
        raise Exception("Wrong file extension")

    generate_qsl_pdf(qso_list)
