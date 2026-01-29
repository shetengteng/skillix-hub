#!/usr/bin/env python3
"""Memory Skill 工具函数"""

import json
import re
import os
from datetime import datetime
from pathlib import Path


def get_project_root() -> Path:
    """
    获取项目根目录
    
    查找顺序：
    1. 从脚本位置向上查找 .cursor 或 .git 目录
    2. 从当前工作目录向上查找 .cursor 或 .git 目录
    """
    # 首先尝试从脚本位置向上查找
    script_path = Path(__file__).resolve()
    current = script_path.parent
    while current != current.parent:
        if (current / ".cursor").exists() or (current / ".git").exists():
            return current
        current = current.parent
    
    # 否则从当前工作目录向上查找
    current = Path.cwd()
    while current != current.parent:
        if (current / ".cursor").exists() or (current / ".git").exists():
            return current
        current = current.parent
    
    # 如果没找到，返回当前目录
    return Path.cwd()


def get_skill_dir() -> Path:
    """获取 Skill 代码目录"""
    # 首先尝试从脚本位置推断
    script_path = Path(__file__).resolve()
    if script_path.parent.name == "scripts":
        return script_path.parent.parent
    # 否则使用项目路径
    return get_project_root() / ".cursor" / "skills" / "memory"


def get_data_dir(location: str = "project") -> Path:
    """
    获取用户数据目录
    
    Args:
        location: "project" 或 "global"
    """
    if location == "global":
        data_dir = Path.home() / ".cursor" / "skills" / "memory-data"
    else:
        data_dir = get_project_root() / ".cursor" / "skills" / "memory-data"
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def initialize_data_dir(location: str = "project"):
    """首次使用时初始化数据目录"""
    data_dir = get_data_dir(location)
    
    # 创建子目录
    (data_dir / "daily").mkdir(parents=True, exist_ok=True)
    (data_dir / "index").mkdir(parents=True, exist_ok=True)
    
    # 初始化索引文件
    index_file = data_dir / "index" / "keywords.json"
    if not index_file.exists():
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump({
                "version": "1.0",
                "updated_at": None,
                "entries": []
            }, f, ensure_ascii=False, indent=2)
    
    # 初始化配置文件（从默认配置复制）
    config_file = data_dir / "config.json"
    if not config_file.exists():
        default_config = get_skill_dir() / "default_config.json"
        if default_config.exists():
            with open(default_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        else:
            # 使用内置默认配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(get_default_config(), f, ensure_ascii=False, indent=2)


def get_default_config() -> dict:
    """获取默认配置"""
    return {
        "version": "1.0",
        "enabled": True,
        "auto_save": True,
        "auto_retrieve": True,
        "storage": {
            "location": "project-first",
            "retention_days": -1
        },
        "retrieval": {
            "max_candidates": 10,
            "max_results": 3,
            "search_scope_days": 30,
            "time_decay_rate": 0.95,
            "source_weight": {
                "project": 1.0,
                "global": 0.7
            }
        }
    }


def load_config(location: str = "project") -> dict:
    """加载配置"""
    initialize_data_dir(location)
    config_path = get_data_dir(location) / "config.json"
    
    default = get_default_config()
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            # 深度合并配置
            return deep_merge(default, user_config)
        except json.JSONDecodeError:
            return default
    return default


def deep_merge(base: dict, override: dict) -> dict:
    """深度合并两个字典"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def extract_keywords(text: str) -> list:
    """
    从文本中提取关键词
    
    Args:
        text: 输入文本
        
    Returns:
        关键词列表（去重，最多20个）
    """
    # 移除标点符号
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
    
    # 分词
    words = text.lower().split()
    
    # 停用词（中英文）
    stopwords = {
        # 英文停用词
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
        'and', 'or', 'but', 'if', 'then', 'else', 'when', 'where', 'why', 'how',
        'this', 'that', 'these', 'those', 'it', 'its', 'i', 'you', 'he', 'she',
        'we', 'they', 'my', 'your', 'his', 'her', 'our', 'their',
        'what', 'which', 'who', 'whom', 'can', 'could', 'will', 'would',
        'should', 'may', 'might', 'must', 'have', 'has', 'had', 'do', 'does', 'did',
        # 中文停用词
        '的', '是', '在', '了', '和', '与', '或', '这个', '那个', '这', '那',
        '我', '你', '他', '她', '它', '我们', '你们', '他们',
        '一个', '一些', '什么', '怎么', '如何', '为什么', '哪个', '哪些',
        '可以', '能够', '需要', '应该', '会', '要', '想', '让', '把', '被',
        '就', '都', '也', '还', '又', '再', '很', '太', '更', '最',
        '吗', '呢', '吧', '啊', '呀', '哦', '嗯'
    }
    
    # 过滤停用词和短词
    keywords = [w for w in words if w not in stopwords and len(w) > 1]
    
    # 去重并保持顺序
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)
    
    # 最多返回20个关键词
    return unique_keywords[:20]


def load_index(location: str = "project") -> dict:
    """加载关键词索引"""
    initialize_data_dir(location)
    index_path = get_data_dir(location) / "index" / "keywords.json"
    
    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    
    return {
        "version": "1.0",
        "updated_at": None,
        "entries": []
    }


def save_index(index: dict, location: str = "project"):
    """保存关键词索引"""
    initialize_data_dir(location)
    index_path = get_data_dir(location) / "index" / "keywords.json"
    
    index["updated_at"] = datetime.now().isoformat()
    
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def time_decay(days_ago: int, decay_rate: float = 0.95) -> float:
    """
    计算时间衰减系数
    
    Args:
        days_ago: 距今天数
        decay_rate: 衰减率（默认0.95，每天衰减5%）
        
    Returns:
        衰减系数 (0-1)
    """
    return decay_rate ** days_ago


def calculate_score(
    query_keywords: set,
    memory_keywords: list,
    days_ago: int,
    is_project_level: bool,
    config: dict = None
) -> float:
    """
    计算记忆的最终权重
    
    Args:
        query_keywords: 查询关键词集合
        memory_keywords: 记忆关键词列表
        days_ago: 距今天数
        is_project_level: 是否为项目级记忆
        config: 配置字典
        
    Returns:
        最终权重分数
    """
    if config is None:
        config = get_default_config()
    
    retrieval_config = config.get("retrieval", {})
    
    # 1. 关键词匹配分
    memory_kw_set = set(memory_keywords)
    matched = query_keywords & memory_kw_set
    if not matched:
        return 0
    kw_score = len(matched) / len(query_keywords)
    
    # 2. 时间衰减
    decay_rate = retrieval_config.get("time_decay_rate", 0.95)
    decay = time_decay(days_ago, decay_rate)
    
    # 3. 来源权重
    source_weight_config = retrieval_config.get("source_weight", {"project": 1.0, "global": 0.7})
    source_weight = source_weight_config.get("project", 1.0) if is_project_level else source_weight_config.get("global", 0.7)
    
    # 最终权重
    return kw_score * decay * source_weight


if __name__ == "__main__":
    # 测试
    print("Project root:", get_project_root())
    print("Skill dir:", get_skill_dir())
    print("Data dir:", get_data_dir())
    print("Keywords:", extract_keywords("继续昨天的 API 重构工作，使用 FastAPI"))
