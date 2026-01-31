#!/usr/bin/env python3
"""
Behavior Prediction Skill V2 - 预测生成

基于工作流程模式和用户画像生成预测建议。
"""

import json
import sys
from datetime import datetime

import utils
from utils import load_json, load_config, WORKFLOW_STAGES
from extract_patterns import get_workflow_patterns, get_preferences, get_project_patterns
from user_profile import load_user_profile


def get_predictions(current_stage: str = None, context: dict = None) -> dict:
    """
    获取预测建议
    
    Args:
        current_stage: 当前工作流程阶段
        context: 上下文信息（项目类型、技术栈等）
    
    Returns:
        预测结果，包含自动执行判断
    """
    # 加载数据
    workflow_patterns = get_workflow_patterns()
    preferences = get_preferences()
    project_patterns = get_project_patterns()
    profile = load_user_profile()
    config = load_config()
    
    # 获取自动执行配置
    auto_exec_config = config.get("prediction", {}).get("auto_execute", {})
    
    result = {
        "current_stage": current_stage,
        "predictions": [],
        "suggestions": [],
        "context_aware": False,
        "auto_execute": {
            "enabled": auto_exec_config.get("enabled", False),
            "should_auto_execute": False,
            "action": None,
            "reason": None
        }
    }
    
    # 如果没有指定当前阶段，返回通用建议
    if not current_stage:
        result["suggestions"] = get_general_suggestions(profile, workflow_patterns)
        return result
    
    # 获取阶段转移预测
    stage_transitions = workflow_patterns.get("stage_transitions", {})
    
    if current_stage in stage_transitions:
        transitions = stage_transitions[current_stage]
        
        # 按概率排序
        sorted_transitions = sorted(
            transitions.items(),
            key=lambda x: x[1].get("probability", 0),
            reverse=True
        )
        
        threshold = config.get("prediction", {}).get("suggest_threshold", 0.5)
        max_suggestions = config.get("prediction", {}).get("max_suggestions", 3)
        
        for next_stage, data in sorted_transitions[:max_suggestions]:
            prob = data.get("probability", 0)
            count = data.get("count", 0)
            
            if prob >= threshold:
                prediction = {
                    "next_stage": next_stage,
                    "probability": prob,
                    "count": count,
                    "confidence": calculate_confidence(prob, count),
                    "description": WORKFLOW_STAGES.get(next_stage, next_stage),
                    "suggestion": generate_suggestion(current_stage, next_stage, prob)
                }
                result["predictions"].append(prediction)
    
    # 结合上下文调整（如果提供）
    if context:
        result = adjust_with_context(result, context, project_patterns)
        result["context_aware"] = True
    
    # 生成最终建议
    if result["predictions"]:
        top_prediction = result["predictions"][0]
        result["top_suggestion"] = top_prediction["suggestion"]
        result["should_suggest"] = top_prediction["confidence"] >= 0.5
        
        # 判断是否应该自动执行
        result["auto_execute"] = evaluate_auto_execute(
            top_prediction, 
            auto_exec_config,
            context
        )
    else:
        result["should_suggest"] = False
    
    return result


def evaluate_auto_execute(prediction: dict, config: dict, context: dict = None) -> dict:
    """
    评估是否应该自动执行预测的动作
    
    Args:
        prediction: 预测结果
        config: 自动执行配置
        context: 上下文信息
    
    Returns:
        自动执行评估结果
    """
    result = {
        "enabled": config.get("enabled", False),
        "should_auto_execute": False,
        "should_confirm": False,
        "action": None,
        "command": None,
        "reason": None
    }
    
    # 检查是否启用自动执行
    if not config.get("enabled", False):
        result["reason"] = "auto_execute_disabled"
        return result
    
    next_stage = prediction.get("next_stage")
    confidence = prediction.get("confidence", 0)
    probability = prediction.get("probability", 0)
    
    # 获取配置阈值
    threshold = config.get("threshold", 0.85)
    confirm_below = config.get("require_confirmation_below", 0.95)
    allowed_actions = config.get("allowed_actions", [])
    forbidden_actions = config.get("forbidden_actions", [])
    
    # 映射阶段到动作
    stage_to_action = {
        "test": "run_test",
        "lint": "run_lint",
        "commit": "git_add",
        "review": "git_status"
    }
    
    action = stage_to_action.get(next_stage, next_stage)
    result["action"] = action
    
    # 检查是否在禁止列表中
    if action in forbidden_actions:
        result["reason"] = f"action_forbidden: {action}"
        return result
    
    # 检查是否在允许列表中
    if action not in allowed_actions:
        result["reason"] = f"action_not_in_allowed_list: {action}"
        return result
    
    # 检查置信度是否达到阈值
    if confidence < threshold:
        result["reason"] = f"confidence_below_threshold: {confidence:.2f} < {threshold}"
        return result
    
    # 生成对应的命令
    result["command"] = generate_auto_command(action, context)
    
    # 判断是否需要确认
    if confidence < confirm_below:
        result["should_confirm"] = True
        result["should_auto_execute"] = False
        result["reason"] = f"confidence_requires_confirmation: {confidence:.2f} < {confirm_below}"
    else:
        result["should_confirm"] = False
        result["should_auto_execute"] = True
        result["reason"] = f"auto_execute_approved: confidence={confidence:.2f}"
    
    return result


