"""
文本分块逻辑：将 Markdown 按标题和滑动窗口切分为 chunk。
"""
from service.config import _DEFAULTS

_IDX = _DEFAULTS["index"]


def chunk_markdown(text, max_tokens=_IDX["chunk_tokens"], overlap=_IDX["chunk_overlap"]):
    """
    将 Markdown 按 ## 标题切分，超长段落再按 max_chars 滑动窗口切块。

    Args:
        text: 原始 Markdown 文本
        max_tokens: 每块最大 token 数（近似）
        overlap: 块间重叠 token 数
    Returns:
        文本块列表
    """
    chars_per_token = 4
    max_chars = max_tokens * chars_per_token
    overlap_chars = overlap * chars_per_token

    # 先按 ## 二级标题切分
    sections = text.split("\n## ")
    if len(sections) <= 1 and len(text) <= max_chars:
        return [text.strip()] if text.strip() else []

    chunks = []
    for i, sec in enumerate(sections):
        sec = sec.strip()
        if not sec:
            continue
        if i > 0:
            sec = "## " + sec
        if len(sec) <= max_chars:
            chunks.append(sec)
        else:
            # 超长段落按滑动窗口切块，带重叠
            start = 0
            while start < len(sec):
                end = start + max_chars
                chunk = sec[start:end]
                if chunk.strip():
                    chunks.append(chunk.strip())
                start = end - overlap_chars
    return chunks
