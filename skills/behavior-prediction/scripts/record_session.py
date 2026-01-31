#!/usr/bin/env python3
"""
Behavior Prediction Skill V2 - 会话记录

记录完整会话内容到本地存储。
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import utils
from utils import (
    ensure_dir, load_json, save_json,
    get_today, get_month, get_timestamp, detect_project_info
)


def record_session(session_data: dict) -> str:
    """
    记录会话到本地
    
    Args:
        session_data: 会话数据，包含 session_summary, operations, conversation, time
    
    Returns:
        session_id
    """
    data_dir = utils.DATA_DIR
    
    # 生成 session_id
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    month_str = now.strftime("%Y-%m")
    
    # 会话目录
    sessions_dir = data_dir / "sessions" / month_str
    ensure_dir(sessions_dir)
    
    # 获取今日已有的会话数
    existing_sessions = list(sessions_dir.glob(f"sess_{date_str}_*.json"))
    session_num = len(existing_sessions) + 1
    session_id = f"sess_{date_str}_{session_num:03d}"
    
    # 构建完整的会话记录
    session_record = {
        "session_id": session_id,
        "version": "2.0",
        "project": detect_project_info(),
        "time": build_time_info(session_data, now),
        "conversation": session_data.get("conversation", {}),
        "operations": session_data.get("operations", {}),
        "summary": session_data.get("session_summary", {})
    }
    
    # 保存会话记录
    session_file = sessions_dir / f"{session_id}.json"
    save_json(session_file, session_record)
    
    # 更新会话索引
    update_session_index(session_id, session_record)
    
    return session_id


def build_time_info(session_data: dict, now: datetime) -> dict:
    """构建时间信息"""
    time_data = session_data.get("time", {})
    
    start_str = time_data.get("start", now.isoformat())
    end_str = time_data.get("end", now.isoformat())
    
    time_info = {
        "start": start_str,
        "end": end_str,
        "recorded_at": now.isoformat(),
        "duration_minutes": 0
    }
    
    # 计算时长
    try:
        # 处理时区
        start_clean = start_str.replace("Z", "+00:00")
        end_clean = end_str.replace("Z", "+00:00")
        
        if "+" not in start_clean and "-" not in start_clean[10:]:
            start = datetime.fromisoformat(start_clean)
        else:
            start = datetime.fromisoformat(start_clean)
        
        if "+" not in end_clean and "-" not in end_clean[10:]:
            end = datetime.fromisoformat(end_clean)
        else:
            end = datetime.fromisoformat(end_clean)
        
        # 简单计算（忽略时区差异）
        start_naive = datetime.fromisoformat(start_str[:19])
        end_naive = datetime.fromisoformat(end_str[:19])
        time_info["duration_minutes"] = int((end_naive - start_naive).total_seconds() / 60)
    except Exception as e:
        time_info["duration_minutes"] = 0
    
    return time_info


def update_session_index(session_id: str, session_record: dict):
    """更新会话索引"""
    data_dir = utils.DATA_DIR
    index_file = data_dir / "index" / "sessions_index.json"
    ensure_dir(index_file)
    
    # 读取或创建索引
    index = load_json(index_file, {"sessions": [], "total_count": 0})
    
    # 添加新会话索引
    summary = session_record.get("summary", {})
    index_entry = {
        "session_id": session_id,
        "date": session_record["time"]["recorded_at"][:10],
        "topic": summary.get("topic", ""),
        "tags": summary.get("tags", []),
        "workflow_stages": summary.get("workflow_stages", []),
        "technologies_used": summary.get("technologies_used", []),
        "duration_minutes": session_record["time"].get("duration_minutes", 0),
        "message_count": session_record.get("conversation", {}).get("message_count", 0)
    }
    
    index["sessions"].append(index_entry)
    index["total_count"] = len(index["sessions"])
    index["updated_at"] = get_timestamp()
    
    # 保留最近 1000 条索引
    if len(index["sessions"]) > 1000:
        index["sessions"] = index["sessions"][-1000:]
        index["total_count"] = len(index["sessions"])
    
    save_json(index_file, index)


def get_session_count_today() -> int:
    """获取今日会话数"""
    data_dir = utils.DATA_DIR
    month_str = get_month()
    date_str = datetime.now().strftime("%Y%m%d")
    
    sessions_dir = data_dir / "sessions" / month_str
    if not sessions_dir.exists():
        return 0
    
    return len(list(sessions_dir.glob(f"sess_{date_str}_*.json")))


def get_recent_sessions(limit: int = 10) -> list:
    """获取最近的会话记录"""
    data_dir = utils.DATA_DIR
    index_file = data_dir / "index" / "sessions_index.json"
    
    index = load_json(index_file, {"sessions": []})
    sessions = index.get("sessions", [])
    
    return sessions[-limit:]


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "message": "Missing session data"
        }))
        sys.exit(1)
    
    try:
        session_data = json.loads(sys.argv[1])
        session_id = record_session(session_data)
        
        print(json.dumps({
            "status": "success",
            "session_id": session_id,
            "message": f"Session {session_id} recorded successfully"
        }, ensure_ascii=False))
        
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
