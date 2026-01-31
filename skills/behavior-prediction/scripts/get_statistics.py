#!/usr/bin/env python3
"""
Behavior Prediction Skill - 获取统计数据

获取预测所需的统计数据，供大模型分析和决策。
"""

import json
import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    DATA_DIR, load_json, get_today,
    load_transition_matrix, load_config,
    get_recent_actions, collect_context
)


def get_statistics(current_action: str) -> dict:
    """
    获取预测所需的统计数据
    
    Args:
        current_action: 当前动作类型
    
    Returns:
        {
            "status": "success",
            "current_action": "动作类型",
            "transitions": {
                "action_b": {"count": 10, "probability": 0.5},
                ...
            },
            "total_samples": 20,
            "recent_sequence": ["action1", "action2", ...],
            "context": {...},
            "prediction_config": {...}
        }
    """
    try:
        # 加载转移矩阵
        matrix = load_transition_matrix()
        
        # 获取当前动作的转移统计
        transitions = matrix.get("matrix", {}).get(current_action, {})
        
        # 计算总样本数
        total_samples = sum(t.get("count", 0) for t in transitions.values())
        
        # 获取最近的动作序列
        recent_sequence = get_recent_actions(limit=10)
        
        # 收集上下文信息
        context = collect_context()
        
        # 加载配置
        config = load_config()
        
        # 获取预测配置
        prediction_config = config.get("prediction", {})
        
        # 构建返回结果
        result = {
            "status": "success",
            "current_action": current_action,
            "transitions": transitions,
            "total_samples": total_samples,
            "recent_sequence": recent_sequence,
            "context": context,
            "prediction_config": prediction_config
        }
        
        # 添加预测建议（如果有足够数据）
        min_samples = config.get("learning", {}).get("min_samples_for_prediction", 3)
        if total_samples >= min_samples and transitions:
            # 找出概率最高的下一步动作
            sorted_transitions = sorted(
                transitions.items(),
                key=lambda x: x[1].get("probability", 0),
                reverse=True
            )
            
            if sorted_transitions:
                top_prediction = sorted_transitions[0]
                result["top_prediction"] = {
                    "action": top_prediction[0],
                    "probability": top_prediction[1].get("probability", 0),
                    "count": top_prediction[1].get("count", 0)
                }
                
                # 检查最近行为模式
                if recent_sequence:
                    recent_pattern = calculate_recent_pattern(
                        recent_sequence,
                        current_action,
                        top_prediction[0]
                    )
                    result["recent_pattern"] = recent_pattern
        
        return result
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def calculate_recent_pattern(
    recent_sequence: list,
    current_action: str,
    predicted_action: str
) -> dict:
    """
    计算最近行为模式
    
    检查最近的动作序列中，current_action 后是否经常跟着 predicted_action
    
    Args:
        recent_sequence: 最近的动作序列
        current_action: 当前动作
        predicted_action: 预测的下一步动作
    
    Returns:
        {
            "occurrences": 3,  # current_action 出现的次数
            "followed_by_prediction": 2,  # 后面跟着 predicted_action 的次数
            "pattern_strength": 0.67  # 模式强度
        }
    """
    occurrences = 0
    followed_by_prediction = 0
    
    for i in range(len(recent_sequence) - 1):
        if recent_sequence[i] == current_action:
            occurrences += 1
            if recent_sequence[i + 1] == predicted_action:
                followed_by_prediction += 1
    
    pattern_strength = 0
    if occurrences > 0:
        pattern_strength = round(followed_by_prediction / occurrences, 2)
    
    return {
        "occurrences": occurrences,
        "followed_by_prediction": followed_by_prediction,
        "pattern_strength": pattern_strength
    }


def get_all_statistics() -> dict:
    """
    获取所有统计数据概览
    
    Returns:
        {
            "status": "success",
            "total_actions": 100,
            "total_transitions": 80,
            "action_types": 15,
            "top_actions": [...],
            "top_transitions": [...]
        }
    """
    try:
        # 加载转移矩阵
        matrix = load_transition_matrix()
        
        # 统计动作类型数量
        action_types = set()
        for from_action, transitions in matrix.get("matrix", {}).items():
            action_types.add(from_action)
            for to_action in transitions.keys():
                action_types.add(to_action)
        
        # 统计每个动作的总次数
        action_counts = {}
        for from_action, transitions in matrix.get("matrix", {}).items():
            for to_action, data in transitions.items():
                count = data.get("count", 0)
                action_counts[from_action] = action_counts.get(from_action, 0) + count
                # 注意：to_action 的计数在它作为 from_action 时统计
        
        # 获取 Top 动作
        top_actions = sorted(
            action_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # 获取 Top 转移
        all_transitions = []
        for from_action, transitions in matrix.get("matrix", {}).items():
            for to_action, data in transitions.items():
                all_transitions.append({
                    "from": from_action,
                    "to": to_action,
                    "count": data.get("count", 0),
                    "probability": data.get("probability", 0)
                })
        
        top_transitions = sorted(
            all_transitions,
            key=lambda x: x["count"],
            reverse=True
        )[:10]
        
        # 统计今日动作数
        today = get_today()
        log_file = DATA_DIR / "actions" / f"{today}.json"
        log_data = load_json(log_file, {"actions": []})
        today_actions = len(log_data.get("actions", []))
        
        return {
            "status": "success",
            "total_transitions": matrix.get("total_transitions", 0),
            "action_types_count": len(action_types),
            "today_actions": today_actions,
            "top_actions": [{"action": a, "count": c} for a, c in top_actions],
            "top_transitions": top_transitions,
            "updated_at": matrix.get("updated_at", "")
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    """主函数：处理命令行输入"""
    if len(sys.argv) < 2:
        # 没有参数时，返回所有统计概览
        result = get_all_statistics()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    try:
        input_data = json.loads(sys.argv[1])
        current_action = input_data.get("current_action", "")
        
        if not current_action:
            # 没有指定动作时，返回所有统计概览
            result = get_all_statistics()
        else:
            result = get_statistics(current_action)
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    except json.JSONDecodeError as e:
        print(json.dumps({
            "status": "error",
            "message": f"Invalid JSON: {e}"
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
