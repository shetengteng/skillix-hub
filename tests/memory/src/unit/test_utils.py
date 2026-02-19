#!/usr/bin/env python3
"""core/utils.py 单元测试。"""
import sys
import os
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skills", "memory-skill", "scripts"))

from core.utils import utcnow, iso_now, today_str, ts_id, date_range, parse_iso


class UtilsTests(unittest.TestCase):

    def test_utcnow_returns_utc_datetime(self):
        now = utcnow()
        self.assertIsInstance(now, datetime)
        self.assertEqual(now.tzinfo, timezone.utc)

    def test_iso_now_format(self):
        result = iso_now()
        self.assertRegex(result, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_today_str_format(self):
        result = today_str()
        self.assertRegex(result, r"^\d{4}-\d{2}-\d{2}$")

    def test_ts_id_format_and_uniqueness(self):
        ids = [ts_id() for _ in range(100)]
        self.assertEqual(len(set(ids)), 100, "ts_id should produce unique values")
        for i in ids:
            self.assertRegex(i, r"^\d{9}-[a-z0-9]{4}$")

    def test_date_range_returns_correct_count(self):
        result = date_range(3)
        self.assertEqual(len(result), 3)
        for d in result:
            self.assertRegex(d, r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(result[0], today_str())

    def test_date_range_zero_returns_empty(self):
        self.assertEqual(date_range(0), [])

    def test_parse_iso_valid(self):
        dt_obj = parse_iso("2026-02-18T14:30:00Z")
        self.assertEqual(dt_obj.year, 2026)
        self.assertEqual(dt_obj.month, 2)
        self.assertEqual(dt_obj.hour, 14)
        self.assertEqual(dt_obj.tzinfo, timezone.utc)

    def test_parse_iso_without_z(self):
        dt_obj = parse_iso("2026-02-18T14:30:00")
        self.assertEqual(dt_obj.year, 2026)

    def test_parse_iso_invalid_returns_min(self):
        dt_obj = parse_iso("not-a-date")
        self.assertEqual(dt_obj, datetime.min.replace(tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main(verbosity=2)
