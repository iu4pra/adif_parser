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
    # TODO conditionally disable all logging
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s', level=logging.CRITICAL)
    unittest.main()
