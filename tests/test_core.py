"""
Unit tests for core functions and downloader utilities
"""

import unittest
from core.utils import parse_time_to_seconds, format_seconds_to_time, format_bytes, sanitize_filename
from core.config import load_config, save_config


class TestCoreUtils(unittest.TestCase):
    def test_parse_time_to_seconds(self):
        # Standard formats
        self.assertEqual(parse_time_to_seconds("00:00:00"), 0)
        self.assertEqual(parse_time_to_seconds("00:01:30"), 90)
        self.assertEqual(parse_time_to_seconds("01:30:15"), 5415)
        self.assertEqual(parse_time_to_seconds("15:00"), 900)
        self.assertEqual(parse_time_to_seconds("45"), 45)
        
        # Word formats
        self.assertEqual(parse_time_to_seconds("1h30m"), 5400)
        self.assertEqual(parse_time_to_seconds("45m"), 2700)
        self.assertEqual(parse_time_to_seconds("30s"), 30)

        # Empty / None
        self.assertIsNone(parse_time_to_seconds(""))
        self.assertIsNone(parse_time_to_seconds(None))
        self.assertIsNone(parse_time_to_seconds("invalid"))

    def test_format_seconds_to_time(self):
        self.assertEqual(format_seconds_to_time(0), "00:00:00")
        self.assertEqual(format_seconds_to_time(90), "00:01:30")
        self.assertEqual(format_seconds_to_time(3665), "01:01:05")
        self.assertEqual(format_seconds_to_time(None), "00:00:00")

    def test_format_bytes(self):
        self.assertEqual(format_bytes(0), "0 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1048576), "1.00 MB")
        self.assertEqual(format_bytes(1073741824), "1.00 GB")

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("Livestream 2026/09/24 <Test>: Good?"), "Livestream 2026_09_24 _Test_ Good_")


class TestConfig(unittest.TestCase):
    def test_load_and_save_config(self):
        cfg = load_config()
        self.assertIn("format", cfg)
        self.assertIn("concurrent_fragments", cfg)


if __name__ == "__main__":
    unittest.main()
