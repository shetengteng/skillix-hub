#!/usr/bin/env python3
"""
Behavior Prediction Skill - 会话结束处理

会话结束时的批量处理，包括补充遗漏的记录和更新统计。

注意：由于实时记录已经保证了数据完整性，会话结束处理是可选的。
即使没有执行，数据也是完整的。
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    DATA_DIR, ensure_data_dirs, load_json, save_json,
    get_today, get_timestamp, load_transition_matrix,
    save_transition_matrix
)


def finalize_session(session_data: dict) -> dict:
    """
    会话结束时的处理
    
    Args:
        session_data: {
            "actions_summary": [
                {"type": "create_file", "tool": "Write", ...},
                ...
            ],
            "start_time": "会话开始时间",
            "end_time": "会话结束时间"
        }
    
    Returns:
        {"status": "success|error", ...}
    """
    try:
        ensure_data_dirs()
        
        actions_summary = session_data.get("actions_summary", [])
        
        if not actions_summary:
            return {
                "status": "success",
                "message": "No actions to process",
                "actions_count": 0
            }
        
        # 1. 补充遗漏的动作记录
        supplemented = supplement_missing_actions(actions_summary)
        
        # 2. 更新转移矩阵（基于完整序列，权重较低避免重复计数）
        update_transitions_from_sequence(actions_summary)
        
        # 3. 记录会话统计
        record_session_stats(session_data, len(actions_summary))
        
        return {
            "status": "success",
            "actions_count": len(actions_summary),
            "supplemented": supplemented,
            "message": f"Session finalized with {len(actions_summary)} actions"
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def supplement_missing_actions(actions_summary: list) -> int:
    """
    补充遗漏的动作记录
    
    Args:
        actions_summary: 会话中的动作列表
    
    Returns:
        补充的动作数量
    """
    today = get_today()
    log_file = DATA_DIR / "actions" / f"{today}.json"
    
    existing = load_json(log_file, {"date": today, "actions": []})
    
    # 收集已记录的动作（通过类型+工具组合识别）
    existing_signatures = set()
    for action in existing.get("actions", []):
        sig = f"{action.get('type', '')}:{action.get('tool', '')}"
        existing_signatures.add(sig)
    
    supplemented = 0
    
    for action in actions_summary:
        action_type = action.get("type", "")
        tool = action.get("tool", "")
        
        if not action_type:
            continue
        
        sig = f"{action_type}:{tool}"
        
        # 简单检查：如果这个组合不在已记录中，补充记录
        # 注意：这是简化的检查，实际可能需要更精细的逻辑
        if sig not in existing_signatures:
            action_record = {
                "id": f"{today}-{len(existing['actions']) + 1:03d}",
                "type": action_type,
                "tool": tool,
                "timestamp": get_timestamp(),
                "details": action.get("details", {}),
                "source": "session_finalize"  # 标记来源
            }
            existing["actions"].append(action_record)
            existing_signatures.add(sig)
            supplemented += 1
    
    if supplemented > 0:
        save_json(log_file, existing)
    
    return supplemented


def update_transitions_from_sequence(actions: list):
    """
    根据动作序列更新转移矩阵
    
    注意：使用较低的权重（0.5）避免与实时记录重复计数
    
    Args:
        actions: 动作列表
    """
    if len(actions) < 2:
        return
    
    matrix = load_transition_matrix()
    
    # 遍历序列，更新转移
    for i in range(len(actions) - 1):
        from_action = actions[i].get("type", "unknown")
        to_action = actions[i + 1].get("type", "unknown")
        
        if from_action == "unknown" or to_action == "unknown":
            continue
        
        if from_action not in matrix["matrix"]:
            matrix["matrix"][from_action] = {}
        
        if to_action not in matrix["matrix"][from_action]:
            matrix["matrix"][from_action][to_action] = {"count": 0}
        
        # 会话结束时的更新权重较低（0.5），避免与实时记录重复计数
        matrix["matrix"][from_action][to_action]["count"] += 0.5
        matrix["total_transitions"] = matrix.get("total_transitions", 0) + 0.5
    
    # 重新计算所有概率
    for from_action in matrix["matrix"]:
        total = sum(t["count"] for t in matrix["matrix"][from_action].values())
        if total > 0:
            for action, data in matrix["matrix"][from_action].items():
                data["probability"] = round(data["count"] / total, 3)
    
    save_transition_matrix(matrix)


def record_session_stats(session_data: dict, actions_count: int):
    """
    记录会话统计信息
    
    Args:
        session_data: 会话数据
        actions_count: 动作数量
    """
    stats_file = DATA_DIR / "stats" / "sessions.json"
    
    stats = load_json(stats_file, {
        "sessions": [],
        "total_sessions": 0
    })
    
    # 提取动作类型
    action_types = list(set(
        a.get("type", "unknown")
        for a in session_data.get("actions_summary", [])
        if a.get("type")
    ))
    
    session_record = {
        "date": get_today(),
        "time": datetime.now().strftime("%H:%M:%S"),
        "actions_count": actions_count,
        "action_types": action_types,
        "start_time": session_data.get("start_time", ""),
        "end_time": session_data.get("end_time", get_timestamp())
    }
    
    stats["sessions"].append(session_record)
    stats["total_sessions"] += 1
    
    # 只保留最近 100 条会话记录
    if len(stats["sessions"]) > 100:
        stats["sessions"] = stats["sessions"][-100:]
    
    save_json(stats_file, stats)


def main():
    """主函数：处理命令行输入"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Missing session data. Usage: finalize_session.py '{\"actions_summary\": [...]}'"
        }))
        sys.exit(1)
    
    try:
        session_data = json.loads(sys.argv[1])
        result = finalize_session(session_data)
        print(json.dumps(result, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(json.dumps({
            "status": "error",
            "message": f"Invalid JSON: {e}"
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
