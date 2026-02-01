#!/usr/bin/env python3
"""
本能管理脚本

用法：
  status                  显示所有本能
  create <json>           创建新本能
  update <id> <json>      更新本能
  delete <id>             删除本能
  evolve                  演化本能为技能
  --check-skill <name>    检查技能类型
  --delete-skill <name>   删除演化技能
  --sync                  同步和清理
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from utils import (
    get_data_dir, get_timestamp, load_config,
    parse_instinct_file, generate_instinct_file,
    load_skills_index, save_skills_index,
    add_skill_to_index, remove_skill_from_index,
    safe_write_file
)


def list_instincts() -> List[Dict]:
    """列出所有本能"""
    instincts_dir = get_data_dir() / "instincts"
    if not instincts_dir.exists():
        return []
    
    instincts = []
    for f in instincts_dir.glob("*.yaml"):
        try:
            content = f.read_text(encoding='utf-8')
            instinct = parse_instinct_file(content)
            instinct["_file"] = str(f)
            instincts.append(instinct)
        except Exception as e:
            print(f"Warning: Failed to parse {f}: {e}", file=sys.stderr)
    
    return instincts


def create_instinct(data: Dict) -> Dict:
    """创建新本能"""
    instincts_dir = get_data_dir() / "instincts"
    instincts_dir.mkdir(parents=True, exist_ok=True)
    
    # 验证必需字段
    if "id" not in data:
        return {"status": "error", "message": "缺少 id 字段"}
    
    # 设置默认值
    data.setdefault("confidence", 0.3)
    data.setdefault("domain", "general")
    data.setdefault("source", "manual")
    data.setdefault("created_at", get_timestamp())
    data.setdefault("updated_at", get_timestamp())
    data.setdefault("evidence_count", 1)
    
    # 生成默认内容
    if "content" not in data:
        data["content"] = f"""# {data['id']}

## 行为
{data.get('trigger', '未指定触发条件')}

