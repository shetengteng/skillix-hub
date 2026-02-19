#!/usr/bin/env python3
"""chunk 切分策略测试。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from test_common import IsolatedWorkspaceCase
from storage.chunker import chunk_markdown


class DetailChunkTests(IsolatedWorkspaceCase):
    def test_chunk_short_and_empty(self):
        self.assertEqual(len(chunk_markdown("Short text")), 1)
        self.assertEqual(len(chunk_markdown("")), 0)

    def test_chunk_long_and_heading_split(self):
        long_text = "## A\n" + ("word " * 500) + "\n## B\n" + ("word " * 500)
        chunks = chunk_markdown(long_text)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(c.strip() for c in chunks))

        heading_text = "## A\nContent A\n## B\nContent B\n## C\nContent C"
        heading_chunks = chunk_markdown(heading_text)
        self.assertGreaterEqual(len(heading_chunks), 3)
        self.assertTrue(heading_chunks[1].startswith("## "))


if __name__ == "__main__":
    import unittest

    unittest.main(verbosity=2)
