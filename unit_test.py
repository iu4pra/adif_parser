#!/usr/bin/python3

# This software under the MIT License
# Unit test for the application
# This is the only file at the moment, might be split in the future if it becomes too big

import adif
import logging
from qso import QSO
import unittest


class ParsingTest(unittest.TestCase):
    """Test cases for the ADIF parser"""

    def test_empty_string(self):
        """Empty strings return no fields"""
        self.assertEqual(adif.parse_adif_string(''), [])
        self.assertEqual(adif.parse_adif_string('\0'), [])
        self.assertEqual(adif.parse_adif_string('\0'*3), [])

    def test_newline(self):
        """String with only newlines return no fields"""
        self.assertEqual(adif.parse_adif_string('\n'), [])
        self.assertEqual(adif.parse_adif_string('\n'*3), [])

    def test_blank_string(self):
        """String with only whitespaces return no fields"""
        self.assertEqual(adif.parse_adif_string(' '), [])
        self.assertEqual(adif.parse_adif_string(' '*5), [])

    def test_string_without_fields(self):
        """String with no valid fields"""
        _test_string = """QRZLogbook download for iu4pra
    Date: Mon Oct  6 11:30:36 2025
    Bookid: 312206
    Records: 200"""
        self.assertEqual(adif.parse_adif_string(_test_string), [])

    def test_single_field(self):
        """Parse a single, well formatted field"""
        self.assertEqual(adif.parse_adif_string('<CALL:6>IK4XYZ'), [
                         {'field': 'CALL', 'len': 6, 'type': None, 'value': 'IK4XYZ'}])

    def test_single_field_with_blanks(self):
        """Parse a single, well formatted field with extra whitespaces"""
        self.assertEqual(adif.parse_adif_string('<CALL:6>IK4XYZ  '), [
                         {'field': 'CALL', 'len': 6, 'type': None, 'value': 'IK4XYZ'}])

    def test_single_field_with_extra(self):
        """Parse a single, well formatted field with extra characters"""
        self.assertEqual(adif.parse_adif_string('<CALL:6>IK4XYZABC'), [
                         {'field': 'CALL', 'len': 6, 'type': None, 'value': 'IK4XYZ'}])

    def test_single_field_with_type(self):
        """Parse a single, well formatted field with type identifier"""
        self.assertEqual(adif.parse_adif_string('<CALL:6:s>IK4XYZ'), [
                         {'field': 'CALL', 'len': 6, 'type': 's', 'value': 'IK4XYZ'}])

    def test_single_field_wrong_type(self):
        self.assertEqual(adif.parse_adif_string('<:6>IK4XYZ'), [])

    def test_single_field_no_len(self):
        """Parse a single, well formatted field without length"""
        self.assertEqual(adif.parse_adif_string('<EOR>'), [
                         {'field': 'EOR', 'len': 0, 'type': None, 'value': None}])

    def test_single_field_wrong_len(self):
        """Parse a single field with a wrong length"""
        for i in range(-5, 1):
            with self.assertRaises(adif.AdifError):
                adif.parse_adif_string(f'<CALL:{i}>IK4XYZ')

    def test_single_field_invalid_len(self):
        """Parse a single field with a non-numeric length"""
        self.assertEqual(adif.parse_adif_string('<CALL:d>IK4XYZ'), [])

    def test_single_field_too_short(self):
        """Single field with insufficient data to fill the value field"""
        with self.assertRaises(adif.AdifError):
            adif.parse_adif_string('<CALL:6>IK4')
        with self.assertRaises(adif.AdifError):
            adif.parse_adif_string('<CALL:6:s>IK4')


class QSOTest(unittest.TestCase):
    """Test cases for the QSO class"""

    def test_blank_qso_not_valid(self):
        """A blank QSO must not be valid"""
        self.assertFalse(QSO({}).is_valid())

    def test_qso_essential_fields(self):
        """A QSO must contain all essential fields"""
        _adif_string = adif.parse_adif_string(
            '<QSO_DATE:8>20251005 <TIME_ON:6>123000 <CALL:6>IW9YZA <BAND:3>12m <MODE:3>FT8 <RST_SENT:2>-- <RST_RCVD:2>-- <EOR>')
        _qso_list = adif.adif_to_qso_list(_adif_string)
        self.assertEqual(len(_qso_list), 1)
        self.assertTrue(_qso_list[0].is_valid())


# Automatically run tests when this module is executed
if __name__ == '__main__':
    # Override logging configuration to show only critical errors
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s', level=logging.CRITICAL)
    # Use this to conditionally disable all logging output
    DISABLE_LOGGING = True
    if DISABLE_LOGGING:
        logging.basicConfig(handlers=[logging.NullHandler()], force=True)

    unittest.main()
