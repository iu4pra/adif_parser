#!/usr/bin/python3

# QSL generator
# Generates a printable QSL starting from an HTML template with Jinja2
# wkhtmltox reference https://wkhtmltopdf.org/downloads.html
from jinja2 import Environment, FileSystemLoader
import os.path
import pypdf
import subprocess

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
if os.path.isfile(TEMPLATE_TEMP_FILENAME):
    os.unlink(TEMPLATE_TEMP_FILENAME)

# Write to file
with open(TEMPLATE_TEMP_FILENAME, 'wt', encoding='utf-8') as f:
    f.write(output)

# Convert single page to PDF
subprocess.run(["./wkhtmltopdf", "--page-width", "14cm",
               "--page-height", "9cm", TEMPLATE_TEMP_FILENAME, PDF_OUTPUT])
