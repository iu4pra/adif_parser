#!/usr/bin/python3

# This software under the MIT License

from datetime import datetime, timedelta, timezone
from random import choice, choices, randint
import logging
import os.path
import re
import requests
import string
import tempfile

# List of essential QSO keys
_ESSENTIAL_KEYS = frozenset(
    [
        "STATION_CALLSIGN",
        "QSO_DATE",
        "TIME_ON",
        "CALL",
        frozenset(["FREQ", "BAND"]),  # At least one among these fields must be present
        "MODE",
    ]
)

# List of QSO keys that will be automatically converted to uppercase upon QSO creation
_UPPERCASE_FIELDS = frozenset(
    [
        "STATION_CALLSIGN",
        "CALL",
        "MODE",
    ]
)

# Regular expression for (basic) callsign validation
_CALLSIGN_SIMPLE_RE = re.compile(r"[A-Z0-9/]{3,}")


class RandomCallGenerator:
    """Helper class to generate random callsigns"""

    scp_fail = False  # Class-level flag to indicate if SCP file download failed
    scp_calls = []  # SuperCheckPartial calls list

    @classmethod
    def download_scp(cls):
        """Fetches the SuperCheckPartial file from the official source"""
        temp_path = None
        try:
            response = requests.get(
                "https://www.supercheckpartial.com/downloads/MASTER.SCP",
                allow_redirects=True,
                timeout=5,  # 5 seconds
            )
            if response.status_code != 200:
                logging.error("Failed to download SuperCheckPartial file")
                cls.scp_fail = True
                return False

            content = response.content
            content_encoding = response.headers.get(
                "Content-Encoding", "identity"
            ).lower()
            content_length = response.headers.get("Content-Length")
            if content_length is not None and content_encoding in ("", "identity"):
                try:
                    expected_length = int(content_length)
                except (TypeError, ValueError):
                    logging.error("Invalid Content-Length for SuperCheckPartial file")
                    cls.scp_fail = True
                    return False
                if len(content) != expected_length:
                    logging.error(
                        "Incomplete SuperCheckPartial download: expected %d bytes, "
                        "received %d",
                        expected_length,
                        len(content),
                    )
                    cls.scp_fail = True
                    return False
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                logging.error("SuperCheckPartial download is not valid UTF-8")
                cls.scp_fail = True
                return False

            lines = text.splitlines()
            if (
                not lines
                or not lines[0].startswith("!!Order,")
                or not any(
                    line.strip() and not line.strip().startswith(("#", "!"))
                    for line in lines[1:]
                )
            ):
                logging.error("SuperCheckPartial download has an invalid file format")
                cls.scp_fail = True
                return False

            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb", prefix=".MASTER.SCP.", dir=".", delete=False
                ) as temp_file:
                    temp_path = temp_file.name
                    bytes_written = temp_file.write(content)
                if bytes_written != len(content):
                    logging.error(
                        "Incomplete write of SuperCheckPartial file: expected %d "
                        "bytes, wrote %d",
                        len(content),
                        bytes_written,
                    )
                    cls.scp_fail = True
                    return False

                os.replace(temp_path, "MASTER.SCP")
                temp_path = None
            except OSError as e:
                logging.error(f"Error while saving SuperCheckPartial file:\n\t{e}")
                cls.scp_fail = True
                return False

            logging.info("SuperCheckPartial file downloaded successfully!")
            cls.scp_fail = False
            return True
        except requests.exceptions.RequestException as e:
            logging.warning(
                f"HTTP Error while downloading SuperCheckPartial file:\n\t{e}"
            )
            cls.scp_fail = True
            return False
        finally:
            if temp_path is not None:
                try:
                    os.unlink(temp_path)
                except FileNotFoundError:
                    pass
                except OSError as e:
                    logging.warning(
                        f"Could not remove temporary SuperCheckPartial file:\n\t{e}"
                    )

    @classmethod
    def _parse_scp(cls, _f):
        """Parses the SuperCheckPartial file and returns a list of valid callsigns"""
        return [
            _line.strip()
            for _line in _f
            if not _line.startswith(("#", "!"))
            and _CALLSIGN_SIMPLE_RE.fullmatch(_line.strip())
        ]

    @classmethod
    def load_scp(cls):
        """Loads the SuperCheckPartial file from the local copy or downloads it if not present"""
        if not cls.scp_fail:
            try:
                if not os.path.isfile("MASTER.SCP"):
                    if not cls.download_scp():
                        logging.error("Failed to download SuperCheckPartial file")
                        cls.scp_fail = True
                        return False
                else:
                    logging.debug(
                        "SuperCheckPartial file present locally, no download needed"
                    )

                if len(cls.scp_calls) == 0 and os.path.isfile("MASTER.SCP"):
                    logging.info(f"""SCP file size: {os.path.getsize("MASTER.SCP")}""")
                    with open("MASTER.SCP", "rt", encoding="utf-8") as f:
                        cls.scp_calls = cls._parse_scp(f.readlines())
                        logging.info(f"Loaded {len(cls.scp_calls)} callsigns")
                if cls.scp_calls:
                    cls.scp_fail = False
                    return True
                cls.scp_fail = True
                return False
            except Exception as e:
                logging.error(f"Error while loading SuperCheckPartial file:\n\t{e}")
                cls.scp_fail = True
                return False
        else:
            # Method already failed
            return False

    @classmethod
    def reset_scp(cls):
        """Clears the SuperCheckPartial calls list"""
        cls.scp_calls = []
        cls.scp_fail = False

    def __init__(self):
        """Class constructor"""

        self.generate_call = None
        self.load_generator()

    def load_generator(self):
        """Attempts to load a callsign generator"""
        # Check if SuperCheckPartial generation is possible
        if not RandomCallGenerator.load_scp():
            logging.warning(
                "Failed to download SuperCheckPartial file, using random callsign generator"
            )
            self.generate_call = RandomCallGenerator.generate_call_random
        else:
            self.generate_call = RandomCallGenerator.generate_call_scp

    # To use the object in a with context
    def __enter__(self):
        if self.generate_call is None:
            self.load_generator()
        return self  # This way "with RandomCallGenerator as callgen:" works!

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logging.error(f"Error: {exc_type}: {exc_val}")

    @classmethod
    def generate_call_scp(cls):
        """Generates a call sign using SuperCheckPartial"""
        # Implementation for generating call signs using SuperCheckPartial file
        if not cls.load_scp():
            logging.warning("Falling back to random callsign generator")
            return cls.generate_call_random()
        return choice(cls.scp_calls)

    @staticmethod
    def generate_call_random():
        """Generates a random call sign without using SuperCheckPartial"""
        if randint(1, 100) <= 50:
            return f"{choice('KNW')}{randint(0, 9)}{''.join(choices(string.ascii_uppercase, k=randint(1, 3)))}"
        return f"I{choice('KUWZ')}{randint(0, 9)}{''.join(choices(string.ascii_uppercase, k=3))}"


