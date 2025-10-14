#!/usr/bin/python3

# QSL generator
# Generates a printable QSO starting from an HTML template with Jinja2
from jinja2 import Environment, FileSystemLoader
import os.path

# loading the environment
env = Environment(loader=FileSystemLoader('.'))

# loading the template
template = env.get_template('template.html')

# rendering the template and storing the resultant text in variable output
output = template.render(qso={'call': 'IZ4HUF'})

# Write output to stdout
# print(output)

# Delete previous file
if os.path.isfile('./template_out.html'):
    os.unlink('./template_out.html')
# Write to file
with open('./template_out.html', 'wt', encoding='utf-8') as f:
    f.write(output)
