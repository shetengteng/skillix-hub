#!/usr/bin/env python3
"""导入记忆数据"""

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
    save_index,
    load_config,
    initialize_data_dir
)


def import_memories(
    input_path: str,
    location: str = "project",
    mode: str = "merge",
    overwrite_existing: bool = False
) -> dict:
    """
    导入记忆数据
    
    Args:
        input_path: 输入文件路径
        location: 目标位置 ("project" 或 "global")
        mode: 导入模式 ("merge" 合并, "replace" 替换)
        overwrite_existing: 是否覆盖已存在的记忆
        
    Returns:
        导入结果
    """
    # 检查配置
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    # 读取导入文件
    input_file = Path(input_path)
    if not input_file.exists():
        return {"success": False, "message": f"文件不存在: {input_path}"}
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
    except json.JSONDecodeError as e:
        return {"success": False, "message": f"JSON 解析错误: {e}"}
    except Exception as e:
        return {"success": False, "message": f"读取文件失败: {e}"}
    
    # 验证版本
    version = import_data.get("version")
    if version != "1.0":
        return {"success": False, "message": f"不支持的导出版本: {version}"}
    
    # 初始化数据目录
    initialize_data_dir(location)
    data_dir = get_data_dir(location)
    
    # 获取导入数据
    imported_entries = import_data.get("index", {}).get("entries", [])
    daily_files = import_data.get("daily_files", {})
    
    if not imported_entries:
        return {
            "success": True,
            "message": "导入文件中没有记忆数据",
            "imported_count": 0
        }
    
    if mode == "replace":
        # 替换模式：清空现有数据
        index = {"version": "1.0", "updated_at": None, "entries": []}
        # 删除现有每日文件
        daily_dir = data_dir / "daily"
        if daily_dir.exists():
            for f in daily_dir.glob("*.md"):
                try:
                    f.unlink()
                except Exception:
                    pass
    else:
        # 合并模式：加载现有索引
        index = load_index(location)
    
    # 获取现有 ID 集合
    existing_ids = set(e.get("id") for e in index.get("entries", []))
    
    # 导入记忆
    imported_count = 0
    skipped_count = 0
    overwritten_count = 0
    
    for entry in imported_entries:
        entry_id = entry.get("id")
        if entry_id in existing_ids:
            if overwrite_existing:
                # 移除旧条目
                index["entries"] = [e for e in index["entries"] if e.get("id") != entry_id]
                overwritten_count += 1
            else:
                skipped_count += 1
                continue
        
        index["entries"].append(entry)
        imported_count += 1
    
    # 保存索引
    save_index(index, location)
    
    # 导入每日文件
    files_imported = 0
    files_skipped = 0
    daily_dir = data_dir / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    
    for date, content in daily_files.items():
        daily_file = daily_dir / f"{date}.md"
        if daily_file.exists() and not overwrite_existing and mode != "replace":
            files_skipped += 1
            continue
        try:
            daily_file.write_text(content, encoding='utf-8')
            files_imported += 1
        except Exception:
            pass
    
    return {
        "success": True,
        "imported_count": imported_count,
        "skipped_count": skipped_count,
        "overwritten_count": overwritten_count,
        "files_imported": files_imported,
        "files_skipped": files_skipped,
        "mode": mode,
        "message": f"已导入 {imported_count} 条记忆，跳过 {skipped_count} 条，覆盖 {overwritten_count} 条"
    }


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": """用法:
  合并导入: python3 import_memory.py '{"input": "backup.json"}'
  替换导入: python3 import_memory.py '{"input": "backup.json", "mode": "replace"}'
  覆盖冲突: python3 import_memory.py '{"input": "backup.json", "overwrite": true}'"""
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
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
        
        if not data.get("input"):
            print(json.dumps({
                "success": False,
                "message": "缺少必需参数: input"
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
        
        result = import_memories(
            input_path=data["input"],
            location=data.get("location", "project"),
            mode=data.get("mode", "merge"),
            overwrite_existing=data.get("overwrite", False)
        )
    else:
        # 简单参数：输入路径
        result = import_memories(input_path=arg)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if not result.get("success", True):
        sys.exit(1)


if __name__ == "__main__":
    main()
