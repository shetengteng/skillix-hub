#!/usr/bin/env python3
"""搜索历史记忆"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from utils import (
    get_data_dir,
    extract_keywords,
    load_index,
    load_config,
    calculate_score,
    initialize_data_dir
)


def search_memories(
    query: str,
    location: str = None,
    max_candidates: int = None,
    search_scope_days: int = None
) -> dict:
    """
    搜索历史记忆
    
    Args:
        query: 搜索查询
        location: 搜索位置 ("project", "global", "project-first")
        max_candidates: 最大候选数量
        search_scope_days: 搜索范围天数
        
    Returns:
        搜索结果
    """
    # 加载配置
    config = load_config("project")
    
    if not config.get("enabled", True):
        return {"query": query, "candidates": [], "message": "Memory Skill 已禁用"}
    
    retrieval_config = config.get("retrieval", {})
    storage_config = config.get("storage", {})
    
    # 使用参数或配置值
    if location is None:
        location = storage_config.get("location", "project-first")
    if max_candidates is None:
        max_candidates = retrieval_config.get("max_candidates", 10)
    if search_scope_days is None:
        search_scope_days = retrieval_config.get("search_scope_days", 30)
    
    # 提取查询关键词
    query_keywords = set(extract_keywords(query))
    
    if not query_keywords:
        return {
            "query": query,
            "candidates": [],
            "message": "未能从查询中提取关键词"
        }
    
    # 计算截止日期
    if search_scope_days > 0:
        cutoff_date = (datetime.now() - timedelta(days=search_scope_days)).strftime("%Y-%m-%d")
    else:
        cutoff_date = "1970-01-01"  # 搜索全部
    
    # 确定搜索位置
    search_locations = []
    if location == "project-first":
        search_locations = [("project", True), ("global", False)]
    elif location == "project-only":
        search_locations = [("project", True)]
    elif location == "global-only":
        search_locations = [("global", False)]
    else:
        search_locations = [("project", True)]
    
    # 搜索所有位置
    all_results = []
    
    for loc, is_project_level in search_locations:
        try:
            initialize_data_dir(loc)
            index = load_index(loc)
            data_dir = get_data_dir(loc)
            
            for entry in index.get("entries", []):
                # 检查日期范围
                if entry["date"] < cutoff_date:
                    continue
                
                # 计算匹配分数
                memory_keywords = entry.get("keywords", [])
                matched = query_keywords & set(memory_keywords)
                
                if not matched:
                    continue
                
                # 计算天数
                try:
                    entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")
                    days_ago = (datetime.now() - entry_date).days
                except ValueError:
                    days_ago = 0
                
                # 计算综合分数
                score = calculate_score(
                    query_keywords,
                    memory_keywords,
                    days_ago,
                    is_project_level,
                    config
                )
                
                if score > 0:
                    all_results.append({
                        "entry": entry,
                        "score": score,
                        "matched_keywords": list(matched),
                        "location": loc,
                        "is_project_level": is_project_level,
                        "data_dir": str(data_dir)
                    })
        except Exception as e:
            # 如果某个位置出错，继续搜索其他位置
            continue
    
    # 按分数排序
    all_results.sort(key=lambda x: -x["score"])
    
    # 取前 N 个候选
    candidates = all_results[:max_candidates]
    
    # 获取详细内容
    detailed_candidates = []
    for c in candidates:
        entry = c["entry"]
        data_dir = Path(c["data_dir"])
        daily_file = data_dir / "daily" / f"{entry['date']}.md"
        
        # 默认内容为摘要
        content = entry.get("summary", "")
        
        # 尝试读取完整内容
        if daily_file.exists():
            try:
                lines = daily_file.read_text(encoding='utf-8').splitlines()
                line_range = entry.get("line_range", [0, len(lines)])
                start, end = line_range
                # 确保范围有效
                start = max(0, start - 1)  # 转为 0-indexed
                end = min(len(lines), end)
                content = "\n".join(lines[start:end])
            except Exception:
                pass
        
        detailed_candidates.append({
            "id": entry["id"],
            "date": entry["date"],
            "session": entry.get("session", 1),
            "summary": entry.get("summary", ""),
            "tags": entry.get("tags", []),
            "score": round(c["score"], 4),
            "matched_keywords": c["matched_keywords"],
            "location": c["location"],
            "content": content
        })
    
    return {
        "query": query,
        "query_keywords": list(query_keywords),
        "candidates_count": len(detailed_candidates),
        "candidates": detailed_candidates,
        "instruction": "请从以上候选记忆中，选出与用户问题最相关的 1-3 条，作为上下文回答用户问题。"
    }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "query": "",
            "candidates": [],
            "message": "用法: python3 search_memory.py \"搜索关键词\""
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    query = sys.argv[1]
    
    # 可选参数
    location = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = search_memories(query, location)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
