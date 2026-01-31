# Skillix Hub

AI 编程助手 Skills 技能仓库 - 提升 AI 编程效率的工具集合。

## 什么是 AI Skill？

AI Skill 是一种可复用的 AI 指令集，帮助 AI 编程助手更好地完成特定任务。每个 Skill 包含：
- 任务说明和触发条件
- 执行脚本和工具
- 使用示例

**支持的 AI 助手**：Cursor、Claude、Copilot、Codeium 等

## 可用 Skills

| Skill | 描述 |
|-------|------|
| [memory](./skills/memory/) | 为 AI 助手提供长期记忆能力，自动记录对话并检索相关历史上下文 |
| [behavior-prediction](./skills/behavior-prediction/) | 学习用户行为模式，预测下一步动作并提供智能建议 |
| [swagger-api-reader](./skills/swagger-api-reader/) | 读取并缓存 Swagger/OpenAPI 文档，支持浏览器认证 |

## 安装使用

### 方式一：通过 Cursor 自然语言安装（推荐）

直接在 Cursor 中使用自然语言告诉 AI 安装所需的 Skill：

**个人级安装**（所有项目可用）：
```
帮我从 https://github.com/shetengteng/skillix-hub 安装 memory skill，我希望所有项目都能使用
```

**项目级安装**（仅当前项目可用）：
```
帮我从 https://github.com/shetengteng/skillix-hub 安装 memory skill 到当前项目
```

Cursor AI 会自动完成克隆仓库、复制文件、安装依赖等操作。

**更新 Skill**：
```
帮我从 https://github.com/shetengteng/skillix-hub 更新 memory skill
```

### 方式二：手动命令行安装

#### 个人级安装（所有项目可用）

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

#### 项目级安装（仅当前项目可用）

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

Memory Skill 为 AI 助手提供长期记忆能力，无需额外依赖。

### 核心功能

- **自动检索**：根据用户问题自动检索相关历史记忆
- **智能保存**：自动判断对话价值并保存重要内容
- **关键词匹配**：基于关键词 + 时间衰减的检索算法
- **查看记忆**：查看今日/指定日期/最近的记忆
- **删除记忆**：删除指定记忆或清空所有记忆
- **导出导入**：备份和恢复记忆数据
- **自动记忆规则**：启用后自动在对话开始时检索、结束时保存

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

# 启用自动记忆规则
python3 ~/.cursor/skills/memory/scripts/setup_auto_retrieve.py '{"action": "enable"}'

# 检查自动记忆状态
python3 ~/.cursor/skills/memory/scripts/setup_auto_retrieve.py '{"action": "check"}'

# 更新自动记忆规则
python3 ~/.cursor/skills/memory/scripts/setup_auto_retrieve.py '{"action": "update"}'

# 禁用自动记忆规则
python3 ~/.cursor/skills/memory/scripts/setup_auto_retrieve.py '{"action": "disable"}'
```

### 触发词

- **检索触发**：继续、上次、之前、昨天、我们讨论过
- **保存触发**：记住这个、save this
- **跳过保存**：不要保存、don't save
- **查看记忆**：查看今日记忆、查看最近记忆
- **导出导入**：导出记忆、导入记忆
- **自动记忆**：启用自动记忆检索、禁用自动记忆检索

## Behavior Prediction Skill 使用说明

Behavior Prediction Skill 学习用户的行为模式，当用户执行动作 A 后，自动预测并建议下一个可能的动作 B。

### 核心功能

- **行为记录**：自动记录用户在 AI 助手中执行的动作
- **模式学习**：分析行为序列，发现 A → B 的关联模式
- **智能预测**：当用户执行动作 A 时，预测并建议动作 B
- **开放式类型**：支持自动识别和注册新的动作类型

### 使用示例

```bash
# 记录动作
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{"type": "create_file", "tool": "Write", "details": {"file_path": "test.py"}}'

# 获取统计数据
python3 ~/.cursor/skills/behavior-prediction/scripts/get_statistics.py '{"current_action": "edit_file"}'

# 获取所有统计概览
python3 ~/.cursor/skills/behavior-prediction/scripts/get_statistics.py

# 会话结束处理
python3 ~/.cursor/skills/behavior-prediction/scripts/finalize_session.py '{"actions_summary": [...]}'

# 检查上次会话
python3 ~/.cursor/skills/behavior-prediction/scripts/check_last_session.py

# 获取数据摘要
python3 ~/.cursor/skills/behavior-prediction/scripts/check_last_session.py '{"action": "summary"}'
```

### 触发词

- **查看模式**：查看我的行为模式、查看行为统计
- **预测**：预测下一步
- **清除**：清除行为记录

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
