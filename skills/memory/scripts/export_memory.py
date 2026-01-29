#!/usr/bin/env python3
"""导出记忆数据"""

import sys
import json
from datetime import datetime
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from utils import (
    get_data_dir,
    get_project_root,
    load_index,
    load_config,
    initialize_data_dir
)


def export_memories(
    output_path: str = None,
    location: str = "project",
    date_from: str = None,
    date_to: str = None,
    include_content: bool = True
) -> dict:
    """
    导出记忆数据
    
    Args:
        output_path: 输出文件路径（默认为 memory-export-{timestamp}.json）
        location: 数据位置 ("project" 或 "global")
        date_from: 起始日期（可选，格式：YYYY-MM-DD）
        date_to: 结束日期（可选，格式：YYYY-MM-DD）
        include_content: 是否包含完整内容（默认 True）
        
    Returns:
        导出结果
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
    
    # 过滤日期范围
    if date_from:
        entries = [e for e in entries if e.get("date", "") >= date_from]
    if date_to:
        entries = [e for e in entries if e.get("date", "") <= date_to]
    
    if not entries:
        return {
            "success": True,
            "message": "没有符合条件的记忆可导出",
            "total_memories": 0
        }
    
    # 收集每日文件内容
    daily_files = {}
    if include_content:
        dates = set(e.get("date") for e in entries if e.get("date"))
        daily_dir = data_dir / "daily"
        for date in dates:
            daily_file = daily_dir / f"{date}.md"
            if daily_file.exists():
                try:
                    daily_files[date] = daily_file.read_text(encoding='utf-8')
                except Exception:
                    pass
    
    # 计算统计信息
    all_dates = [e.get("date") for e in entries if e.get("date")]
    all_keywords = set()
    for e in entries:
        all_keywords.update(e.get("keywords", []))
    
    # 构建导出数据
    export_data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "source": {
            "location": location,
            "project_path": str(get_project_root()) if location == "project" else None
        },
        "statistics": {
            "total_memories": len(entries),
            "date_range": {
                "start": min(all_dates) if all_dates else None,
                "end": max(all_dates) if all_dates else None
            },
            "total_keywords": len(all_keywords),
            "total_files": len(daily_files)
        },
        "index": {
            "version": index.get("version", "1.0"),
            "entries": entries
        },
        "daily_files": daily_files if include_content else {}
    }
    
    # 生成输出路径
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"memory-export-{timestamp}.json"
    
    # 写入文件
    output_file = Path(output_path)
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return {"success": False, "message": f"写入文件失败: {e}"}
    
    return {
        "success": True,
        "output_file": str(output_file.absolute()),
        "total_memories": len(entries),
        "total_files": len(daily_files),
        "date_range": export_data["statistics"]["date_range"],
        "message": f"已导出 {len(entries)} 条记忆到 {output_file}"
    }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        # 默认导出所有记忆
        result = export_memories()
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
        
        result = export_memories(
            output_path=data.get("output"),
            location=data.get("location", "project"),
            date_from=data.get("date_from"),
            date_to=data.get("date_to"),
            include_content=data.get("include_content", True)
        )
    else:
        # 简单参数：输出路径
        result = export_memories(output_path=arg)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if not result.get("success", True):
        sys.exit(1)


if __name__ == "__main__":
    main()
