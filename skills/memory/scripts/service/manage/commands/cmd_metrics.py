"""metrics 子命令：统计 Memory Save 各层命中率"""
import os
import json
import glob
from datetime import timedelta

from ._helpers import _json_out, _paths
from core.utils import utcnow, parse_iso


def cmd_metrics(args):
    memory_dir, daily_dir, _ = _paths(args.project_path)
    days = getattr(args, "days", 7) or 7

    if not os.path.isdir(daily_dir):
        _json_out("ok", "metrics", data={"error": "daily 目录不存在"})
        return

    cutoff = utcnow() - timedelta(days=days)

    layer_counts = {
        "layer1_rules": 0,
        "layer2_precompact": 0,
        "layer3_auto": 0,
        "layer4_stop": 0,
        "none": 0,
    }
    total_sessions = 0
    duplicates_blocked = 0

    for fpath in sorted(glob.glob(os.path.join(daily_dir, "*.jsonl"))):
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ts = parse_iso(entry.get("timestamp", ""))
                if ts < cutoff:
                    continue

                if entry.get("type") == "session_metrics":
                    total_sessions += 1
                    source = entry.get("summary_source", "none")
                    if source in layer_counts:
                        layer_counts[source] += 1
                    else:
                        layer_counts["none"] += 1

    summary = {
        "days": days,
        "total_sessions": total_sessions,
        "layers": layer_counts,
    }

    if total_sessions > 0:
        summary["stop_hook_rate"] = round(layer_counts["layer4_stop"] / total_sessions * 100, 1)
        summary["layer1_rate"] = round(layer_counts["layer1_rules"] / total_sessions * 100, 1)
        summary["auto_generate_rate"] = round(layer_counts["layer3_auto"] / total_sessions * 100, 1)

    _json_out("ok", "metrics", data=summary)