class QSO:
    """Class representing a single QSO record"""

    def __init__(self, data: dict):
        # Check input data
        assert isinstance(data, dict)

        # Internal data storage
        self._d: dict = {}

        for key in data:
            value = data[key]
            # Only non-null fields are reported
            if value is None or value == "":
                logging.warning(f"Skipping key {key} with invalid value")
            else:
                # All keys are put uppercase and values are converted to string
                if key.upper() in _UPPERCASE_FIELDS:
                    self._d[key.upper()] = str(value).upper()
                else:
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
            # If the element itself is a frozenset, then check at least one of the elements is present
            if isinstance(key, frozenset):
                if not any(self._d.get(field) for field in key):
                    logging.warning(f"No fields among {key} found, invalid QSO")
                    return False
            else:
                if not self._d.get(key):
                    logging.warning(f"Essential field {key} not found, invalid QSO")
                    return False

        # All mandatory uppercase fields must be uppercase
        for key in _UPPERCASE_FIELDS:
            value = self._d.get(key)
            if value and value.upper() != value:
                logging.warning(
                    f"Bad mandatory uppercase field {key}, invalid QSO: {value}"
                )
                return False

        # Callsign validation (maybe regex?)
        match_station_callsign = _CALLSIGN_SIMPLE_RE.fullmatch(
            self._d.get("STATION_CALLSIGN")
        )
        if not match_station_callsign:
            logging.warning(
                f"""Bad STATION_CALLSIGN, invalid QSO: {self._d.get("STATION_CALLSIGN")}"""
            )
            return False

        match_call = _CALLSIGN_SIMPLE_RE.fullmatch(self._d.get("CALL"))
        if not match_call:
            logging.warning(f"""Bad CALL, invalid QSO: {self._d.get("CALL")}""")
            return False

        # Date validation (QSO_DATE and QSO_DATE_OFF must be in YYYYMMDD format)
        try:
            datetime.strptime(self._d.get("QSO_DATE"), "%Y%m%d")
        except ValueError:
            logging.warning(f"Invalid QSO_DATE format: {self._d.get('QSO_DATE')}")
            return False

        if self._d.get("QSO_DATE_OFF"):
            try:
                datetime.strptime(self._d.get("QSO_DATE_OFF"), "%Y%m%d")
            except ValueError:
                logging.warning(
                    f"Invalid QSO_DATE_OFF format: {self._d.get('QSO_DATE_OFF')}"
                )
                return False

        # TIME_ON validation (must be in HHMM or HHMMSS format)
        try:
            datetime.strptime(self._d.get("TIME_ON"), "%H%M")
        except ValueError:
            try:
                datetime.strptime(self._d.get("TIME_ON"), "%H%M%S")
            except ValueError:
                logging.warning(f"Invalid TIME_ON format: {self._d.get('TIME_ON')}")
                return False

        # TIME_OFF validation (must be in HHMM or HHMMSS format)
        if self._d.get("TIME_OFF"):
            try:
                datetime.strptime(self._d.get("TIME_OFF"), "%H%M")
            except ValueError:
                try:
                    datetime.strptime(self._d.get("TIME_OFF"), "%H%M%S")
                except ValueError:
                    logging.warning(
                        f"Invalid TIME_OFF format: {self._d.get('TIME_OFF')}"
                    )
                    return False

        # Check QSO end time is after QSO start time (if end time exists)
        if self._d.get("TIME_OFF") and self._d.get("QSO_DATE_OFF"):
            try:
                dt_on = QSO.timestamp(self._d.get("QSO_DATE"), self._d.get("TIME_ON"))
                dt_off = QSO.timestamp(
                    self._d.get("QSO_DATE_OFF"), self._d.get("TIME_OFF")
                )
                if dt_off < dt_on:
                    logging.warning(
                        f"QSO end time {dt_off} is before start time {dt_on}, invalid QSO"
                    )
                    return False
            except Exception as e:
                logging.warning(f"Error while checking QSO timestamps: {e}")
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
    def random(
        valid: bool = True, _call_generator=RandomCallGenerator.generate_call_random
    ):
        """Generate a random QSO object"""
        start_date = datetime(2020, 1, 1)
        end_date = datetime.today()
        qso_date = start_date + timedelta(
            days=randint(0, (end_date - start_date).days), minutes=randint(0, 1439)
        )

        _dict = {
            "STATION_CALLSIGN": _call_generator(),
            "QSO_DATE": qso_date.strftime("%Y%m%d"),
            "TIME_ON": qso_date.strftime("%H%M"),
            "CALL": _call_generator(),
            "BAND": choice(["80m", "40m", "20m", "15m", "10m"]),
            "MODE": choice(["SSB", "CW", "FT8"]),
        }
        _qso = QSO(_dict)
        return _qso


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    callgen = RandomCallGenerator()
    print("CALLSIGN:", RandomCallGenerator.generate_call_scp())
