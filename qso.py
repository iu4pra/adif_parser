#!/usr/bin/python3

import logging

# List of essential QSO keys
_ESSENTIAL_KEYS = [
    "QSO_DATE",
    "TIME_ON",
    "CALL",
    "FREQ",
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
