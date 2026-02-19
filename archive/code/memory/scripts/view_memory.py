#!/usr/bin/env python3
"""查看记忆"""

import sys
import json
from datetime import datetime
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from utils import (
    get_data_dir,
    load_index,
    initialize_data_dir,
    load_config
)


def view_memories_by_date(
    date: str = None,
    location: str = "project"
) -> dict:
    """
    查看指定日期的记忆
    
    Args:
        date: 日期（格式：YYYY-MM-DD），默认为今天
        location: 存储位置 ("project" 或 "global")
        
    Returns:
        查看结果
    """
    # 检查配置
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    # 初始化数据目录
    initialize_data_dir(location)
    data_dir = get_data_dir(location)
    
    # 默认为今天
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # 加载索引
    index = load_index(location)
    entries = index.get("entries", [])
    
    # 过滤指定日期的记忆
    date_entries = [e for e in entries if e.get("date") == date]
    
    if not date_entries:
        return {
            "success": True,
            "date": date,
            "count": 0,
            "memories": [],
            "message": f"日期 {date} 没有记忆"
        }
    
    # 获取详细内容
    memories = []
    daily_file = data_dir / "daily" / f"{date}.md"
    file_content = ""
    
    if daily_file.exists():
        try:
            file_content = daily_file.read_text(encoding='utf-8')
            lines = file_content.splitlines()
        except Exception:
            lines = []
    else:
        lines = []
    
    for entry in date_entries:
        content = entry.get("summary", "")
        line_range = entry.get("line_range", [])
        
        # 尝试读取完整内容
        if lines and line_range:
            start, end = line_range
            start = max(0, start - 1)  # 转为 0-indexed
            end = min(len(lines), end)
            content = "\n".join(lines[start:end])
            
            # 检查是否已删除
            if "<!-- DELETED:" in content:
                continue
        
        memories.append({
            "id": entry.get("id"),
            "session": entry.get("session", 1),
            "summary": entry.get("summary", ""),
            "tags": entry.get("tags", []),
            "keywords": entry.get("keywords", []),
            "content": content
        })
    
    return {
        "success": True,
        "date": date,
        "count": len(memories),
        "memories": memories,
        "message": f"日期 {date} 共有 {len(memories)} 条记忆"
    }


def view_recent_memories(
    days: int = 7,
    location: str = "project"
) -> dict:
    """
    查看最近几天的记忆
    
    Args:
        days: 天数（默认 7 天）
        location: 存储位置 ("project" 或 "global")
        
    Returns:
        查看结果
    """
    # 检查配置
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    # 初始化数据目录
    initialize_data_dir(location)
    
    # 加载索引
    index = load_index(location)
    entries = index.get("entries", [])
    
    # 计算截止日期
    from datetime import timedelta
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # 过滤最近的记忆
    recent_entries = [e for e in entries if e.get("date", "") >= cutoff_date]
    
    # 按日期分组
    by_date = {}
    for entry in recent_entries:
        date = entry.get("date")
        if date not in by_date:
            by_date[date] = []
        by_date[date].append({
            "id": entry.get("id"),
            "session": entry.get("session", 1),
            "summary": entry.get("summary", ""),
            "tags": entry.get("tags", [])
        })
    
    # 按日期排序（最近的在前）
    sorted_dates = sorted(by_date.keys(), reverse=True)
    result_by_date = []
    for date in sorted_dates:
        result_by_date.append({
            "date": date,
            "count": len(by_date[date]),
            "memories": by_date[date]
        })
    
    total_count = sum(len(by_date[d]) for d in by_date)
    
    return {
        "success": True,
        "days": days,
        "total_count": total_count,
        "by_date": result_by_date,
        "message": f"最近 {days} 天共有 {total_count} 条记忆"
    }


def list_all_dates(location: str = "project") -> dict:
    """
    列出所有有记忆的日期
    
    Args:
        location: 存储位置 ("project" 或 "global")
        
    Returns:
        日期列表
    """
    # 检查配置
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    # 初始化数据目录
    initialize_data_dir(location)
    
    # 加载索引
    index = load_index(location)
    entries = index.get("entries", [])
    
    # 统计每个日期的记忆数量
    date_counts = {}
    for entry in entries:
        date = entry.get("date")
        if date:
            date_counts[date] = date_counts.get(date, 0) + 1
    
    # 按日期排序（最近的在前）
    sorted_dates = sorted(date_counts.keys(), reverse=True)
    dates = [{"date": d, "count": date_counts[d]} for d in sorted_dates]
    
    return {
        "success": True,
        "total_dates": len(dates),
        "total_memories": len(entries),
        "dates": dates,
        "message": f"共有 {len(dates)} 天的记忆，总计 {len(entries)} 条"
    }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        # 默认查看今日记忆
        result = view_memories_by_date()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    arg = sys.argv[1]
    
    # 检查是否为 JSON 参数
    if arg.startswith('{'):
        try:
            data = json.loads(arg)
        except json.JSONDecodeError as e:
            print(json.dumps({
                "success": False,
                "message": f"JSON 解析错误: {e}"
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
        
        location = data.get("location", "project")
        
        if data.get("list_dates"):
            result = list_all_dates(location)
        elif data.get("recent"):
            days = data.get("days", 7)
            result = view_recent_memories(days, location)
        elif data.get("date"):
            result = view_memories_by_date(data["date"], location)
        else:
            result = view_memories_by_date(None, location)
    else:
        # 简单参数：日期或 "today" 或 "recent"
        if arg == "today":
            result = view_memories_by_date()
        elif arg == "recent":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            result = view_recent_memories(days)
        elif arg == "list":
            result = list_all_dates()
        else:
            # 假设是日期
            result = view_memories_by_date(arg)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if not result.get("success", True):
        sys.exit(1)


if __name__ == "__main__":
    main()
