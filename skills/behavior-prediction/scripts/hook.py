#!/usr/bin/env python3
"""
Behavior Prediction Skill V2 - 统一 Hook 入口

支持的操作：
- --init: 会话开始时调用，加载用户画像和预测建议
- --finalize: 会话结束时调用，记录会话并更新模式
"""

import argparse
import json
import sys
from datetime import datetime

from utils import get_data_dir, ensure_data_dirs, get_timestamp, load_config
from record_session import record_session
from extract_patterns import extract_and_update_patterns, get_workflow_patterns
from user_profile import (
    load_user_profile, update_user_profile,
    get_ai_summary, generate_suggestions
)


def auto_finalize_pending_session() -> dict:
    """
    自动 finalize 上一个未完成的会话
    
    检查是否有 pending session，如果有则自动保存
    """
    data_dir = get_data_dir()
    pending_file = data_dir / "pending_session.json"
    
    if not pending_file.exists():
        return None
    
    try:
        from utils import load_json, save_json
        pending = load_json(pending_file)
        
        if not pending or not pending.get("actions"):
            # 没有动作记录，删除 pending 文件
            pending_file.unlink()
            return None
        
        # 构建会话数据
        session_data = {
            "session_summary": {
                "topic": pending.get("topic", "自动保存的会话"),
                "goals": [],
                "completed_tasks": [],
                "technologies_used": [],
                "workflow_stages": pending.get("stages", []),
                "tags": []
            },
            "operations": {
                "files": {
                    "created": [],
                    "modified": [],
                    "deleted": []
                },
                "commands": []
            },
            "conversation": {
                "user_messages": [],
                "message_count": 0
            },
            "time": {
                "start": pending.get("start_time", get_timestamp()),
                "end": get_timestamp()
            }
        }
        
        # 从 actions 中提取信息
        for action in pending.get("actions", []):
            action_type = action.get("type", "")
            if action_type in ["create_file", "modify_file"]:
                file_path = action.get("details", {}).get("file_path", "")
                if file_path:
                    if action_type == "create_file":
                        session_data["operations"]["files"]["created"].append(file_path)
                    else:
                        session_data["operations"]["files"]["modified"].append(file_path)
            elif action_type == "run_command":
                cmd = action.get("details", {}).get("command", "")
                if cmd:
                    session_data["operations"]["commands"].append({
                        "command": cmd,
                        "type": action.get("details", {}).get("command_type", "other"),
                        "exit_code": action.get("details", {}).get("exit_code", 0)
                    })
        
        # 记录会话
        session_id = record_session(session_data)
        
        # 删除 pending 文件
        pending_file.unlink()
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "上一个会话已自动保存"
        }
        
    except Exception as e:
        # 出错时删除 pending 文件
        try:
            pending_file.unlink()
        except:
            pass
        return {"status": "error", "message": str(e)}


def handle_init() -> dict:
    """
    会话开始时的初始化
    
    返回：
    - 用户画像
    - 行为模式
    - AI 摘要
    - 建议
    """
    try:
        ensure_data_dirs()
        
        # 0. 自动 finalize 上一个未完成的会话
        auto_finalized = auto_finalize_pending_session()
        
        # 1. 更新并加载用户画像（会自动检查是否需要更新）
        profile = update_user_profile()
        
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
        
        # 添加自动 finalize 结果
        if auto_finalized and auto_finalized.get("status") == "success":
            result["auto_finalized_session"] = auto_finalized
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def handle_finalize(session_data: dict) -> dict:
    """
    会话结束时的处理
    
    参数：
    - session_data: 会话数据（摘要、操作、对话等）
    
    处理：
    1. 记录会话到 sessions/
    2. 提取并更新行为模式
    3. 检查是否需要更新用户画像
    """
    try:
        ensure_data_dirs()
        
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
        
        return {
            "status": "success",
            "session_id": session_id,
            "patterns_updated": patterns_result.get("workflow_updated", False),
            "new_insights": patterns_result.get("new_insights", []),
            "next_suggestions": next_suggestions,
            "message": f"会话 {session_id} 已记录"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def handle_record(action_data: dict) -> dict:
    """
    记录动作到 pending session
    
    参数：
    - action_data: 动作数据，包含 type, tool, details, context
    """
    try:
        from utils import load_json, save_json
        
        data_dir = get_data_dir()
        pending_file = data_dir / "pending_session.json"
        
        # 加载或创建 pending session
        if pending_file.exists():
            pending = load_json(pending_file)
        else:
            pending = {
                "start_time": get_timestamp(),
                "actions": [],
                "stages": []
            }
        
        # 添加动作
        action = {
            "timestamp": get_timestamp(),
            "type": action_data.get("type", "unknown"),
            "tool": action_data.get("tool", ""),
            "details": action_data.get("details", {}),
            "context": action_data.get("context", {})
        }
        pending["actions"].append(action)
        
        # 更新阶段
        stage = action_data.get("context", {}).get("task_stage", "")
        if stage and stage not in pending["stages"]:
            pending["stages"].append(stage)
        
        # 保存
        save_json(pending_file, pending)
        
        return {
            "status": "success",
            "action_count": len(pending["actions"]),
            "stages": pending["stages"]
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description='Behavior Prediction Hook V2')
    parser.add_argument('--init', action='store_true', help='Initialize session')
    parser.add_argument('--record', type=str, help='Record action to pending session')
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
