#!/usr/bin/python3

# This software under the MIT License

from datetime import date, datetime, timedelta, timezone
from random import choice, choices, randint
import logging
import string

# List of essential QSO keys
_ESSENTIAL_KEYS = [
    "STATION_CALLSIGN",
    "QSO_DATE",
    "TIME_ON",
    "CALL",
    ["FREQ", "BAND"],  # At least one among these fields must be present
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
            if value is None or value == "":
                logging.warning(f"Skipping key {key} with invalid value")
            else:
                # All keys are put uppercase and values are converted to string
                self._d[key.upper()] = str(value)

    def __str__(self):
        """String representation of the object"""
        _str = ""
        for key in self._d.keys():
            _str += f"{key} = {self._d[key]}\n"
        return _str

    def is_valid(self):
        """Checks if the QSO is valid"""
        # All essential fields must be present
        for key in _ESSENTIAL_KEYS:
            # If the key itself is a list the check at least one of the elements is present
            if isinstance(key, list):
                if (
                    len(
                        [
                            self._d.get(tuple_key)
                            for tuple_key in key
                            if self._d.get(tuple_key)
                        ]
                    )
                    == 0
                ):
                    logging.warning(
                        f"No fields among {key} ({len([self._d.get(tuple_key) for tuple_key in key if self._d.get(tuple_key)])}) found, invalid QSO"
                    )
                    return False
            else:
                if key not in self._d.keys() or not self._d.get(key):
                    logging.warning(f"Essential field {key} not found, invalid QSO")
                    return False
        return True

    @staticmethod
    def timestamp(qso_date: str, time_on: str):
        """Returns the timestamp of the QSO in UTC"""

        # Get date and time
        qso_date = qso_date[:8]  # Discard extra characters if present
        time_on = time_on[:6]  # Discard extra characters if present
        if len(time_on) < 6:  # HHMMSS
            time_on = time_on.ljust(
                6, "0"
            )  # Pad with zeros so everything is in HHMMSS format

        # Parse date and time
        dt = datetime.strptime(qso_date + time_on, "%Y%m%d%H%M%S")
        dt = dt.replace(tzinfo=timezone.utc)

        return dt

    def timestamp_on(self):
        """Returns the timestamp of the QSO start time in UTC"""
        # Check if essential fields are present
        if not self.is_valid():
            raise ValueError("Invalid QSO, cannot compute timestamp")

        return QSO.timestamp(self._d.get("QSO_DATE"), self._d.get("TIME_ON"))

    def timestamp_off(self):
        """Returns the timestamp of the QSO end time in UTC"""
        # Check if essential fields are present
        if not self.is_valid():
            raise ValueError("Invalid QSO, cannot compute timestamp")

        return QSO.timestamp(self._d.get("QSO_DATE_OFF"), self._d.get("TIME_OFF"))

    @staticmethod
    def random(valid: bool = True):
        """Generate a random QSO object"""
        start_date = datetime(2020, 1, 1)
        end_date = datetime.today()
        qso_date = start_date + timedelta(days=randint(0, (end_date - start_date).days), minutes=randint(0, 1399))

        _dict = {
            "STATION_CALLSIGN": f"I{choice('KUWZ')}{randint(0,9)}{''.join(choices(string.ascii_uppercase, k=3))}",
            "QSO_DATE": qso_date.strftime("%Y%m%d"),
            "TIME_ON": qso_date.strftime("%H%M"),
            "CALL": f"{choice('KNW')}{randint(0,9)}{''.join(choices(string.ascii_uppercase, k=randint(1,3)))}",
            "BAND": choice(["80m", "40m", "20m", "15m", "10m"]),
            "MODE": choice(["SSB", "CW", "FT8"]),
        }
        _qso = QSO(_dict)
        assert valid == False or _qso.is_valid()
        return _qso
