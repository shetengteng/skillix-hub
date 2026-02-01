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
| [behavior-prediction](./skills/behavior-prediction/) | 学习用户行为模式，记录会话内容，预测下一步操作并提供智能建议 |
| [continuous-learning](./skills/continuous-learning/) | 持续学习用户与 AI 的交互模式，自动提取可复用知识，生成新技能 |
| [swagger-api-reader](./skills/swagger-api-reader/) | 读取并缓存 Swagger/OpenAPI 文档，支持浏览器认证 |
| [uniapp-mp-generator](./skills/uniapp-mp-generator/) | uni-app 小程序代码生成器，根据需求文档自动生成 Vue3 页面、API、Store 等代码 |

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

## Memory Skill v2.0 使用说明

Memory Skill 为 AI 助手提供长期记忆能力，无需额外依赖。

### v2.0 新特性

- **关键词触发保存**：检测到决策/偏好/配置/计划等关键词时自动保存
- **临时记忆机制**：实时保存，会话结束时汇总
- **智能汇总**：自动合并相似记忆，生成结构化记忆
- **会话 Hook**：支持 `--init`, `--save`, `--finalize`, `--status`

### 核心功能

- **自动检索**：根据用户问题自动检索相关历史记忆
- **关键词触发**：检测到特定关键词时自动保存临时记忆
- **智能汇总**：会话结束时合并相似记忆
- **查看记忆**：查看今日/指定日期/最近的记忆
- **删除记忆**：删除指定记忆、清空临时记忆、清空所有记忆
- **导出导入**：备份和恢复记忆数据

### 使用示例

```bash
# 会话开始（自动 finalize 上一个会话）
python3 ~/.cursor/skills/memory/scripts/hook.py --init

# 保存临时记忆（检测关键词）
python3 ~/.cursor/skills/memory/scripts/hook.py --save '{"user_message": "我们决定使用 FastAPI"}'

# 查看会话状态
python3 ~/.cursor/skills/memory/scripts/hook.py --status

# 会话结束（汇总临时记忆）
python3 ~/.cursor/skills/memory/scripts/hook.py --finalize

# 搜索记忆
python3 ~/.cursor/skills/memory/scripts/search_memory.py "API 设计"

# 查看今日记忆
python3 ~/.cursor/skills/memory/scripts/view_memory.py today

# 删除指定记忆
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{"id": "2026-01-29-001"}'

# 清空临时记忆
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{"clear_temp": true}'

# 清空所有记忆
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{"clear_all": true, "confirm": true}'

# 删除日期范围内的记忆
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{"start_date": "2026-01-01", "end_date": "2026-01-31"}'

# 导出记忆
python3 ~/.cursor/skills/memory/scripts/export_memory.py

# 导入记忆
python3 ~/.cursor/skills/memory/scripts/import_memory.py '{"input": "backup.json"}'

# 启用自动记忆规则
python3 ~/.cursor/skills/memory/scripts/setup_auto_retrieve.py '{"action": "enable"}'
```

### 关键词触发保存

| 类型 | 中文关键词 | 英文关键词 |
|------|-----------|-----------|
| 决策类 | 决定、选择、使用、采用 | decide, choose, use, adopt |
| 偏好类 | 喜欢、习惯、偏好、风格 | prefer, like, habit, style |
| 配置类 | 配置、设置、规范、命名 | config, setting, convention |
| 计划类 | 下一步、待办、TODO、计划 | next step, todo, plan |
| 重要类 | 重要、记住、注意、关键 | important, remember, note |

### 触发词

- **检索触发**：继续、上次、之前、昨天、我们讨论过
- **保存触发**：记住这个、save this
- **跳过保存**：不要保存、don't save
- **查看记忆**：查看今日记忆、查看会话状态
- **汇总记忆**：汇总记忆、summarize memories
- **清空记忆**：清空临时记忆、清空所有记忆

## Behavior Prediction Skill V2 使用说明

