#!/usr/bin/env python3
"""
工具函数模块

提供 Continuous Learning Skill 的通用工具函数。
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any


# ─────────────────────────────────────────────
# 路径管理
# ─────────────────────────────────────────────

def get_skill_dir() -> Path:
    """获取 Skill 代码目录"""
    return Path(__file__).parent.parent


def get_project_root() -> Path:
    """获取项目根目录"""
    # 尝试找到 .cursor 或 .git 目录
    current = Path.cwd()
    
    while current != current.parent:
        if (current / ".cursor").exists() or (current / ".git").exists():
            return current
        current = current.parent
    
    return Path.cwd()


def get_data_dir() -> Path:
    """
    获取用户数据目录
    
    优先级：
    1. 项目级: <project>/.cursor/skills/continuous-learning-data/
    2. 全局级: ~/.cursor/skills/continuous-learning-data/
    """
    # 检查项目级目录
    project_root = get_project_root()
    project_data_dir = project_root / ".cursor" / "skills" / "continuous-learning-data"
    
    if project_data_dir.exists():
        return project_data_dir
    
    # 检查全局目录
    global_data_dir = Path.home() / ".cursor" / "skills" / "continuous-learning-data"
    
    if global_data_dir.exists():
        return global_data_dir
    
    # 默认创建项目级目录
    project_data_dir.mkdir(parents=True, exist_ok=True)
    return project_data_dir


def ensure_data_dirs():
    """确保数据目录存在"""
    data_dir = get_data_dir()
    
    dirs = [
        data_dir / "observations",
        data_dir / "instincts",
        data_dir / "evolved" / "skills",
        data_dir / "evolved" / "commands",
        data_dir / "profile"
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# 配置管理
# ─────────────────────────────────────────────

def load_config() -> Dict:
    """加载配置"""
    data_dir = get_data_dir()
    config_path = data_dir / "config.json"
    
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            pass
    
    # 从默认配置复制
    default_config = get_skill_dir() / "default_config.json"
    if default_config.exists():
        try:
            config = json.loads(default_config.read_text(encoding='utf-8'))
            save_config(config)
            return config
        except json.JSONDecodeError:
            pass
    
    # 返回默认配置
    return get_default_config()


def save_config(config: Dict):
    """保存配置"""
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    config_path = data_dir / "config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')


def get_default_config() -> Dict:
    """获取默认配置"""
    return {
        "version": "1.0",
        "enabled": True,
        "observation": {
            "enabled": True,
            "retention_days": 90,
            "max_file_size_mb": 10
        },
        "detection": {
            "enabled": True,
            "patterns": [
                "user_corrections",
                "error_resolutions",
                "tool_preferences",
                "project_conventions"
            ],
            "min_evidence_count": 2
        },
        "instincts": {
            "min_confidence": 0.3,
            "auto_apply_threshold": 0.7,
            "confidence_decay_rate": 0.02,
            "max_instincts": 100
        },
        "evolution": {
            "enabled": True,
            "cluster_threshold": 3,
            "auto_evolve": False,
            "retention_days": 180
        }
    }


# ─────────────────────────────────────────────
# 时间工具
# ─────────────────────────────────────────────

def get_timestamp() -> str:
    """获取 ISO8601 时间戳"""
    return datetime.now().isoformat()


def get_date_str() -> str:
    """获取日期字符串 YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")


def get_month_str() -> str:
    """获取月份字符串 YYYY-MM"""
    return datetime.now().strftime("%Y-%m")


def calculate_days_since(timestamp: str) -> int:
    """计算距离指定时间的天数"""
    if not timestamp:
        return float('inf')
    
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now()
        if dt.tzinfo:
            now = now.astimezone()
        return (now - dt).days
    except:
        return float('inf')


# ─────────────────────────────────────────────
# Pending Session 管理
# ─────────────────────────────────────────────

def get_pending_session_path() -> Path:
    """获取 pending session 文件路径"""
    return get_data_dir() / "pending_session.json"


def load_pending_session() -> Optional[Dict]:
    """加载 pending session"""
    path = get_pending_session_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return None
    return None


