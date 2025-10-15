#!/usr/bin/python3

import adif
import logging
from qso import QSO
import unittest


class ParsingTest(unittest.TestCase):
    """Test cases for the ADIF parser"""

    def test_parse_empty_strings(self):
        assert adif.parse_adif_string('') == []
        assert adif.parse_adif_string('\n') == []
        assert adif.parse_adif_string('\n'*3) == []
        assert adif.parse_adif_string('\0') == []
        assert adif.parse_adif_string('\0'*3) == []
        assert adif.parse_adif_string(' ') == []
        assert adif.parse_adif_string(' '*5) == []

    def test_parse_single_field(self):
        assert adif.parse_adif_string('<CALL:6>IK4XYZ') == [
            {'field': 'CALL', 'len': 6, 'type': None, 'value': 'IK4XYZ'}]

    def test_parse_single_field_with_blanks(self):
        assert adif.parse_adif_string('<CALL:6>IK4XYZ  ') == [
            {'field': 'CALL', 'len': 6, 'type': None, 'value': 'IK4XYZ'}]

    def test_parse_single_field_with_extra(self):
        assert adif.parse_adif_string('<CALL:6>IK4XYZABC') == [
            {'field': 'CALL', 'len': 6, 'type': None, 'value': 'IK4XYZ'}]

    def test_parse_single_field_with_type(self):
        assert adif.parse_adif_string('<CALL:6:s>IK4XYZ') == [
            {'field': 'CALL', 'len': 6, 'type': 's', 'value': 'IK4XYZ'}]

    def test_parse_single_field_too_short(self):
        with unittest.TestCase.assertRaises(self, adif.AdifError):
            adif.parse_adif_string('<CALL:6>IK4')
        with unittest.TestCase.assertRaises(self, adif.AdifError):
            adif.parse_adif_string('<CALL:6:s>IK4')


class QSOTest(unittest.TestCase):
    """Test cases for the QSO class"""

    def test_blank_qso_not_valid(self):
        """A blank QSO must not be valid"""
        assert not QSO({}).is_valid()


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
