#!/usr/bin/python3

# This software under the MIT License
# Simple wkhtmltox wrapper

import os.path
import platform
import subprocess

# Base path for executables
WKHTMLTOX_BASE_PATH = "./"


def wkhtmltoimage(args: list = []):
    """Invokes wkhtmltoimage with the given arguments"""
    _os = platform.uname()[0]
    if _os == 'Windows':
        subprocess.run(
            [os.path.join(WKHTMLTOX_BASE_PATH, "wkhtmltoimage.exe")] + args)
    elif _os == 'Linux':
        subprocess.run(
            [os.path.join(WKHTMLTOX_BASE_PATH, "wkhtmltoimage")] + args)
    else:
        raise NotImplementedError("Not implemented for the given OS")


def wkhtmltopdf(args: list = []):
    """Invokes wkhtmltopdf with the given arguments"""
    _os = platform.uname()[0]
    if _os == 'Windows':
        subprocess.run(
            [os.path.join(WKHTMLTOX_BASE_PATH, "wkhtmltopdf.exe")] + args)
    elif _os == 'Linux':
        subprocess.run(
            [os.path.join(WKHTMLTOX_BASE_PATH, "wkhtmltopdf")] + args)
    else:
        raise NotImplementedError("Not implemented for the given OS")
