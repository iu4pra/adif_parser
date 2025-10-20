#!/usr/bin/python3

# QSL generator
# Generates a printable QSL starting from an HTML template with Jinja2
# wkhtmltox reference https://wkhtmltopdf.org/downloads.html
from jinja2 import Environment, FileSystemLoader
from qso import QSO
# import argparse TODO later on for entry point
import os
import pickle
import pypdf
import subprocess


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


# QSO list
# TODO dumpfile for testing only!
QSO_DUMP_FILE = './sample_log.dump'
# Compiled template filename
TEMPLATE_TEMP_FILENAME = './template_out.html'
# Temporary PDF base name
# Usage: filename = PDF_TEMP_BASE_NAME % index
PDF_TEMP_BASE_NAME = './qsl_%04d.pdf'
# Final PDF_filename
PDF_OUTPUT = './out.pdf'

# Command options for wkhtmltopdf
cmd_options = {"--page-width": "14cm", "--page-height": "9cm"}

# Delete previous files
unlink_if_exists(PDF_OUTPUT)
unlink_if_exists(TEMPLATE_TEMP_FILENAME)
subprocess.run("rm -vf *.pdf", shell=True, capture_output=True)

# Loading the environment
env = Environment(loader=FileSystemLoader('.'))

# Loading the template
template = env.get_template('template.html')

# Unpickle data
# FIXME for testing only!
with open(QSO_DUMP_FILE, 'rb') as f:
    qso_list = pickle.load(f)

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

# Delete temporary files
unlink_if_exists(TEMPLATE_TEMP_FILENAME)
# Delete qso_*.pdf
result = subprocess.run(
    f"rm -fv {PDF_TEMP_BASE_NAME.replace('%04d','*')}", shell=True)
