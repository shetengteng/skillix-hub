#!/usr/bin/env python3
"""
JSONL → SQLite 增量同步：将 MEMORY.md、facts.jsonl、sessions.jsonl、daily/*.jsonl
同步到 index.sqlite，生成 FTS 全文索引和可选向量嵌入，供 search_memory 检索。

使用场景：安装后或定期执行，支持 --rebuild 全量重建。
"""
import sys
import os
import json
import glob

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

import argparse

from service.config import MEMORY_MD, FACTS_FILE, SESSIONS_FILE, INDEX_DB, DAILY_DIR_NAME, _DEFAULTS
from service.config import get_memory_dir
from storage.sqlite_store import SQLiteStore
from storage.chunker import chunk_markdown
from storage.jsonl import read_jsonl
from core.utils import iso_now
from core.embedding import is_available as embedding_is_available
from service.logger import get_logger, redirect_to_project

log = get_logger("sync")


def get_file_mtime(path):
    """获取文件修改时间戳，失败返回 0。"""
    try:
        return int(os.path.getmtime(path))
    except OSError:
        return 0


def sync_file(store, memory_dir, rel_path, full_path):
    """
    增量同步单个 JSONL 文件到 SQLite。根据 mtime 和 last_line 跳过已同步内容。

    Returns:
        本次新增的 chunk 数量
    """
    mtime = get_file_mtime(full_path)
    state = store.get_sync_state(rel_path)

    if state and state["mtime"] == mtime:
        return 0

    start_line = state["last_line"] if state else 0
    entries = read_jsonl(full_path)
    new_entries = entries[start_line:]

    if not new_entries:
        store.update_sync_state(rel_path, len(entries), "", mtime)
        return 0

    emb_func = _get_embed_func()
    count = 0
    for entry in new_entries:
        # session_start 无实质内容，跳过
        if entry.get("type") == "session_start":
            continue
        content = entry.get("content") or entry.get("summary", "")
        if not content:
            continue

        embedding = emb_func(content) if emb_func else None
        store.upsert_chunk(
            chunk_id=entry.get("id", f"{rel_path}-{start_line + count}"),
            content=content,
            chunk_type=entry.get("type", "fact"),
            memory_type=entry.get("memory_type"),
            entities=json.dumps(entry.get("entities", []), ensure_ascii=False),
            confidence=entry.get("confidence", 0.8),
            source_file=rel_path,
            source_id=entry.get("id"),
            timestamp=entry.get("timestamp", ""),
            embedding=embedding,
        )
        count += 1

    last_id = new_entries[-1].get("id", "") if new_entries else ""
    store.update_sync_state(rel_path, len(entries), last_id, mtime)
    return count


def sync_memory_md(store, memory_dir):
    """
    将 MEMORY.md 切块后同步到 SQLite，chunk_type 为 core。
    根据 mtime 判断是否需要重新同步。
    """
    md_path = os.path.join(memory_dir, MEMORY_MD)
    if not os.path.exists(md_path):
        return 0

    mtime = get_file_mtime(md_path)
    state = store.get_sync_state(MEMORY_MD)
    if state and state["mtime"] == mtime:
        return 0

    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return 0

    chunks = chunk_markdown(text)
    emb_func = _get_embed_func()
    count = 0
    for i, chunk in enumerate(chunks):
        embedding = emb_func(chunk) if emb_func else None
        store.upsert_chunk(
            chunk_id=f"core-{i}",
            content=chunk,
            chunk_type="core",
            source_file=MEMORY_MD,
            timestamp="",
            embedding=embedding,
        )
        count += 1

    store.update_sync_state(MEMORY_MD, 0, "", mtime)
    return count


def _get_embed_func():
    """获取嵌入函数，若 sentence-transformers 不可用则返回 None。"""
    try:
        from core.embedding import embed_text, is_available
        if is_available():
            log.info("嵌入模型可用，将生成向量索引")
            return embed_text
        else:
            log.warning("嵌入模型不可用，仅建立 FTS 索引")
    except Exception as e:
        log.warning("嵌入模块加载异常: %s", e)
    return None


def sync_all(memory_dir, rebuild=False):
    """
    同步所有记忆源到 SQLite：facts、sessions、daily/*.jsonl、MEMORY.md。

    Args:
        memory_dir: 记忆数据根目录
        rebuild: 若为 True，先删除旧索引再全量重建
    Returns:
        本次新增的 chunk 总数
    """
    db_path = os.path.join(memory_dir, INDEX_DB)

    if rebuild and os.path.exists(db_path):
        log.info("重建模式：删除旧索引 %s", db_path)
        os.remove(db_path)

    log.info("开始同步 %s", memory_dir)
    store = SQLiteStore(db_path)
    total = 0

    facts_path = os.path.join(memory_dir, FACTS_FILE)
    if os.path.exists(facts_path):
        total += sync_file(store, memory_dir, FACTS_FILE, facts_path)

    sessions_path = os.path.join(memory_dir, SESSIONS_FILE)
    if os.path.exists(sessions_path):
        total += sync_file(store, memory_dir, SESSIONS_FILE, sessions_path)

    daily_dir = os.path.join(memory_dir, DAILY_DIR_NAME)
    if os.path.isdir(daily_dir):
        # 按文件名排序，保证日期顺序
        for fpath in sorted(glob.glob(os.path.join(daily_dir, "*.jsonl"))):
            rel = os.path.join(DAILY_DIR_NAME, os.path.basename(fpath))
            total += sync_file(store, memory_dir, rel, fpath)

    total += sync_memory_md(store, memory_dir)

    total_chunks = store.count_chunks()
    store.set_meta("total_chunks", total_chunks)
    store.set_meta("last_sync", iso_now())
    if embedding_is_available():
        store.set_meta("embedding_model", _DEFAULTS["embedding"]["model"])

    store.close()
    log.info("同步完成: 本次新增 %d 条, 总计 %d 条 chunk", total, total_chunks)
    return total


def main():
    """CLI 入口：解析 --rebuild、--project-path，执行 sync_all。"""
    parser = argparse.ArgumentParser(description="Sync JSONL → SQLite")
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--project-path", default=os.getcwd())
    args = parser.parse_args()

    redirect_to_project(args.project_path)

    memory_dir = os.path.join(args.project_path, ".cursor", "skills", "memory-data")
    if not os.path.isdir(memory_dir):
        print(f"Memory directory not found: {memory_dir}", file=sys.stderr)
        sys.exit(1)

    total = sync_all(memory_dir, rebuild=args.rebuild)
    print(f"Sync complete: {total} entries processed, "
          f"DB: {os.path.join(memory_dir, INDEX_DB)}")


if __name__ == "__main__":
    main()
