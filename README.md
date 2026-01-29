# Skillix Hub

Cursor Skills 技能仓库 - 提升 AI 编程效率的工具集合。

## 什么是 Cursor Skill？

Cursor Skill 是一种可复用的 AI 指令集，帮助 Cursor AI 更好地完成特定任务。每个 Skill 包含：
- 任务说明和触发条件
- 执行脚本和工具
- 使用示例

## 可用 Skills

| Skill | 描述 |
|-------|------|
| [memory](./skills/memory/) | 为 Cursor 提供长期记忆能力，自动记录对话并检索相关历史上下文 |
| [swagger-api-reader](./skills/swagger-api-reader/) | 读取并缓存 Swagger/OpenAPI 文档，支持浏览器认证 |

## 安装使用

### 方式一：个人级安装（所有项目可用）

```bash
# 克隆仓库
git clone https://github.com/shetengteng/skillix-hub.git

# 复制 Memory Skill 到 Cursor skills 目录
cp -r skillix-hub/skills/memory ~/.cursor/skills/

# 复制 Swagger API Reader 到 Cursor skills 目录
cp -r skillix-hub/skills/swagger-api-reader ~/.cursor/skills/

# 安装 Swagger API Reader 依赖
pip install -r ~/.cursor/skills/swagger-api-reader/scripts/requirements.txt
```

### 方式二：项目级安装（仅当前项目可用）

```bash
# 在项目根目录
mkdir -p .cursor/skills

# 复制所需的 Skill
cp -r skillix-hub/skills/memory .cursor/skills/
cp -r skillix-hub/skills/swagger-api-reader .cursor/skills/

# 安装依赖（如需要）
pip install -r .cursor/skills/swagger-api-reader/scripts/requirements.txt
```

## Memory Skill 使用说明

Memory Skill 为 Cursor 提供长期记忆能力，无需额外依赖。

### 核心功能

- **自动检索**：根据用户问题自动检索相关历史记忆
- **智能保存**：自动判断对话价值并保存重要内容
- **关键词匹配**：基于关键词 + 时间衰减的检索算法
- **查看记忆**：查看今日/指定日期/最近的记忆
- **删除记忆**：删除指定记忆或清空所有记忆
- **导出导入**：备份和恢复记忆数据

### 使用示例

```bash
# 保存记忆
python3 ~/.cursor/skills/memory/scripts/save_memory.py '{"topic": "API 设计", "key_info": ["使用 FastAPI"], "tags": ["#api"]}'

# 搜索记忆
python3 ~/.cursor/skills/memory/scripts/search_memory.py "API 设计"

# 查看今日记忆
python3 ~/.cursor/skills/memory/scripts/view_memory.py today

# 删除指定记忆
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{"id": "2026-01-29-001"}'

# 导出记忆
python3 ~/.cursor/skills/memory/scripts/export_memory.py

# 导入记忆
python3 ~/.cursor/skills/memory/scripts/import_memory.py '{"input": "backup.json"}'
```

### 触发词

- **检索触发**：继续、上次、之前、昨天、我们讨论过
- **保存触发**：记住这个、save this
- **跳过保存**：不要保存、don't save
- **查看记忆**：查看今日记忆、查看最近记忆
- **导出导入**：导出记忆、导入记忆

## 贡献

欢迎提交 PR 添加新的 Skill！

### Skill 结构规范

```
skill-name/
├── SKILL.md              # 必需：主指令文件
├── scripts/              # 可选：执行脚本
│   ├── main.py
│   └── requirements.txt
└── templates/            # 可选：模板文件
```

### SKILL.md 格式

```markdown
---
name: skill-name
description: 简短描述，说明功能和触发条件
---

# Skill 标题

## 使用方法
...
```

## 许可证

MIT License
