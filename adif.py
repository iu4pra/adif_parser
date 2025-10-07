#!/usr/bin/python3

# ADIF file parser
# This software under the MIT License
# Sources:
#  https://pypi.org/project/adif-io/
#  https://www.adif.org/100/adif_100.htm
#  https://regex101.com/

import math
import re
from collections.abc import MutableMapping
from datetime import datetime, timedelta, timezone
from typing import Iterator


class AdifError(Exception):
    """Base error."""
    pass


class AdifHeaderWithoutEOHError(AdifError):
    """Error for header found, but not terminated with <EOH>"""
    pass


class AdifDuplicateFieldError(AdifError):
    """Error for duplicate fileds in one QSO record or in the header."""
    pass


def check_field(t: dict):
    """Integrity checks on a single ADIF field
        TODO: implement value type check, if anyone ever needs it"""
    if t.get('field') is None:
        raise AdifError("Field name doesn't exist")

    field = t.get('field')

    if field.upper() not in ['EOH', 'EOR']:
        if t.get('len') is None:
            raise AdifError("Invalid length value for field {field}")

        length = 0
        try:
            length = int(t.get('len'))
        except ValueError as e:
            raise AdifError(f"Invalid length value for field {field}")
        except Exception as e:
            raise e

        if length <= 0:
            raise AdifError("Invalid length, must be positive")

        value = t.get('value')
        if len(value) < length:
            raise AdifError("Field value too short")

    # All tests passed
    return True


# Field parsing regex
# field_generic_re = re.compile(r"<(?:(?P<field>\w+)(?:>|\:(?P<len>\d+)>(?P<value>[^<]+)?))", re.IGNORECASE)
FIELD_GENERIC_RE = re.compile(
    r"<(?:(?P<field>\w+)(?:>|\:(?P<len>\d+)(?:\:(?P<type>\w+))?>(?P<value>[^<]+)?))", re.IGNORECASE)

# Testing code
if __name__ == '__main__':
    import os.path
    import logging
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    logging.root.setLevel(logging.DEBUG)
    # Example file
    LOGFILE = './iu4pra_sample_log.adi'
    logging.info(f"Analisi del file {os.path.basename(LOGFILE)}")

    # Ordered list with all the fields parsed from the ADI file
    field_list = []

    # Field parsing
    with open(LOGFILE, 'rt') as f:
        for line in f.readlines():
            if FIELD_GENERIC_RE.match(line.strip()):
                logging.info("Match generic")
                for m in FIELD_GENERIC_RE.findall(line):
                    field = dict(zip(['field', 'len', 'type', 'value'], m))
                    field_list.append(field)
                    logging.debug(f"{field} \t Check: {check_field(field)}")
    while field_list.pop(0)['field'].upper() != 'EOH':
        logging.debug(field_list[0]['field'])
        pass
