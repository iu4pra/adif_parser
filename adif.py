#!/usr/bin/python3

# ADIF file parser
# This software under the MIT License
# Sources:
#  https://pypi.org/project/adif-io/
#  https://www.adif.org/100/adif_100.htm
#  https://regex101.com/

import logging
import os.path
import re
from datetime import datetime, timedelta, timezone


class AdifError(Exception):
    """Base error."""
    pass


class QSO:
    """Class representing a single QSO record"""

    def __init__(self, data: dict[str, str]):
        assert isinstance(data, dict[str, str])

        # Internal data storage
        self._d: dict[str, str] = {}

        for key in dict.keys():
            value = data[key]
            # Only non-null fields are reported
            if value is None or len(value) == 0:
                logging.warning(f"Skipping key {key} with invalid value")
            else:
                # All keys are put uppercase and values are converted to string
                self._d[key.upper()] = str(value)


def check_field(t: dict):
    """Integrity checks on a single ADIF field
        TODO: implement value type check, if anyone ever needs it"""
    if t.get('field') is None:
        raise AdifError("No field name found")

    # Field name (now it's valid)
    field = t.get('field')

    if field.upper() not in ['EOH', 'EOR']:
        if t.get('len') is None:
            raise AdifError(f"Invalid length value for field {field}")

        length = 0
        try:
            length = int(t.get('len'))
        except ValueError as e:
            raise AdifError(
                f"Invalid length value for field {field} ({length})")
        except Exception as e:
            raise e

        # Field length is now valid
        if length <= 0:
            raise AdifError(f"Invalid length ({length}), must be positive")

        value = t.get('value')
        if len(value) < length:
            raise AdifError(
                f"Field value too short ({len(value)}, expected {length})")

    # All tests passed
    return True


# Field parsing regex
# field_generic_re = re.compile(r"<(?:(?P<field>\w+)(?:>|\:(?P<len>\d+)>(?P<value>[^<]+)?))", re.IGNORECASE)
FIELD_GENERIC_RE = re.compile(
    r"<(?:(?P<field>\w+)(?:>|\:(?P<len>\d+)(?:\:(?P<type>\w+))?>(?P<value>[^<]+)?))", re.IGNORECASE)

# Testing code
if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    # logging.root.setLevel(logging.DEBUG)
    # Example file
    LOGFILE = './iu4pra_sample_log.adi'
    logging.info(f"Analisi del file {os.path.basename(LOGFILE)}")

    # Ordered list with all the fields parsed from the ADI file
    field_list = []

    # Field parsing
    with open(LOGFILE, 'rt') as f:
        for line_no, line in enumerate(f.readlines(), 1):
            if FIELD_GENERIC_RE.match(line.strip()):
                logging.debug("Match found")
                for m in FIELD_GENERIC_RE.findall(line):
                    field = dict(zip(['field', 'len', 'type', 'value'], m))
                    field_list.append(field)
                    logging.debug(f"{field} \t Check: {check_field(field)}")
            else:
                if len(line.strip()) > 0:
                    logging.warning(
                        f"Match not found on line {line_no}:\n'{line.strip()}'")

    # Searching for EOH field
    eoh_found, eoh_index = False, 0
    for index, field in enumerate(field_list):
        if field['field'].upper() == 'EOH':
            logging.info(f"EOH found at index {index}")
            eoh_found = True
            eoh_index = index
            break

    if not eoh_found:
        logging.warning("EOH field not found")

    # Discarding all header data, not used at the moment
    del field_list[0:eoh_index+1]
