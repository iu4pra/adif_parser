#!/usr/bin/python3

# This software under the MIT License

from datetime import date, datetime, timedelta, timezone
from random import choice, choices, randint
import logging
import os.path
import requests
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


class RandomCallGenerator:
    """Helper class to generate random callsigns"""

    def __init__(self):
        """Class constructor"""

        self.generate_call = None
        self.load_generator()

    def load_generator(self):
        """Attempts to load a callsign generator"""
        try:
            # Check if SuperCheckPartial file exists locally
            if os.path.isfile("MASTER.SCP"):
                logging.info("SuperCheckPartial file found locally")
            else:
                logging.warning(
                    "SuperCheckPartial file not found locally, attempting download..."
                )
                # Try to download it if not present
                response = requests.get(
                    "https://www.supercheckpartial.com/downloads/MASTER.SCP",
                    allow_redirects=True,
                )
                if response.status_code != 200:
                    logging.error("Failed to download SuperCheckPartial file")
                    # Download failed, generate random callsigns instead
                else:
                    # Download successfull, save the file locally fot future use
                    with open("MASTER.SCP", "wb") as f:
                        f.write(response.content)
                    logging.info("SuperCheckPartial file downloaded successfully!")
        except requests.exceptions.RequestException as e:
            logging.warning(
                f"HTTP Error while checking/downloading SuperCheckPartial file:\n\t{e}"
            )
        except Exception as e:
            logging.error(
                f"Error while checking/downloading SuperCheckPartial file:\n\t{e}"
            )
        finally:
            if os.path.isfile("MASTER.SCP"):
                self.generate_call = self.generate_call_scp
            else:
                self.generate_call = self.generate_call_random

    # To use the object in a with context
    def __enter__(self):
        if self.generate_call is None:
            self.load_generator()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logging.error(f"Error: {exc_type}: {exc_val}")
        # TODO complete

    def generate_call_scp(self):
        """Generates a call sign using SuperCheckPartial"""
        # Implementation for generating call signs using SuperCheckPartial file
        logging.warning(f"""SCP file size: {os.path.getsize("MASTER.SCP")}""")

        i = 1
        with open("MASTER.SCP", "rt", encoding="utf-8") as f:
            for _line in f:  # More memory-efficient than for _line in f.readlines()
                if not _line.startswith(("#", "!")):
                    if i == 1:
                        retval = _line.strip()
                    else:
                        if randint(1, i) == 1:
                            retval = _line.strip()
                    i += 1
                else:
                    logging.info(f"Skipping line: {_line.strip()}")

        logging.warning(f"Generated callsign {retval}")
        return retval

    def generate_call_random(self):
        """Generates a random call sign without using SuperCheckPartial"""
        if randint(1, 100) <= 50:
            return f"{choice('KNW')}{randint(0,9)}{''.join(choices(string.ascii_uppercase, k=randint(1,3)))}"
        return f"I{choice('KUWZ')}{randint(0,9)}{''.join(choices(string.ascii_uppercase, k=3))}"


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
        qso_date = start_date + timedelta(
            days=randint(0, (end_date - start_date).days), minutes=randint(0, 1399)
        )

        _dict = {
            "STATION_CALLSIGN": f"I{choice('KUWZ')}{randint(0,9)}{''.join(choices(string.ascii_uppercase, k=3))}",
            "QSO_DATE": qso_date.strftime("%Y%m%d"),
            "TIME_ON": qso_date.strftime("%H%M"),
            "CALL": f"{choice('KNW')}{randint(0,9)}{''.join(choices(string.ascii_uppercase, k=randint(1,3)))}",
            "BAND": choice(["80m", "40m", "20m", "15m", "10m"]),
            "MODE": choice(["SSB", "CW", "FT8"]),
        }
        _qso = QSO(_dict)
        return _qso
