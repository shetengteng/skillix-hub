#!/usr/bin/env python3
"""
分析脚本 - 从观察记录中提取模式

用法：
  --session <path>        分析指定会话文件
  --recent <days>         分析最近 N 天
  --observations <json>   分析观察数据
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional

# 添加脚本目录到路径
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from utils import get_data_dir, get_timestamp, load_config


# ─────────────────────────────────────────────
# 纠正关键词
# ─────────────────────────────────────────────

CORRECTION_KEYWORDS_CN = [
    "不要", "不是", "错了", "改成", "应该是", "换成",
    "别用", "不对", "修改", "改为", "不行"
]

CORRECTION_KEYWORDS_EN = [
    "no", "not", "wrong", "should be", "instead",
    "don't", "change to", "fix", "incorrect"
]

CORRECTION_KEYWORDS = CORRECTION_KEYWORDS_CN + CORRECTION_KEYWORDS_EN


def analyze_observations(observations: List[Dict]) -> Dict:
    """
    分析观察记录，提取模式
    
    Args:
        observations: 观察记录列表
    
    Returns:
        分析结果
    """
    result = {
        "patterns_found": [],
        "user_corrections": [],
        "error_resolutions": [],
        "tool_preferences": [],
        "pattern_count": 0
    }
    
    if not observations:
        return result
    
    # 1. 检测用户纠正
    corrections = detect_user_corrections(observations)
    result["user_corrections"] = corrections
    
    # 2. 检测错误解决
    resolutions = detect_error_resolutions(observations)
    result["error_resolutions"] = resolutions
    
    # 3. 检测工具偏好
    preferences = detect_tool_preferences(observations)
    result["tool_preferences"] = preferences
    
    # 4. 汇总模式
    all_patterns = corrections + resolutions + preferences
    result["patterns_found"] = all_patterns
    result["pattern_count"] = len(all_patterns)
    
    return result


def detect_user_corrections(observations: List[Dict]) -> List[Dict]:
    """
    检测用户纠正模式
    
    特征：
    1. AI 执行了某个操作
    2. 用户立即给出负面反馈或纠正
    3. AI 修改了之前的操作
    """
    corrections = []
    
    for i, obs in enumerate(observations):
        if obs.get("event") == "user_feedback":
            content = obs.get("content", "").lower()
            
            # 检查是否包含纠正关键词
            is_correction = any(kw in content for kw in CORRECTION_KEYWORDS)
            
            if is_correction:
                # 查找之前的 AI 操作
                prev_action = find_previous_action(observations, i)
                
                if prev_action:
                    corrections.append({
                        "type": "user_correction",
                        "original_action": prev_action,
                        "correction": obs.get("content"),
                        "timestamp": obs.get("timestamp")
                    })
    
    return corrections


def detect_error_resolutions(observations: List[Dict]) -> List[Dict]:
    """
    检测错误解决模式
    
    特征：
    1. 工具调用返回错误
    2. 后续操作解决了错误
    """
    resolutions = []
    
    for i, obs in enumerate(observations):
        # 检测错误事件
        is_error = (
            obs.get("event") == "tool_error" or
            obs.get("has_error") or
            (obs.get("event") == "tool_call" and obs.get("exit_code", 0) != 0)
        )
        
        if is_error:
            error_content = obs.get("error", obs.get("output", ""))
            
            # 查找后续的修复操作
            fix_action = find_fix_action(observations, i)
            
            if fix_action:
                resolutions.append({
                    "type": "error_resolution",
                    "error": str(error_content)[:200],  # 截断
                    "fix": fix_action,
                    "timestamp": obs.get("timestamp")
                })
    
    return resolutions


def detect_tool_preferences(observations: List[Dict]) -> List[Dict]:
    """
    检测工具偏好
    
    特征：
    1. 某个工具被频繁使用
    2. 使用频率超过阈值
    """
    tool_counts = {}
    
    for obs in observations:
        if obs.get("event") == "tool_call":
            tool = obs.get("tool", "unknown")
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
    
    # 找出高频工具
    preferences = []
    total = sum(tool_counts.values())
    
    if total == 0:
        return preferences
    
    for tool, count in tool_counts.items():
        ratio = count / total
        # 至少 3 次且占比 20%
        if count >= 3 and ratio >= 0.2:
            preferences.append({
                "type": "tool_preference",
                "tool": tool,
                "count": count,
                "ratio": round(ratio, 2)
            })
    
    # 按使用次数排序
    preferences.sort(key=lambda x: x["count"], reverse=True)
    
    return preferences


def find_previous_action(observations: List[Dict], current_index: int) -> Optional[Dict]:
    """查找之前的 AI 操作"""
    for i in range(current_index - 1, -1, -1):
        obs = observations[i]
        if obs.get("event") == "tool_call":
            return {
                "tool": obs.get("tool"),
                "input": obs.get("input"),
                "timestamp": obs.get("timestamp")
            }
    return None


def find_fix_action(observations: List[Dict], error_index: int) -> Optional[Dict]:
    """查找修复操作"""
    # 在错误后的 5 个操作内查找
    for i in range(error_index + 1, min(error_index + 6, len(observations))):
        obs = observations[i]
        if obs.get("event") == "tool_call":
            return {
                "tool": obs.get("tool"),
                "input": obs.get("input"),
                "timestamp": obs.get("timestamp")
            }
    return None


def analyze_session_file(filepath: Path) -> Dict:
    """分析会话文件"""
    observations = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    observations.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    
    return analyze_observations(observations)


def analyze_recent_sessions(days: int) -> Dict:
    """分析最近 N 天的会话"""
    from datetime import datetime, timedelta
    
    data_dir = get_data_dir()
    obs_dir = data_dir / "observations"
    
    if not obs_dir.exists():
        return {"status": "error", "message": "观察目录不存在"}
    
    # 收集所有观察记录
    all_observations = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for month_dir in obs_dir.iterdir():
        if not month_dir.is_dir():
            continue
        
        for obs_file in month_dir.glob("*.jsonl"):
            # 检查文件修改时间
            mtime = datetime.fromtimestamp(obs_file.stat().st_mtime)
            if mtime < cutoff_date:
                continue
            
            with open(obs_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            all_observations.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
    
    result = analyze_observations(all_observations)
    result["session_count"] = len(list(obs_dir.rglob("*.jsonl")))
    result["days_analyzed"] = days
    
    return result


def main():
    parser = argparse.ArgumentParser(description='分析脚本')
    parser.add_argument('--session', type=str, help='分析指定会话文件')
    parser.add_argument('--recent', type=int, help='分析最近 N 天')
    parser.add_argument('--observations', type=str, help='分析观察数据 JSON')
    
    args = parser.parse_args()
    
    if args.observations:
        try:
            observations = json.loads(args.observations)
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}, ensure_ascii=False))
            sys.exit(1)
        result = analyze_observations(observations)
    elif args.session:
        path = Path(args.session)
        if not path.exists():
            print(json.dumps({"status": "error", "message": "文件不存在"}, ensure_ascii=False))
            sys.exit(1)
        result = analyze_session_file(path)
    elif args.recent:
        result = analyze_recent_sessions(args.recent)
    else:
        result = {"status": "error", "message": "请指定 --session, --recent 或 --observations"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
