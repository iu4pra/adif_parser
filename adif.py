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
    """Class representing a single QSO record
    TODO: move to separate file"""

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
            length = t.get('len')
            assert isinstance(length, int)
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


def is_type(f: dict, type: str):
    """Checks ADIF field type"""
    assert isinstance(f.get('field'), str)
    return f['field'].casefold() == type.casefold()


def index_of(item_list: list, cond, cond_value: bool = True):
    """Returns the index of the first element satisfying the condition or -1 if not found
    If cond_value = False returns the index of the first element NOT satisfying the condition
    Example usage:
    index_of(field_list, lambda x: is_type(x, 'EOR'))"""
    for index, item in enumerate(item_list):
        if cond(item) == cond_value:
            return index
    return -1


FIELD_GENERIC_RE_NO_VALUE = re.compile(
    r"<(?P<field>\w+)(?:>|\:(?P<len>\d+)(?:\:(?P<type>\w+))?>)", re.IGNORECASE)

# Testing code
if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    # logging.root.setLevel(logging.DEBUG)

    # Example file
    # LOGFILE = './iu4pra_sample_log.adi'
    LOGFILE = './sample_log.adi'
    logging.info(f"Analysis of file {os.path.basename(LOGFILE)}")

    # Ordered list with all the fields parsed from the ADI file
    field_list = []

    # Field parsing
    with open(LOGFILE, 'rt') as f:

        cursor = 0  # File cursor
        # Read all the file
        adif_log = f.read()
        while len(adif_log) > 0 and cursor < (len(adif_log) - 1):
            match = FIELD_GENERIC_RE_NO_VALUE.search(adif_log, cursor)
            if match:
                # Match found
                logging.debug(
                    f"Match found at position {match.start()} to {match.end()}")
                
                # Log discared data
                discared_string_pretty = adif_log[cursor:match.start()].replace('\n','\\n')
                logging.debug(f"Discarded {match.start()-cursor} byte(s) ({discared_string_pretty})")

                # Compile field from match
                field = match.groupdict()

                # Converting field length to int
                field['len'] = int(field['len'] or 0)

                # If the field has some length, copy the value according to the declared size
                if field['len'] > 0:
                    field['value'] = adif_log[match.end():match.end() +
                                              field['len']]
                else:
                    field['value'] = None

                field_list.append(field)

                # Field data checking
                logging.debug(f"{field} \t Check: {check_field(field)}")

                # Update cursor position
                cursor = match.end() + field['len']

                logging.debug(
                    f"Next match search will go from position {cursor} to {len(adif_log)-1}")
            else:
                logging.debug(
                    f"No match found starting from {cursor} to {len(adif_log)-1}")
                logging.info("No more matches, exiting")
                break

    # Searching for EOH field
    eoh_index = index_of(field_list, lambda x: is_type(x, 'EOH'))
    if eoh_index > 0:
        logging.info(f"EOH found at index {eoh_index}")
    else:
        logging.warning("EOH field not found")

    # Discarding all header data, not used at the moment
    del field_list[0:eoh_index+1]
    logging.info(
        f"ADIF field list has {len(field_list)} entries after stripping {eoh_index+1} header entries")

    # Group data into QSOs and create QSO objects
    qso_list: list[QSO] = []
    # Move one element a time on a smaller support list until EOR is reached
    # If a key already exists raise an error
    # EOR found, discard it
    # End of list found before EOR, raise error
