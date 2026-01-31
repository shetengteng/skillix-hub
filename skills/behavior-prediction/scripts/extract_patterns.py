#!/usr/bin/env python3
"""
Behavior Prediction Skill V2 - 模式提取

从会话记录中提取行为模式：
1. 工作流程模式（设计 → 实现 → 测试 → 提交）
2. 偏好模式（技术栈、编码风格）
3. 项目模式（不同项目类型的开发流程）
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter

import utils
from utils import (
    ensure_dir, load_json, save_json,
    get_timestamp, WORKFLOW_STAGES
)


def extract_and_update_patterns(session_data: dict) -> dict:
    """
    从新会话中提取模式并更新
    
    Args:
        session_data: 会话数据
    
    Returns:
        更新结果
    """
    results = {
        "workflow_updated": False,
        "preferences_updated": False,
        "project_patterns_updated": False,
        "new_insights": []
    }
    
    # 1. 更新工作流程模式
    workflow_result = update_workflow_patterns(session_data)
    results["workflow_updated"] = workflow_result.get("updated", False)
    if workflow_result.get("new_patterns"):
        results["new_insights"].extend(workflow_result["new_patterns"])
    
    # 2. 更新偏好数据
    prefs_result = update_preferences(session_data)
    results["preferences_updated"] = prefs_result.get("updated", False)
    
    # 3. 更新项目模式
    project_result = update_project_patterns(session_data)
    results["project_patterns_updated"] = project_result.get("updated", False)
    
    return results


def update_workflow_patterns(session_data: dict) -> dict:
    """更新工作流程模式"""
    data_dir = utils.DATA_DIR
    patterns_file = data_dir / "patterns" / "workflow_patterns.json"
    ensure_dir(patterns_file)
    
    # 读取或创建模式数据
    patterns = load_json(patterns_file, {
        "version": "2.0",
        "patterns": [],
        "stage_transitions": {},
        "stage_counts": {},
        "total_sessions": 0,
        "updated_at": None
    })
    
    # 获取本次会话的工作流程阶段
    summary = session_data.get("session_summary", {})
    stages = summary.get("workflow_stages", [])
    
    if not stages:
        return {"updated": False}
    
    result = {"updated": True, "new_patterns": []}
    
    # 更新阶段计数
    for stage in stages:
        if stage not in patterns["stage_counts"]:
            patterns["stage_counts"][stage] = 0
        patterns["stage_counts"][stage] += 1
    
    # 更新阶段转移统计
    for i in range(len(stages) - 1):
        from_stage = stages[i]
        to_stage = stages[i + 1]
        
        if from_stage not in patterns["stage_transitions"]:
            patterns["stage_transitions"][from_stage] = {}
        
        if to_stage not in patterns["stage_transitions"][from_stage]:
            patterns["stage_transitions"][from_stage][to_stage] = {"count": 0}
            result["new_patterns"].append(f"发现新的工作流程：{from_stage} → {to_stage}")
        
        patterns["stage_transitions"][from_stage][to_stage]["count"] += 1
    
    # 重新计算转移概率
    for from_stage, transitions in patterns["stage_transitions"].items():
        total = sum(t["count"] for t in transitions.values())
        for to_stage, data in transitions.items():
            data["probability"] = round(data["count"] / total, 3) if total > 0 else 0
    
    # 更新会话计数
    patterns["total_sessions"] += 1
    patterns["updated_at"] = get_timestamp()
    
    # 识别常见模式序列
    patterns["patterns"] = identify_common_sequences(patterns["stage_transitions"])
    
    # 保存
    save_json(patterns_file, patterns)
    
    return result


def identify_common_sequences(transitions: dict) -> list:
    """从转移数据中识别常见的工作流程序列"""
    sequences = []
    
    # 找出高频转移
    high_freq = []
    for from_stage, to_stages in transitions.items():
        for to_stage, data in to_stages.items():
            if data["count"] >= 2:  # 至少出现 2 次
                high_freq.append({
                    "from": from_stage,
                    "to": to_stage,
                    "count": data["count"],
                    "probability": data["probability"]
                })
    
    # 按频率排序
    high_freq.sort(key=lambda x: x["count"], reverse=True)
    
    # 构建序列模式
    for trans in high_freq[:10]:
        sequences.append({
            "sequence": [trans["from"], trans["to"]],
            "count": trans["count"],
            "probability": trans["probability"],
            "description": f"{trans['from']} → {trans['to']}"
        })
    
    return sequences


def update_preferences(session_data: dict) -> dict:
    """更新用户偏好数据"""
    data_dir = utils.DATA_DIR
    prefs_file = data_dir / "patterns" / "preferences.json"
    ensure_dir(prefs_file)
    
    # 读取或创建偏好数据
    prefs = load_json(prefs_file, {
        "version": "2.0",
        "tech_stack": {
            "languages": {},
            "frameworks": {},
            "tools": {}
        },
        "workflow": {
            "stages_frequency": {},
            "common_tags": {}
        },
        "total_sessions": 0,
        "updated_at": None
    })
    
    summary = session_data.get("session_summary", {})
    
    # 更新技术栈统计
    technologies = summary.get("technologies_used", [])
    for tech in technologies:
        tech_lower = tech.lower()
        category = classify_technology(tech_lower)
        
        if tech_lower not in prefs["tech_stack"][category]:
            prefs["tech_stack"][category][tech_lower] = {"count": 0}
        
        prefs["tech_stack"][category][tech_lower]["count"] += 1
    
    # 更新工作流程阶段频率
    stages = summary.get("workflow_stages", [])
    for stage in stages:
        if stage not in prefs["workflow"]["stages_frequency"]:
            prefs["workflow"]["stages_frequency"][stage] = 0
        prefs["workflow"]["stages_frequency"][stage] += 1
    
    # 更新标签统计
    tags = summary.get("tags", [])
    for tag in tags:
        if tag not in prefs["workflow"]["common_tags"]:
            prefs["workflow"]["common_tags"][tag] = 0
        prefs["workflow"]["common_tags"][tag] += 1
    
    # 更新计数
    prefs["total_sessions"] += 1
    prefs["updated_at"] = get_timestamp()
    
    # 计算偏好分数
    calculate_preference_scores(prefs)
    
    # 保存
    save_json(prefs_file, prefs)
    
    return {"updated": True}


def classify_technology(tech: str) -> str:
    """分类技术类型"""
    languages = ["python", "javascript", "typescript", "java", "go", "rust", "c", "cpp", "ruby", "php"]
    frameworks = ["fastapi", "flask", "django", "vue", "react", "angular", "express", "spring", "rails"]
    
    if tech in languages:
        return "languages"
    elif tech in frameworks:
        return "frameworks"
    else:
        return "tools"


def calculate_preference_scores(prefs: dict):
    """计算各项的偏好分数（0-1）"""
    total_sessions = prefs["total_sessions"]
    if total_sessions == 0:
        return
    
    # 计算技术栈偏好分数
    for category in ["languages", "frameworks", "tools"]:
        items = prefs["tech_stack"][category]
        if not items:
            continue
        
        max_count = max(item["count"] for item in items.values())
        for item in items.values():
            item["preference"] = round(item["count"] / max_count, 2) if max_count > 0 else 0


def update_project_patterns(session_data: dict) -> dict:
    """更新项目模式"""
    data_dir = utils.DATA_DIR
    project_file = data_dir / "patterns" / "project_patterns.json"
    ensure_dir(project_file)
    
    # 读取或创建项目模式数据
    project_patterns = load_json(project_file, {
        "version": "2.0",
        "patterns": {},
        "total_sessions": 0,
        "updated_at": None
    })
    
    # 获取项目类型
    summary = session_data.get("session_summary", {})
    tags = summary.get("tags", [])
    technologies = summary.get("technologies_used", [])
    
    project_type = infer_project_type(tags, technologies)
    
    if project_type:
        if project_type not in project_patterns["patterns"]:
            project_patterns["patterns"][project_type] = {
                "count": 0,
                "common_stages": {},
                "common_tech": {},
                "common_tags": {}
            }
        
        pattern = project_patterns["patterns"][project_type]
        pattern["count"] += 1
        
        # 统计常见阶段
        for stage in summary.get("workflow_stages", []):
            if stage not in pattern["common_stages"]:
                pattern["common_stages"][stage] = 0
            pattern["common_stages"][stage] += 1
        
        # 统计常见技术
        for tech in technologies:
            tech_lower = tech.lower()
            if tech_lower not in pattern["common_tech"]:
                pattern["common_tech"][tech_lower] = 0
            pattern["common_tech"][tech_lower] += 1
        
        # 统计常见标签
        for tag in tags:
            if tag not in pattern["common_tags"]:
                pattern["common_tags"][tag] = 0
            pattern["common_tags"][tag] += 1
    
    project_patterns["total_sessions"] += 1
    project_patterns["updated_at"] = get_timestamp()
    
    # 保存
    save_json(project_file, project_patterns)
    
    return {"updated": True}


def infer_project_type(tags: list, technologies: list) -> str:
    """根据标签和技术推断项目类型"""
    tags_lower = [t.lower() for t in tags]
    tech_lower = [t.lower() for t in technologies]
    
    # API/后端项目
    if any(t in tags_lower for t in ["#api", "#backend", "#server"]):
        return "backend_api"
    if any(t in tech_lower for t in ["fastapi", "flask", "django", "express", "spring"]):
        return "backend_api"
    
    # 前端项目
    if any(t in tags_lower for t in ["#frontend", "#ui", "#web"]):
        return "frontend"
    if any(t in tech_lower for t in ["vue", "react", "angular", "svelte"]):
        return "frontend"
    
    # 全栈项目
    if any(t in tags_lower for t in ["#fullstack"]):
        return "fullstack"
    
    # 工具/脚本
    if any(t in tags_lower for t in ["#script", "#tool", "#cli"]):
        return "tool_script"
    
    # 文档/设计
    if any(t in tags_lower for t in ["#doc", "#design", "#documentation"]):
        return "documentation"
    
    return "general"


def get_workflow_patterns() -> dict:
    """获取工作流程模式"""
    data_dir = utils.DATA_DIR
    patterns_file = data_dir / "patterns" / "workflow_patterns.json"
    return load_json(patterns_file, {"patterns": [], "stage_transitions": {}})


def get_preferences() -> dict:
    """获取偏好数据"""
    data_dir = utils.DATA_DIR
    prefs_file = data_dir / "patterns" / "preferences.json"
    return load_json(prefs_file, {"tech_stack": {}, "workflow": {}})


def get_project_patterns() -> dict:
    """获取项目模式"""
    data_dir = utils.DATA_DIR
    project_file = data_dir / "patterns" / "project_patterns.json"
    return load_json(project_file, {"patterns": {}})


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        # 无参数时，返回当前模式数据
        result = {
            "workflow_patterns": get_workflow_patterns(),
            "preferences": get_preferences(),
            "project_patterns": get_project_patterns()
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    try:
        session_data = json.loads(sys.argv[1])
        result = extract_and_update_patterns(session_data)
        
        print(json.dumps({
            "status": "success",
            **result
        }, ensure_ascii=False, indent=2))
        
    except json.JSONDecodeError as e:
        print(json.dumps({
            "status": "error",
            "message": f"Invalid JSON: {e}"
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
