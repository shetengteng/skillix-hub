#!/usr/bin/env python3
"""
Behavior Prediction Skill V2 - 统一 Hook 入口

支持的操作：
- --init: 会话开始时调用，加载用户画像和预测建议（同时检查并自动 finalize 上一个未完成的会话）
- --record: 记录动作到当前会话
- --finalize: 会话结束时调用，记录会话并更新模式
"""

import argparse
import json
import sys
from datetime import datetime

from utils import (
    get_data_dir, ensure_data_dirs, get_timestamp, load_config,
    load_pending_session, save_pending_session, clear_pending_session,
    add_action_to_pending_session, build_session_data_from_pending
)
from record_session import record_session
from extract_patterns import extract_and_update_patterns, get_workflow_patterns
from user_profile import (
    load_user_profile, update_user_profile,
    get_ai_summary, generate_suggestions
)


def auto_finalize_pending_session() -> dict:
    """
    自动 finalize 上一个未完成的会话
    
    Returns:
        finalize 结果，如果没有 pending session 则返回 None
    """
    pending_data = load_pending_session()
    if not pending_data:
        return None
    
    # 检查是否有动作记录
    actions = pending_data.get("actions", [])
    if not actions:
        # 没有动作记录，直接清除
        clear_pending_session()
        return {"status": "skipped", "reason": "no_actions"}
    
    # 构建 session data 并 finalize
    session_data = build_session_data_from_pending(pending_data)
    
    try:
        result = handle_finalize(session_data, auto_finalized=True)
        clear_pending_session()
        return result
    except Exception as e:
        # finalize 失败也要清除，避免无限循环
        clear_pending_session()
        return {"status": "error", "message": str(e)}


