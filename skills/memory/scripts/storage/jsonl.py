"""
JSONL 文件读写工具

负责读取 .jsonl 文件（每行一个 JSON 对象），并实现按时间衰减的记忆加载策略。
"""
import json
import os
from datetime import timedelta
from core.utils import utcnow, parse_iso
from service.config import _DEFAULTS

_M = _DEFAULTS["memory"]
LOAD_DAYS_FULL = _M["load_days_full"]
LOAD_DAYS_PARTIAL = _M["load_days_partial"]
LOAD_DAYS_MAX = _M["load_days_max"]
LOAD_PARTIAL_PER_DAY = _M["partial_per_day"]
LOAD_IMPORTANT_CONFIDENCE = _M["important_confidence"]
LOAD_FACTS_LIMIT = _M["facts_limit"]


def read_jsonl(filepath: str) -> list:
    """读取整个 JSONL 文件，跳过空行和解析失败的行"""
    if not os.path.exists(filepath):
        return []
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def read_last_entry(filepath: str):
    """读取 JSONL 文件的最后一条未删除记录"""
    if not os.path.exists(filepath):
        return None
    last = None
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entry = json.loads(line)
                    if not entry.get("deleted_at"):
                        last = entry
                except json.JSONDecodeError:
                    continue
    return last


def read_daily_facts(daily_dir: str) -> list:
    """
    读取 daily/ 目录下所有 .jsonl 文件，合并返回 type=fact 的条目。
    按时间降序排列。
    """
    import glob
    if not os.path.isdir(daily_dir):
        return []
    all_entries = []
    for fpath in sorted(glob.glob(os.path.join(daily_dir, "*.jsonl"))):
        for entry in read_jsonl(fpath):
            if entry.get("deleted_at"):
                continue
            if entry.get("type") in ("fact", None):
                if "content" in entry:
                    all_entries.append(entry)
    all_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return all_entries


def read_recent_facts_from_daily(daily_dir: str) -> list:
    """
    从 daily/ 目录读取事实并应用衰减策略（近多远少）。
    这是 load_memory.py 的主要事实来源。
    """
    all_facts = read_daily_facts(daily_dir)
    if not all_facts:
        return []
    return _apply_decay(all_facts)


def _apply_decay(entries: list) -> list:
    """对事实列表应用衰减策略，返回筛选后的结果"""
    now = utcnow()
    full_cutoff = now - timedelta(days=LOAD_DAYS_FULL)
    partial_cutoff = now - timedelta(days=LOAD_DAYS_PARTIAL)
    max_cutoff = now - timedelta(days=LOAD_DAYS_MAX)

    full_items = []
    partial_buckets = {}
    important_items = []

    for e in entries:
        ts = parse_iso(e.get("timestamp", "") or e.get("created_at", ""))
        if ts < max_cutoff:
            continue
        if ts >= full_cutoff:
            full_items.append(e)
        elif ts >= partial_cutoff:
            day = ts.strftime("%Y-%m-%d")
            partial_buckets.setdefault(day, []).append(e)
        else:
            if e.get("confidence", 0) >= LOAD_IMPORTANT_CONFIDENCE:
                important_items.append(e)

    partial_items = []
    for day_entries in partial_buckets.values():
        partial_items.extend(day_entries[-LOAD_PARTIAL_PER_DAY:])

    result = full_items + partial_items + important_items
    result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return result[:LOAD_FACTS_LIMIT]


def read_recent_facts(filepath: str) -> list:
    """
    按衰减策略读取事实：近多远少

    加载规则：
    - 最近 LOAD_DAYS_FULL 天：全部加载
    - LOAD_DAYS_FULL ~ LOAD_DAYS_PARTIAL 天前：每天最多 LOAD_PARTIAL_PER_DAY 条
    - LOAD_DAYS_PARTIAL ~ LOAD_DAYS_MAX 天前：只加载高置信度(≥0.9)的条目
    - LOAD_DAYS_MAX 天前：完全不加载
    - 最终结果按时间降序排列，上限 LOAD_FACTS_LIMIT 条
    """
    entries = read_jsonl(filepath)
    if not entries:
        return []

    now = utcnow()
    full_cutoff = now - timedelta(days=LOAD_DAYS_FULL)
    partial_cutoff = now - timedelta(days=LOAD_DAYS_PARTIAL)
    max_cutoff = now - timedelta(days=LOAD_DAYS_MAX)

    full_items = []           # 最近 N 天内：全量
    partial_buckets = {}      # N~M 天前：按天分桶
    important_items = []      # M~K 天前：只保留高置信度

    for e in entries:
        ts = parse_iso(e.get("timestamp", "") or e.get("created_at", ""))
        if ts < max_cutoff:
            continue
        if ts >= full_cutoff:
            full_items.append(e)
        elif ts >= partial_cutoff:
            day = ts.strftime("%Y-%m-%d")
            partial_buckets.setdefault(day, []).append(e)
        else:
            if e.get("confidence", 0) >= LOAD_IMPORTANT_CONFIDENCE:
                important_items.append(e)

    # 从每天的桶中取最新 N 条（文件追加写入，后面的更新）
    partial_items = []
    for day_entries in partial_buckets.values():
        partial_items.extend(day_entries[-LOAD_PARTIAL_PER_DAY:])

    # 合并、排序、截断
    result = full_items + partial_items + important_items
    result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return result[:LOAD_FACTS_LIMIT]
