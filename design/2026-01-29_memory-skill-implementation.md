# Memory Skill 实施文档

> 基于设计文档推荐方案：**关键词 + 大模型二次筛选**
> 
> 详细设计请参考：`2026-01-29_memory-skill-design.md`

## 1. 核心原则

- **零外部依赖**：不使用 sentence-transformers 等外部库
- **利用大模型能力**：让 Cursor 内置的大模型进行语义理解
- **代码数据分离**：Skill 代码可更新，用户数据永不覆盖

## 2. 目录结构

**项目级记忆（优先）**：
```
<project>/.cursor/skills/
├── memory/                      # Skill 代码（可安全更新）
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── save_memory.py       # 保存记忆
│   │   ├── search_memory.py     # 搜索记忆
│   │   ├── view_memory.py       # 查看记忆
│   │   ├── delete_memory.py     # 删除记忆
│   │   └── utils.py             # 工具函数
│   └── default_config.json
└── memory-data/                 # 用户数据（永不覆盖）
    ├── daily/
    │   └── 2026-01-29.md
    ├── index/
    │   └── keywords.json
    └── config.json
```

**全局级记忆（备选）**：
```
~/.cursor/skills/memory-data/    # 跨项目的通用记忆
```

**搜索策略**：项目级优先 → 全局级备选 → 合并结果

## 3. 核心文件

### 3.1 SKILL.md

```markdown
# Memory Skill

为 Cursor 提供长期记忆能力。

## 意图识别（核心入口）

### 意图分类

| 意图类型 | 触发检索 | 信号词示例 |
|----------|---------|-----------|
| 延续性意图 | ✅ | 继续、上次、之前、昨天、我们讨论过 |
| 偏好相关 | ✅ | 我喜欢、我习惯、按照我的风格 |
| 项目相关 | ✅ | 这个项目、我们的、当前、项目里 |
| 独立问题 | ❌ | Python 怎么读文件（通用知识） |
| 新话题 | ❌ | 换个话题、新问题、另外 |

### 检索决策

1. 检查排除信号 → 有则不检索
2. 检查强信号词 → 有则检索
3. 检查弱信号词 → 结合上下文判断
4. 无信号 → 新会话检索，旧会话不检索

### 保存决策

- ✅ 重要决策、用户偏好、项目配置、待办计划
- ❌ 通用问答、临时调试、闲聊、重复内容

## 检索流程

1. 意图识别，判断是否需要检索
2. 运行 `search_memory.py` 获取候选记忆
3. 大模型从候选中选出最相关的 1-3 条
4. 将相关记忆注入上下文

## 保存流程

1. 意图识别，判断是否值得保存
2. 提取主题、关键信息、标签
3. 运行 `save_memory.py` 保存记忆
```

### 3.2 keywords.json 格式

```json
{
  "version": "1.0",
  "updated_at": "2026-01-29T10:30:45Z",
  "entries": [
    {
      "id": "2026-01-29-001",
      "date": "2026-01-29",
      "session": 1,
      "keywords": ["memory", "skill", "design"],
      "summary": "Memory Skill 设计讨论",
      "tags": ["#skill", "#design"],
      "line_range": [3, 35]
    }
  ]
}
```

### 3.3 每日记忆文件格式

```markdown
# 2026-01-29 对话记忆

## Session 1 - 10:30:45

### 主题
Memory Skill 设计讨论

### 关键信息
- 用户希望创建长期记忆功能
- 检索方式：关键词 + 大模型二次筛选

### 标签
#skill #memory #design

---
```

### 3.4 config.json

```json
{
  "version": "1.0",
  "enabled": true,
  "auto_save": true,
  "auto_retrieve": true,
  "storage": { "location": "project-first", "retention_days": -1 },
  "retrieval": { "max_candidates": 10, "max_results": 3, "search_scope_days": 30 }
}
```

