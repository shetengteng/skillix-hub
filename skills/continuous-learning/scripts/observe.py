#!/usr/bin/env python3
"""
观察脚本 - 管理会话生命周期

用法：
  --init                  会话开始时调用
  --record <json>         记录观察
  --finalize <json>       会话结束时调用
"""

import argparse
import json
import sys
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from utils import (
    get_data_dir, ensure_data_dirs, get_timestamp, get_month_str,
    load_config, load_pending_session, save_pending_session,
    clear_pending_session, add_observation_to_pending,
    load_skills_index, parse_instinct_file
)


def auto_finalize_pending_session() -> dict:
    """
    自动 finalize 上一个未完成的会话
    
    Returns:
        finalize 结果，如果没有 pending session 则返回 None
    """
    pending = load_pending_session()
    if not pending:
        return None
    
    observations = pending.get("observations", [])
    if not observations:
        clear_pending_session()
        return {"status": "skipped", "reason": "no_observations"}
    
    # 保存观察记录
    try:
        save_observations(pending)
        clear_pending_session()
        return {
            "status": "success",
            "message": "上一个会话已自动保存",
            "observation_count": len(observations)
        }
    except Exception as e:
        clear_pending_session()
        return {"status": "error", "message": str(e)}


def save_observations(session_data: dict):
    """保存观察记录到文件"""
    data_dir = get_data_dir()
    month_dir = data_dir / "observations" / get_month_str()
    month_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成文件名
    timestamp = get_timestamp().replace(":", "-").replace(".", "-")
    filename = f"obs_{timestamp}.jsonl"
    filepath = month_dir / filename
    
    # 写入观察记录
    with open(filepath, 'w', encoding='utf-8') as f:
        for obs in session_data.get("observations", []):
            f.write(json.dumps(obs, ensure_ascii=False) + '\n')
        
        # 添加会话元数据
        metadata = {
            "type": "session_metadata",
            "session_start": session_data.get("session_start"),
            "session_end": session_data.get("session_end", get_timestamp()),
            "topic": session_data.get("topic"),
            "summary": session_data.get("summary")
        }
        f.write(json.dumps(metadata, ensure_ascii=False) + '\n')


def load_instincts_summary() -> dict:
    """加载本能摘要"""
    data_dir = get_data_dir()
    instincts_dir = data_dir / "instincts"
    
    if not instincts_dir.exists():
        return {"count": 0, "domains": [], "high_confidence": []}
    
    instincts = []
    for f in instincts_dir.glob("*.yaml"):
        try:
            content = f.read_text(encoding='utf-8')
            instinct = parse_instinct_file(content)
            instincts.append(instinct)
        except:
            pass
    
    # 统计
    domains = list(set(i.get("domain", "general") for i in instincts))
    high_confidence = [i for i in instincts if i.get("confidence", 0) >= 0.7]
    
    return {
        "count": len(instincts),
        "domains": domains,
        "high_confidence": [
            {
                "id": i.get("id"),
                "trigger": i.get("trigger"),
                "confidence": i.get("confidence")
            }
            for i in high_confidence
        ]
    }


def generate_suggestions(skills: list, instincts: dict) -> list:
    """生成建议"""
    suggestions = []
    
    if skills:
        suggestions.append(f"已学习 {len(skills)} 个技能")
    
    if instincts.get("high_confidence"):
        for inst in instincts["high_confidence"][:3]:
            confidence = inst.get('confidence', 0)
            suggestions.append(f"高置信度本能: {inst.get('trigger', '未知')} ({confidence:.0%})")
    
    if not suggestions:
        suggestions.append("暂无学习历史，开始积累吧！")
    
    return suggestions


def handle_init() -> dict:
    """
    会话开始时的初始化
    
    处理流程：
    1. 自动 finalize 上一个未完成的会话
    2. 创建新的 pending session
    3. 加载已学习的知识
    4. 返回摘要和建议
    """
    try:
        ensure_data_dirs()
        
        # 1. 自动 finalize 上一个会话
        auto_result = auto_finalize_pending_session()
        
        # 2. 创建新的 pending session
        save_pending_session({})
        
        # 3. 加载配置
        config = load_config()
        
        # 4. 加载已学习的知识
        skills_index = load_skills_index()
        learned_skills = skills_index.get("skills", [])
        
        # 5. 加载本能摘要
        instincts_summary = load_instincts_summary()
        
        # 6. 生成建议
        suggestions = generate_suggestions(learned_skills, instincts_summary)
        
        result = {
            "status": "success",
            "learned_skills_count": len(learned_skills),
            "instincts_count": instincts_summary.get("count", 0),
            "high_confidence_instincts": instincts_summary.get("high_confidence", []),
            "suggestions": suggestions
        }
        
        if auto_result and auto_result.get("status") == "success":
            result["auto_finalized"] = auto_result
        
        return result
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def handle_record(data: dict) -> dict:
    """
    记录观察
    
    Args:
        data: 观察数据
    
    Returns:
        记录结果
    """
    try:
        ensure_data_dirs()
        add_observation_to_pending(data)
        return {"status": "success", "message": "观察已记录"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def handle_finalize(data: dict) -> dict:
    """
    会话结束时的处理
    
    Args:
        data: 会话数据（摘要、主题等）
    
    Returns:
        处理结果
    """
    try:
        ensure_data_dirs()
        
        # 1. 获取 pending session
        pending = load_pending_session()
        if pending:
            # 合并数据
            if "observations" not in data:
                data["observations"] = []
            data["observations"].extend(pending.get("observations", []))
            data["session_start"] = pending.get("session_start")
        
        data["session_end"] = get_timestamp()
        
        # 2. 保存观察记录
        if data.get("observations"):
            save_observations(data)
        
        # 3. 触发模式分析（可选）
        analysis_result = None
        config = load_config()
        if config.get("detection", {}).get("enabled", True):
            try:
                from analyze import analyze_observations
                analysis_result = analyze_observations(data.get("observations", []))
            except ImportError:
                pass
            except Exception as e:
                analysis_result = {"error": str(e)}
        
        # 4. 清除 pending session
        clear_pending_session()
        
        return {
            "status": "success",
            "message": "会话已保存",
            "observation_count": len(data.get("observations", [])),
            "analysis": analysis_result
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description='观察脚本')
    parser.add_argument('--init', action='store_true', help='会话开始')
    parser.add_argument('--record', type=str, help='记录观察')
    parser.add_argument('--finalize', type=str, help='会话结束')
    
    args = parser.parse_args()
    
    if args.init:
        result = handle_init()
    elif args.record:
        try:
            data = json.loads(args.record)
        except json.JSONDecodeError as e:
            result = {"status": "error", "message": f"Invalid JSON: {e}"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)
        result = handle_record(data)
    elif args.finalize:
        try:
            data = json.loads(args.finalize)
        except json.JSONDecodeError as e:
            result = {"status": "error", "message": f"Invalid JSON: {e}"}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)
        result = handle_finalize(data)
    else:
        result = {"status": "error", "message": "请指定 --init, --record 或 --finalize"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
