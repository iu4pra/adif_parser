#!/usr/bin/python3

# This software under the MIT License
# Unit test for ADIF parser

import unittest
import adif
from qso import QSO

class TestAdifParser(unittest.TestCase):

    def test_empty_string(self):
        """Empty strings return no fields"""
        self.assertEqual(adif.parse_adif_string(""), [])
        self.assertEqual(adif.parse_adif_string("\0"), [])
        self.assertEqual(adif.parse_adif_string("\0" * 3), [])

    def test_newline(self):
        """String with only newlines return no fields"""
        self.assertEqual(adif.parse_adif_string("\n"), [])
        self.assertEqual(adif.parse_adif_string("\n" * 3), [])

    def test_blank_string(self):
        """String with only whitespaces return no fields"""
        self.assertEqual(adif.parse_adif_string(" "), [])
        self.assertEqual(adif.parse_adif_string(" " * 5), [])

    def test_string_without_fields(self):
        """String with no valid fields"""
        _test_string = """QRZLogbook download for iu4pra
    Date: Mon Oct  6 11:30:36 2025
    Bookid: 312206
    Records: 200"""
        self.assertEqual(adif.parse_adif_string(_test_string), [])

    def test_single_field(self):
        """Parse a single, well formatted field"""
        self.assertEqual(
            adif.parse_adif_string("<CALL:6>IK4XYZ"),
            [{"field": "CALL", "len": 6, "type": None, "value": "IK4XYZ"}],
        )

    def test_check_field_case_1(self):
        field = adif.parse_adif_string("<CALL:6>IK4XYZ")[0]
        field.pop("field")
        with self.assertRaises(adif.AdifError):
            adif.check_field(field)

    def test_check_field_case_2(self):
        field = adif.parse_adif_string("<CALL:6>IK4XYZ")[0]
        field.pop("len")
        with self.assertRaises(adif.AdifError):
            adif.check_field(field)

    def test_check_field_case_3(self):
        field = adif.parse_adif_string("<CALL:6>IK4XYZ")[0]
        field["len"] = 0
        with self.assertRaises(adif.AdifError):
            adif.check_field(field)

    def test_check_field_case_4(self):
        field = adif.parse_adif_string("<CALL:6>IK4XYZ")[0]
        field["len"] = -1
        with self.assertRaises(adif.AdifError):
            adif.check_field(field)

    def test_check_field_case_5(self):
        field = adif.parse_adif_string("<CALL:6>IK4XYZ")[0]
        field["len"] = "0"
        with self.assertRaises(adif.AdifError):
            adif.check_field(field)

    def test_check_field_case_6(self):
        field = adif.parse_adif_string("<CALL:6>IK4XYZ")[0]
        field["len"] = 7
        with self.assertRaises(adif.AdifError):
            adif.check_field(field)

    def test_single_field_with_blanks(self):
        """Parse a single, well formatted field with extra whitespaces"""
        self.assertEqual(
            adif.parse_adif_string("<CALL:6>IK4XYZ  "),
            [{"field": "CALL", "len": 6, "type": None, "value": "IK4XYZ"}],
        )

    def test_single_field_with_extra(self):
        """Parse a single, well formatted field with extra characters"""
        self.assertEqual(
            adif.parse_adif_string("<CALL:6>IK4XYZABC"),
            [{"field": "CALL", "len": 6, "type": None, "value": "IK4XYZ"}],
        )

    def test_single_field_with_type(self):
        """Parse a single, well formatted field with type identifier"""
        self.assertEqual(
            adif.parse_adif_string("<CALL:6:s>IK4XYZ"),
            [{"field": "CALL", "len": 6, "type": "s", "value": "IK4XYZ"}],
        )

    def test_single_field_wrong_type(self):
        self.assertEqual(adif.parse_adif_string("<:6>IK4XYZ"), [])

    def test_single_field_no_len(self):
        """Parse a single, well formatted field without length"""
        self.assertEqual(
            adif.parse_adif_string("<EOR>"),
            [{"field": "EOR", "len": 0, "type": None, "value": None}],
        )

    def test_single_field_wrong_len(self):
        """Parse a single field with a wrong length"""
        for i in range(-5, 1):
            with self.assertRaises(adif.AdifError):
                adif.parse_adif_string(f"<CALL:{i}>IK4XYZ")

    def test_single_field_invalid_len(self):
        """Parse a single field with a non-numeric length"""
        self.assertEqual(adif.parse_adif_string("<CALL:d>IK4XYZ"), [])

    def test_single_field_too_short(self):
        """Single field with insufficient data to fill the value field"""
        with self.assertRaises(adif.AdifError):
            adif.parse_adif_string("<CALL:6>IK4")
        with self.assertRaises(adif.AdifError):
            adif.parse_adif_string("<CALL:6:s>IK4")

    def test_parse_simple_string(self):
        # FIXED: Changed <CALL:5> to <CALL:4> so it matches "W1AW" exactly
        data = "<CALL:4>W1AW <EOR>"
        fields = adif.parse_adif_string(data)

        # Expecting 2 fields: CALL and EOR
        self.assertEqual(len(fields), 2)
        self.assertEqual(fields[0]["field"], "CALL")
        self.assertEqual(fields[0]["value"], "W1AW")  # Now this will match
        self.assertEqual(fields[1]["field"], "EOR")

    def test_parse_complex_types(self):
        # Testing fields with data types (e.g., <FREQ:6:N>)
        data = "<FREQ:6:N>14.074 <MODE:3>FT8 <EOR>"
        # Note: I also ensured MODE length matches "FT8" (3 chars)
        fields = adif.parse_adif_string(data)

        self.assertEqual(fields[0]["field"], "FREQ")
        self.assertEqual(fields[0]["value"], "14.074")
        self.assertEqual(fields[0]["type"], "N")  # Type check

    def test_header_stripping(self):
        # Test if the parser correctly removes the header
        data = "Generated by Logger32 <EOH><CALL:5>K1ABC <EOR>"
        fields = adif.parse_adif_string(data)

        # Let's test the specific remove_header function
        clean_fields, eoh_index = adif.remove_header(fields)

        # After stripping, only CALL and EOR should remain
        self.assertEqual(clean_fields[0]["field"], "CALL")
        self.assertEqual(clean_fields[1]["field"], "EOR")

    def test_qso_list_creation(self):
        # Test converting raw fields into a list of QSO objects
        # FIXED: Adjusted lengths to match data (3 chars for K1A and K2B)
        data = "<CALL:3>K1A <EOR> <CALL:3>K2B <EOR>"
        fields = adif.parse_adif_string(data)
        qso_list = adif.adif_to_qso_list(fields)

        self.assertEqual(len(qso_list), 2)
        self.assertEqual(qso_list[0]._d["CALL"], "K1A")
        self.assertEqual(qso_list[1]._d["CALL"], "K2B")

    def test_parse_non_file(self):
        with self.assertRaises(AssertionError):
            adif.parse_adif_file(None)

    def test_parse_not_existing_file(self):
        with self.assertRaises(AssertionError):
            adif.parse_adif_file("not_exists")

    def test_parse_existing_file(self):
        field_list = adif.parse_adif_file("samples/minimal_1qso.adi")
        self.assertEqual(len(field_list), 16)

    def test_qso_list_from_file(self):
        qso_list = adif.qso_list_from_file("samples/minimal_1qso.adi")
        assert isinstance(qso_list[0], QSO)
        self.assertEqual(len(qso_list), 1)

if __name__ == "__main__":
    unittest.main()
