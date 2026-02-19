#!/usr/bin/env python3
"""service/manage/commands/_helpers.py 单元测试。"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skills", "memory-skill", "scripts"))

from service.manage.commands._helpers import _parse_value, _all_dotpaths


class HelpersTests(unittest.TestCase):

    def test_parse_value_bool_true(self):
        self.assertIs(_parse_value("true"), True)
        self.assertIs(_parse_value("True"), True)
        self.assertIs(_parse_value("TRUE"), True)

    def test_parse_value_bool_false(self):
        self.assertIs(_parse_value("false"), False)

    def test_parse_value_int(self):
        self.assertEqual(_parse_value("42"), 42)
        self.assertEqual(_parse_value("0"), 0)
        self.assertEqual(_parse_value("-5"), -5)

    def test_parse_value_float(self):
        self.assertAlmostEqual(_parse_value("3.14"), 3.14)

    def test_parse_value_string(self):
        self.assertEqual(_parse_value("hello"), "hello")
        self.assertEqual(_parse_value(""), "")

    def test_all_dotpaths_flat(self):
        d = {"a": 1, "b": 2}
        paths = _all_dotpaths(d)
        self.assertEqual(sorted(paths), ["a", "b"])

    def test_all_dotpaths_nested(self):
        d = {"memory": {"facts_limit": 20, "decay": {"window_days": 7}}}
        paths = _all_dotpaths(d)
        self.assertIn("memory.facts_limit", paths)
        self.assertIn("memory.decay.window_days", paths)

    def test_all_dotpaths_empty(self):
        self.assertEqual(_all_dotpaths({}), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
