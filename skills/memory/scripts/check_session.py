#!/usr/bin/env python3
"""
Memory Skill - 会话检查脚本

在每次新会话开始时执行，检查上次会话状态并进行必要的数据维护。
这是三层保障机制中的第三层（兜底层）。

功能：
1. 检查上次会话是否正常结束
2. 提供数据摘要供 AI 参考
3. 清理过期数据（如果配置了保留天数）
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from utils import (
    get_data_dir,
    load_config,
    load_index,
    save_index,
    initialize_data_dir
)


def check_session(location: str = "project") -> dict:
    """
    检查会话状态
    
    Args:
        location: 存储位置 ("project" 或 "global")
        
    Returns:
        检查结果，包含状态和建议
    """
    # 检查配置
    config = load_config(location)
    if not config.get("enabled", True):
        return {
            "status": "disabled",
            "message": "Memory Skill 已禁用"
        }
    
    # 初始化数据目录
    initialize_data_dir(location)
    data_dir = get_data_dir(location)
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 加载索引
    index = load_index(location)
    
    # 获取数据摘要
    summary = get_data_summary(index, data_dir, location)
    
    # 检查是否需要清理过期数据
    retention_days = config.get("storage", {}).get("retention_days", -1)
    cleaned_count = 0
    if retention_days > 0:
        cleaned_count = cleanup_old_memories(index, data_dir, retention_days, location)
    
    # 获取最近的记忆
    recent_memories = get_recent_memories(index, days=7)
    
    return {
        "status": "success",
        "date": today,
        "summary": summary,
        "recent_memories": recent_memories,
        "cleaned_count": cleaned_count,
        "suggestions": generate_suggestions(summary, recent_memories)
    }


def get_data_summary(index: dict, data_dir: Path, location: str) -> dict:
    """获取数据摘要"""
    entries = index.get("entries", [])
    
    # 统计信息
    total_memories = len(entries)
    
    # 按日期分组
    dates = set(e["date"] for e in entries)
    total_days = len(dates)
    
    # 今日记忆数
    today = datetime.now().strftime("%Y-%m-%d")
    today_count = len([e for e in entries if e["date"] == today])
    
    # 最后更新时间
    last_updated = index.get("updated_at", None)
    
    # 数据目录大小
    daily_dir = data_dir / "daily"
    file_count = len(list(daily_dir.glob("*.md"))) if daily_dir.exists() else 0
    
    return {
        "total_memories": total_memories,
        "total_days": total_days,
        "today_count": today_count,
        "file_count": file_count,
        "last_updated": last_updated,
        "data_dir": str(data_dir),
        "location": location
    }


def get_recent_memories(index: dict, days: int = 7) -> list:
    """获取最近 N 天的记忆摘要"""
    entries = index.get("entries", [])
    
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    recent = [
        {
            "id": e["id"],
            "date": e["date"],
            "summary": e["summary"],
            "tags": e.get("tags", [])
        }
        for e in entries
        if e["date"] >= cutoff_date
    ]
    
    # 按日期倒序排列
    recent.sort(key=lambda x: (x["date"], x["id"]), reverse=True)
    
    return recent[:20]  # 最多返回 20 条


def cleanup_old_memories(index: dict, data_dir: Path, retention_days: int, location: str) -> int:
    """清理过期的记忆"""
    cutoff_date = (datetime.now() - timedelta(days=retention_days)).strftime("%Y-%m-%d")
    
    entries = index.get("entries", [])
    original_count = len(entries)
    
    # 过滤掉过期的记忆
    index["entries"] = [e for e in entries if e["date"] >= cutoff_date]
    
    cleaned_count = original_count - len(index["entries"])
    
    if cleaned_count > 0:
        # 保存更新后的索引
        save_index(index, location)
        
        # 删除过期的每日文件
        daily_dir = data_dir / "daily"
        if daily_dir.exists():
            for md_file in daily_dir.glob("*.md"):
                file_date = md_file.stem  # 文件名格式: YYYY-MM-DD.md
                if file_date < cutoff_date:
                    md_file.unlink()
    
    return cleaned_count


def generate_suggestions(summary: dict, recent_memories: list) -> list:
    """生成建议"""
    suggestions = []
    
    # 如果没有记忆，建议开始记录
    if summary["total_memories"] == 0:
        suggestions.append({
            "type": "info",
            "message": "这是你的第一次使用 Memory Skill，对话中的重要内容会被自动保存"
        })
    
    # 如果今天还没有记忆
    elif summary["today_count"] == 0 and recent_memories:
        suggestions.append({
            "type": "context",
            "message": f"最近 7 天有 {len(recent_memories)} 条记忆，可能与当前对话相关"
        })
    
    # 如果有很多记忆
    elif summary["total_memories"] > 100:
        suggestions.append({
            "type": "tip",
            "message": f"已积累 {summary['total_memories']} 条记忆，考虑设置 retention_days 自动清理旧记忆"
        })
    
    return suggestions


def main():
    """命令行入口"""
    # 解析参数
    location = "project"
    action = "check"
    
    if len(sys.argv) > 1:
        try:
            data = json.loads(sys.argv[1])
            location = data.get("location", "project")
            action = data.get("action", "check")
        except json.JSONDecodeError:
            # 如果不是 JSON，可能是简单的位置参数
            location = sys.argv[1]
    
    if action == "check":
        result = check_session(location)
    elif action == "summary":
        # 只返回摘要
        config = load_config(location)
        if not config.get("enabled", True):
            result = {"status": "disabled", "message": "Memory Skill 已禁用"}
        else:
            initialize_data_dir(location)
            data_dir = get_data_dir(location)
            index = load_index(location)
            result = {
                "status": "success",
                "summary": get_data_summary(index, data_dir, location)
            }
    elif action == "cleanup":
        # 手动触发清理
        config = load_config(location)
        retention_days = config.get("storage", {}).get("retention_days", -1)
        if retention_days <= 0:
            result = {
                "status": "skipped",
                "message": "retention_days 未设置或为 -1，不执行清理"
            }
        else:
            initialize_data_dir(location)
            data_dir = get_data_dir(location)
            index = load_index(location)
            cleaned = cleanup_old_memories(index, data_dir, retention_days, location)
            result = {
                "status": "success",
                "cleaned_count": cleaned,
                "message": f"已清理 {cleaned} 条过期记忆"
            }
    else:
        result = {
            "status": "error",
            "message": f"未知操作: {action}"
        }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
