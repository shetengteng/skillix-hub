#!/usr/bin/env python3
"""
Memory Skill 汇总脚本

将临时记忆汇总为结构化的每日记忆。

用法：
  --session               汇总当前会话的临时记忆
  --date <YYYY-MM-DD>     汇总指定日期的临时记忆
  --all                   汇总所有未处理的临时记忆
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from utils import (
    load_config, get_data_dir, initialize_data_dir,
    get_temp_memories, clear_pending_session,
    calculate_similarity, extract_keywords
)


def group_by_category(temp_memories: List[Dict]) -> Dict[str, List[Dict]]:
    """
    按类别分组临时记忆
    
    Args:
        temp_memories: 临时记忆列表
        
    Returns:
        按类别分组的字典
    """
    groups = {}
    
    for mem in temp_memories:
        category = mem.get("trigger_category", "general")
        if category not in groups:
            groups[category] = []
        groups[category].append(mem)
    
    return groups


def merge_similar_memories(memories: List[Dict], similarity_threshold: float = 0.8) -> List[Dict]:
    """
    合并相似的记忆
    
    Args:
        memories: 记忆列表
        similarity_threshold: 相似度阈值
        
    Returns:
        合并后的记忆列表
    """
    if not memories:
        return []
    
    merged = []
    used = set()
    
    for i, mem1 in enumerate(memories):
        if i in used:
            continue
        
        # 找出与当前记忆相似的所有记忆
        similar_group = [mem1]
        
        for j, mem2 in enumerate(memories[i+1:], start=i+1):
            if j in used:
                continue
            
            # 计算相似度
            topic1 = mem1.get("extracted_info", {}).get("topic", "")
            topic2 = mem2.get("extracted_info", {}).get("topic", "")
            
            if topic1 and topic2:
                similarity = calculate_similarity(topic1, topic2)
            else:
                # 使用用户消息计算相似度
                msg1 = mem1.get("user_message", "")
                msg2 = mem2.get("user_message", "")
                similarity = calculate_similarity(msg1, msg2)
            
            if similarity >= similarity_threshold:
                similar_group.append(mem2)
                used.add(j)
        
        # 合并相似记忆
        if len(similar_group) > 1:
            merged_mem = merge_memory_group(similar_group)
        else:
            merged_mem = mem1
        
        merged.append(merged_mem)
        used.add(i)
    
    return merged


def merge_memory_group(memories: List[Dict]) -> Dict:
    """
    合并一组相似的记忆
    
    Args:
        memories: 相似记忆列表
        
    Returns:
        合并后的单个记忆
    """
    # 使用最新的记忆作为基础
    memories_sorted = sorted(memories, key=lambda x: x.get("timestamp", ""), reverse=True)
    base = memories_sorted[0].copy()
    
    # 合并所有 key_info
    all_key_info = []
    all_tags = set()
    
    for mem in memories:
        info = mem.get("extracted_info", {})
        all_key_info.extend(info.get("key_info", []))
        all_tags.update(info.get("tags", []))
    
    # 去重 key_info
    unique_key_info = list(dict.fromkeys(all_key_info))
    
    # 更新合并后的记忆
    if "extracted_info" not in base:
        base["extracted_info"] = {}
    
    base["extracted_info"]["key_info"] = unique_key_info
    base["extracted_info"]["tags"] = list(all_tags)
    base["merged_count"] = len(memories)
    
    return base


def generate_session_content(memories: List[Dict], session_time: str = None) -> str:
    """
    生成会话内容的 Markdown 格式
    
    Args:
        memories: 记忆列表
        session_time: 会话时间
        
    Returns:
        Markdown 格式的内容
    """
    if session_time is None:
        session_time = datetime.now().strftime("%H:%M:%S")
    
    lines = [f"## Session - {session_time}", ""]
    
    # 提取主题
    topics = []
    for mem in memories:
        topic = mem.get("extracted_info", {}).get("topic", "")
        if topic and topic not in topics:
            topics.append(topic)
    
    if topics:
        lines.append("### 主题")
        lines.append(", ".join(topics[:3]))  # 最多 3 个主题
        lines.append("")
    
    # 提取关键信息
    all_key_info = []
    for mem in memories:
        info = mem.get("extracted_info", {})
        all_key_info.extend(info.get("key_info", []))
    
    # 去重
    unique_key_info = list(dict.fromkeys(all_key_info))
    
    if unique_key_info:
        lines.append("### 关键信息")
        for info in unique_key_info[:10]:  # 最多 10 条
            lines.append(f"- {info}")
        lines.append("")
    
    # 提取标签
    all_tags = set()
    for mem in memories:
        info = mem.get("extracted_info", {})
        all_tags.update(info.get("tags", []))
    
    if all_tags:
        lines.append("### 标签")
        lines.append(" ".join(sorted(all_tags)))
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    return "\n".join(lines)


def save_to_daily_file(content: str, date_str: str = None, location: str = "project") -> str:
    """
    保存到每日记忆文件
    
    Args:
        content: 要保存的内容
        date_str: 日期字符串 (YYYY-MM-DD)
        location: 存储位置
        
    Returns:
        保存的文件路径
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    data_dir = get_data_dir(location)
    daily_dir = data_dir / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    
    daily_file = daily_dir / f"{date_str}.md"
    
    # 如果文件不存在，创建标题
    if not daily_file.exists():
        header = f"# {date_str} 对话记忆\n\n"
        with open(daily_file, 'w', encoding='utf-8') as f:
            f.write(header)
    
    # 追加内容
    with open(daily_file, 'a', encoding='utf-8') as f:
        f.write(content)
    
    return str(daily_file)