def save_pending_session(data: Dict):
    """保存 pending session"""
    path = get_pending_session_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if "session_start" not in data:
        data["session_start"] = get_timestamp()
    if "observations" not in data:
        data["observations"] = []
    
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def clear_pending_session():
    """清除 pending session"""
    path = get_pending_session_path()
    if path.exists():
        path.unlink()


def add_observation_to_pending(observation: Dict):
    """添加观察记录到 pending session"""
    pending = load_pending_session()
    if pending is None:
        pending = {"session_start": get_timestamp(), "observations": []}
    
    if "timestamp" not in observation:
        observation["timestamp"] = get_timestamp()
    
    pending["observations"].append(observation)
    save_pending_session(pending)


# ─────────────────────────────────────────────
# 技能索引管理
# ─────────────────────────────────────────────

def load_skills_index() -> Dict:
    """加载技能索引"""
    index_path = get_data_dir() / "evolved" / "skills-index.json"
    if index_path.exists():
        try:
            return json.loads(index_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            pass
    return {"skills": [], "last_updated": None}


def save_skills_index(index: Dict):
    """保存技能索引"""
    index["last_updated"] = get_timestamp()
    index_path = get_data_dir() / "evolved" / "skills-index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')


def add_skill_to_index(skill_info: Dict):
    """添加技能到索引"""
    index = load_skills_index()
    
    # 检查是否已存在
    existing_idx = None
    for i, s in enumerate(index["skills"]):
        if s["name"] == skill_info["name"]:
            existing_idx = i
            break
    
    if existing_idx is not None:
        # 更新现有记录
        index["skills"][existing_idx] = skill_info
    else:
        # 添加新记录
        index["skills"].append(skill_info)
    
    save_skills_index(index)


def remove_skill_from_index(skill_name: str):
    """从索引中移除技能"""
    index = load_skills_index()
    index["skills"] = [s for s in index["skills"] if s["name"] != skill_name]
    save_skills_index(index)


# ─────────────────────────────────────────────
# 本能文件解析
# ─────────────────────────────────────────────

def parse_instinct_file(content: str) -> Dict:
    """
    解析本能文件
    
    格式：
    ---
    id: xxx
    trigger: "xxx"
    confidence: 0.7
    ---
    
    # 标题
    
    ## 行为
    内容
    """
    result = {}
    lines = content.split('\n')
    
    in_frontmatter = False
    frontmatter_count = 0
    content_lines = []
    
    for line in lines:
        if line.strip() == '---':
            frontmatter_count += 1
            if frontmatter_count == 1:
                in_frontmatter = True
            elif frontmatter_count == 2:
                in_frontmatter = False
            continue
        
        if in_frontmatter:
            if ':' in line:
                # 分割键值对
                colon_idx = line.index(':')
                key = line[:colon_idx].strip()
                value = line[colon_idx + 1:].strip()
                
                # 移除引号
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # 类型转换
                if key == 'confidence':
                    try:
                        result[key] = float(value)
                    except ValueError:
                        result[key] = 0.5
                elif key == 'evidence_count':
                    try:
                        result[key] = int(value)
                    except ValueError:
                        result[key] = 1
                else:
                    result[key] = value
        else:
            content_lines.append(line)
    
    result['content'] = '\n'.join(content_lines).strip()
    return result


def generate_instinct_file(instinct: Dict) -> str:
    """生成本能文件内容"""
    lines = ['---']
    
    # 按顺序输出字段
    field_order = ['id', 'trigger', 'confidence', 'domain', 'source', 
                   'created_at', 'updated_at', 'evidence_count']
    
    for key in field_order:
        if key in instinct:
            value = instinct[key]
            if isinstance(value, str) and (' ' in value or ':' in value):
                lines.append(f'{key}: "{value}"')
            else:
                lines.append(f'{key}: {value}')
    
    lines.append('---')
    lines.append('')
    
    if 'content' in instinct:
        lines.append(instinct['content'])
    
    return '\n'.join(lines)


# ─────────────────────────────────────────────
# 文件操作
# ─────────────────────────────────────────────

def safe_write_file(path: Path, content: str, encoding: str = 'utf-8'):
    """安全写入文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)


def safe_read_file(path: Path, encoding: str = 'utf-8') -> Optional[str]:
    """安全读取文件"""
    if path.exists():
        try:
            return path.read_text(encoding=encoding)
        except:
            return None
    return None