Behavior Prediction Skill V2 学习用户的行为模式，记录会话内容，预测下一步操作并提供智能建议。

### 核心功能

- **会话记录**：会话结束时记录完整会话内容
- **模式学习**：提取工作流程、偏好、项目模式
- **智能预测**：基于模式预测下一步操作
- **用户画像**：综合分析生成用户画像
- **自动执行**：高置信度预测时支持自动执行

### 使用示例

```bash
# 会话开始时初始化
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --init

# 会话结束时记录
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --finalize '{
  "session_summary": {
    "topic": "API 开发",
    "workflow_stages": ["design", "implement", "test"]
  },
  "operations": {"files": {"created": ["user.py"], "modified": [], "deleted": []}, "commands": []},
  "conversation": {"user_messages": [], "message_count": 5},
  "time": {"start": "2026-01-31T10:00:00Z", "end": "2026-01-31T10:30:00Z"}
}'

# 获取预测
python3 ~/.cursor/skills/behavior-prediction/scripts/get_predictions.py '{"current_stage": "implement"}'

# 查看用户画像
python3 ~/.cursor/skills/behavior-prediction/scripts/user_profile.py

# 更新用户画像
python3 ~/.cursor/skills/behavior-prediction/scripts/user_profile.py '{"action": "update"}'

# 查看行为模式
python3 ~/.cursor/skills/behavior-prediction/scripts/extract_patterns.py
```

### 触发词

- **查看模式**：查看我的行为模式、查看行为统计
- **查看画像**：查看用户画像、更新用户画像
- **预测**：预测下一步

## uni-app 小程序代码生成器使用说明

uni-app 小程序代码生成器根据需求文档自动生成符合项目规范的代码。

### 核心功能

- **页面生成**：自动生成 Vue3 页面（列表、详情、表单）
- **API 生成**：生成 CRUD 接口文件
- **Store 生成**：生成 Pinia 状态管理
- **组件生成**：生成卡片、筛选等组件
- **Schema 生成**：生成数据库集合定义

### 使用方式

提供需求文档，AI 会自动生成代码：

```markdown
# 学生管理模块

## 数据字段
- name: 姓名（必填，字符串）
- phone: 电话（必填，字符串）
- status: 状态（必填，枚举：active/inactive）

## 页面列表
- 学生列表页
- 学生详情页
- 新增学生页
```

### 触发词

- **生成代码**：帮我生成 xxx 模块
- **根据需求**：根据需求文档生成代码

## Continuous Learning Skill 使用说明

Continuous Learning Skill 从用户与 AI 的交互中自动提取可复用的知识，生成新的技能文件。

### 核心功能

- **观察记录**：记录会话中的关键动作和用户反馈
- **模式检测**：识别用户纠正、错误解决、工具偏好等模式
- **本能生成**：将检测到的模式转换为原子化的本能
- **技能演化**：将相关本能聚合为完整的技能文档

### 学习的模式类型

| 模式类型 | 描述 | 示例 |
|---------|------|------|
| **用户纠正** | 用户纠正 AI 的行为 | "不要用 class，用函数" |
| **错误解决** | 特定错误的解决方案 | CORS 错误 → 配置 proxy |
| **工具偏好** | 用户偏好的工具/方法 | 偏好 pytest 而非 unittest |
| **项目规范** | 项目特定的约定 | API 路径使用 /api/v2 前缀 |

### 使用示例

```bash
# 会话开始时初始化
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --init

# 记录观察
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --record '{"event": "tool_call", "tool": "Write"}'

# 会话结束时保存
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --finalize '{"topic": "API 开发"}'

# 查看本能状态
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py status

# 演化本能为技能
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py evolve

# 启用自动学习规则
python3 ~/.cursor/skills/continuous-learning/scripts/setup_rule.py '{"action": "enable"}'
```

### 触发词

- **启用学习**：启用持续学习规则
- **禁用学习**：禁用持续学习规则
- **查看知识**：查看学习到的知识
- **演化技能**：演化本能

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
