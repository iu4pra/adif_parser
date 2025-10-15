#!/usr/bin/python3

import logging
from qso import QSO
import unittest


class QSOTest(unittest.TestCase):
    """Test cases for the QSO class"""

    def test_blank_qso_not_valid(self):
        """A blank QSO must not be valid"""
        assert not QSO({}).is_valid()


# Automatically run tests when this module is executed
if __name__ == '__main__':
    # Override logging configuration to show only critical errors
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    # Use this to conditionally disable all logging output
    DISABLE_LOGGING = True
    if DISABLE_LOGGING:
        logging.basicConfig(handlers=[logging.NullHandler()])
    unittest.main()
