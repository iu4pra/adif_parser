#!/usr/bin/python3

# This software under the MIT License
# Unit test for QSO class

import adif
import unittest
from qso import QSO


class QSOTest(unittest.TestCase):

    def test_blank_qso_not_valid(self):
        """A blank QSO must not be valid"""
        self.assertFalse(QSO({}).is_valid())

    def test_valid_qso(self):
        # A perfectly valid QSO dictionary
        data = {
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
            "<QSO_DATE:8>20251005 <TIME_ON:6>123000 <CALL:6>IW9YZA <BAND:3>12m <MODE:3>FT8 <RST_SENT:2>-- <RST_RCVD:2>-- <EOR>"
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

    def test_missing_essential_field_single(self):
        # Missing TIME_ON
        data = {"CALL": "W1AW", "QSO_DATE": "20230101", "BAND": "20m", "MODE": "CW"}
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


if __name__ == "__main__":
    unittest.main()
