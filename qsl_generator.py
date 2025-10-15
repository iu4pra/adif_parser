#!/usr/bin/python3

# QSL generator
# Generates a printable QSO starting from an HTML template with Jinja2
# wkhtmltox reference https://wkhtmltopdf.org/downloads.html
from jinja2 import Environment, FileSystemLoader
import os.path

# Loading the environment
env = Environment(loader=FileSystemLoader('.'))

# Loading the template
template = env.get_template('template.html')

# Rendering the template and storing the resultant text in variable output
output = template.render(qso={'call': 'IZ4HUF', 'band': '12M', 'freq': '14080', 'rst_sent': 599})

# Write output to stdout
# print(output)

# Delete previous file
TEMPLATE_OUT_FILENAME = './template_out.html'
if os.path.isfile(TEMPLATE_OUT_FILENAME):
    os.unlink(TEMPLATE_OUT_FILENAME)

# Write to file
with open(TEMPLATE_OUT_FILENAME, 'wt', encoding='utf-8') as f:
    f.write(output)
