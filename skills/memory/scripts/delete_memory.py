#!/usr/bin/env python3
"""删除记忆"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from utils import (
    get_data_dir,
    load_index,
    save_index,
    initialize_data_dir,
    load_config
)


def delete_memory_by_id(
    memory_id: str,
    location: str = "project"
) -> dict:
    """
    删除指定 ID 的记忆
    
    Args:
        memory_id: 记忆 ID（格式：YYYY-MM-DD-NNN）
        location: 存储位置 ("project" 或 "global")
        
    Returns:
        删除结果
    """
    # 检查配置
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    # 初始化数据目录
    initialize_data_dir(location)
    data_dir = get_data_dir(location)
    
    # 加载索引
    index = load_index(location)
    entries = index.get("entries", [])
    
    # 查找要删除的记忆
    target_entry = None
    target_index = -1
    for i, entry in enumerate(entries):
        if entry.get("id") == memory_id:
            target_entry = entry
            target_index = i
            break
    
    if target_entry is None:
        return {
            "success": False,
            "message": f"未找到记忆: {memory_id}"
        }
    
    # 从索引中删除
    entries.pop(target_index)
    index["entries"] = entries
    save_index(index, location)
    
    # 尝试从每日文件中删除内容（可选，保留文件但标记为已删除）
    date = target_entry.get("date")
    line_range = target_entry.get("line_range", [])
    
    deleted_from_file = False
    if date and line_range:
        daily_file = data_dir / "daily" / f"{date}.md"
        if daily_file.exists():
            try:
                lines = daily_file.read_text(encoding='utf-8').splitlines()
                start, end = line_range
                start = max(0, start - 1)  # 转为 0-indexed
                end = min(len(lines), end)
                
                # 标记为已删除而不是物理删除（保持行号一致性）
                for i in range(start, end):
                    if i < len(lines):
                        lines[i] = f"<!-- DELETED: {lines[i]} -->"
                
                daily_file.write_text('\n'.join(lines), encoding='utf-8')
                deleted_from_file = True
            except Exception as e:
                # 文件删除失败不影响索引删除
                pass
    
    return {
        "success": True,
        "memory_id": memory_id,
        "date": date,
        "deleted_from_index": True,
        "deleted_from_file": deleted_from_file,
        "message": f"记忆已删除: {memory_id}"
    }


def delete_memories_by_date(
    date: str,
    location: str = "project"
) -> dict:
    """
    删除指定日期的所有记忆
    
    Args:
        date: 日期（格式：YYYY-MM-DD）
        location: 存储位置 ("project" 或 "global")
        
    Returns:
        删除结果
    """
    # 检查配置
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    # 初始化数据目录
    initialize_data_dir(location)
    data_dir = get_data_dir(location)
    
    # 加载索引
    index = load_index(location)
    entries = index.get("entries", [])
    
    # 过滤掉指定日期的记忆
    original_count = len(entries)
    entries = [e for e in entries if e.get("date") != date]
    deleted_count = original_count - len(entries)
    
    if deleted_count == 0:
        return {
            "success": False,
            "message": f"未找到日期 {date} 的记忆"
        }
    
    # 保存更新后的索引
    index["entries"] = entries
    save_index(index, location)
    
    # 删除每日文件
    daily_file = data_dir / "daily" / f"{date}.md"
    file_deleted = False
    if daily_file.exists():
        try:
            daily_file.unlink()
            file_deleted = True
        except Exception:
            pass
    
    return {
        "success": True,
        "date": date,
        "deleted_count": deleted_count,
        "file_deleted": file_deleted,
        "message": f"已删除 {date} 的 {deleted_count} 条记忆"
    }


def clear_all_memories(
    location: str = "project",
    confirm: bool = False
) -> dict:
    """
    清空所有记忆
    
    Args:
        location: 存储位置 ("project" 或 "global")
        confirm: 确认删除（必须为 True 才会执行）
        
    Returns:
        删除结果
    """
    if not confirm:
        return {
            "success": False,
            "message": "清空所有记忆需要确认，请设置 confirm=true"
        }
    
    # 检查配置
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    # 初始化数据目录
    initialize_data_dir(location)
    data_dir = get_data_dir(location)
    
    # 加载索引获取记忆数量
    index = load_index(location)
    total_count = len(index.get("entries", []))
    
    # 清空索引
    index["entries"] = []
    save_index(index, location)
    
    # 删除所有每日文件
    daily_dir = data_dir / "daily"
    files_deleted = 0
    if daily_dir.exists():
        for f in daily_dir.glob("*.md"):
            try:
                f.unlink()
                files_deleted += 1
            except Exception:
                pass
    
    return {
        "success": True,
        "location": location,
        "deleted_count": total_count,
        "files_deleted": files_deleted,
        "message": f"已清空所有记忆，共删除 {total_count} 条记忆，{files_deleted} 个文件"
    }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": """用法:
  删除指定记忆: python3 delete_memory.py '{"id": "2026-01-29-001"}'
  删除指定日期: python3 delete_memory.py '{"date": "2026-01-29"}'
  清空所有记忆: python3 delete_memory.py '{"clear_all": true, "confirm": true}'"""
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({
            "success": False,
            "message": f"JSON 解析错误: {e}"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    location = data.get("location", "project")
    
    # 根据参数决定操作
    if data.get("clear_all"):
        result = clear_all_memories(location, data.get("confirm", False))
    elif data.get("date"):
        result = delete_memories_by_date(data["date"], location)
    elif data.get("id"):
        result = delete_memory_by_id(data["id"], location)
    else:
        result = {
            "success": False,
            "message": "请提供 id、date 或 clear_all 参数"
        }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
