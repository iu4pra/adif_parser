#!/usr/bin/python3

import logging

# List of essential QSO keys
_ESSENTIAL_KEYS = [
    "QSO_DATE",
    "TIME_ON",
    "CALL",
    ["FREQ", "BAND"], # At least one must be present
    "MODE",
]


class QSO:
    """Class representing a single QSO record"""

    def __init__(self, data: dict):
        # Check input data
        assert isinstance(data, dict)

        # Internal data storage
        self._d: dict = {}

        for key in data.keys():
            value = data[key]
            # Only non-null fields are reported
            if value is None or value == '':
                logging.warning(f"Skipping key {key} with invalid value")
            else:
                # All keys are put uppercase and values are converted to string
                self._d[key.upper()] = str(value)

    def __str__(self):
        """String representation of the object"""
        _str = ''
        for key in self._d.keys():
            _str += f"{key} = {self._d[key]}\n"
        return _str

    def is_valid(self):
        """Checks if the QSO is valid"""
        # All essential fields must be present
        for key in _ESSENTIAL_KEYS:
            # If the key itself is a list the check at least one of the elements is present
            if isinstance(key, list):
                if len([self._d.get(tuple_key) for tuple_key in key if self._d.get(tuple_key)]) == 0:
                    logging.warning(
                        f"No fields among {key} ({len([self._d.get(tuple_key) for tuple_key in key if self._d.get(tuple_key)])}) found, invalid QSO")
                    return False
            else:
                if key not in self._d.keys() or not self._d.get(key):
                    logging.warning(
                        f"Essential field {key} not found, invalid QSO")
                    return False
        return True