def generate_auto_command(action: str, context: dict = None) -> str:
    """
    根据动作生成对应的命令
    
    Args:
        action: 动作类型
        context: 上下文信息
    
    Returns:
        要执行的命令
    """
    # 基础命令映射
    command_map = {
        "run_test": "pytest",
        "run_lint": "ruff check .",
        "git_status": "git status",
        "git_add": "git add -A",
        "git_diff": "git diff"
    }
    
    command = command_map.get(action)
    
    if not command:
        return None
    
    # 根据上下文调整命令
    if context:
        # 如果有特定的测试文件
        if action == "run_test" and context.get("test_file"):
            command = f"pytest {context['test_file']}"
        
        # 如果有特定的目录
        if action == "run_lint" and context.get("directory"):
            command = f"ruff check {context['directory']}"
    
    return command


def calculate_confidence(probability: float, count: int) -> float:
    """
    计算置信度
    
    综合考虑概率和样本量
    """
    # 基础置信度 = 概率
    base = probability
    
    # 样本量调整
    # count < 3: 降低置信度
    # count >= 10: 提高置信度
    if count < 3:
        sample_factor = 0.7
    elif count < 5:
        sample_factor = 0.85
    elif count < 10:
        sample_factor = 1.0
    else:
        sample_factor = 1.1
    
    confidence = base * sample_factor
    
    # 限制在 0-1 范围
    return min(max(confidence, 0), 1)


def generate_suggestion(from_stage: str, to_stage: str, probability: float) -> str:
    """生成自然语言建议"""
    from_desc = WORKFLOW_STAGES.get(from_stage, from_stage)
    to_desc = WORKFLOW_STAGES.get(to_stage, to_stage)
    
    if probability >= 0.8:
        # 高置信度 - 肯定语气
        templates = [
            f"根据你的习惯，接下来应该是{to_desc}",
            f"通常{from_desc}后你会{to_desc}，要继续吗？",
            f"下一步：{to_desc}"
        ]
    elif probability >= 0.6:
        # 中置信度 - 建议语气
        templates = [
            f"你可能想要{to_desc}",
            f"要{to_desc}吗？",
            f"接下来是否需要{to_desc}？"
        ]
    else:
        # 低置信度 - 询问语气
        templates = [
            f"是否需要{to_desc}？",
            f"要进行{to_desc}吗？"
        ]
    
    return templates[0]


def adjust_with_context(result: dict, context: dict, project_patterns: dict) -> dict:
    """根据上下文调整预测"""
    project_type = context.get("project_type")
    
    if project_type and project_type in project_patterns.get("patterns", {}):
        pattern = project_patterns["patterns"][project_type]
        common_stages = pattern.get("common_stages", {})
        
        # 调整预测的置信度
        for prediction in result["predictions"]:
            next_stage = prediction["next_stage"]
            if next_stage in common_stages:
                # 如果这个阶段在该项目类型中常见，提高置信度
                stage_count = common_stages[next_stage]
                if stage_count >= 3:
                    prediction["confidence"] = min(prediction["confidence"] * 1.2, 1.0)
                    prediction["context_boost"] = True
    
    return result


def get_general_suggestions(profile: dict, patterns: dict) -> list:
    """获取通用建议（无当前阶段时）"""
    suggestions = []
    
    # 基于用户画像
    prefs = profile.get("preferences", {})
    common_stages = prefs.get("common_stages", [])
    
    if common_stages:
        suggestions.append(f"你最常进行的工作：{', '.join(common_stages[:3])}")
    
    # 基于工作流程模式
    common_seqs = patterns.get("patterns", [])
    for seq in common_seqs[:3]:
        desc = seq.get("description", "")
        if desc:
            suggestions.append(f"常见流程：{desc}")
    
    return suggestions


def predict_next_action(current_actions: list, context: dict = None) -> dict:
    """
    基于当前动作序列预测下一步
    
    Args:
        current_actions: 当前会话中已执行的动作/阶段列表
        context: 上下文信息
    
    Returns:
        预测结果
    """
    if not current_actions:
        return {"predictions": [], "should_suggest": False}
    
    # 取最后一个动作作为当前阶段
    current_stage = current_actions[-1]
    
    return get_predictions(current_stage, context)


def get_workflow_suggestion(workflow_stages: list) -> dict:
    """
    根据工作流程阶段列表获取建议
    
    Args:
        workflow_stages: 当前会话的工作流程阶段列表
    
    Returns:
        建议结果
    """
    if not workflow_stages:
        return {
            "has_suggestion": False,
            "message": "暂无建议"
        }
    
    current_stage = workflow_stages[-1]
    predictions = get_predictions(current_stage)
    
    if predictions.get("should_suggest") and predictions.get("predictions"):
        top = predictions["predictions"][0]
        return {
            "has_suggestion": True,
            "current_stage": current_stage,
            "suggested_next": top["next_stage"],
            "confidence": top["confidence"],
            "message": top["suggestion"]
        }
    
    return {
        "has_suggestion": False,
        "current_stage": current_stage,
        "message": "暂无明确的下一步建议"
    }


def main():
    """命令行入口"""
    current_stage = None
    context = None
    
    if len(sys.argv) > 1:
        try:
            args = json.loads(sys.argv[1])
            current_stage = args.get("current_stage")
            context = args.get("context")
        except:
            current_stage = sys.argv[1]
    
    result = get_predictions(current_stage, context)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
