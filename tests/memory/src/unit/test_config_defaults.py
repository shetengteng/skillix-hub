#!/usr/bin/env python3
"""config/defaults.py 工具函数单元测试"""
import sys
import os
import json
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skills", "memory", "scripts"))

from service.config.defaults import (
    _deep_merge, _get_dotpath, _set_dotpath,
    _load_json_file, _save_json_file, get_project_path,
)


class TestDeepMerge(unittest.TestCase):

    def test_simple_merge(self):
        base = {"a": 1, "b": 2}
        overlay = {"b": 3, "c": 4}
        result = _deep_merge(base, overlay)
        self.assertEqual(result, {"a": 1, "b": 3, "c": 4})

    def test_nested_merge(self):
        base = {"x": {"a": 1, "b": 2}, "y": 10}
        overlay = {"x": {"b": 99, "c": 3}}
        result = _deep_merge(base, overlay)
        self.assertEqual(result["x"], {"a": 1, "b": 99, "c": 3})
        self.assertEqual(result["y"], 10)

    def test_overlay_replaces_non_dict_with_dict(self):
        base = {"x": "string"}
        overlay = {"x": {"nested": True}}
        result = _deep_merge(base, overlay)
        self.assertEqual(result["x"], {"nested": True})

    def test_does_not_mutate_inputs(self):
        base = {"a": {"b": 1}}
        overlay = {"a": {"c": 2}}
        _deep_merge(base, overlay)
        self.assertNotIn("c", base["a"])

    def test_empty_overlay(self):
        base = {"a": 1}
        result = _deep_merge(base, {})
        self.assertEqual(result, {"a": 1})

    def test_empty_base(self):
        result = _deep_merge({}, {"a": 1})
        self.assertEqual(result, {"a": 1})

    def test_deeply_nested(self):
        base = {"l1": {"l2": {"l3": {"val": "old"}}}}
        overlay = {"l1": {"l2": {"l3": {"val": "new", "extra": True}}}}
        result = _deep_merge(base, overlay)
        self.assertEqual(result["l1"]["l2"]["l3"]["val"], "new")
        self.assertTrue(result["l1"]["l2"]["l3"]["extra"])


class TestGetDotpath(unittest.TestCase):

    def test_single_level(self):
        self.assertEqual(_get_dotpath({"a": 1}, "a"), 1)

    def test_nested(self):
        d = {"memory": {"facts_limit": 15}}
        self.assertEqual(_get_dotpath(d, "memory.facts_limit"), 15)

    def test_missing_returns_default(self):
        self.assertIsNone(_get_dotpath({}, "a.b.c"))
        self.assertEqual(_get_dotpath({}, "a.b", default=42), 42)

    def test_partial_path(self):
        d = {"a": {"b": 1}}
        self.assertIsNone(_get_dotpath(d, "a.b.c"))

    def test_non_dict_intermediate(self):
        d = {"a": "string"}
        self.assertIsNone(_get_dotpath(d, "a.b"))


class TestSetDotpath(unittest.TestCase):

    def test_single_level(self):
        d = {}
        _set_dotpath(d, "a", 1)
        self.assertEqual(d, {"a": 1})

    def test_nested(self):
        d = {}
        _set_dotpath(d, "a.b.c", 42)
        self.assertEqual(d["a"]["b"]["c"], 42)

    def test_overwrite_existing(self):
        d = {"a": {"b": 1}}
        _set_dotpath(d, "a.b", 99)
        self.assertEqual(d["a"]["b"], 99)

    def test_creates_intermediate_dicts(self):
        d = {"a": "not_a_dict"}
        _set_dotpath(d, "a.b", 1)
        self.assertEqual(d["a"]["b"], 1)


class TestLoadJsonFile(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_load_valid_json(self):
        path = os.path.join(self.tmpdir, "test.json")
        with open(path, "w") as f:
            json.dump({"key": "value"}, f)
        self.assertEqual(_load_json_file(path), {"key": "value"})

    def test_missing_file_returns_empty(self):
        self.assertEqual(_load_json_file("/nonexistent/path.json"), {})

    def test_invalid_json_returns_empty(self):
        path = os.path.join(self.tmpdir, "bad.json")
        with open(path, "w") as f:
            f.write("not json")
        self.assertEqual(_load_json_file(path), {})

    def test_non_dict_json_returns_empty(self):
        path = os.path.join(self.tmpdir, "array.json")
        with open(path, "w") as f:
            json.dump([1, 2, 3], f)
        self.assertEqual(_load_json_file(path), {})


class TestSaveJsonFile(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_reload(self):
        path = os.path.join(self.tmpdir, "out.json")
        data = {"version": 1, "name": "测试"}
        _save_json_file(path, data)
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded, data)

    def test_creates_parent_dirs(self):
        path = os.path.join(self.tmpdir, "a", "b", "c.json")
        _save_json_file(path, {"ok": True})
        self.assertTrue(os.path.isfile(path))

    def test_overwrites_existing(self):
        path = os.path.join(self.tmpdir, "overwrite.json")
        _save_json_file(path, {"v": 1})
        _save_json_file(path, {"v": 2})
        with open(path, "r") as f:
            self.assertEqual(json.load(f)["v"], 2)


class TestGetProjectPath(unittest.TestCase):

    def test_extracts_from_workspace_roots(self):
        event = {"workspace_roots": ["/home/user/project"]}
        self.assertEqual(get_project_path(event), "/home/user/project")

    def test_empty_roots_falls_back_to_cwd(self):
        event = {"workspace_roots": []}
        self.assertEqual(get_project_path(event), os.getcwd())

    def test_no_roots_key_falls_back_to_cwd(self):
        self.assertEqual(get_project_path({}), os.getcwd())

    def test_multiple_roots_uses_first(self):
        event = {"workspace_roots": ["/first", "/second"]}
        self.assertEqual(get_project_path(event), "/first")


if __name__ == "__main__":
    unittest.main(verbosity=2)
