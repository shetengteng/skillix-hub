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
│   │   ├── save_memory.py
│   │   ├── search_memory.py
│   │   └── utils.py
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

| 命令 | 描述 |
|------|------|
| `记住这个` / `save this` | 手动保存当前对话 |
| `不要保存` / `don't save` | 跳过本次对话保存 |
| `搜索记忆: xxx` | 主动搜索历史记忆 |
| `查看今日记忆` | 查看今天的记忆 |
| `删除记忆: xxx` | 删除特定记忆 |

## 9. 使用示例

```
[用户]: 继续昨天的 API 重构工作

[Memory Skill]:
检索到相关记忆: 2026-01-28 - API 重构讨论，决定使用 FastAPI

[AI 响应]:
基于昨天的讨论，我们决定使用 FastAPI 替换 Flask。接下来需要...
```
