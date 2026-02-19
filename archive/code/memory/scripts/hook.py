#!/usr/bin/env python3
"""
Memory Skill 会话 Hook

管理会话生命周期，支持：
- 会话开始时初始化
- 实时保存临时记忆
- 会话结束时汇总保存

用法：
  --init                  会话开始时调用
  --save <json>           保存临时记忆
  --finalize [json]       会话结束时调用
  --status                查看当前会话状态
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from utils import (
    load_config, get_data_dir, initialize_data_dir,
    detect_save_trigger, add_temp_memory, get_temp_memories,
    load_pending_session, save_pending_session, clear_pending_session,
    cleanup_old_temp_memories
)


def auto_finalize_pending_session(location: str = "project") -> dict:
    """
    自动 finalize 上一个未完成的会话
    
    Returns:
        finalize 结果，如果没有 pending session 则返回 None
    """
    pending = load_pending_session(location)
    if not pending:
        return None
    
    temp_memories = pending.get("temp_memories", [])
    if not temp_memories:
        clear_pending_session(location)
        return {"status": "skipped", "reason": "no_temp_memories"}
    
    # 调用汇总脚本
    try:
        from summarize import summarize_temp_memories
        result = summarize_temp_memories(temp_memories, location)
        clear_pending_session(location)
        return {
            "status": "success",
            "message": "上一个会话已自动保存",
            "memory_count": len(temp_memories),
            "summarize_result": result
        }
    except ImportError:
        # 如果汇总脚本不存在，直接保存
        clear_pending_session(location)
        return {
            "status": "partial",
            "message": "上一个会话临时记忆已清除（汇总脚本未找到）",
            "memory_count": len(temp_memories)
        }
    except Exception as e:
        clear_pending_session(location)
        return {"status": "error", "message": str(e)}


def handle_init(location: str = "project") -> dict:
    """
    会话开始时的初始化
    
    处理流程：
    1. 自动 finalize 上一个未完成的会话
    2. 创建新的 pending session
    3. 清理过期的临时记忆
    4. 返回状态信息
    """
    try:
        initialize_data_dir(location)
        
        # 1. 自动 finalize 上一个会话
        auto_result = auto_finalize_pending_session(location)
        
        # 2. 创建新的 pending session
        save_pending_session({}, location)
        
        # 3. 清理过期的临时记忆
        cleanup_old_temp_memories(location)
        
        # 4. 加载配置
        config = load_config(location)
        
        result = {
            "status": "success",
            "session_start": datetime.now().isoformat(),
            "save_trigger_enabled": config.get("save_trigger", {}).get("enabled", True),
            "temp_memory_enabled": config.get("temp_memory", {}).get("enabled", True)
        }
        
        if auto_result and auto_result.get("status") == "success":
            result["auto_finalized"] = auto_result
        
        return result
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def handle_save(data: dict, location: str = "project") -> dict:
    """
    保存临时记忆
    
    Args:
        data: 记忆数据，包含：
            - user_message: 用户消息
            - ai_response: AI 回复（可选）
            - topic: 主题（可选，会自动提取）
            - key_info: 关键信息列表（可选）
            - tags: 标签列表（可选）
        location: 存储位置
    
    Returns:
        保存结果
    """
    try:
        config = load_config(location)
        
        # 检查是否启用临时记忆
        if not config.get("temp_memory", {}).get("enabled", True):
            return {"status": "disabled", "message": "临时记忆功能已禁用"}
        
        user_message = data.get("user_message", "")
        
        # 检测是否应该保存
        trigger_result = detect_save_trigger(user_message, config)
        
        if not trigger_result.get("should_save", False) and not data.get("force", False):
            return {
                "status": "skipped",
                "reason": "no_trigger_keyword",
                "message": "未检测到保存触发关键词"
            }
        
        # 构建临时记忆
        temp_memory = {
            "trigger_keyword": trigger_result.get("trigger_keyword"),
            "trigger_category": trigger_result.get("trigger_category"),
            "confidence": trigger_result.get("confidence", 0),
            "user_message": user_message,
            "ai_response": data.get("ai_response", ""),
            "extracted_info": {
                "topic": data.get("topic", ""),
                "key_info": data.get("key_info", []),
                "tags": data.get("tags", [])
            }
        }
        
        # 保存临时记忆
        add_temp_memory(temp_memory, location)
        
        return {
            "status": "success",
            "message": "临时记忆已保存",
            "trigger_keyword": trigger_result.get("trigger_keyword"),
            "trigger_category": trigger_result.get("trigger_category")
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def handle_finalize(data: dict = None, location: str = "project") -> dict:
    """
    会话结束时的处理
    
    Args:
        data: 会话数据（可选），包含：
            - topic: 会话主题
            - summary: 会话摘要
        location: 存储位置
    
    Returns:
        处理结果
    """
    try:
        if data is None:
            data = {}
        
        # 获取临时记忆
        temp_memories = get_temp_memories(location)
        
        if not temp_memories:
            clear_pending_session(location)
            return {
                "status": "success",
                "message": "会话结束（无临时记忆需要保存）",
                "memory_count": 0
            }
        
        # 调用汇总脚本
        try:
            from summarize import summarize_temp_memories
            result = summarize_temp_memories(temp_memories, location, data)
            clear_pending_session(location)
            return {
                "status": "success",
                "message": "会话已保存",
                "memory_count": len(temp_memories),
                "summarize_result": result
            }
        except ImportError:
            # 如果汇总脚本不存在，使用简单保存
            from save_memory import save_memory_internal
            
            # 合并所有临时记忆的信息
            all_key_info = []
            all_tags = set()
            
            for mem in temp_memories:
                info = mem.get("extracted_info", {})
                all_key_info.extend(info.get("key_info", []))
                all_tags.update(info.get("tags", []))
            
            # 保存
            memory_data = {
                "topic": data.get("topic", "会话记忆"),
                "key_info": list(set(all_key_info)) if all_key_info else ["会话内容"],
                "tags": list(all_tags) if all_tags else ["#session"]
            }
            
            save_result = save_memory_internal(memory_data, location)
            clear_pending_session(location)
            
            return {
                "status": "success",
                "message": "会话已保存（简单模式）",
                "memory_count": len(temp_memories),
                "save_result": save_result
            }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def handle_status(location: str = "project") -> dict:
    """
    查看当前会话状态
    
    Returns:
        状态信息
    """
    try:
        pending = load_pending_session(location)
        
        if not pending:
            return {
                "status": "no_session",
                "message": "当前没有活跃的会话"
            }
        
        temp_memories = pending.get("temp_memories", [])
        
        return {
            "status": "active",
            "session_start": pending.get("session_start"),
            "temp_memory_count": len(temp_memories),
            "recent_memories": [
                {
                    "id": m.get("id"),
                    "trigger_keyword": m.get("trigger_keyword"),
                    "timestamp": m.get("timestamp")
                }
                for m in temp_memories[-5:]  # 最近 5 条
            ]
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description='Memory Skill 会话 Hook')
    parser.add_argument('--init', action='store_true', help='会话开始')
    parser.add_argument('--save', type=str, help='保存临时记忆')
    parser.add_argument('--finalize', type=str, nargs='?', const='{}', help='会话结束')
    parser.add_argument('--status', action='store_true', help='查看状态')
    parser.add_argument('--location', type=str, default='project', help='存储位置')
    
    args = parser.parse_args()
    
    if args.init:
        result = handle_init(args.location)
    elif args.save:
        try:
            data = json.loads(args.save)
        except json.JSONDecodeError as e:
            result = {"status": "error", "message": f"Invalid JSON: {e}"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)
        result = handle_save(data, args.location)
    elif args.finalize is not None:
        try:
            data = json.loads(args.finalize) if args.finalize else {}
        except json.JSONDecodeError as e:
            result = {"status": "error", "message": f"Invalid JSON: {e}"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)
        result = handle_finalize(data, args.location)
    elif args.status:
        result = handle_status(args.location)
    else:
        result = {"status": "error", "message": "请指定 --init, --save, --finalize 或 --status"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
