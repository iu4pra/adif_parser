#!/usr/bin/python3

# This software under the MIT License
# wkhtmltox wrapper

import os
import platform
import subprocess


def wkhtmltoimage(args: list = []):
    """Invokes wkhtmltoimage with the given arguments"""
    _os = platform.uname()[0]
    if _os == 'Windows':
        subprocess.run(["./wkhtmltoimage.exe"] + args)
    elif _os == 'Linux':
        subprocess.run(["./wkhtmltoimage"] + args)
    raise NotImplementedError("Not implemented for the given OS")


def wkhtmltopdf(args: list = []):
    """Invokes wkhtmltopdf with the given arguments"""
    _os = platform.uname()[0]
    if _os == 'Windows':
        subprocess.run(["./wkhtmltopdf.exe"] + args)
    elif _os == 'Linux':
        subprocess.run(["./wkhtmltopdf"] + args)
    raise NotImplementedError("Not implemented for the given OS")


wkhtmltoimage()
wkhtmltopdf()