## 证据
- 创建于 {data['created_at']}
"""
    
    # 生成文件内容
    content = generate_instinct_file(data)
    
    # 保存文件
    filepath = instincts_dir / f"{data['id']}.yaml"
    safe_write_file(filepath, content)
    
    return {
        "status": "success",
        "message": f"本能 '{data['id']}' 已创建",
        "path": str(filepath)
    }


def update_instinct(instinct_id: str, data: Dict) -> Dict:
    """更新本能"""
    instincts_dir = get_data_dir() / "instincts"
    filepath = instincts_dir / f"{instinct_id}.yaml"
    
    if not filepath.exists():
        return {"status": "error", "message": f"本能 '{instinct_id}' 不存在"}
    
    # 加载现有本能
    content = filepath.read_text(encoding='utf-8')
    instinct = parse_instinct_file(content)
    
    # 更新字段
    instinct.update(data)
    instinct["updated_at"] = get_timestamp()
    
    # 增加证据计数
    if "evidence_count" in instinct:
        instinct["evidence_count"] += 1
    
    # 保存
    new_content = generate_instinct_file(instinct)
    safe_write_file(filepath, new_content)
    
    return {
        "status": "success",
        "message": f"本能 '{instinct_id}' 已更新"
    }


def delete_instinct(instinct_id: str) -> Dict:
    """删除本能"""
    instincts_dir = get_data_dir() / "instincts"
    filepath = instincts_dir / f"{instinct_id}.yaml"
    
    if not filepath.exists():
        return {"status": "error", "message": f"本能 '{instinct_id}' 不存在"}
    
    filepath.unlink()
    
    return {
        "status": "success",
        "message": f"本能 '{instinct_id}' 已删除"
    }


def check_skill(skill_name: str) -> Dict:
    """检查技能是否是演化生成的"""
    index = load_skills_index()
    
    for skill in index.get("skills", []):
        if skill["name"] == skill_name:
            return {
                "is_evolved": True,
                "skill_name": skill_name,
                "path": skill.get("path"),
                "cursor_path": skill.get("cursor_path")
            }
    
    # 检查是否存在于 Cursor skills 目录
    cursor_path = Path.home() / ".cursor" / "skills" / skill_name
    if cursor_path.exists():
        return {
            "is_evolved": False,
            "skill_name": skill_name,
            "suggestion": f"'{skill_name}' 不是演化生成的技能。"
                         f"如果要删除，请手动执行: rm -rf {cursor_path}"
        }
    
    return {
        "is_evolved": False,
        "skill_name": skill_name,
        "suggestion": f"未找到名为 '{skill_name}' 的技能"
    }


def delete_evolved_skill(skill_name: str, delete_instincts: bool = False) -> Dict:
    """删除演化生成的技能"""
    result = {"status": "success", "deleted": [], "errors": []}
    
    # 1. 检查是否是演化技能
    check_result = check_skill(skill_name)
    if not check_result.get("is_evolved"):
        return {
            "status": "not_evolved",
            "message": check_result.get("suggestion")
        }
    
    # 2. 删除源文件
    evolved_path = get_data_dir() / "evolved" / "skills" / skill_name
    if evolved_path.exists():
        shutil.rmtree(evolved_path)
        result["deleted"].append(f"源文件: {evolved_path}")
    
    # 3. 删除 Cursor 同步
    cursor_path = Path.home() / ".cursor" / "skills" / f"evolved-{skill_name}"
    if cursor_path.exists():
        if cursor_path.is_symlink():
            cursor_path.unlink()
            result["deleted"].append(f"符号链接: {cursor_path}")
        else:
            shutil.rmtree(cursor_path)
            result["deleted"].append(f"同步目录: {cursor_path}")
    
    # 4. 更新索引
    remove_skill_from_index(skill_name)
    result["deleted"].append("技能索引已更新")
    
    # 5. 可选：删除相关本能
    if delete_instincts:
        deleted_instincts = delete_related_instincts(skill_name)
        result["deleted"].extend(deleted_instincts)
    
    return result


def delete_related_instincts(skill_name: str) -> List[str]:
    """删除与技能相关的本能"""
    deleted = []
    
    # 读取技能的 evolved_from 信息
    skill_path = get_data_dir() / "evolved" / "skills" / skill_name / "SKILL.md"
    if not skill_path.exists():
        return deleted
    
    content = skill_path.read_text(encoding='utf-8')
    
    # 简单解析 evolved_from
    instinct_ids = []
    in_evolved_from = False
    for line in content.split('\n'):
        if 'evolved_from:' in line:
            in_evolved_from = True
            continue
        if in_evolved_from:
            if line.strip().startswith('-'):
                # 提取本能 ID
                parts = line.strip()[1:].strip().split()
                if parts:
                    instinct_id = parts[0]
                    instinct_ids.append(instinct_id)
            elif line.strip() and not line.strip().startswith('-'):
                in_evolved_from = False
    
    # 删除相关本能
    for instinct_id in instinct_ids:
        instinct_path = get_data_dir() / "instincts" / f"{instinct_id}.yaml"
        if instinct_path.exists():
            instinct_path.unlink()
            deleted.append(f"本能: {instinct_id}")
    
    return deleted


def evolve_instincts() -> Dict:
    """将相关本能演化为技能"""
    instincts = list_instincts()
    
    if len(instincts) < 3:
        return {
            "status": "insufficient",
            "message": f"需要至少 3 个本能才能演化，当前有 {len(instincts)} 个"
        }
    
    # 按领域分组
    by_domain = {}
    for inst in instincts:
        domain = inst.get("domain", "general")
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(inst)
    
    # 找出可以演化的领域
    evolvable = []
    config = load_config()
    cluster_threshold = config.get("evolution", {}).get("cluster_threshold", 3)
    
    for domain, domain_instincts in by_domain.items():
        if len(domain_instincts) >= cluster_threshold:
            avg_confidence = sum(i.get("confidence", 0.5) for i in domain_instincts) / len(domain_instincts)
            if avg_confidence >= 0.5:
                evolvable.append({
                    "domain": domain,
                    "instincts": domain_instincts,
                    "avg_confidence": avg_confidence
                })
    
    if not evolvable:
        return {
            "status": "no_candidates",
            "message": "没有找到可以演化的本能组合（需要同一领域至少 3 个本能，平均置信度 >= 50%）"
        }
    
    # 生成技能
    created_skills = []
    for candidate in evolvable:
        skill_name = f"{candidate['domain']}-workflow"
        skill_result = create_evolved_skill(skill_name, candidate["instincts"])
        if skill_result.get("status") == "success":
            created_skills.append(skill_name)
    
    return {
        "status": "success",
        "created_skills": created_skills,
        "message": f"已创建 {len(created_skills)} 个技能"
    }


def create_evolved_skill(skill_name: str, instincts: List[Dict]) -> Dict:
    """创建演化技能"""
    # 1. 创建技能目录
    skill_dir = get_data_dir() / "evolved" / "skills" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. 生成 SKILL.md
    skill_content = generate_skill_content(skill_name, instincts)
    skill_file = skill_dir / "SKILL.md"
    safe_write_file(skill_file, skill_content)
    
    # 3. 同步到 Cursor
    cursor_dir = Path.home() / ".cursor" / "skills" / f"evolved-{skill_name}"
    try:
        if cursor_dir.exists():
            shutil.rmtree(cursor_dir)
        shutil.copytree(skill_dir, cursor_dir)
        synced = True
    except Exception as e:
        synced = False
        print(f"Warning: Failed to sync to Cursor: {e}", file=sys.stderr)
    
    # 4. 更新索引
    triggers = []
    for inst in instincts:
        trigger = inst.get("trigger", "")
        # 提取关键词
        words = trigger.replace("时", " ").replace("后", " ").replace("前", " ").split()
        triggers.extend(words)
    
    add_skill_to_index({
        "name": skill_name,
        "path": str(skill_dir),
        "cursor_path": str(cursor_dir),
        "triggers": list(set(triggers)),
        "domains": list(set(inst.get("domain", "general") for inst in instincts)),
        "evolved_at": get_timestamp(),
        "synced": synced
    })
    
    return {
        "status": "success",
        "skill_name": skill_name,
        "path": str(skill_dir),
        "cursor_path": str(cursor_dir),
        "synced": synced
    }


def generate_skill_content(skill_name: str, instincts: List[Dict]) -> str:
    """生成技能文件内容"""
    lines = [
        "---",
        f"name: {skill_name}",
        f"description: 基于 {len(instincts)} 个本能演化生成的技能",
        "evolved_from:"
    ]
    
    for inst in instincts:
        confidence = inst.get('confidence', 0.5)
        lines.append(f"  - {inst.get('id')} (置信度: {confidence})")
    
    lines.append(f"evolved_at: \"{get_timestamp()}\"")
    lines.append("---")
    lines.append("")
    
    # 标题
    title = skill_name.replace("-", " ").title()
    lines.append(f"# {title}")
    lines.append("")
    
    # 触发条件
    lines.append("## 触发条件")
    lines.append("")
    for inst in instincts:
        trigger = inst.get('trigger', '未知触发条件')
        lines.append(f"- {trigger}")
    lines.append("")
    
    # 行为
    lines.append("## 行为")
    lines.append("")
    for inst in instincts:
        content = inst.get("content", "")
        # 提取行为部分
        if "## 行为" in content:
            action = content.split("## 行为")[1].split("##")[0].strip()
            if action:
                lines.append(f"- {action[:200]}")
    
    if len(lines) == lines.index("## 行为") + 2:
        lines.append("- 根据本能执行相应操作")
    
    return "\n".join(lines)


def sync_and_cleanup() -> Dict:
    """同步和清理"""
    result = {"synced": [], "cleaned": [], "errors": []}
    
    # 1. 检查索引中的技能是否存在
    index = load_skills_index()
    for skill in index.get("skills", []):
        skill_path = Path(skill.get("path", ""))
        if not skill_path.exists():
            # 技能不存在，清理索引
            remove_skill_from_index(skill["name"])
            result["cleaned"].append(f"索引: {skill['name']}")
            
            # 清理 Cursor 同步
            cursor_path = Path(skill.get("cursor_path", ""))
            if cursor_path.exists():
                try:
                    if cursor_path.is_symlink():
                        cursor_path.unlink()
                    else:
                        shutil.rmtree(cursor_path)
                    result["cleaned"].append(f"Cursor: {cursor_path}")
                except Exception as e:
                    result["errors"].append(f"清理失败: {cursor_path}: {e}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description='本能管理脚本')
    parser.add_argument('command', nargs='?', help='命令: status, create, update, delete, evolve')
    parser.add_argument('args', nargs='*', help='命令参数')
    parser.add_argument('--check-skill', type=str, help='检查技能类型')
    parser.add_argument('--delete-skill', type=str, help='删除演化技能')
    parser.add_argument('--sync', action='store_true', help='同步和清理')
    
    args = parser.parse_args()
    
    if args.check_skill:
        result = check_skill(args.check_skill)
    elif args.delete_skill:
        result = delete_evolved_skill(args.delete_skill)
    elif args.sync:
        result = sync_and_cleanup()
    elif args.command == 'status':
        instincts = list_instincts()
        result = {
            "status": "success",
            "count": len(instincts),
            "instincts": [
                {
                    "id": i.get("id"),
                    "trigger": i.get("trigger"),
                    "confidence": i.get("confidence"),
                    "domain": i.get("domain")
                }
                for i in instincts
            ]
        }
    elif args.command == 'create':
        if not args.args:
            result = {"status": "error", "message": "请提供本能数据 JSON"}
        else:
            try:
                data = json.loads(args.args[0])
            except json.JSONDecodeError as e:
                result = {"status": "error", "message": f"Invalid JSON: {e}"}
                print(json.dumps(result, ensure_ascii=False, indent=2))
                sys.exit(1)
            result = create_instinct(data)
    elif args.command == 'update':
        if len(args.args) < 2:
            result = {"status": "error", "message": "请提供本能 ID 和更新数据 JSON"}
        else:
            try:
                data = json.loads(args.args[1])
            except json.JSONDecodeError as e:
                result = {"status": "error", "message": f"Invalid JSON: {e}"}
                print(json.dumps(result, ensure_ascii=False, indent=2))
                sys.exit(1)
            result = update_instinct(args.args[0], data)
    elif args.command == 'delete':
        if not args.args:
            result = {"status": "error", "message": "请提供本能 ID"}
        else:
            result = delete_instinct(args.args[0])
    elif args.command == 'evolve':
        result = evolve_instincts()
    else:
        result = {
            "status": "error",
            "message": "请指定命令: status, create, update, delete, evolve\n"
                      "或使用: --check-skill, --delete-skill, --sync"
        }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
