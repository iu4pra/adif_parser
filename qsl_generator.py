#!/usr/bin/python3

# QSL generator
# Generates a printable QSL starting from an HTML template with Jinja2
# wkhtmltox reference https://wkhtmltopdf.org/downloads.html
from jinja2 import Environment, FileSystemLoader
import os
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

# Loading the environment
env = Environment(loader=FileSystemLoader('.'))

# Loading the template
template = env.get_template('template.html')

# Rendering the template and storing the resulting text in variable output
output = template.render(
    qso={'call': 'IZ4HUF', 'band': '12M', 'freq': '14.080', 'rst_sent': 599})

# Delete previous files
TEMPLATE_TEMP_FILENAME = './template_out.html'
PDF_OUTPUT = './out.pdf'
unlink_if_exists(PDF_OUTPUT)
unlink_if_exists(TEMPLATE_TEMP_FILENAME)

# Write to file
with open(TEMPLATE_TEMP_FILENAME, 'wt', encoding='utf-8') as f:
    f.write(output)

cmd_options = {"--page-width": "14cm", "--page-height": "9cm"}

# Convert single page to PDF
subprocess.run(["./wkhtmltopdf"] + dict_to_cmd_list(cmd_options) +
               [TEMPLATE_TEMP_FILENAME, PDF_OUTPUT])

# Delete temporary files
unlink_if_exists(TEMPLATE_TEMP_FILENAME)
