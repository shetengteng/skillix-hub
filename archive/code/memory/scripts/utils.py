#!/usr/bin/env python3
"""Memory Skill 工具函数"""

import json
import re
import os
from datetime import datetime
from pathlib import Path


# 支持的 AI 助手 skills 目录名称（按优先级排序）
SUPPORTED_SKILLS_DIRS = [".cursor", ".claude", ".ai", ".copilot", ".codeium"]


def get_project_root() -> Path:
    """
    获取项目根目录
    
    查找顺序：
    1. 从脚本位置向上查找支持的 AI 助手目录或 .git 目录
    2. 从当前工作目录向上查找支持的 AI 助手目录或 .git 目录
    """
    # 首先尝试从脚本位置向上查找
    script_path = Path(__file__).resolve()
    current = script_path.parent
    while current != current.parent:
        # 检查是否存在任何支持的 AI 助手目录
        for skills_dir in SUPPORTED_SKILLS_DIRS:
            if (current / skills_dir).exists():
                return current
        if (current / ".git").exists():
            return current
        current = current.parent
    
    # 否则从当前工作目录向上查找
    current = Path.cwd()
    while current != current.parent:
        for skills_dir in SUPPORTED_SKILLS_DIRS:
            if (current / skills_dir).exists():
                return current
        if (current / ".git").exists():
            return current
        current = current.parent
    
    # 如果没找到，返回当前目录
    return Path.cwd()


def get_skills_base_dir(project_root: Path = None) -> str:
    """
    获取当前项目使用的 AI 助手目录名称
    
    Args:
        project_root: 项目根目录，如果为 None 则自动获取
        
    Returns:
        AI 助手目录名称（如 ".cursor", ".ai" 等）
    """
    if project_root is None:
        project_root = get_project_root()
    
    # 按优先级检查存在的目录
    for skills_dir in SUPPORTED_SKILLS_DIRS:
        if (project_root / skills_dir).exists():
            return skills_dir
    
    # 默认使用 .cursor（向后兼容）
    return ".cursor"


def get_skill_dir() -> Path:
    """获取 Skill 代码目录"""
    # 首先尝试从脚本位置推断
    script_path = Path(__file__).resolve()
    if script_path.parent.name == "scripts":
        return script_path.parent.parent
    # 否则使用项目路径
    project_root = get_project_root()
    skills_base = get_skills_base_dir(project_root)
    return project_root / skills_base / "skills" / "memory"


