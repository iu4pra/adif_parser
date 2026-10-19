#!/usr/bin/python3

# This software under the MIT License
# Unit test for QSO class

import datetime

import adif
import unittest
from qso import QSO, RandomCallGenerator
from unittest.mock import patch


class QSOTest(unittest.TestCase):

    def test_blank_qso_not_valid(self):
        """A blank QSO must not be valid"""
        self.assertFalse(QSO({}).is_valid())

    def test_valid_qso(self):
        # A perfectly valid QSO dictionary
        data = {
            "STATION_CALLSIGN": "K1ABC",
            "CALL": "W1AW",
            "QSO_DATE": "20230101",
            "TIME_ON": "120000",
            "BAND": "20m",
            "MODE": "CW",
        }
        q = QSO(data)
        self.assertTrue(q.is_valid())

    def test_to_string(self):
        data = {
            "CALL": "W1AW",
            "QSO_DATE": "20230101",
            "TIME_ON": "120000",
            "BAND": "20m",
            "MODE": "CW",
        }
        q = QSO(data)
        self.assertEqual(
            q.__str__(),
            "CALL = W1AW\nQSO_DATE = 20230101\nTIME_ON = 120000\nBAND = 20m\nMODE = CW\n",
        )

    def test_qso_essential_fields(self):
        """A QSO must contain all essential fields"""
        _adif_string = adif.parse_adif_string(
            "<STATION_CALLSIGN:5>W1ABC <QSO_DATE:8>20251005 <TIME_ON:6>123000 <CALL:6>IW9YZA <BAND:3>12m <MODE:3>FT8 <RST_SENT:2>-- <RST_RCVD:2>-- <EOR>"
        )
        _qso_list = adif.adif_to_qso_list(_adif_string)
        self.assertEqual(len(_qso_list), 1)
        self.assertTrue(_qso_list[0].is_valid())

    def test_null_field_1(self):
        # Missing TIME_ON
        data = {"CALL": "W1AW", "QSO_DATE": "", "TIME_ON": "120000", "MODE": "CW"}
        q = QSO(data)
        self.assertFalse(q.is_valid())

    def test_null_field_2(self):
        # Missing TIME_ON
        data = {"CALL": "W1AW", "QSO_DATE": "20230101", "TIME_ON": None, "MODE": "CW"}
        q = QSO(data)
        self.assertFalse(q.is_valid())

    def test_missing_essential_field_single_1(self):
        # Missing TIME_ON
        data = {
            "STATION_CALLSIGN": "W1ABC",
            "CALL": "W1AW",
            "QSO_DATE": "20230101",
            "BAND": "20m",
            "MODE": "CW",
        }
        q = QSO(data)
        self.assertFalse(q.is_valid())

    def test_missing_essential_field_single_2(self):
        # Missing STATION_CALLSIGN
        data = {
            "CALL": "W1AW",
            "QSO_DATE": "20230101",
            "TIME_ON": "120000",
            "BAND": "20m",
            "MODE": "CW",
        }
        q = QSO(data)
        self.assertFalse(q.is_valid())

    def test_missing_essential_field_list(self):
        # Missing TIME_ON
        data = {
            "CALL": "W1AW",
            "QSO_DATE": "20230101",
            "TIME_ON": "120000",
            "MODE": "CW",
        }
        q = QSO(data)
        self.assertFalse(q.is_valid())

    def test_freq_instead_of_band(self):
        # The logic allows EITHER Band OR Freq. Test Freq only.
        data = {
            "STATION_CALLSIGN": "W1ABC",
            "CALL": "W1AW",
            "QSO_DATE": "20230101",
            "TIME_ON": "120000",
            "FREQ": "14.000",
            "MODE": "SSB",
        }
        q = QSO(data)
        self.assertTrue(q.is_valid())

    def test_normalization(self):
        # Test that lowercase input keys are converted to uppercase
        data = {"call": "K1ABC"}  # lowercase key
        q = QSO(data)

        # Internal dictionary should have 'CALL'
        self.assertIn("CALL", q._d)
        self.assertEqual(q._d["CALL"], "K1ABC")


