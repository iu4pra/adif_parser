#!/usr/bin/python3

# ADIF file parser
# This software under the MIT License
# Sources:
#   https://pypi.org/project/adif-io/
#   https://www.adif.org/100/adif_100.htm
#   https://regex101.com/

"""
ADIF Parser Module

This module handles the parsing of Amateur Data Interchange Format (ADIF) files.
It is responsible for:
1. Reading raw .adi files.
2. Splitting the content into individual ADIF tags (fields).
3. Validating the integrity of these fields (checking lengths and types).
4. Converting the raw fields into structured QSO objects.
"""

import logging
import os.path
import pickle
import re
from datetime import datetime, timedelta, timezone
from qso import QSO


class AdifError(Exception):
    """Base error."""
    pass


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


def adif_field_to_qso_field(_adif: dict):
    """Convenience function to convert an ADIF field dict into a QSO field dict"""
    return {_adif['field']: _adif['value']}


# Regex to parse ADIF fields from the log (without value)
# Explanation of the pattern:
#   <             : Matches the opening bracket of an ADIF tag.
#   (?P<field>\w+): Captures the field name (alphanumeric) into group 'field'.
#   (?:           : Non-capturing group for the rest of the tag logic.
#     >           : Matches a closing bracket (simple tag like <EOR>).
#     |           : OR
#     \:          : Matches a colon separator.
#     (?P<len>[-\d]+) : Captures the length (digits/hyphens) into group 'len'.
#     (?:         : Optional non-capturing group for the data type.
#       \:        : Matches a colon separator.
#       (?P<type>\w+) : Captures the data type into group 'type'.
#     )?          : End optional type group.
#   )             : End non-capturing group.
#   >             : Matches the closing bracket.
_FIELD_GENERIC_RE_NO_VALUE = re.compile(
    r"<(?P<field>\w+)(?:>|\:(?P<len>[-\d]+)(?:\:(?P<type>\w+))?>)", re.IGNORECASE)


def parse_adif_string(_adif: str):
    field_list = []
    # String cursor
    cursor = 0
    while len(_adif) > 0 and cursor < (len(_adif) - 1):
        match = _FIELD_GENERIC_RE_NO_VALUE.search(_adif, cursor)
        if match:
            # Match found
            logging.debug(
                f"Match found at position {match.start()} to {match.end()}")

            # Log discared data
            discared_string_pretty = _adif[cursor:match.start()].replace(
                '\n', '\\n')
            logging.debug(
                f"Discarded {match.start()-cursor} byte(s) ({discared_string_pretty})")

            # Compile field from match
            field = match.groupdict()

            # Converting field length to int
            field['len'] = int(field['len'] or 0)

            # Field lengths must be non negative
            if field['len'] < 0:
                raise AdifError("Field lenght must be non negative")

            # If the field has some length, copy the value according to the declared size
            if field['len'] > 0:
                field['value'] = _adif[match.end():match.end() +
                                       field['len']]
            else:
                field['value'] = None

            if field['len'] > 0 and len(field['value']) != field['len']:
                raise AdifError(
                    f"Impossible to fetch {field['len']} bytes from log, found {len(field['value'])}")

            if field['value'] is not None and field['value'].find('<') >= 0:
                logging.warning(
                    f"Possible len value too long for field {field['field']} ({field['value']}), < detected")

            field_list.append(field)

            # Field data check
            logging.debug(f"{field} \t Check: {check_field(field)}")

            # Update cursor position
            cursor = match.end() + field['len']

            logging.debug(
                f"Next match search will go from position {cursor} to {len(_adif)-1}")
        else:
            logging.debug(
                f"No match found starting from {cursor} to {len(_adif)-1}")
            logging.info("No more matches, exiting")
            break
    return field_list


def parse_adif_file(filename: str):
    """Parse an ADIF file and returns the ordered list of its fields"""
    # Input type check
    assert isinstance(filename, str)
    with open(filename, 'rt') as f:
        field_list = parse_adif_string(f.read())
    return field_list


def remove_header(_adif_fields: list):
    """Remove header data from an ADIF field list created by parse_adif_string() """
    # Input type check
    assert isinstance(_adif_fields, list)
    # Look for EOH
    eoh_index = index_of(_adif_fields, lambda x: is_type(x, 'EOH'))
    if eoh_index > 0:
        logging.debug(f"EOH found at index {eoh_index}")
    else:
        logging.info("EOH field not found during header stripping")

    # Remove header data
    del _adif_fields[0:eoh_index+1]
    logging.debug(
        f"ADIF field list has {len(_adif_fields)} entries after stripping {eoh_index+1} header entries")
    return _adif_fields, eoh_index


def adif_to_qso_list(_adif_fields: list):
    """Parse QSO data from an ADIF list

        Header is automatically stripped if not already done"""
    # Input type check
    assert isinstance(_adif_fields, list)
    # Strip header
    _adif_fields, eoh_index = remove_header(_adif_fields)

    logging.info(f"Automatic header stripping: eoh_index = {eoh_index}")

    _qso_list: list[QSO] = []

    field_list_temp = []

    while len(_adif_fields) > 0:
        # Move one element a time on a smaller support list until EOR is reached
        field_list_temp.append(_adif_fields.pop(0))

        if is_type(field_list_temp[-1], 'EOR'):
            # EOR found, discard it and create QSO object
            del field_list_temp[-1]

            _dict = {}  # Support dict for creating QSO
            for f in field_list_temp:
                # Raise an error if a field already exists for the QSO
                if _dict.get(f['field']):
                    raise AdifError(
                        f"Duplicate field {f['field']} ({_dict.get(f['field'])})")
                else:
                    _dict.update(adif_field_to_qso_field(f))

            field_list_temp.clear()

            logging.debug(f"Creating a QSO object based on {_dict}")
            _qso_list.append(QSO(_dict))
        else:
            if len(_adif_fields) == 0:
                # End of list found before EOR, raise error
                raise AdifError("End of list found before EOR")

    return _qso_list


def qso_list_from_file(filename: str):
    """Convenience function to convert an ADIF file into a QSO list"""
    field_list = parse_adif_file(filename)
    qso_list: list[QSO] = adif_to_qso_list(field_list)
    return qso_list


# Testing code
if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)

    # Use this to add debug info
    ADIF_DEBUG = True
    if ADIF_DEBUG:
        logging.root.setLevel(logging.DEBUG)

    # Example files:
    #   './iu4pra_sample_log.adi'
    #   './sample_log.adi'
    #   './sample_2qso.adi'
    LOGFILE = './sample_log.adi'
    logging.info(f"Analysis of file {os.path.basename(LOGFILE)}")

    # Create QSO objects
    qso_list: list[QSO] = qso_list_from_file(LOGFILE)

    logging.info(f"QSO list contains {len(qso_list)} entries")
    for q in qso_list:
        logging.debug(q)
        logging.debug(f"is_valid(): {q.is_valid()}")

    # Dumping the QSO list for the QSL generator module
    with open(os.path.splitext(LOGFILE)[0]+'.dump', 'wb') as f:
        pickle.dump(qso_list, f)