**配置参数说明**：
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enabled` | `true` | **总开关**，`false` 完全禁用 |
| `auto_save` | `true` | 自动保存开关 |
| `auto_retrieve` | `true` | 自动检索开关 |
| `storage.location` | `project-first` | 存储位置策略（见下表） |
| `storage.retention_days` | `-1` | 记忆保留天数，`-1` 永久保留 |
| `retrieval.max_candidates` | `10` | 关键词筛选候选数量 |
| `retrieval.max_results` | `3` | 最终返回记忆数量 |
| `retrieval.search_scope_days` | `30` | 检索范围天数，`-1` 搜索全部 |

**存储位置策略**：
| 选项 | 说明 |
|------|------|
| `project-first` | 默认，项目级优先，全局级备选 |
| `project-only` | 只使用项目级记忆 |
| `global-only` | 只使用全局级记忆 |

## 4. 记忆权重机制

记忆的最终权重由三个因素综合计算：

```
最终权重 = 关键词匹配分 × 时间衰减系数 × 来源权重
```

### 4.1 权重因素

| 因素 | 计算方式 | 默认值 | 可配置 |
|------|---------|--------|--------|
| **关键词匹配分** | 匹配数 / 查询词数 | - | ❌ |
| **时间衰减系数** | rate^天数 | 0.95 | ✅ `time_decay_rate` |
| **来源权重** | 项目/全局 | 1.0/0.7 | ✅ `source_weight` |

**配置示例**：
```json
{
  "retrieval": {
    "time_decay_rate": 0.99,
    "source_weight": { "project": 1.0, "global": 0.9 }
  }
}
```

### 4.2 时间衰减参考

| 天数 | 衰减系数 | 说明 |
|------|---------|------|
| 0 (今天) | 1.00 | 无衰减 |
| 7 | 0.70 | 衰减 30% |
| 30 | 0.21 | 衰减 79% |

### 4.3 计算示例

| 记忆 | 关键词分 | 天数 | 来源 | 最终分 |
|------|---------|------|------|--------|
| A | 1.0 | 1 | 项目 | 0.95 |
| B | 0.5 | 0 | 项目 | 0.50 |
| C | 1.0 | 7 | 全局 | 0.49 |

排序：A > B > C

## 5. 脚本实现

### 5.1 utils.py

```python
#!/usr/bin/env python3
"""Memory Skill 工具函数"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

def get_skill_dir() -> Path:
    """获取 Skill 代码目录"""
    return Path.cwd() / ".cursor" / "skills" / "memory"

def get_data_dir() -> Path:
    """获取用户数据目录"""
    data_dir = Path.cwd() / ".cursor" / "skills" / "memory-data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def initialize_data_dir():
    """首次使用时初始化数据目录"""
    data_dir = get_data_dir()
    (data_dir / "daily").mkdir(parents=True, exist_ok=True)
    (data_dir / "index").mkdir(parents=True, exist_ok=True)
    
    index_file = data_dir / "index" / "keywords.json"
    if not index_file.exists():
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump({"version": "1.0", "updated_at": None, "entries": []}, f, ensure_ascii=False, indent=2)

def extract_keywords(text: str) -> list:
    """从文本中提取关键词"""
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.lower().split()
    stopwords = {'the', 'a', 'is', 'are', 'to', 'of', 'in', 'for', 'on', 'with',
                 '的', '是', '在', '了', '和', '与', '或', '这个', '那个'}
    keywords = [w for w in words if w not in stopwords and len(w) > 1]
    return list(dict.fromkeys(keywords))[:20]

def load_index() -> dict:
    """加载关键词索引"""
    initialize_data_dir()
    index_path = get_data_dir() / "index" / "keywords.json"
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"version": "1.0", "updated_at": None, "entries": []}

def save_index(index: dict):
    """保存关键词索引"""
    index_path = get_data_dir() / "index" / "keywords.json"
    index["updated_at"] = datetime.now().isoformat()
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

def load_config() -> dict:
    """加载配置"""
    default = {"retrieval": {"max_candidates": 10, "max_results": 3, "search_scope_days": 30}}
    config_path = get_data_dir() / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return {**default, **json.load(f)}
    return default
```

### 5.2 save_memory.py

```python
#!/usr/bin/env python3
"""保存对话记忆"""

import sys
import json
from datetime import datetime
from utils import get_data_dir, extract_keywords, load_index, save_index, initialize_data_dir

def save_memory(topic: str, key_info: list, tags: list = None):
    initialize_data_dir()
    data_dir = get_data_dir()
    today = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    
    index = load_index()
    session_num = len([e for e in index["entries"] if e["date"] == today]) + 1
    memory_id = f"{today}-{session_num:03d}"
    
    # 构建 Markdown
    md = f"\n## Session {session_num} - {time_str}\n\n### 主题\n{topic}\n\n### 关键信息\n"
    md += "".join(f"- {info}\n" for info in key_info)
    if tags:
        md += f"\n### 标签\n{' '.join(tags)}\n"
    md += "\n---\n"
    
    # 写入文件
    daily_file = data_dir / "daily" / f"{today}.md"
    daily_file.parent.mkdir(parents=True, exist_ok=True)
    if not daily_file.exists():
        daily_file.write_text(f"# {today} 对话记忆\n", encoding='utf-8')
    with open(daily_file, 'a', encoding='utf-8') as f:
        f.write(md)
    
    # 更新索引
    lines = daily_file.read_text(encoding='utf-8').count('\n')
    index["entries"].append({
        "id": memory_id, "date": today, "session": session_num,
        "keywords": extract_keywords(f"{topic} {' '.join(key_info)}"),
        "summary": topic, "tags": tags or [], "line_range": [lines - md.count('\n'), lines]
    })
    save_index(index)
    print(f"记忆已保存: {memory_id}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        save_memory(data.get("topic", ""), data.get("key_info", []), data.get("tags"))
```

### 5.3 search_memory.py

```python
#!/usr/bin/env python3
"""搜索历史记忆"""

import sys
import json
from datetime import datetime, timedelta
from utils import get_data_dir, extract_keywords, load_index, load_config

def search_memories(query: str) -> dict:
    index = load_index()
    config = load_config()
    query_keywords = set(extract_keywords(query))
    
    if not query_keywords:
        return {"query": query, "candidates": [], "message": "未找到相关记忆"}
    
    cutoff = (datetime.now() - timedelta(days=config["retrieval"]["search_scope_days"])).strftime("%Y-%m-%d")
    
    results = []
    for entry in index["entries"]:
        if entry["date"] < cutoff:
            continue
        matched = query_keywords & set(entry["keywords"])
        if matched:
            days_ago = (datetime.now() - datetime.strptime(entry["date"], "%Y-%m-%d")).days
            score = len(matched) * (0.95 ** days_ago)
            results.append({"entry": entry, "score": score, "matched": list(matched)})
    
    results.sort(key=lambda x: -x["score"])
    candidates = results[:config["retrieval"]["max_candidates"]]
    
    # 获取详细内容
    data_dir = get_data_dir()
    detailed = []
    for c in candidates:
        entry = c["entry"]
        daily_file = data_dir / "daily" / f"{entry['date']}.md"
        content = entry["summary"]
        if daily_file.exists():
            lines = daily_file.read_text(encoding='utf-8').splitlines()
            start, end = entry["line_range"]
            content = "\n".join(lines[max(0, start-1):min(len(lines), end)])
        detailed.append({
            "id": entry["id"], "date": entry["date"], "summary": entry["summary"],
            "score": round(c["score"], 3), "matched_keywords": c["matched"], "content": content
        })
    
    return {
        "query": query, "candidates_count": len(detailed), "candidates": detailed,
        "instruction": "请从以上候选记忆中，选出与用户问题最相关的 1-3 条"
    }

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Memory Skill"
    print(json.dumps(search_memories(query), ensure_ascii=False, indent=2))
```

### 5.4 view_memory.py

```python
#!/usr/bin/env python3
"""查看记忆"""

import sys
import json
from datetime import datetime, timedelta
from utils import get_data_dir, load_index, load_config, initialize_data_dir

def view_memories_by_date(date: str = None, location: str = "project") -> dict:
    """查看指定日期的记忆"""
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    initialize_data_dir(location)
    data_dir = get_data_dir(location)
    
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    index = load_index(location)
    date_entries = [e for e in index.get("entries", []) if e.get("date") == date]
    
    if not date_entries:
        return {"success": True, "date": date, "count": 0, "memories": []}
    
    # 获取详细内容
    memories = []
    daily_file = data_dir / "daily" / f"{date}.md"
    lines = daily_file.read_text(encoding='utf-8').splitlines() if daily_file.exists() else []
    
    for entry in date_entries:
        content = entry.get("summary", "")
        line_range = entry.get("line_range", [])
        if lines and line_range:
            start, end = max(0, line_range[0] - 1), min(len(lines), line_range[1])
            content = "\n".join(lines[start:end])
        memories.append({
            "id": entry.get("id"), "session": entry.get("session", 1),
            "summary": entry.get("summary", ""), "tags": entry.get("tags", []),
            "content": content
        })
    
    return {"success": True, "date": date, "count": len(memories), "memories": memories}

def view_recent_memories(days: int = 7, location: str = "project") -> dict:
    """查看最近几天的记忆"""
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    index = load_index(location)
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    recent_entries = [e for e in index.get("entries", []) if e.get("date", "") >= cutoff_date]
    
    # 按日期分组
    by_date = {}
    for entry in recent_entries:
        date = entry.get("date")
        if date not in by_date:
            by_date[date] = []
        by_date[date].append({"id": entry.get("id"), "summary": entry.get("summary", "")})
    
    return {"success": True, "days": days, "total_count": len(recent_entries),
            "by_date": [{"date": d, "memories": by_date[d]} for d in sorted(by_date.keys(), reverse=True)]}

def list_all_dates(location: str = "project") -> dict:
    """列出所有有记忆的日期"""
    index = load_index(location)
    date_counts = {}
    for entry in index.get("entries", []):
        date = entry.get("date")
        date_counts[date] = date_counts.get(date, 0) + 1
    return {"success": True, "total_dates": len(date_counts),
            "dates": [{"date": d, "count": date_counts[d]} for d in sorted(date_counts.keys(), reverse=True)]}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        result = view_memories_by_date()
    elif sys.argv[1] == "today":
        result = view_memories_by_date()
    elif sys.argv[1] == "recent":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        result = view_recent_memories(days)
    elif sys.argv[1] == "list":
        result = list_all_dates()
    else:
        result = view_memories_by_date(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 5.5 delete_memory.py

```python
#!/usr/bin/env python3
"""删除记忆"""

import sys
import json
from datetime import datetime
from utils import get_data_dir, load_index, save_index, initialize_data_dir, load_config

def delete_memory_by_id(memory_id: str, location: str = "project") -> dict:
    """删除指定 ID 的记忆"""
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    initialize_data_dir(location)
    data_dir = get_data_dir(location)
    index = load_index(location)
    entries = index.get("entries", [])
    
    # 查找并删除
    target_entry = None
    for i, entry in enumerate(entries):
        if entry.get("id") == memory_id:
            target_entry = entries.pop(i)
            break
    
    if target_entry is None:
        return {"success": False, "message": f"未找到记忆: {memory_id}"}
    
    index["entries"] = entries
    save_index(index, location)
    
    # 标记文件中的内容为已删除
    date = target_entry.get("date")
    line_range = target_entry.get("line_range", [])
    if date and line_range:
        daily_file = data_dir / "daily" / f"{date}.md"
        if daily_file.exists():
            lines = daily_file.read_text(encoding='utf-8').splitlines()
            start, end = max(0, line_range[0] - 1), min(len(lines), line_range[1])
            for i in range(start, end):
                lines[i] = f"<!-- DELETED: {lines[i]} -->"
            daily_file.write_text('\n'.join(lines), encoding='utf-8')
    
    return {"success": True, "memory_id": memory_id, "message": f"记忆已删除: {memory_id}"}

def delete_memories_by_date(date: str, location: str = "project") -> dict:
    """删除指定日期的所有记忆"""
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    initialize_data_dir(location)
    data_dir = get_data_dir(location)
    index = load_index(location)
    
    original_count = len(index.get("entries", []))
    index["entries"] = [e for e in index.get("entries", []) if e.get("date") != date]
    deleted_count = original_count - len(index["entries"])
    
    if deleted_count == 0:
        return {"success": False, "message": f"未找到日期 {date} 的记忆"}
    
    save_index(index, location)
    
    # 删除每日文件
    daily_file = data_dir / "daily" / f"{date}.md"
    if daily_file.exists():
        daily_file.unlink()
    
    return {"success": True, "date": date, "deleted_count": deleted_count}

def clear_all_memories(location: str = "project", confirm: bool = False) -> dict:
    """清空所有记忆"""
    if not confirm:
        return {"success": False, "message": "清空所有记忆需要确认，请设置 confirm=true"}
    
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    initialize_data_dir(location)
    data_dir = get_data_dir(location)
    index = load_index(location)
    total_count = len(index.get("entries", []))
    
    index["entries"] = []
    save_index(index, location)
    
    # 删除所有每日文件
    daily_dir = data_dir / "daily"
    files_deleted = 0
    if daily_dir.exists():
        for f in daily_dir.glob("*.md"):
            f.unlink()
            files_deleted += 1
    
    return {"success": True, "deleted_count": total_count, "files_deleted": files_deleted}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "用法: python3 delete_memory.py '{\"id\": \"xxx\"}'"}, ensure_ascii=False))
        sys.exit(1)
    
    data = json.loads(sys.argv[1])
    if data.get("clear_all"):
        result = clear_all_memories(confirm=data.get("confirm", False))
    elif data.get("date"):
        result = delete_memories_by_date(data["date"])
    elif data.get("id"):
        result = delete_memory_by_id(data["id"])
    else:
        result = {"success": False, "message": "请提供 id、date 或 clear_all 参数"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

## 6. 工作流程

### 检索流程

```
用户输入问题 → 大模型判断是否需要检索 → 运行 search_memory.py 
→ 大模型从候选中选择最相关的 → 注入上下文 → 回答问题
```

### 保存流程

```
对话结束 → 大模型判断是否值得保存 → 提取主题/关键信息/标签 
→ 运行 save_memory.py → 更新索引
```

### 查看流程

```
用户请求查看记忆 → 运行 view_memory.py → 返回记忆列表/内容
```

**命令示例**：
```bash
# 查看今日记忆
python3 view_memory.py today

# 查看指定日期记忆
python3 view_memory.py "2026-01-29"

# 查看最近 7 天记忆
python3 view_memory.py recent 7

# 列出所有有记忆的日期
python3 view_memory.py list
```

### 删除流程

```
用户请求删除记忆 → 运行 delete_memory.py → 更新索引 → 标记/删除文件
```

**命令示例**：
```bash
# 删除指定记忆
python3 delete_memory.py '{"id": "2026-01-29-001"}'

# 删除指定日期的所有记忆
python3 delete_memory.py '{"date": "2026-01-29"}'

# 清空所有记忆（需确认）
python3 delete_memory.py '{"clear_all": true, "confirm": true}'
```

**注意**：清空所有记忆是危险操作，必须设置 `confirm: true` 才会执行。

## 7. Skill 指令

### 7.1 意图识别指令（核心入口）

```markdown
## Memory Skill - 意图识别

### 第一步：分析用户问题

**用户问题**: {user_query}

### 第二步：识别意图类型

检查以下信号词：

**强信号词（高置信度）**：
- 延续性：继续、上次、之前、昨天、我们讨论过、你记得
- 偏好：我喜欢、我习惯、按照我的风格
- 项目：这个项目、我们的、当前、项目里

**排除信号词**：
- 换个话题、新问题、另外、顺便问一下

### 第三步：输出决策

```json
{
  "intent_type": "continuation|preference|project|independent|new_topic",
  "should_retrieve": true/false,
  "reason": "判断理由"
}
```

如果 should_retrieve = true → 执行检索指令
如果 should_retrieve = false → 直接回答
```

### 7.2 检索指令

```markdown
## 执行检索

运行 search_memory.py "{提取的关键词}"

从返回的候选记忆中，选出最相关的 1-3 条，作为上下文回答用户问题。
```

### 7.3 保存指令

```markdown
## 智能保存

判断本次对话是否值得保存：
- ✅ 重要决策、用户偏好、项目配置、待办计划
- ❌ 通用问答、临时调试、闲聊

如值得保存，提取 JSON 并运行：
python3 save_memory.py '{"topic": "主题", "key_info": ["要点"], "tags": ["#tag"]}'
```

## 8. 用户交互命令

| 命令 | 描述 | 对应脚本 |
|------|------|---------|
| `记住这个` / `save this` | 手动保存当前对话 | `save_memory.py` |
| `不要保存` / `don't save` | 跳过本次对话保存 | - |
| `搜索记忆: xxx` | 主动搜索历史记忆 | `search_memory.py` |
| `查看今日记忆` | 查看今天的记忆 | `view_memory.py today` |
| `查看最近记忆` | 查看最近 7 天的记忆 | `view_memory.py recent 7` |
| `查看 xxx 日期记忆` | 查看指定日期的记忆 | `view_memory.py "2026-01-29"` |
| `列出所有记忆日期` | 列出所有有记忆的日期 | `view_memory.py list` |
| `删除记忆: xxx` | 删除特定记忆 | `delete_memory.py '{"id": "xxx"}'` |
| `删除 xxx 日期记忆` | 删除指定日期的所有记忆 | `delete_memory.py '{"date": "xxx"}'` |
| `清空所有记忆` | 清空所有记忆（需确认） | `delete_memory.py '{"clear_all": true, "confirm": true}'` |

## 9. 使用示例

```
[用户]: 继续昨天的 API 重构工作

[Memory Skill]:
检索到相关记忆: 2026-01-28 - API 重构讨论，决定使用 FastAPI

[AI 响应]:
基于昨天的讨论，我们决定使用 FastAPI 替换 Flask。接下来需要...
```

## 10. 导出/导入功能设计

### 10.1 功能概述

导出/导入功能允许用户：
- **导出**：将记忆数据备份为 JSON 文件，便于迁移或存档
- **导入**：从 JSON 文件恢复记忆数据，支持合并或覆盖模式

### 10.2 导出格式

导出文件采用 JSON 格式，包含完整的记忆数据和元信息：

```json
{
  "version": "1.0",
  "exported_at": "2026-01-29T15:30:00Z",
  "source": {
    "location": "project",
    "project_path": "/path/to/project"
  },
  "statistics": {
    "total_memories": 25,
    "date_range": {
      "start": "2026-01-01",
      "end": "2026-01-29"
    },
    "total_keywords": 150
  },
  "index": {
    "version": "1.0",
    "entries": [
      {
        "id": "2026-01-29-001",
        "date": "2026-01-29",
        "session": 1,
        "keywords": ["api", "design"],
        "summary": "API 设计讨论",
        "tags": ["#api", "#design"],
        "line_range": [3, 35]
      }
    ]
  },
  "daily_files": {
    "2026-01-29": "# 2026-01-29 对话记忆\n\n## Session 1 - 10:30:45\n..."
  }
}
```

### 10.3 脚本设计

#### export_memory.py

```python
#!/usr/bin/env python3
"""导出记忆数据"""

import sys
import json
from datetime import datetime
from pathlib import Path
from utils import get_data_dir, load_index, load_config, initialize_data_dir

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
        date_from: 起始日期（可选）
        date_to: 结束日期（可选）
        include_content: 是否包含完整内容（默认 True）
        
    Returns:
        导出结果
    """
    config = load_config(location)
    if not config.get("enabled", True):
        return {"success": False, "message": "Memory Skill 已禁用"}
    
    initialize_data_dir(location)
    data_dir = get_data_dir(location)
    index = load_index(location)
    entries = index.get("entries", [])
    
    # 过滤日期范围
    if date_from:
        entries = [e for e in entries if e.get("date", "") >= date_from]
    if date_to:
        entries = [e for e in entries if e.get("date", "") <= date_to]
    
    # 收集每日文件内容
    daily_files = {}
    if include_content:
        dates = set(e.get("date") for e in entries)
        daily_dir = data_dir / "daily"
        for date in dates:
            daily_file = daily_dir / f"{date}.md"
            if daily_file.exists():
                daily_files[date] = daily_file.read_text(encoding='utf-8')
    
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
                "start": min(e.get("date") for e in entries) if entries else None,
                "end": max(e.get("date") for e in entries) if entries else None
            },
            "total_keywords": len(set(kw for e in entries for kw in e.get("keywords", [])))
        },
        "index": {
            "version": index.get("version", "1.0"),
            "entries": entries
        },
        "daily_files": daily_files
    }
    
    # 生成输出路径
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"memory-export-{timestamp}.json"
    
    # 写入文件
    output_file = Path(output_path)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    return {
        "success": True,
        "output_file": str(output_file.absolute()),
        "total_memories": len(entries),
        "total_files": len(daily_files),
        "message": f"已导出 {len(entries)} 条记忆到 {output_file}"
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
        result = export_memories(
            output_path=data.get("output"),
            location=data.get("location", "project"),
            date_from=data.get("date_from"),
            date_to=data.get("date_to"),
            include_content=data.get("include_content", True)
        )
    else:
        result = export_memories()
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

#### import_memory.py

```python
#!/usr/bin/env python3
"""导入记忆数据"""

import sys
import json
from datetime import datetime
from pathlib import Path
from utils import get_data_dir, load_index, save_index, load_config, initialize_data_dir

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
    
    # 验证版本
    if import_data.get("version") != "1.0":
        return {"success": False, "message": f"不支持的导出版本: {import_data.get('version')}"}
    
    initialize_data_dir(location)
    data_dir = get_data_dir(location)
    
    imported_entries = import_data.get("index", {}).get("entries", [])
    daily_files = import_data.get("daily_files", {})
    
    if mode == "replace":
        # 替换模式：清空现有数据
        index = {"version": "1.0", "updated_at": None, "entries": []}
        # 删除现有每日文件
        daily_dir = data_dir / "daily"
        if daily_dir.exists():
            for f in daily_dir.glob("*.md"):
                f.unlink()
    else:
        # 合并模式：加载现有索引
        index = load_index(location)
    
    # 获取现有 ID 集合
    existing_ids = set(e.get("id") for e in index.get("entries", []))
    
    # 导入记忆
    imported_count = 0
    skipped_count = 0
    
    for entry in imported_entries:
        entry_id = entry.get("id")
        if entry_id in existing_ids:
            if overwrite_existing:
                # 移除旧条目
                index["entries"] = [e for e in index["entries"] if e.get("id") != entry_id]
            else:
                skipped_count += 1
                continue
        
        index["entries"].append(entry)
        imported_count += 1
    
    # 保存索引
    save_index(index, location)
    
    # 导入每日文件
    files_imported = 0
    daily_dir = data_dir / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    
    for date, content in daily_files.items():
        daily_file = daily_dir / f"{date}.md"
        if daily_file.exists() and not overwrite_existing:
            continue
        daily_file.write_text(content, encoding='utf-8')
        files_imported += 1
    
    return {
        "success": True,
        "imported_count": imported_count,
        "skipped_count": skipped_count,
        "files_imported": files_imported,
        "mode": mode,
        "message": f"已导入 {imported_count} 条记忆，跳过 {skipped_count} 条"
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": "用法: python3 import_memory.py '{\"input\": \"path/to/file.json\"}'"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    data = json.loads(sys.argv[1])
    if not data.get("input"):
        print(json.dumps({"success": False, "message": "缺少必需参数: input"}, ensure_ascii=False))
        sys.exit(1)
    
    result = import_memories(
        input_path=data["input"],
        location=data.get("location", "project"),
        mode=data.get("mode", "merge"),
        overwrite_existing=data.get("overwrite", False)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 10.4 工作流程

#### 导出流程

```
用户请求导出 → 运行 export_memory.py → 生成 JSON 文件
```

**命令示例**：
```bash
# 导出所有记忆
python3 export_memory.py

# 导出到指定文件
python3 export_memory.py '{"output": "backup.json"}'

# 导出指定日期范围
python3 export_memory.py '{"date_from": "2026-01-01", "date_to": "2026-01-15"}'

# 仅导出索引（不含内容）
python3 export_memory.py '{"include_content": false}'
```

#### 导入流程

```
用户请求导入 → 运行 import_memory.py → 更新索引和文件
```

**命令示例**：
```bash
# 合并导入（默认）
python3 import_memory.py '{"input": "backup.json"}'

# 替换导入（清空现有数据）
python3 import_memory.py '{"input": "backup.json", "mode": "replace"}'

# 合并导入并覆盖冲突
python3 import_memory.py '{"input": "backup.json", "overwrite": true}'

# 导入到全局位置
python3 import_memory.py '{"input": "backup.json", "location": "global"}'
```

### 10.5 用户交互命令

| 命令 | 描述 | 对应脚本 |
|------|------|---------|
| `导出记忆` / `export memories` | 导出所有记忆 | `export_memory.py` |
| `导出记忆到 xxx` | 导出到指定文件 | `export_memory.py '{"output": "xxx"}'` |
| `导入记忆 xxx` | 从文件导入记忆 | `import_memory.py '{"input": "xxx"}'` |
| `替换导入 xxx` | 替换模式导入 | `import_memory.py '{"input": "xxx", "mode": "replace"}'` |

### 10.6 使用场景

1. **备份恢复**：定期导出记忆作为备份，系统重装后可恢复
2. **项目迁移**：将项目级记忆导出，在新项目中导入
3. **团队共享**：导出通用知识记忆，团队成员导入使用
4. **版本控制**：将导出文件纳入 Git 管理，追踪记忆变化

### 10.7 注意事项

1. **隐私保护**：导出文件可能包含敏感信息，注意存储安全
2. **版本兼容**：导入时会检查版本号，不兼容版本将拒绝导入
3. **冲突处理**：默认合并模式下，相同 ID 的记忆会被跳过
4. **文件大小**：大量记忆导出可能生成较大文件，建议分段导出
