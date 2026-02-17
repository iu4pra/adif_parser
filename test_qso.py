import unittest
from qso import QSO

class TestQSO(unittest.TestCase):

    def test_valid_qso(self):
        # A perfectly valid QSO dictionary
        data = {
            'CALL': 'W1AW',
            'QSO_DATE': '20230101',
            'TIME_ON': '120000',
            'BAND': '20m',
            'MODE': 'CW'
        }
        q = QSO(data)
        self.assertTrue(q.is_valid())

    def test_missing_essential_field(self):
        # Missing TIME_ON
        data = {
            'CALL': 'W1AW',
            'QSO_DATE': '20230101',
            'BAND': '20m',
            'MODE': 'CW'
        }
        q = QSO(data)
        self.assertFalse(q.is_valid())

    def test_freq_instead_of_band(self):
        # The logic allows EITHER Band OR Freq. Test Freq only.
        data = {
            'CALL': 'W1AW',
            'QSO_DATE': '20230101',
            'TIME_ON': '120000',
            'FREQ': '14.000',
            'MODE': 'SSB'
        }
        q = QSO(data)
        self.assertTrue(q.is_valid())

    def test_normalization(self):
        # Test that lowercase input keys are converted to uppercase
        data = {'call': 'k1abc'} # lowercase key
        q = QSO(data)
        
        # Internal dictionary should have 'CALL'
        self.assertIn('CALL', q._d)
        self.assertEqual(q._d['CALL'], 'k1abc')

if __name__ == '__main__':
    unittest.main()