def get_data_dir(location: str = "project") -> Path:
    """
    获取用户数据目录
    
    Args:
        location: "project" 或 "global"
    """
    if location == "global":
        # 全局目录优先使用 .cursor，保持向后兼容
        global_base = ".cursor"
        for skills_dir in SUPPORTED_SKILLS_DIRS:
            if (Path.home() / skills_dir).exists():
                global_base = skills_dir
                break
        data_dir = Path.home() / global_base / "skills" / "memory-data"
    else:
        project_root = get_project_root()
        skills_base = get_skills_base_dir(project_root)
        data_dir = project_root / skills_base / "skills" / "memory-data"
    
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
        "version": "2.0",
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
        },
        "save_trigger": {
            "enabled": True,
            "min_message_length": 5,
            "custom_keywords": {
                "zh": [],
                "en": []
            },
            "excluded_keywords": {
                "zh": [],
                "en": []
            }
        },
        "temp_memory": {
            "enabled": True,
            "retention_days": 30,
            "max_per_session": 50
        },
        "summarize": {
            "enabled": True,
            "similarity_threshold": 0.8,
            "time_window_minutes": 10,
            "auto_on_session_end": True,
            "auto_on_next_session": True
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


# ─────────────────────────────────────────────
# 保存触发关键词
# ─────────────────────────────────────────────

SAVE_TRIGGER_KEYWORDS = {
    "zh": {
        "decision": ["决定", "选择", "使用", "采用", "确定", "选用", "改用", "换成", "替换"],
        "preference": ["喜欢", "习惯", "偏好", "风格", "方式", "倾向", "常用", "一般"],
        "config": ["配置", "设置", "规范", "约定", "前缀", "后缀", "命名", "格式", "路径"],
        "plan": ["下一步", "待办", "TODO", "计划", "接下来", "之后", "后续", "安排"],
        "important": ["重要", "记住", "注意", "关键", "核心", "必须", "一定", "务必"],
        "project": ["项目", "模块", "功能", "接口", "API", "数据库", "表", "字段"],
        "tech": ["框架", "库", "工具", "语言", "版本", "依赖", "环境", "部署"]
    },
    "en": {
        "decision": ["decide", "choose", "use", "adopt", "select", "switch to", "replace"],
        "preference": ["prefer", "like", "habit", "style", "way", "usually", "always"],
        "config": ["config", "setting", "convention", "prefix", "suffix", "naming", "format", "path"],
        "plan": ["next step", "todo", "plan", "then", "after", "later", "schedule"],
        "important": ["important", "remember", "note", "key", "core", "must", "critical"],
        "project": ["project", "module", "feature", "api", "database", "table", "field"],
        "tech": ["framework", "library", "tool", "language", "version", "dependency", "deploy"]
    }
}


def detect_save_trigger(text: str, config: dict = None) -> dict:
    """
    检测文本中是否包含保存触发关键词
    
    Args:
        text: 输入文本
        config: 配置字典
        
    Returns:
        {
            "should_save": bool,
            "trigger_keyword": str or None,
            "trigger_category": str or None,
            "confidence": float
        }
    """
    if config is None:
        config = load_config()
    
    trigger_config = config.get("save_trigger", {})
    
    # 检查是否启用
    if not trigger_config.get("enabled", True):
        return {"should_save": False, "trigger_keyword": None, "trigger_category": None, "confidence": 0}
    
    # 检查最小长度
    min_length = trigger_config.get("min_message_length", 10)
    if len(text) < min_length:
        return {"should_save": False, "trigger_keyword": None, "trigger_category": None, "confidence": 0}
    
    text_lower = text.lower()
    
    # 检查排除关键词
    excluded = trigger_config.get("excluded_keywords", {})
    for kw in excluded.get("zh", []) + excluded.get("en", []):
        if kw.lower() in text_lower:
            return {"should_save": False, "trigger_keyword": None, "trigger_category": None, "confidence": 0}
    
    # 检查触发关键词
    matched_keywords = []
    matched_categories = []
    
    # 检查内置关键词
    for lang in ["zh", "en"]:
        for category, keywords in SAVE_TRIGGER_KEYWORDS.get(lang, {}).items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    matched_keywords.append(kw)
                    matched_categories.append(category)
    
    # 检查自定义关键词
    custom = trigger_config.get("custom_keywords", {})
    for kw in custom.get("zh", []) + custom.get("en", []):
        if kw.lower() in text_lower:
            matched_keywords.append(kw)
            matched_categories.append("custom")
    
    if matched_keywords:
        # 计算置信度（匹配的关键词越多，置信度越高）
        confidence = min(1.0, len(matched_keywords) * 0.3)
        
        return {
            "should_save": True,
            "trigger_keyword": matched_keywords[0],
            "trigger_category": matched_categories[0],
            "confidence": confidence,
            "all_matches": list(set(matched_keywords)),
            "all_categories": list(set(matched_categories))
        }
    
    return {"should_save": False, "trigger_keyword": None, "trigger_category": None, "confidence": 0}


# ─────────────────────────────────────────────
# 临时记忆管理
# ─────────────────────────────────────────────

def get_temp_dir(location: str = "project") -> Path:
    """获取临时记忆目录"""
    data_dir = get_data_dir(location)
    temp_dir = data_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def get_current_session_id() -> str:
    """获取当前会话 ID"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_pending_session_path(location: str = "project") -> Path:
    """获取 pending session 文件路径"""
    return get_data_dir(location) / "pending_session.json"


def load_pending_session(location: str = "project") -> dict:
    """加载 pending session"""
    path = get_pending_session_path(location)
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    return None


def save_pending_session(data: dict, location: str = "project"):
    """保存 pending session"""
    path = get_pending_session_path(location)
    
    if "session_start" not in data:
        data["session_start"] = datetime.now().isoformat()
    if "temp_memories" not in data:
        data["temp_memories"] = []
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clear_pending_session(location: str = "project"):
    """清除 pending session"""
    path = get_pending_session_path(location)
    if path.exists():
        path.unlink()


def add_temp_memory(memory: dict, location: str = "project"):
    """
    添加临时记忆
    
    Args:
        memory: 临时记忆数据
        location: 存储位置
    """
    pending = load_pending_session(location)
    if pending is None:
        pending = {"session_start": datetime.now().isoformat(), "temp_memories": []}
    
    # 添加时间戳和 ID
    if "timestamp" not in memory:
        memory["timestamp"] = datetime.now().isoformat()
    if "id" not in memory:
        memory["id"] = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    # 检查最大数量限制
    config = load_config(location)
    max_per_session = config.get("temp_memory", {}).get("max_per_session", 50)
    
    if len(pending.get("temp_memories", [])) >= max_per_session:
        # 移除最旧的
        pending["temp_memories"] = pending["temp_memories"][1:]
    
    pending["temp_memories"].append(memory)
    save_pending_session(pending, location)


def get_temp_memories(location: str = "project") -> list:
    """获取当前会话的临时记忆"""
    pending = load_pending_session(location)
    if pending:
        return pending.get("temp_memories", [])
    return []


def cleanup_old_temp_memories(location: str = "project"):
    """清理过期的临时记忆"""
    config = load_config(location)
    retention_days = config.get("temp_memory", {}).get("retention_days", 30)
    
    if retention_days < 0:
        return  # 永久保留
    
    temp_dir = get_temp_dir(location)
    cutoff_date = datetime.now().date()
    
    for temp_file in temp_dir.glob("*.jsonl"):
        try:
            # 从文件名提取日期
            date_str = temp_file.stem.split("_")[0]
            file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            days_old = (cutoff_date - file_date).days
            if days_old > retention_days:
                temp_file.unlink()
        except (ValueError, IndexError):
            pass


# ─────────────────────────────────────────────
# 相似度计算
# ─────────────────────────────────────────────

def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度
    使用关键词重叠率
    
    Args:
        text1: 文本1
        text2: 文本2
        
    Returns:
        相似度 (0-1)
    """
    words1 = set(extract_keywords(text1))
    words2 = set(extract_keywords(text2))
    
    if not words1 or not words2:
        return 0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union) if union else 0


if __name__ == "__main__":
    # 测试
    print("Project root:", get_project_root())
    print("Skill dir:", get_skill_dir())
    print("Data dir:", get_data_dir())
    print("Keywords:", extract_keywords("继续昨天的 API 重构工作，使用 FastAPI"))
    
    # 测试保存触发检测
    test_texts = [
        "我们决定使用 FastAPI",
        "我喜欢函数式风格",
        "API 前缀配置为 /api/v2",
        "下一步要实现认证功能",
        "这个很重要，记住",
        "今天天气不错"
    ]
    
    print("\n保存触发检测测试:")
    for text in test_texts:
        result = detect_save_trigger(text)
        print(f"  '{text}' -> {result['should_save']} ({result['trigger_keyword']})")
