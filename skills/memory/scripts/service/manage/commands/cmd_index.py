"""rebuild-index / doctor 子命令"""
import sys
import os
import json
import glob

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.."))

from service.config import get_config
from service.config import INDEX_DB
from storage.jsonl import read_jsonl

from ._helpers import _json_out, _paths, _sync_index


def cmd_rebuild_index(args):
    project_path = args.project_path
    synced = _sync_index(project_path, full=args.full)
    if synced:
        _json_out("ok", "rebuild-index", {"full": args.full, "success": True})
    else:
        _json_out("error", "rebuild-index", error={"code": "SYNC_FAILED", "message": "索引同步失败"})
        sys.exit(4)


def cmd_doctor(args):
    project_path = args.project_path
    memory_dir, daily_dir, sessions_path = _paths(project_path)

    checks = []

    jsonl_total = 0
    jsonl_errors = 0
    all_ids = []
    if os.path.isdir(daily_dir):
        for fpath in sorted(glob.glob(os.path.join(daily_dir, "*.jsonl"))):
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    jsonl_total += 1
                    try:
                        e = json.loads(line)
                        if "id" in e:
                            all_ids.append(e["id"])
                    except json.JSONDecodeError:
                        jsonl_errors += 1

    if os.path.isfile(sessions_path):
        with open(sessions_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                jsonl_total += 1
                try:
                    e = json.loads(line)
                    if "id" in e:
                        all_ids.append(e["id"])
                except json.JSONDecodeError:
                    jsonl_errors += 1

    checks.append({
        "name": "JSONL 可解析性",
        "status": "pass" if jsonl_errors == 0 else "fail",
        "detail": f"{jsonl_total} 条, {jsonl_errors} 解析错误" if jsonl_errors else f"{jsonl_total} 条全部有效",
    })

    dup_ids = len(all_ids) - len(set(all_ids))
    dup_pct = round(dup_ids / max(len(all_ids), 1) * 100, 1)
    checks.append({
        "name": "ID 唯一性",
        "status": "pass" if dup_pct < 1 else "warn",
        "detail": f"{len(set(all_ids))} 个 ID, {dup_ids} 重复 ({dup_pct}%)" if dup_ids else f"{len(set(all_ids))} 个 ID 无重复",
    })

    idx_path = os.path.join(memory_dir, INDEX_DB)
    if os.path.isfile(idx_path):
        try:
            import sqlite3
            conn = sqlite3.connect(idx_path)
            chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            conn.close()
            checks.append({"name": "SQLite 可访问", "status": "pass", "detail": f"{chunk_count} 个 chunks"})
        except Exception as ex:
            checks.append({"name": "SQLite 可访问", "status": "fail", "detail": str(ex)})
    else:
        checks.append({"name": "SQLite 可访问", "status": "warn", "detail": "index.sqlite 不存在"})

    if os.path.isfile(idx_path):
        try:
            import sqlite3
            conn = sqlite3.connect(idx_path)
            row = conn.execute("SELECT value FROM meta WHERE key='last_sync'").fetchone()
            conn.close()
            if row:
                idx_mtime = os.path.getmtime(idx_path)
                newest_jsonl = 0
                if os.path.isdir(daily_dir):
                    for fpath in glob.glob(os.path.join(daily_dir, "*.jsonl")):
                        newest_jsonl = max(newest_jsonl, os.path.getmtime(fpath))
                lag = int(newest_jsonl - idx_mtime) if newest_jsonl > idx_mtime else 0
                lag_min = lag // 60
                checks.append({
                    "name": "索引时效性",
                    "status": "warn" if lag_min > 10 else "pass",
                    "detail": f"滞后 {lag_min} 分钟" if lag_min > 0 else "索引是最新的",
                })
            else:
                checks.append({"name": "索引时效性", "status": "warn", "detail": "无 last_sync 记录"})
        except Exception:
            pass

    cfg = get_config(project_path)
    cache_dir = os.path.expanduser(cfg.get("embedding.cache_dir"))
    model_name = cfg.get("embedding.model")
    cache_dir_name = "models--" + model_name.replace("/", "--")
    model_exists = os.path.isdir(os.path.join(cache_dir, cache_dir_name))
    checks.append({
        "name": "模型缓存",
        "status": "pass" if model_exists else "warn",
        "detail": f"{model_name} {'存在' if model_exists else '不存在'}",
    })

    daily_counts = {}
    if os.path.isdir(daily_dir):
        for fpath in sorted(glob.glob(os.path.join(daily_dir, "*.jsonl"))):
            day = os.path.basename(fpath).replace(".jsonl", "")
            daily_counts[day] = len(read_jsonl(fpath))
    max_daily = max(daily_counts.values()) if daily_counts else 0
    checks.append({
        "name": "单日写入异常",
        "status": "warn" if max_daily > 100 else "pass",
        "detail": f"最大单日 {max_daily} 条" + (", 可能异常" if max_daily > 100 else ""),
    })

    summary = {"pass": 0, "warn": 0, "fail": 0}
    for c in checks:
        summary[c["status"]] = summary.get(c["status"], 0) + 1

    _json_out("ok", "doctor", {"checks": checks, "summary": summary})