def handle_init() -> dict:
    """
    会话开始时的初始化
    
    处理流程：
    1. 检查并自动 finalize 上一个未完成的会话
    2. 创建新的 pending session
    3. 返回用户画像、行为模式、AI 摘要、建议
    """
    try:
        ensure_data_dirs()
        
        # 0. 检查并自动 finalize 上一个未完成的会话
        auto_finalize_result = auto_finalize_pending_session()
        
        # 1. 创建新的 pending session
        save_pending_session({})
        
        # 2. 加载用户画像
        profile = load_user_profile()
        
        # 2. 加载行为模式
        patterns = get_workflow_patterns()
        
        # 3. 生成 AI 可用的摘要
        ai_summary = get_ai_summary(profile, patterns)
        
        # 4. 生成建议
        suggestions = generate_suggestions(profile, patterns)
        
        # 5. 构建简化的用户画像（用于返回）
        profile_summary = {
            "updated_at": profile.get("updated_at"),
            "stats": profile.get("stats", {}),
            "preferences": {
                "common_file_types": profile.get("preferences", {}).get("common_file_types", []),
                "common_purposes": profile.get("preferences", {}).get("common_purposes", []),
                "preferred_task_flow": profile.get("preferences", {}).get("preferred_task_flow", [])
            },
            "time_patterns": profile.get("time_patterns", {})
        }
        
        # 6. 构建简化的行为模式（用于返回）
        patterns_summary = {
            "updated_at": patterns.get("updated_at"),
            "common_sequences": [
                {
                    "sequence": p.get("sequence", []),
                    "count": p.get("count", 0),
                    "description": p.get("description", "")
                }
                for p in patterns.get("patterns", [])[:5]
            ],
            "top_transitions": []
        }
        
        # 提取高概率转移
        stage_transitions = patterns.get("stage_transitions", {})
        for from_stage, transitions in stage_transitions.items():
            for to_stage, data in transitions.items():
                if data.get("probability", 0) >= 0.5:
                    patterns_summary["top_transitions"].append({
                        "from": from_stage,
                        "to": to_stage,
                        "probability": data.get("probability", 0),
                        "count": data.get("count", 0)
                    })
        
        # 按概率排序
        patterns_summary["top_transitions"].sort(
            key=lambda x: x["probability"],
            reverse=True
        )
        patterns_summary["top_transitions"] = patterns_summary["top_transitions"][:10]
        
        result = {
            "status": "success",
            "user_profile": profile_summary,
            "behavior_patterns": patterns_summary,
            "ai_summary": ai_summary,
            "profile_summary": f"用户活跃了 {profile.get('stats', {}).get('active_days', 0)} 天，"
                              f"共进行了 {profile.get('stats', {}).get('total_sessions', 0)} 次会话。"
                              f" 最活跃时段：{', '.join(str(h) + ':00' for h in profile.get('time_patterns', {}).get('most_active_hours', [])[:3])}。"
                              if profile.get('stats', {}).get('total_sessions', 0) > 0
                              else "新用户，暂无历史数据。",
            "suggestions": suggestions
        }
        
        # 如果有自动 finalize 的结果，添加到返回值
        if auto_finalize_result and auto_finalize_result.get("status") == "success":
            result["auto_finalized_session"] = {
                "session_id": auto_finalize_result.get("session_id"),
                "message": "上一个会话已自动保存"
            }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def handle_record(action_data: dict) -> dict:
    """
    记录动作到当前会话
    
    Args:
        action_data: 动作数据
    
    Returns:
        记录结果
    """
    try:
        ensure_data_dirs()
        
        # 添加时间戳（如果没有）
        if "timestamp" not in action_data:
            action_data["timestamp"] = get_timestamp()
        
        # 添加到 pending session
        add_action_to_pending_session(action_data)
        
        return {
            "status": "success",
            "message": "Action recorded"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def handle_finalize(session_data: dict, auto_finalized: bool = False) -> dict:
    """
    会话结束时的处理
    
    参数：
    - session_data: 会话数据（摘要、操作、对话等）
    - auto_finalized: 是否为自动 finalize（由 --init 触发）
    
    处理：
    1. 合并 pending session 中的动作记录
    2. 记录会话到 sessions/
    3. 提取并更新行为模式
    4. 检查是否需要更新用户画像
    5. 清除 pending session
    """
    try:
        ensure_data_dirs()
        
        # 0. 如果不是自动 finalize，合并 pending session 中的动作
        if not auto_finalized:
            pending_data = load_pending_session()
            if pending_data:
                pending_actions = pending_data.get("actions", [])
                if pending_actions:
                    # 合并动作到 session_data
                    if "operations" not in session_data:
                        session_data["operations"] = {}
                    session_data["operations"]["recorded_actions"] = pending_actions
                    
                    # 使用 pending session 的开始时间
                    if "time" not in session_data:
                        session_data["time"] = {}
                    if not session_data["time"].get("start"):
                        session_data["time"]["start"] = pending_data.get("session_start", get_timestamp())
        
        # 1. 记录会话
        session_id = record_session(session_data)
        
        # 2. 提取并更新模式
        patterns_result = extract_and_update_patterns(session_data)
        
        # 3. 检查是否需要更新用户画像
        config = load_config()
        if config.get("profile", {}).get("auto_update", True):
            update_user_profile(force=False)  # 非强制，按间隔更新
        
        # 4. 生成下次建议
        next_suggestions = []
        workflow_stages = session_data.get("session_summary", {}).get("workflow_stages", [])
        if workflow_stages:
            from get_predictions import get_predictions
            predictions = get_predictions(workflow_stages[-1])
            if predictions.get("predictions"):
                top = predictions["predictions"][0]
                next_suggestions.append(f"下次你可能想要：{top.get('suggestion', '')}")
        
        # 5. 清除 pending session（如果不是自动 finalize）
        if not auto_finalized:
            clear_pending_session()
        
        return {
            "status": "success",
            "session_id": session_id,
            "patterns_updated": patterns_result.get("workflow_updated", False),
            "new_insights": patterns_result.get("new_insights", []),
            "next_suggestions": next_suggestions,
            "message": f"会话 {session_id} 已记录",
            "auto_finalized": auto_finalized
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def main():
    parser = argparse.ArgumentParser(description='Behavior Prediction Hook V2')
    parser.add_argument('--init', action='store_true', help='Initialize session (auto-finalizes previous pending session)')
    parser.add_argument('--record', type=str, help='Record action to current session')
    parser.add_argument('--finalize', type=str, help='Finalize session with data')
    
    args = parser.parse_args()
    
    if args.init:
        result = handle_init()
    elif args.record:
        try:
            action_data = json.loads(args.record)
        except json.JSONDecodeError as e:
            result = {"status": "error", "message": f"Invalid JSON: {e}"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)
        result = handle_record(action_data)
    elif args.finalize:
        try:
            session_data = json.loads(args.finalize)
        except json.JSONDecodeError as e:
            result = {"status": "error", "message": f"Invalid JSON: {e}"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)
        result = handle_finalize(session_data)
    else:
        result = {
            "status": "error",
            "message": "No action specified. Use --init, --record, or --finalize"
        }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