def update_index(memories: List[Dict], date_str: str, location: str = "project"):
    """
    更新关键词索引
    
    Args:
        memories: 记忆列表
        date_str: 日期字符串
        location: 存储位置
    """
    from utils import load_index, save_index
    
    index = load_index(location)
    
    # 提取所有关键词
    all_keywords = set()
    all_tags = set()
    
    for mem in memories:
        # 从用户消息提取关键词
        user_msg = mem.get("user_message", "")
        all_keywords.update(extract_keywords(user_msg))
        
        # 从 extracted_info 提取
        info = mem.get("extracted_info", {})
        topic = info.get("topic", "")
        if topic:
            all_keywords.update(extract_keywords(topic))
        
        all_tags.update(info.get("tags", []))
    
    # 创建索引条目
    entry = {
        "date": date_str,
        "keywords": list(all_keywords),
        "tags": list(all_tags),
        "memory_count": len(memories),
        "created_at": datetime.now().isoformat()
    }
    
    # 检查是否已存在该日期的条目
    existing_idx = None
    for i, e in enumerate(index.get("entries", [])):
        if e.get("date") == date_str:
            existing_idx = i
            break
    
    if existing_idx is not None:
        # 合并关键词和标签
        existing = index["entries"][existing_idx]
        existing["keywords"] = list(set(existing.get("keywords", []) + entry["keywords"]))
        existing["tags"] = list(set(existing.get("tags", []) + entry["tags"]))
        existing["memory_count"] = existing.get("memory_count", 0) + entry["memory_count"]
        existing["updated_at"] = datetime.now().isoformat()
    else:
        index["entries"].append(entry)
    
    save_index(index, location)


def summarize_temp_memories(
    temp_memories: List[Dict],
    location: str = "project",
    session_data: Dict = None
) -> Dict:
    """
    汇总临时记忆
    
    Args:
        temp_memories: 临时记忆列表
        location: 存储位置
        session_data: 会话数据（可选）
        
    Returns:
        汇总结果
    """
    if not temp_memories:
        return {"status": "skipped", "reason": "no_memories"}
    
    config = load_config(location)
    summarize_config = config.get("summarize", {})
    
    # 1. 按类别分组
    groups = group_by_category(temp_memories)
    
    # 2. 合并相似记忆
    similarity_threshold = summarize_config.get("similarity_threshold", 0.8)
    merged_memories = []
    
    for category, memories in groups.items():
        merged = merge_similar_memories(memories, similarity_threshold)
        merged_memories.extend(merged)
    
    # 3. 生成会话内容
    session_time = None
    if temp_memories:
        first_timestamp = temp_memories[0].get("timestamp", "")
        if first_timestamp:
            try:
                dt = datetime.fromisoformat(first_timestamp)
                session_time = dt.strftime("%H:%M:%S")
            except ValueError:
                pass
    
    content = generate_session_content(merged_memories, session_time)
    
    # 4. 保存到每日文件
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = save_to_daily_file(content, date_str, location)
    
    # 5. 更新索引
    update_index(merged_memories, date_str, location)
    
    return {
        "status": "success",
        "original_count": len(temp_memories),
        "merged_count": len(merged_memories),
        "file_path": file_path,
        "date": date_str
    }


def handle_session(location: str = "project") -> Dict:
    """处理当前会话的临时记忆"""
    temp_memories = get_temp_memories(location)
    
    if not temp_memories:
        return {"status": "skipped", "reason": "no_temp_memories"}
    
    result = summarize_temp_memories(temp_memories, location)
    
    if result.get("status") == "success":
        clear_pending_session(location)
    
    return result


def handle_date(date_str: str, location: str = "project") -> Dict:
    """处理指定日期的临时记忆"""
    # 这个功能暂时不实现，因为临时记忆是按会话存储的
    return {"status": "not_implemented", "message": "按日期汇总功能暂未实现"}


def handle_all(location: str = "project") -> Dict:
    """处理所有未处理的临时记忆"""
    # 目前只处理当前会话
    return handle_session(location)


def main():
    parser = argparse.ArgumentParser(description='Memory Skill 汇总脚本')
    parser.add_argument('--session', action='store_true', help='汇总当前会话')
    parser.add_argument('--date', type=str, help='汇总指定日期')
    parser.add_argument('--all', action='store_true', help='汇总所有')
    parser.add_argument('--location', type=str, default='project', help='存储位置')
    
    args = parser.parse_args()
    
    if args.session:
        result = handle_session(args.location)
    elif args.date:
        result = handle_date(args.date, args.location)
    elif args.all:
        result = handle_all(args.location)
    else:
        result = {"status": "error", "message": "请指定 --session, --date 或 --all"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
