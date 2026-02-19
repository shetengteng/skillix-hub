#!/usr/bin/env python3
"""保存对话记忆"""

import sys
import json
from datetime import datetime
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from utils import (
    get_data_dir,
    extract_keywords,
    load_index,
    save_index,
    initialize_data_dir,
    load_config
)


def save_memory(
    topic: str,
    key_info: list,
    tags: list = None,
    location: str = "project"
) -> dict:
    """
    保存对话记忆
    
    Args:
        topic: 对话主题
        key_info: 关键信息列表
        tags: 标签列表（以 # 开头）
        location: 存储位置 ("project" 或 "global")
        
    Returns:
        保存结果
    """
    # 检查配置
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    # 初始化数据目录
    initialize_data_dir(location)
    data_dir = get_data_dir(location)
    
    # 获取当前日期和时间
    today = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    
    # 加载索引，计算会话编号
    index = load_index(location)
    today_entries = [e for e in index["entries"] if e["date"] == today]
    session_num = len(today_entries) + 1
    memory_id = f"{today}-{session_num:03d}"
    
    # 构建 Markdown 内容
    md_content = f"\n## Session {session_num} - {time_str}\n\n"
    md_content += f"### 主题\n{topic}\n\n"
    md_content += "### 关键信息\n"
    for info in key_info:
        md_content += f"- {info}\n"
    
    if tags:
        md_content += f"\n### 标签\n{' '.join(tags)}\n"
    
    md_content += "\n---\n"
    
    # 写入每日文件
    daily_file = data_dir / "daily" / f"{today}.md"
    daily_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 如果文件不存在，创建文件头
    if not daily_file.exists():
        daily_file.write_text(f"# {today} 对话记忆\n", encoding='utf-8')
    
    # 计算行号范围（在追加之前）
    existing_lines = daily_file.read_text(encoding='utf-8').count('\n')
    start_line = existing_lines + 1
    
    # 追加内容
    with open(daily_file, 'a', encoding='utf-8') as f:
        f.write(md_content)
    
    # 计算结束行号
    end_line = start_line + md_content.count('\n') - 1
    
    # 提取关键词
    text_for_keywords = f"{topic} {' '.join(key_info)}"
    keywords = extract_keywords(text_for_keywords)
    
    # 更新索引
    index["entries"].append({
        "id": memory_id,
        "date": today,
        "session": session_num,
        "keywords": keywords,
        "summary": topic,
        "tags": tags or [],
        "line_range": [start_line, end_line]
    })
    save_index(index, location)
    
    return {
        "success": True,
        "memory_id": memory_id,
        "date": today,
        "session": session_num,
        "file": str(daily_file),
        "keywords": keywords,
        "message": f"记忆已保存: {memory_id}"
    }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": "用法: python3 save_memory.py '{\"topic\": \"主题\", \"key_info\": [\"要点\"], \"tags\": [\"#tag\"]}'"
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
    
    # 提取参数
    topic = data.get("topic", "")
    key_info = data.get("key_info", [])
    tags = data.get("tags", [])
    location = data.get("location", "project")
    
    if not topic:
        print(json.dumps({
            "success": False,
            "message": "缺少必需参数: topic"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    if not key_info:
        print(json.dumps({
            "success": False,
            "message": "缺少必需参数: key_info"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    # 保存记忆
    result = save_memory(topic, key_info, tags, location)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
