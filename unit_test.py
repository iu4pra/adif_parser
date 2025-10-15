#!/usr/bin/python3

import adif
import logging
from qso import QSO
import unittest


class ParsingTest(unittest.TestCase):
    """Test cases for the ADIF parser"""

    def test_parse_empty_string(self):
        """Empty strings return no fields"""
        assert adif.parse_adif_string('') == []
        assert adif.parse_adif_string('\0') == []
        assert adif.parse_adif_string('\0'*3) == []

    def test_parse_newline(self):
        """String with newlines only return no fields"""
        assert adif.parse_adif_string('\n') == []
        assert adif.parse_adif_string('\n'*3) == []

    def test_parse_blank_string(self):
        """String with whitespaces return no fields"""
        assert adif.parse_adif_string(' ') == []
        assert adif.parse_adif_string(' '*5) == []

    def test_parse_string_without_fields(self):
        """String with no valid fields"""
        _test_string = """QRZLogbook download for iu4pra
    Date: Mon Oct  6 11:30:36 2025
    Bookid: 312206
    Records: 200"""
        assert adif.parse_adif_string(_test_string) == []

    def test_parse_single_field(self):
        """Parse a single, well formatted field"""
        assert adif.parse_adif_string('<CALL:6>IK4XYZ') == [
            {'field': 'CALL', 'len': 6, 'type': None, 'value': 'IK4XYZ'}]

    def test_parse_single_field_with_blanks(self):
        """Parse a single, well formatted field with extra whitespaces"""
        assert adif.parse_adif_string('<CALL:6>IK4XYZ  ') == [
            {'field': 'CALL', 'len': 6, 'type': None, 'value': 'IK4XYZ'}]

    def test_parse_single_field_with_extra(self):
        """Parse a single, well formatted field with extra characters"""
        assert adif.parse_adif_string('<CALL:6>IK4XYZABC') == [
            {'field': 'CALL', 'len': 6, 'type': None, 'value': 'IK4XYZ'}]

    def test_parse_single_field_with_type(self):
        """Parse a single, well formatted field with type identifier"""
        assert adif.parse_adif_string('<CALL:6:s>IK4XYZ') == [
            {'field': 'CALL', 'len': 6, 'type': 's', 'value': 'IK4XYZ'}]

    def test_parse_single_field_no_len(self):
        """Parse a single field with a wrong length"""
        assert adif.parse_adif_string('<EOR>') == [
            {'field': 'EOR', 'len': 0, 'type': None, 'value': None}]

    def test_parse_single_field_wrong_len(self):
        """Parse a single field with a wrong length"""
        with unittest.TestCase.assertRaises(self, adif.AdifError):
            adif.parse_adif_string('<CALL:-1>IK4XYZ')

    def test_parse_single_field_too_short(self):
        """Single field with insufficient data to fill the value field"""
        with unittest.TestCase.assertRaises(self, adif.AdifError):
            adif.parse_adif_string('<CALL:6>IK4')
        with unittest.TestCase.assertRaises(self, adif.AdifError):
            adif.parse_adif_string('<CALL:6:s>IK4')


class QSOTest(unittest.TestCase):
    """Test cases for the QSO class"""

    def test_blank_qso_not_valid(self):
        """A blank QSO must not be valid"""
        assert not QSO({}).is_valid()

    def test_qso_essential_fields(self):
        """A QSO must contain all essential fields"""
        _adif_string = adif.parse_adif_string(
            '<QSO_DATE:8>20251005 <TIME_ON:6>123000 <CALL:6>IW9YZA <BAND:3>12m <MODE:3>FT8 <RST_SENT:2>-- <RST_RCVD:2>-- <EOR>')
        _qso_list = adif.adif_to_qso_list(_adif_string)
        assert len(_qso_list) == 1
        assert _qso_list[0].is_valid()


# Automatically run tests when this module is executed
if __name__ == '__main__':
    # Override logging configuration to show only critical errors
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s', level=logging.CRITICAL)
    # Use this to conditionally disable all logging output
    # TODO doesn't work at the moment
    DISABLE_LOGGING = True
    if DISABLE_LOGGING:
        logging.basicConfig(handlers=[logging.NullHandler()])

    unittest.main()