class QSOTimestampTest(unittest.TestCase):

    def test_timestamp(self):
        timestamp = QSO.timestamp("20230101", "123456")

        self.assertEqual(
            timestamp,
            datetime.datetime(2023, 1, 1, 12, 34, 56, tzinfo=datetime.timezone.utc),
        )

    def test_timestamp_truncates_extra_characters(self):
        timestamp = QSO.timestamp("2023010199", "123456789")

        self.assertEqual(
            timestamp,
            datetime.datetime(2023, 1, 1, 12, 34, 56, tzinfo=datetime.timezone.utc),
        )

    def test_timestamp_pads_short_time(self):
        timestamp = QSO.timestamp("20230101", "1234")

        self.assertEqual(
            timestamp,
            datetime.datetime(2023, 1, 1, 12, 34, 0, tzinfo=datetime.timezone.utc),
        )

    def test_timestamp_on(self):
        q = QSO(
            {
                "STATION_CALLSIGN": "K1ABC",
                "CALL": "W1AW",
                "QSO_DATE": "20230101",
                "TIME_ON": "123456",
                "BAND": "20m",
                "MODE": "CW",
            }
        )

        self.assertEqual(
            q.timestamp_on(),
            datetime.datetime(2023, 1, 1, 12, 34, 56, tzinfo=datetime.timezone.utc),
        )

    def test_timestamp_on_invalid_qso(self):
        with self.assertRaises(ValueError):
            QSO({}).timestamp_on()

    def test_timestamp_off(self):
        q = QSO(
            {
                "STATION_CALLSIGN": "K1ABC",
                "CALL": "W1AW",
                "QSO_DATE": "20230101",
                "TIME_ON": "123456",
                "QSO_DATE_OFF": "20230102",
                "TIME_OFF": "010203",
                "BAND": "20m",
                "MODE": "CW",
            }
        )

        self.assertEqual(
            q.timestamp_off(),
            datetime.datetime(2023, 1, 2, 1, 2, 3, tzinfo=datetime.timezone.utc),
        )

    def test_timestamp_off_invalid_qso(self):
        with self.assertRaises(ValueError):
            QSO({}).timestamp_off()


class RandomQSOTest(unittest.TestCase):
    def test_random_valis_qso_is_valid(self):
        self.assertTrue(QSO.random(valid=True).is_valid())


class RandomCallGeneratorTest(unittest.TestCase):
    def test_callsign_is_generated_1(self):
        callgen = RandomCallGenerator()
        assert callgen.generate_call() is not None

    def test_callsign_is_generated_2(self):
        callgen = RandomCallGenerator()
        assert callgen.generate_call().strip() != ""

    # TODO split + mock randint
    @patch("qso.randint")
    def test_callsign_is_generated_local_1(self, mock_randint):
        mock_randint.return_value = 1
        callgen = RandomCallGenerator()
        assert callgen.generate_call_random() is not None

    @patch("qso.randint")
    def test_callsign_is_generated_local_2(self, mock_randint):
        mock_randint.return_value = 51
        callgen = RandomCallGenerator()
        assert callgen.generate_call_random() is not None

    @patch("qso.randint")
    def test_callsign_is_generated_local_3(self, mock_randint):
        mock_randint.return_value = 1
        callgen = RandomCallGenerator()
        assert callgen.generate_call_random().strip() != ""

    @patch("qso.randint")
    def test_callsign_is_generated_local_4(self, mock_randint):
        mock_randint.return_value = 51
        callgen = RandomCallGenerator()
        assert callgen.generate_call_random().strip() != ""

    @patch("qso.RandomCallGenerator.generate_call_random", wraps=None)
    @patch("qso.RandomCallGenerator.generate_call_scp", wraps=None)
    @patch("qso.os.path.isfile")
    def test_scp_file_found_1(self, mock_isfile, mock_gencall_scp, mock_gencall_random):
        mock_isfile.return_value = True
        callgen = RandomCallGenerator()
        callgen.generate_call()
        mock_gencall_random.assert_not_called()
        mock_gencall_scp.assert_called()

    @patch("qso.RandomCallGenerator.generate_call_random", wraps=None)
    @patch("qso.RandomCallGenerator.generate_call_scp", wraps=None)
    @patch("qso.os.path.isfile")
    def test_scp_file_not_found_1(
        self, mock_isfile, mock_gencall_scp, mock_gencall_random
    ):
        mock_isfile.return_value = False
        callgen = RandomCallGenerator()
        callgen.generate_call()
        mock_gencall_scp.assert_not_called()
        mock_gencall_random.assert_called()

    @patch("qso.RandomCallGenerator.load_generator", wraps=None)
    @patch("qso.os.path.isfile")
    def test_with_scope(self, mock_isfile, mock_load_generator):
        mock_isfile.return_value = False
        callgen = RandomCallGenerator()
        with callgen:
            mock_load_generator.assert_called()


if __name__ == "__main__":
    unittest.main()
