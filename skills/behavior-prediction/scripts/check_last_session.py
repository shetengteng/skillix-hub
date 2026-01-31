#!/usr/bin/env python3
"""
Behavior Prediction Skill - 会话开始检查

检查上次会话是否正常结束，如果没有则补充处理。
这是一个兜底机制，确保数据完整性。

建议在每次新会话开始时调用。
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    DATA_DIR, ensure_data_dirs, load_json, save_json,
    get_today, get_timestamp, load_transition_matrix,
    save_transition_matrix
)


def check_last_session() -> dict:
    """
    检查上次会话是否正常结束
    
    Returns:
        {
            "status": "success",
            "action": "none|processed|recalculated",
            "reason": "..."
        }
    """
    try:
        ensure_data_dirs()
        
        stats_file = DATA_DIR / "stats" / "sessions.json"
        stats = load_json(stats_file, {
            "sessions": [],
            "last_check": None,
            "total_sessions": 0
        })
        
        today = get_today()
        last_check = stats.get("last_check")
        
        # 如果今天已经检查过，跳过
        if last_check == today:
            return {
                "status": "success",
                "action": "none",
                "reason": "Already checked today"
            }
        
        # 更新检查时间
        stats["last_check"] = today
        save_json(stats_file, stats)
        
        # 检查转移矩阵是否需要更新
        matrix = load_transition_matrix()
        matrix_updated = matrix.get("updated_at", "")
        
        # 检查昨天的数据
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_log = DATA_DIR / "actions" / f"{yesterday}.json"
        
        needs_recalculation = False
        
        if yesterday_log.exists():
            # 如果矩阵最后更新时间早于昨天，可能需要重新计算
            if matrix_updated and matrix_updated[:10] < yesterday:
                needs_recalculation = True
        
        # 检查是否有数据但矩阵为空
        if not matrix.get("matrix") and has_action_logs():
            needs_recalculation = True
        
        if needs_recalculation:
            recalculate_transition_matrix()
            return {
                "status": "success",
                "action": "recalculated",
                "reason": "Recalculated transition matrix from action logs"
            }
        
        return {
            "status": "success",
            "action": "none",
            "reason": "No action needed, data is up to date"
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def has_action_logs() -> bool:
    """检查是否有动作日志文件"""
    actions_dir = DATA_DIR / "actions"
    if not actions_dir.exists():
        return False
    return any(actions_dir.glob("*.json"))


def recalculate_transition_matrix():
    """
    重新计算转移矩阵（基于所有日志）
    
    当检测到数据不一致时调用此函数重建矩阵。
    """
    actions_dir = DATA_DIR / "actions"
    
    if not actions_dir.exists():
        return
    
    # 收集所有转移
    all_transitions = {}
    total = 0
    
    # 遍历所有日志文件（按日期排序）
    log_files = sorted(actions_dir.glob("*.json"))
    
    for log_file in log_files:
        log_data = load_json(log_file, {"actions": []})
        actions = log_data.get("actions", [])
        
        # 遍历动作序列
        for i in range(len(actions) - 1):
            from_action = actions[i].get("type", "unknown")
            to_action = actions[i + 1].get("type", "unknown")
            
            if from_action == "unknown" or to_action == "unknown":
                continue
            
            if from_action not in all_transitions:
                all_transitions[from_action] = {}
            
            if to_action not in all_transitions[from_action]:
                all_transitions[from_action][to_action] = {"count": 0}
            
            all_transitions[from_action][to_action]["count"] += 1
            total += 1
    
    # 计算概率
    for from_action in all_transitions:
        row_total = sum(t["count"] for t in all_transitions[from_action].values())
        if row_total > 0:
            for to_action, data in all_transitions[from_action].items():
                data["probability"] = round(data["count"] / row_total, 3)
    
    # 保存
    matrix = {
        "version": "1.0",
        "matrix": all_transitions,
        "total_transitions": total,
        "updated_at": get_timestamp(),
        "recalculated": True,
        "recalculated_at": get_timestamp()
    }
    save_transition_matrix(matrix)


def get_data_summary() -> dict:
    """
    获取数据摘要
    
    Returns:
        数据摘要信息
    """
    try:
        actions_dir = DATA_DIR / "actions"
        
        # 统计日志文件
        log_files = list(actions_dir.glob("*.json")) if actions_dir.exists() else []
        
        # 统计总动作数
        total_actions = 0
        for log_file in log_files:
            log_data = load_json(log_file, {"actions": []})
            total_actions += len(log_data.get("actions", []))
        
        # 加载转移矩阵
        matrix = load_transition_matrix()
        
        return {
            "status": "success",
            "log_files_count": len(log_files),
            "total_actions": total_actions,
            "total_transitions": matrix.get("total_transitions", 0),
            "matrix_updated_at": matrix.get("updated_at", ""),
            "data_dir": str(DATA_DIR)
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    """主函数：处理命令行输入"""
    # 检查是否有参数
    if len(sys.argv) > 1:
        try:
            input_data = json.loads(sys.argv[1])
            action = input_data.get("action", "check")
            
            if action == "summary":
                result = get_data_summary()
            elif action == "recalculate":
                recalculate_transition_matrix()
                result = {
                    "status": "success",
                    "action": "recalculated",
                    "reason": "Manual recalculation requested"
                }
            else:
                result = check_last_session()
        except json.JSONDecodeError:
            result = check_last_session()
    else:
        result = check_last_session()
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
