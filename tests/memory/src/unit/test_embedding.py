#!/usr/bin/env python3
"""core/embedding.py 单元测试。

嵌入模型可能未安装，测试需要处理降级情况。
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skills", "memory-skill", "scripts"))

from core.embedding import is_available, embed_text, embed_batch, get_dimensions


class EmbeddingTests(unittest.TestCase):

    def test_is_available_returns_bool(self):
        result = is_available()
        self.assertIsInstance(result, bool)

    @unittest.skipUnless(is_available(), "嵌入模型未安装")
    def test_embed_text_returns_float_list(self):
        vec = embed_text("测试文本")
        self.assertIsInstance(vec, list)
        self.assertTrue(len(vec) > 0)
        self.assertIsInstance(vec[0], float)

    @unittest.skipUnless(is_available(), "嵌入模型未安装")
    def test_embed_batch_returns_list_of_vectors(self):
        texts = ["文本一", "文本二", "文本三"]
        vecs = embed_batch(texts)
        self.assertIsInstance(vecs, list)
        self.assertEqual(len(vecs), 3)
        self.assertEqual(len(vecs[0]), len(vecs[1]))

    @unittest.skipUnless(is_available(), "嵌入模型未安装")
    def test_get_dimensions_positive(self):
        dim = get_dimensions()
        self.assertGreater(dim, 0)

    def test_embed_text_unavailable_returns_none(self):
        if is_available():
            self.skipTest("模型已安装，跳过降级测试")
        result = embed_text("test")
        self.assertIsNone(result)

    def test_get_dimensions_unavailable_returns_zero(self):
        if is_available():
            self.skipTest("模型已安装，跳过降级测试")
        self.assertEqual(get_dimensions(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
