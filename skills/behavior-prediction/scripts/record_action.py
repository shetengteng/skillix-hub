#!/usr/bin/env python3
"""
Behavior Prediction Skill - 记录动作

记录单个动作到今日日志，并更新转移矩阵。
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
    save_transition_matrix, register_action_type
)


def record_action(action_data: dict) -> dict:
    """
    记录一个动作到今日日志，并更新转移矩阵
    
    Args:
        action_data: {
            "type": "动作类型",
            "tool": "工具名称",
            "timestamp": "ISO8601时间（可选）",
            "details": {...},
            "classification": {
                "confidence": 0.95,
                "is_new_type": false,
                "description": "类型描述（新类型时）"
            }
        }
    
    Returns:
        {"status": "success|skipped|error", ...}
    """
    try:
        ensure_data_dirs()
        
        # 获取动作类型
        action_type = action_data.get("type", "unknown")
        
        if not action_type or action_type == "unknown":
            return {"status": "error", "message": "Missing or invalid action type"}
        
        # 今日日志文件
        today = get_today()
        log_file = DATA_DIR / "actions" / f"{today}.json"
        
        # 读取或创建日志
        log_data = load_json(log_file, {"date": today, "actions": []})
        
        # 频率控制：5秒内相同动作不重复记录
        if log_data["actions"]:
            last_action = log_data["actions"][-1]
            if last_action.get("type") == action_type:
                try:
                    last_time_str = last_action.get("timestamp", "")
                    if last_time_str:
                        # 处理时间戳格式
                        last_time_str = last_time_str.replace("Z", "+00:00")
                        last_time = datetime.fromisoformat(last_time_str)
                        now = datetime.now().astimezone()
                        if (now - last_time).total_seconds() < 5:
                            return {
                                "status": "skipped",
                                "reason": "duplicate within 5s"
                            }
                except (ValueError, TypeError):
                    pass  # 时间解析失败，继续记录
        
        # 生成动作 ID
        action_id = f"{today}-{len(log_data['actions']) + 1:03d}"
        
        # 构建动作记录
        action_record = {
            "id": action_id,
            "type": action_type,
            "tool": action_data.get("tool", "unknown"),
            "timestamp": action_data.get("timestamp", get_timestamp()),
            "details": action_data.get("details", {}),
        }
        
        # 如果有分类信息，添加到记录
        if "classification" in action_data:
            action_record["classification"] = action_data["classification"]
        
        # 追加到日志
        log_data["actions"].append(action_record)
        save_json(log_file, log_data)
        
        # 注册动作类型（如果是新类型）
        classification = action_data.get("classification", {})
        if classification.get("is_new_type"):
            register_action_type(
                action_type,
                description=classification.get("description", ""),
                is_new=True
            )
        else:
            register_action_type(action_type)
        
        # 更新转移矩阵（如果有前一个动作）
        if len(log_data["actions"]) >= 2:
            prev_action = log_data["actions"][-2]["type"]
            update_transition(prev_action, action_type)
        
        return {
            "status": "success",
            "action_id": action_id,
            "type": action_type,
            "total_actions_today": len(log_data["actions"])
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def update_transition(from_action: str, to_action: str):
    """
    更新转移矩阵
    
    Args:
        from_action: 前一个动作类型
        to_action: 当前动作类型
    """
    matrix = load_transition_matrix()
    
    # 初始化
    if from_action not in matrix["matrix"]:
        matrix["matrix"][from_action] = {}
    
    if to_action not in matrix["matrix"][from_action]:
        matrix["matrix"][from_action][to_action] = {"count": 0}
    
    # 更新计数
    matrix["matrix"][from_action][to_action]["count"] += 1
    matrix["total_transitions"] = matrix.get("total_transitions", 0) + 1
    
    # 重新计算该行的概率
    total = sum(t["count"] for t in matrix["matrix"][from_action].values())
    for action, data in matrix["matrix"][from_action].items():
        data["probability"] = round(data["count"] / total, 3)
    
    save_transition_matrix(matrix)


def main():
    """主函数：处理命令行输入"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Missing action data. Usage: record_action.py '{\"type\": \"...\", ...}'"
        }))
        sys.exit(1)
    
    try:
        action_data = json.loads(sys.argv[1])
        result = record_action(action_data)
        print(json.dumps(result, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(json.dumps({
            "status": "error",
            "message": f"Invalid JSON: {e}"
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
