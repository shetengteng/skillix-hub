#!/usr/bin/env python3
"""
Behavior Prediction Skill V2 - 用户画像管理

管理用户画像的加载、更新和查询。
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter

import utils
from utils import (
    ensure_dir, load_json, save_json,
    get_timestamp, get_today, load_config
)


def load_user_profile() -> dict:
    """加载用户画像"""
    data_dir = utils.DATA_DIR
    profile_file = data_dir / "profile" / "user_profile.json"
    
    if profile_file.exists():
        return load_json(profile_file)
    
    return get_default_profile()


def get_default_profile() -> dict:
    """获取默认用户画像"""
    return {
        "version": "2.0",
        "updated_at": get_timestamp(),
        "stats": {
            "total_sessions": 0,
            "total_actions": 0,
            "active_days": 0,
            "first_seen": None,
            "last_seen": None
        },
        "preferences": {
            "common_file_types": [],
            "common_purposes": [],
            "preferred_task_flow": []
        },
        "time_patterns": {
            "most_active_hours": [],
            "avg_session_duration_minutes": 0
        }
    }


def update_user_profile(force: bool = False) -> dict:
    """
    根据历史数据更新用户画像
    
    Args:
        force: 是否强制更新（忽略更新间隔）
    
    Returns:
        更新后的用户画像
    """
    data_dir = utils.DATA_DIR
    
    # 检查是否需要更新
    if not force:
        config = load_config()
        interval = config.get("profile", {}).get("update_interval_sessions", 10)
        
        current_profile = load_user_profile()
        index = load_json(data_dir / "index" / "sessions_index.json", {"total_count": 0})
        
        sessions_since_update = index["total_count"] - current_profile.get("stats", {}).get("total_sessions", 0)
        
        if sessions_since_update < interval:
            return current_profile
    
    # 加载会话索引
    index_file = data_dir / "index" / "sessions_index.json"
    index = load_json(index_file, {"sessions": []})
    sessions = index.get("sessions", [])
    
    if not sessions:
        return get_default_profile()
    
    # 统计基本信息
    total_sessions = len(sessions)
    dates = set(s["date"] for s in sessions if "date" in s)
    active_days = len(dates)
    
    # 统计时间模式
    durations = [s.get("duration_minutes", 0) for s in sessions if s.get("duration_minutes", 0) > 0]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # 统计工作流程偏好
    all_stages = []
    all_tags = []
    all_tech = []
    
    for session in sessions:
        all_stages.extend(session.get("workflow_stages", []))
        all_tags.extend(session.get("tags", []))
        all_tech.extend(session.get("technologies_used", []))
    
    # 计算频率
    stage_counts = Counter(all_stages)
    tag_counts = Counter(all_tags)
    tech_counts = Counter(all_tech)
    
    # 构建用户画像
    profile = {
        "version": "2.0",
        "updated_at": get_timestamp(),
        "stats": {
            "total_sessions": total_sessions,
            "active_days": active_days,
            "first_seen": min(dates) if dates else None,
            "last_seen": max(dates) if dates else None
        },
        "preferences": {
            "common_stages": [stage for stage, _ in stage_counts.most_common(5)],
            "common_tags": [tag for tag, _ in tag_counts.most_common(10)],
            "common_tech": [tech for tech, _ in tech_counts.most_common(10)],
            "preferred_task_flow": extract_preferred_flow(sessions)
        },
        "time_patterns": {
            "avg_session_duration_minutes": round(avg_duration, 1),
            "most_active_hours": extract_active_hours(sessions)
        },
        "work_style": analyze_work_style(sessions, stage_counts)
    }
    
    # 保存用户画像
    profile_file = data_dir / "profile" / "user_profile.json"
    ensure_dir(profile_file)
    save_json(profile_file, profile)
    
    return profile


def extract_preferred_flow(sessions: list) -> list:
    """提取偏好的工作流程"""
    # 统计常见的阶段序列
    sequences = []
    for session in sessions:
        stages = session.get("workflow_stages", [])
        if len(stages) >= 2:
            for i in range(len(stages) - 1):
                sequences.append(f"{stages[i]} → {stages[i+1]}")
    
    if not sequences:
        return []
    
    seq_counts = Counter(sequences)
    return [seq for seq, _ in seq_counts.most_common(5)]


def extract_active_hours(sessions: list) -> list:
    """提取最活跃的时间段"""
    # 由于索引中可能没有详细时间，这里返回空
    # 可以在后续版本中增强
    return []


def analyze_work_style(sessions: list, stage_counts: Counter) -> dict:
    """分析工作风格"""
    total = sum(stage_counts.values())
    if total == 0:
        return {}
    
    style = {}
    
    # 设计倾向
    design_count = stage_counts.get("design", 0)
    style["planning_tendency"] = round(design_count / total, 2) if total > 0 else 0
    
    # 测试倾向
    test_count = stage_counts.get("test", 0)
    style["test_driven"] = round(test_count / total, 2) if total > 0 else 0
    
    # 文档倾向
    doc_count = stage_counts.get("document", 0)
    style["documentation_focus"] = round(doc_count / total, 2) if total > 0 else 0
    
    # 重构倾向
    refactor_count = stage_counts.get("refactor", 0)
    style["refactoring_habit"] = round(refactor_count / total, 2) if total > 0 else 0
    
    return style


def get_ai_summary(profile: dict = None, patterns: dict = None) -> dict:
    """
    生成 AI 可用的摘要信息
    
    这个摘要会在会话开始时返回给 AI，帮助 AI 了解用户
    """
    if profile is None:
        profile = load_user_profile()
    
    if patterns is None:
        from extract_patterns import get_workflow_patterns
        patterns = get_workflow_patterns()
    
    stats = profile.get("stats", {})
    prefs = profile.get("preferences", {})
    work_style = profile.get("work_style", {})
    
    # 构建描述
    description_parts = []
    
    active_days = stats.get("active_days", 0)
    total_sessions = stats.get("total_sessions", 0)
    
    if active_days > 0:
        description_parts.append(f"这是一个活跃了 {active_days} 天的用户")
    
    if total_sessions > 0:
        description_parts.append(f"共进行了 {total_sessions} 次会话")
    
    # 主要活动
    common_stages = prefs.get("common_stages", [])
    if common_stages:
        description_parts.append(f"主要工作阶段：{', '.join(common_stages[:3])}")
    
    common_tech = prefs.get("common_tech", [])
    if common_tech:
        description_parts.append(f"常用技术：{', '.join(common_tech[:3])}")
    
    summary = {
        "summary": {
            "description": "，".join(description_parts) if description_parts else "新用户，暂无历史数据",
            "total_sessions": total_sessions,
            "active_days": active_days,
            "main_activities": common_stages[:3] if common_stages else []
        },
        "behavior_patterns": {
            "description": "用户的典型工作流程",
            "common_sequences": []
        },
        "predictions": {
            "description": "基于历史数据的预测规则",
            "rules": []
        },
        "preferences": {
            "description": "用户的偏好设置",
            "file_types": [],
            "work_style": describe_work_style(work_style),
            "common_purposes": prefs.get("common_tags", [])[:5]
        }
    }
    
    # 添加常见序列
    if patterns:
        common_seqs = patterns.get("patterns", [])
        for seq in common_seqs[:5]:
            summary["behavior_patterns"]["common_sequences"].append({
                "pattern": seq.get("description", ""),
                "frequency": f"中（出现 {seq.get('count', 0)} 次）" if seq.get("count", 0) < 10 else f"高（出现 {seq.get('count', 0)} 次）",
                "suggestion": f"当用户执行 {seq.get('sequence', [''])[0]} 后，可以主动询问是否需要执行 {seq.get('sequence', ['', ''])[1]}"
            })
        
        # 添加预测规则
        stage_transitions = patterns.get("stage_transitions", {})
        for from_stage, transitions in stage_transitions.items():
            for to_stage, data in transitions.items():
                prob = data.get("probability", 0)
                if prob >= 0.5:
                    summary["predictions"]["rules"].append({
                        "when": f"用户完成 {from_stage} 阶段后",
                        "then": f"{int(prob * 100)}% 概率会进入 {to_stage} 阶段",
                        "action": f"主动询问：需要进行 {to_stage} 吗？" if prob < 0.8 else f"主动执行：{to_stage}"
                    })
    
    return summary


def describe_work_style(work_style: dict) -> str:
    """描述工作风格"""
    if not work_style:
        return "灵活多变"
    
    traits = []
    
    if work_style.get("planning_tendency", 0) > 0.2:
        traits.append("注重规划")
    
    if work_style.get("test_driven", 0) > 0.2:
        traits.append("测试驱动")
    
    if work_style.get("documentation_focus", 0) > 0.1:
        traits.append("重视文档")
    
    if work_style.get("refactoring_habit", 0) > 0.1:
        traits.append("持续重构")
    
    return "、".join(traits) if traits else "灵活多变"


def generate_suggestions(profile: dict = None, patterns: dict = None) -> list:
    """根据用户画像和行为模式生成建议"""
    if profile is None:
        profile = load_user_profile()
    
    if patterns is None:
        from extract_patterns import get_workflow_patterns
        patterns = get_workflow_patterns()
    
    suggestions = []
    
    # 基于常见工作流程的建议
    common_sequences = patterns.get("patterns", [])
    for seq in common_sequences[:3]:
        desc = seq.get("description", "")
        if desc:
            suggestions.append(f"你常见的工作流程：{desc}")
    
    # 基于偏好的建议
    prefs = profile.get("preferences", {})
    common_stages = prefs.get("common_stages", [])
    if common_stages:
        suggestions.append(f"你最常进行的工作阶段：{', '.join(common_stages[:3])}")
    
    common_tech = prefs.get("common_tech", [])
    if common_tech:
        suggestions.append(f"你常用的技术栈：{', '.join(common_tech[:3])}")
    
    # 基于转移概率的建议
    stage_transitions = patterns.get("stage_transitions", {})
    for from_stage, transitions in stage_transitions.items():
        for to_stage, data in transitions.items():
            prob = data.get("probability", 0)
            if prob >= 0.6:
                suggestions.append(f"你通常在 {from_stage} 后执行 {to_stage} ({int(prob * 100)}%)")
    
    return suggestions[:10]  # 最多返回 10 条建议


def main():
    """命令行入口"""
    action = "get"
    if len(sys.argv) > 1:
        try:
            args = json.loads(sys.argv[1])
            action = args.get("action", "get")
        except:
            action = sys.argv[1]
    
    if action == "update":
        profile = update_user_profile(force=True)
        print(json.dumps({
            "status": "success",
            "message": "User profile updated",
            "profile": profile
        }, ensure_ascii=False, indent=2))
    
    elif action == "summary":
        summary = get_ai_summary()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    elif action == "suggestions":
        suggestions = generate_suggestions()
        print(json.dumps({
            "suggestions": suggestions
        }, ensure_ascii=False, indent=2))
    
    else:  # get
        profile = load_user_profile()
        print(json.dumps(profile, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
