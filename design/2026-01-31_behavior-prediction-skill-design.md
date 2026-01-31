# 用户行为预测 Skill 设计文档

## 1. 概述

**Skill 名称**: behavior-prediction  
**描述**: 学习用户的行为模式，当用户执行动作 A 后，自动预测并帮助执行下一个可能的动作 B。

### 1.1 问题背景

在日常开发工作中，用户经常有固定的行为模式：
- 修改代码后 → 运行测试
- 创建新文件后 → 添加到 git
- 修改配置文件后 → 重启服务
- 写完功能后 → 写单元测试
- 修改 API 后 → 更新文档

这些重复性的行为模式目前需要用户手动执行，AI 助手无法主动预测和帮助。

### 1.2 解决方案

创建一个 Behavior Prediction Skill，实现：
- **行为记录**：记录用户在 AI 助手中执行的动作序列
- **模式学习**：分析行为序列，发现 A → B 的关联模式
- **智能预测**：当用户执行动作 A 时，预测并建议动作 B
- **自动执行**：高置信度时自动执行，低置信度时询问用户

### 1.3 核心原则

- **零外部依赖**：不使用机器学习库，充分利用 Cursor 内置大模型能力
- **大模型驱动**：动作分类、模式识别、预测生成全部由大模型完成
- **本地存储**：所有数据存储在本地，用户完全控制，不过滤敏感信息
- **用户可控**：用户可以开关自动执行、删除行为记录
- **渐进式学习**：随着使用时间增长，预测越来越准确

### 1.4 兼容性设计

本 Skill 支持多种 AI 助手，不仅限于 Cursor：

| AI 助手 | 目录名称 | 支持状态 |
|---------|----------|----------|
| Cursor | `.cursor` | ✅ 完全支持 |
| Claude | `.claude` | ✅ 完全支持 |
| GitHub Copilot | `.copilot` | ✅ 完全支持 |
| Codeium | `.codeium` | ✅ 完全支持 |
| 通用 AI | `.ai` | ✅ 完全支持 |

**自动检测机制**：
- 系统会按优先级检测当前使用的 AI 助手目录
- 自动选择对应的数据存储位置
- 保持向后兼容（默认使用 `.cursor`）

### 1.5 核心设计理念：充分利用大模型能力

> **关键洞察**：Skill 运行在 AI 助手环境中，内置的大模型（Claude/GPT）具有强大的语义理解、模式识别和推理能力。我们应该**最大化利用大模型能力**，而不是重新实现机器学习算法。

**大模型能做什么**：

| 能力 | 传统方案 | 大模型方案 | 优势 |
|------|----------|-----------|------|
| 动作分类 | 关键词匹配/正则 | 语义理解 | 更准确，支持模糊匹配 |
| 模式识别 | 统计算法 | 上下文推理 | 能发现隐含模式 |
| 预测生成 | 概率计算 | 综合推理 | 考虑更多上下文因素 |
| 建议文案 | 模板填充 | 自然语言生成 | 更自然、个性化 |

**设计原则**：
1. **数据存储用脚本**：Python 脚本负责数据的读写和简单统计
2. **智能分析用大模型**：复杂的分类、识别、预测交给大模型
3. **Skill 指令是核心**：通过 SKILL.md 指导大模型如何分析和预测

## 2. 核心概念

### 2.1 什么是"动作"

在 Cursor/AI 助手环境中，"动作"可以定义为：

| 动作类型 | 示例 | 识别方式 |
|----------|------|----------|
| **文件操作** | 创建文件、修改文件、删除文件 | 工具调用记录 |
| **命令执行** | `npm install`、`git commit`、`python test.py` | Shell 命令 |
| **代码生成** | 生成函数、生成类、生成测试 | AI 响应类型 |
| **搜索查询** | 搜索文件、搜索代码、语义搜索 | 工具调用记录 |
| **用户指令** | "帮我写测试"、"重构这个函数" | 用户消息分类 |

### 2.2 行为序列

行为序列是用户在一次会话中执行的动作列表：

```
会话 1: [创建文件] → [写代码] → [运行测试] → [修复 bug] → [提交代码]
会话 2: [修改配置] → [重启服务] → [测试 API]
会话 3: [创建文件] → [写代码] → [运行测试] → [提交代码]
```

### 2.3 行为模式

从行为序列中提取的 A → B 关联：

| 动作 A | 动作 B | 出现次数 | 置信度 |
|--------|--------|----------|--------|
| 创建文件 | 写代码 | 15 | 0.95 |
| 写代码 | 运行测试 | 12 | 0.80 |
| 运行测试 | 提交代码 | 8 | 0.60 |
| 修改配置 | 重启服务 | 10 | 0.90 |

## 3. 技术可行性分析

### 3.1 数据采集可行性

#### 3.1.1 可采集的数据源

| 数据源 | 可行性 | 采集方式 | 说明 |
|--------|--------|----------|------|
| **用户消息** | ✅ 高 | 对话记录 | 用户的指令和问题 |
| **AI 工具调用** | ✅ 高 | Skill 内部记录 | 文件操作、搜索、命令执行 |
| **Shell 命令** | ✅ 高 | 命令执行记录 | 用户执行的终端命令 |
| **文件变更** | ⚠️ 中 | Git diff / 文件监听 | 需要额外机制 |
| **IDE 操作** | ❌ 低 | 无法直接获取 | Cursor API 限制 |

#### 3.1.2 数据采集时机

```
用户发送消息
    ↓
AI 处理并执行工具调用
    ↓
[Behavior Skill] 记录动作
    ↓
AI 返回响应
    ↓
[Behavior Skill] 预测下一步并建议
```

### 3.2 模式识别可行性

#### 3.2.1 方案对比

| 方案 | 复杂度 | 准确度 | 依赖 | 推荐 |
|------|--------|--------|------|------|
| **频率统计** | ⭐ | ⭐⭐⭐ | 无 | ✅ 数据基础 |
| **马尔可夫链** | ⭐⭐ | ⭐⭐⭐⭐ | 无 | ✅ 数据基础 |
| **大模型分析** | ⭐⭐ | ⭐⭐⭐⭐⭐ | Cursor 内置 | ✅ **核心方案** |
| **机器学习** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | sklearn 等 | ❌ 过重 |

#### 3.2.2 推荐方案：统计数据 + 大模型智能分析（核心）

> **核心思想**：脚本负责数据收集和简单统计，大模型负责智能分析和预测决策。

**架构分工**：

```
┌─────────────────────────────────────────────────────────────┐
│                    Cursor 大模型                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ 动作分类     │  │ 模式分析     │  │ 预测决策 + 建议生成  │  │
│  │ (语义理解)   │  │ (上下文推理) │  │ (综合判断)          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↑↓
┌─────────────────────────────────────────────────────────────┐
│                    Python 脚本                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ 动作记录     │  │ 统计计算     │  │ 数据读写            │  │
│  │ (JSON存储)   │  │ (频率/转移)  │  │ (文件操作)          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**为什么大模型是核心**：

1. **动作分类更准确**
   - 传统方案：`if "pytest" in command` → 硬编码，容易遗漏
   - 大模型方案：理解 `python -m pytest tests/ -v` 是运行测试，即使没见过这个格式

2. **模式识别更智能**
   - 传统方案：只能发现 A→B 的频率关系
   - 大模型方案：能理解"用户修改了测试文件，下一步很可能是运行测试"

3. **预测更合理**
   - 传统方案：纯概率，可能在不合适的时机建议
   - 大模型方案：考虑当前上下文，判断建议是否合适

**统计数据的作用**：
- 为大模型提供**历史行为数据**作为参考
- 提供**频率信息**帮助大模型判断置信度
- 作为**冷启动**的基础（预置常见模式）

```python
# 转移概率矩阵示例（作为大模型的参考数据）
transition_matrix = {
    "create_file": {
        "write_code": {"count": 45, "probability": 0.70},
        "git_add": {"count": 10, "probability": 0.15},
        "run_test": {"count": 5, "probability": 0.08}
    },
    "write_code": {
        "run_test": {"count": 30, "probability": 0.50},
        "git_commit": {"count": 15, "probability": 0.25}
    }
}
```

**大模型分析示例**：

```markdown
## 预测分析任务

### 输入数据
- 当前动作：write_code（修改了 src/api/user.py）
- 历史统计：write_code 后 50% 运行测试，25% 提交代码
- 当前上下文：
  - 修改的是 API 文件
  - 项目有 tests/ 目录
  - 最近 3 次 write_code 后都运行了测试

### 请分析
1. 下一步最可能是什么动作？
2. 置信度是多少？
3. 是否应该建议用户？
4. 如果建议，用什么自然语言表达？
```

### 3.3 预测与执行可行性

#### 3.3.1 预测触发时机

| 触发时机 | 说明 | 实现难度 |
|----------|------|----------|
| **对话结束时** | AI 完成响应后预测 | ⭐ 简单 |
| **工具执行后** | 每次工具调用后预测 | ⭐⭐ 中等 |
| **用户空闲时** | 检测用户无输入时预测 | ⭐⭐⭐ 复杂 |

推荐：**对话结束时** 触发预测，简单且不打扰用户。

#### 3.3.2 执行策略

| 置信度 | 策略 | 示例 |
|--------|------|------|
| > 0.9 | 自动执行 | 自动运行测试 |
| 0.7 - 0.9 | 询问确认 | "要运行测试吗？" |
| 0.5 - 0.7 | 建议提示 | "你可能想运行测试" |
| < 0.5 | 不提示 | - |

### 3.4 技术挑战与解决方案

| 挑战 | 严重程度 | 解决方案 |
|------|----------|----------|
| **动作分类不准确** | ⭐⭐⭐ | 使用大模型进行分类 |
| **冷启动问题** | ⭐⭐ | 预置常见模式 + 快速学习 |
| **误预测干扰用户** | ⭐⭐⭐ | 置信度阈值 + 用户反馈 |
| **数据采集不完整** | ⭐⭐ | 只采集可获取的数据 |
| **存储空间增长** | ⭐ | 定期清理 + 聚合统计 |

## 4. 存储架构

### 4.1 目录结构

```
<project>/.cursor/skills/
├── behavior-prediction/           # Skill 代码
│   ├── SKILL.md                   # Skill 入口
│   ├── scripts/
│   │   ├── record_action.py       # 记录动作
│   │   ├── predict_next.py        # 预测下一步
│   │   ├── analyze_patterns.py    # 分析模式
│   │   └── utils.py               # 工具函数
│   └── default_config.json        # 默认配置
│
└── behavior-prediction-data/      # 用户数据
    ├── actions/                   # 动作记录
    │   └── 2026-01-31.json        # 每日动作日志
    ├── patterns/
    │   └── transition_matrix.json # 转移概率矩阵
    ├── feedback/
    │   └── user_feedback.json     # 用户反馈记录
    └── config.json                # 用户配置
```

### 4.2 动作记录格式

```json
// actions/2026-01-31.json
{
  "date": "2026-01-31",
  "sessions": [
    {
      "session_id": "sess_001",
      "start_time": "2026-01-31T10:00:00Z",
      "actions": [
        {
          "id": "act_001",
          "timestamp": "2026-01-31T10:00:05Z",
          "type": "create_file",
          "details": {
            "file_path": "src/utils/helper.py",
            "file_type": "python"
          },
          "context": {
            "user_message": "创建一个工具函数文件",
            "project": "my-project"
          }
        },
        {
          "id": "act_002",
          "timestamp": "2026-01-31T10:01:30Z",
          "type": "write_code",
          "details": {
            "file_path": "src/utils/helper.py",
            "code_type": "function",
            "lines_added": 25
          }
        }
      ]
    }
  ]
}
```

### 4.3 转移概率矩阵格式

```json
// patterns/transition_matrix.json
{
  "version": "1.0",
  "updated_at": "2026-01-31T12:00:00Z",
  "total_transitions": 150,
  "matrix": {
    "create_file": {
      "write_code": { "count": 45, "probability": 0.75 },
      "git_add": { "count": 10, "probability": 0.17 },
      "run_test": { "count": 5, "probability": 0.08 }
    },
    "write_code": {
      "run_test": { "count": 30, "probability": 0.50 },
      "git_commit": { "count": 15, "probability": 0.25 },
      "write_code": { "count": 10, "probability": 0.17 },
      "refactor": { "count": 5, "probability": 0.08 }
    }
  },
  "action_counts": {
    "create_file": 60,
    "write_code": 80,
    "run_test": 45,
    "git_commit": 30
  }
}
```

### 4.4 用户反馈格式

```json
// feedback/user_feedback.json
{
  "version": "1.0",
  "feedbacks": [
    {
      "timestamp": "2026-01-31T10:05:00Z",
      "prediction": {
        "from_action": "write_code",
        "to_action": "run_test",
        "confidence": 0.85
      },
      "user_response": "accepted",  // accepted, rejected, ignored
      "actual_action": "run_test"
    }
  ],
  "stats": {
    "total_predictions": 100,
    "accepted": 70,
    "rejected": 15,
    "ignored": 15,
    "accuracy": 0.70
  }
}
```

## 5. 动作分类体系

### 5.1 标准动作类型

| 类别 | 动作类型 | 描述 | 识别特征 |
|------|----------|------|----------|
| **文件操作** | `create_file` | 创建新文件 | Write 工具 + 新文件 |
| | `edit_file` | 编辑现有文件 | StrReplace 工具 |
| | `delete_file` | 删除文件 | Delete 工具 |
| | `read_file` | 读取文件 | Read 工具 |
| **代码生成** | `write_code` | 编写代码 | 代码块生成 |
| | `write_test` | 编写测试 | 测试文件/函数 |
| | `refactor` | 重构代码 | 重构相关指令 |
| | `fix_bug` | 修复 bug | 错误修复相关 |
| **命令执行** | `run_test` | 运行测试 | pytest/npm test 等 |
| | `run_build` | 构建项目 | npm build/make 等 |
| | `run_server` | 启动服务 | npm start/python app.py |
| | `install_dep` | 安装依赖 | npm install/pip install |
| **Git 操作** | `git_add` | 暂存文件 | git add |
| | `git_commit` | 提交代码 | git commit |
| | `git_push` | 推送代码 | git push |
| | `git_pull` | 拉取代码 | git pull |
| **搜索查询** | `search_code` | 搜索代码 | Grep/SemanticSearch |
| | `search_file` | 搜索文件 | Glob 工具 |
| **其他** | `ask_question` | 询问问题 | 问答类消息 |
| | `explain_code` | 解释代码 | 解释相关指令 |

### 5.2 动作识别方案对比

> **核心问题**：动作类型和识别特征应该硬编码在代码中，还是依赖大模型来分类？

#### 5.2.1 方案对比

| 维度 | 硬编码方案 | 大模型分类方案 |
|------|-----------|---------------|
| **准确性** | ⭐⭐⭐ 依赖规则完整性 | ⭐⭐⭐⭐⭐ 语义理解，更准确 |
| **灵活性** | ⭐⭐ 新命令需要更新代码 | ⭐⭐⭐⭐⭐ 自动适应新命令 |
| **性能** | ⭐⭐⭐⭐⭐ 毫秒级 | ⭐⭐⭐ 需要大模型推理 |
| **一致性** | ⭐⭐⭐⭐⭐ 相同输入相同输出 | ⭐⭐⭐ 可能有轻微波动 |
| **维护成本** | ⭐⭐ 需要持续更新规则 | ⭐⭐⭐⭐⭐ 几乎为零 |
| **离线能力** | ⭐⭐⭐⭐⭐ 完全离线 | ⭐⭐⭐ 依赖大模型 |

#### 5.2.2 推荐方案：大模型分类（核心）+ 规则兜底

**设计理念**：充分利用 Cursor 大模型的语义理解能力，同时保留简单规则作为兜底。

```
┌─────────────────────────────────────────────────────────────┐
│                    动作分类流程                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. 大模型分类（主要）                                        │
│    - 理解工具调用的语义                                      │
│    - 结合用户消息理解意图                                    │
│    - 输出动作类型 + 置信度                                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 规则验证/兜底（辅助）                                     │
│    - 如果大模型置信度低，用规则验证                          │
│    - 如果大模型无法分类，用规则兜底                          │
└─────────────────────────────────────────────────────────────┘
```

#### 5.2.3 大模型分类实现（SKILL.md 指令）

在 Always Applied Rule 中，让大模型直接进行分类：

```markdown
## 动作分类指令

当执行工具调用后，请分类这个动作：

### 输入信息
- 工具名称：{tool_name}
- 工具参数：{tool_params}
- 用户消息：{user_message}

### 动作类型定义

| 类别 | 动作类型 | 语义描述 |
|------|----------|----------|
| 文件操作 | create_file | 创建新文件 |
| | edit_file | 修改已有文件 |
| | delete_file | 删除文件 |
| 代码生成 | write_code | 编写业务代码 |
| | write_test | 编写测试代码 |
| | refactor | 重构代码 |
| 命令执行 | run_test | 运行测试 |
| | run_build | 构建项目 |
| | run_server | 启动服务 |
| | install_dep | 安装依赖 |
| Git 操作 | git_add | 暂存文件 |
| | git_commit | 提交代码 |
| | git_push | 推送代码 |

### 分类要求

1. **理解语义**：不要只看命令关键词，要理解实际意图
   - `python -m pytest` → run_test（虽然没有 "test" 关键词）
   - `npm run test:unit` → run_test
   - `make check` → run_test（如果是测试命令）

2. **结合上下文**：参考用户消息理解意图
   - 用户说"帮我测试一下" + Shell 命令 → run_test
   - 用户说"构建项目" + Shell 命令 → run_build

3. **输出格式**：
```json
{
  "action_type": "run_test",
  "confidence": 0.95,
  "reason": "命令 pytest 是 Python 测试框架"
}
```
```

#### 5.2.4 为什么大模型分类更好？

**场景 1：命令变体**

| 命令 | 硬编码方案 | 大模型方案 |
|------|-----------|-----------|
| `pytest tests/` | ✅ 匹配 "pytest" | ✅ 理解是测试 |
| `python -m pytest` | ❌ 可能漏掉 | ✅ 理解是测试 |
| `py.test` | ❌ 可能漏掉 | ✅ 理解是测试 |
| `npm run test:e2e` | ❌ 可能漏掉 | ✅ 理解是测试 |
| `make test` | ❌ 需要特殊处理 | ✅ 理解是测试 |

**场景 2：新工具/框架**

| 命令 | 硬编码方案 | 大模型方案 |
|------|-----------|-----------|
| `vitest` | ❌ 未知命令 | ✅ 理解是测试框架 |
| `bun test` | ❌ 未知命令 | ✅ 理解是测试 |
| `deno test` | ❌ 未知命令 | ✅ 理解是测试 |

**场景 3：上下文理解**

| 场景 | 硬编码方案 | 大模型方案 |
|------|-----------|-----------|
| 用户说"跑一下测试" + `npm run dev` | ❌ 分类为 run_server | ✅ 可能理解用户意图有误，提示确认 |
| 用户说"构建项目" + `npm run build:prod` | ❌ 可能漏掉 | ✅ 理解是构建 |

#### 5.2.5 规则兜底（可选）

保留简单规则作为兜底，用于：
1. 大模型分类失败时
2. 需要快速分类（不想等大模型）时
3. 离线场景

```python
# 简单规则兜底（仅在大模型无法分类时使用）
FALLBACK_RULES = {
    "Write": lambda params: "create_file" if is_new_file(params) else "edit_file",
    "StrReplace": lambda params: "edit_file",
    "Delete": lambda params: "delete_file",
    "Shell": lambda params: classify_shell_fallback(params.get("command", "")),
}

def classify_shell_fallback(command: str) -> str:
    """Shell 命令的简单规则分类"""
    command_lower = command.lower()
    
    # 只匹配最明显的模式
    if any(kw in command_lower for kw in ["pytest", "jest", "mocha", "test"]):
        return "run_test"
    if any(kw in command_lower for kw in ["build", "compile"]):
        return "run_build"
    if any(kw in command_lower for kw in ["git commit"]):
        return "git_commit"
    
    return "shell_command"  # 默认
```

#### 5.2.6 动作类型的可扩展性设计（重要）

> **核心问题**：动作类型是否应该固定？是否会限制系统的灵活性？

**答案：动作类型应该是开放的、可扩展的，而不是固定的。**

##### 设计理念：开放式动作类型

```
┌─────────────────────────────────────────────────────────────┐
│                    动作类型体系                              │
├─────────────────────────────────────────────────────────────┤
│ 核心类型（预定义）                                           │
│ - 常见的、高频的动作类型                                     │
│ - 作为大模型分类的参考                                       │
│ - 不是限制，只是建议                                         │
├─────────────────────────────────────────────────────────────┤
│ 扩展类型（动态生成）                                         │
│ - 大模型根据实际情况创建                                     │
│ - 自动学习新的动作模式                                       │
│ - 用户可以自定义                                             │
└─────────────────────────────────────────────────────────────┘
```

##### 为什么不应该固定动作类型？

| 场景 | 固定类型的问题 | 开放类型的优势 |
|------|---------------|---------------|
| **新工具出现** | `docker compose up` 无法分类 | 自动创建 `container_start` |
| **特定领域** | 机器学习项目的 `train_model` | 自动识别并创建新类型 |
| **用户习惯** | 用户有独特的工作流程 | 学习用户特有的动作模式 |
| **跨语言/框架** | 不同技术栈的命令差异 | 统一理解语义，灵活分类 |

##### 开放式动作类型实现

**1. 核心类型（作为参考，不是限制）**

```markdown
## 常见动作类型（参考）

以下是常见的动作类型，但**不限于此列表**：

### 文件操作
- create_file: 创建新文件
- edit_file: 修改已有文件
- delete_file: 删除文件
- rename_file: 重命名文件
- move_file: 移动文件

### 代码相关
- write_code: 编写代码
- write_test: 编写测试
- refactor: 重构代码
- fix_bug: 修复 bug
- code_review: 代码审查

### 命令执行
- run_test: 运行测试
- run_build: 构建项目
- run_server: 启动服务
- install_dep: 安装依赖

### Git 操作
- git_add, git_commit, git_push, git_pull, git_merge, git_rebase

### 其他（可扩展）
- deploy: 部署应用
- database_migrate: 数据库迁移
- generate_docs: 生成文档
- ... (大模型可自由扩展)
```

**2. 大模型分类指令（支持扩展）**

```markdown
## 动作分类指令（支持扩展）

### 分类规则

1. **优先使用已知类型**：如果动作明显属于某个已知类型，使用该类型

2. **可以创建新类型**：如果动作不属于任何已知类型，可以创建新类型
   - 新类型命名规则：`动词_名词`，如 `train_model`、`deploy_app`
   - 保持语义清晰

3. **记录新类型**：创建新类型时，记录其语义描述

### 示例

| 命令 | 分类结果 | 说明 |
|------|----------|------|
| `pytest tests/` | run_test | 已知类型 |
| `docker compose up` | container_start | 新类型 |
| `python train.py` | train_model | 新类型（ML 项目） |
| `terraform apply` | infra_deploy | 新类型（IaC） |
| `npm run lint` | lint_code | 新类型 |

### 输出格式

```json
{
  "action_type": "train_model",
  "is_new_type": true,
  "description": "训练机器学习模型",
  "confidence": 0.90
}
```
```

**3. 动态类型注册**

```python
# 动作类型注册表（自动扩展）
# types_registry.json

{
  "version": "1.0",
  "types": {
    "create_file": {
      "category": "file_operation",
      "description": "创建新文件",
      "source": "predefined"
    },
    "run_test": {
      "category": "command_execution",
      "description": "运行测试",
      "source": "predefined"
    },
    "train_model": {
      "category": "ml_operation",
      "description": "训练机器学习模型",
      "source": "auto_generated",
      "first_seen": "2026-01-31",
      "count": 5
    },
    "container_start": {
      "category": "container_operation",
      "description": "启动容器",
      "source": "auto_generated",
      "first_seen": "2026-01-31",
      "count": 3
    }
  }
}
```

##### 类型合并与归一化

**问题**：大模型可能为相同语义创建不同的类型名称

| 场景 | 可能的类型名 |
|------|-------------|
| 运行测试 | run_test, execute_test, test_run |
| 启动容器 | container_start, docker_up, start_container |

**解决方案**：类型归一化

```markdown
## 类型归一化规则

1. **语义相似的类型自动合并**
   - 大模型在分类时，检查是否有语义相似的已有类型
   - 如果有，使用已有类型而不是创建新类型

2. **定期清理**
   - 统计各类型的使用频率
   - 低频类型可能是误分类，考虑合并到相似类型

3. **用户可手动合并**
   - 用户可以指定类型别名
   - 如：`docker_up` → `container_start`
```

##### 实际场景示例

**场景 1：机器学习项目**

```
用户执行：python train.py --epochs 100

大模型分类：
{
  "action_type": "train_model",
  "is_new_type": true,
  "description": "训练机器学习模型",
  "category": "ml_operation"
}

后续预测：
- train_model → evaluate_model (0.7)
- train_model → save_model (0.2)
```

**场景 2：DevOps 工作流**

```
用户执行：kubectl apply -f deployment.yaml

大模型分类：
{
  "action_type": "k8s_deploy",
  "is_new_type": true,
  "description": "部署 Kubernetes 资源"
}

后续预测：
- k8s_deploy → k8s_check_status (0.6)
- k8s_deploy → k8s_logs (0.3)
```

**场景 3：数据工程**

```
用户执行：dbt run

大模型分类：
{
  "action_type": "dbt_run",
  "is_new_type": true,
  "description": "运行 dbt 数据转换"
}

后续预测：
- dbt_run → dbt_test (0.8)
```

##### 总结：开放式动作类型的优势

| 优势 | 说明 |
|------|------|
| **无限扩展** | 不受预定义类型限制 |
| **领域适应** | 自动适应不同技术领域 |
| **用户个性化** | 学习用户特有的工作模式 |
| **未来兼容** | 新工具/框架自动支持 |
| **零维护** | 不需要手动更新类型列表 |

#### 5.2.7 置信度计算详解

> **核心问题**：置信度是如何计算的？

在本系统中，有两种置信度：
1. **分类置信度**：大模型对动作分类结果的确信程度
2. **预测置信度**：对下一步动作预测的确信程度

##### 一、分类置信度（大模型输出）

**分类置信度由大模型直接输出**，基于以下因素：

| 因素 | 影响 | 示例 |
|------|------|------|
| **命令明确性** | 命令越明确，置信度越高 | `pytest` → 0.95, `python script.py` → 0.60 |
| **上下文支持** | 用户消息支持分类结果 | 用户说"运行测试" + `npm run test` → 0.98 |
| **类型匹配度** | 与已知类型的匹配程度 | 完全匹配已知类型 → 高，新类型 → 中 |

**大模型分类指令中的置信度说明**：

```markdown
## 置信度评估标准

请根据以下标准评估分类置信度：

### 高置信度 (0.9-1.0)
- 命令/操作非常明确，几乎没有歧义
- 用户消息明确说明了意图
- 完全匹配已知的动作类型
- 示例：`pytest tests/` + 用户说"运行测试" → 0.98

### 中高置信度 (0.7-0.9)
- 命令/操作较明确，但有轻微歧义
- 用户消息部分支持分类结果
- 示例：`npm run dev` → 0.80（可能是 run_server 或 run_build）

### 中置信度 (0.5-0.7)
- 命令/操作有一定歧义
- 需要创建新的动作类型
- 示例：`python train.py` → 0.65（新类型 train_model）

### 低置信度 (<0.5)
- 无法确定动作类型
- 命令过于通用或不明确
- 示例：`python script.py` → 0.40（不知道脚本做什么）
```

##### 二、预测置信度（综合计算）

**预测置信度是综合多个因素计算的**，由大模型根据统计数据和上下文进行综合判断。

**计算因素**：

```
预测置信度 = f(历史概率, 样本量, 上下文支持度, 最近行为模式)
```

| 因素 | 权重 | 说明 |
|------|------|------|
| **历史概率** | 40% | 转移矩阵中 A→B 的概率 |
| **样本量** | 20% | 观察到 A→B 的次数（样本越多越可信） |
| **上下文支持度** | 25% | 当前上下文是否支持这个预测 |
| **最近行为模式** | 15% | 最近几次是否出现相同模式 |

**详细计算方法**：

```markdown
## 预测置信度计算

### 输入数据
- 历史概率：P(B|A) = 0.50（从转移矩阵获取）
- 样本量：count(A→B) = 30
- 上下文：修改了测试文件
- 最近 5 次 A 后的动作：[B, B, B, C, B]

### 计算步骤

#### 1. 基础置信度（基于历史概率）
base_confidence = P(B|A) = 0.50

#### 2. 样本量调整
- 样本量越大，置信度越可信
- 使用对数函数避免过度依赖大样本

sample_factor = min(1.0, log(count + 1) / log(50))
             = min(1.0, log(31) / log(50))
             = min(1.0, 0.88)
             = 0.88

#### 3. 上下文调整
- 如果上下文支持预测，提高置信度
- 如果上下文不支持，降低置信度

context_factor = 1.0  # 默认
if 修改了测试文件 and 预测是 run_test:
    context_factor = 1.3  # 上下文强烈支持
elif 修改了配置文件 and 预测是 run_test:
    context_factor = 0.8  # 上下文不太支持

#### 4. 最近行为模式调整
- 如果最近多次出现相同模式，提高置信度

recent_pattern = count(B in 最近5次) / 5 = 4/5 = 0.80
pattern_factor = 1.0 + (recent_pattern - 0.5) * 0.4
              = 1.0 + 0.3 * 0.4
              = 1.12

#### 5. 综合计算
final_confidence = base_confidence 
                 × (0.5 + 0.5 × sample_factor)
                 × context_factor
                 × pattern_factor

= 0.50 × (0.5 + 0.5 × 0.88) × 1.3 × 1.12
= 0.50 × 0.94 × 1.3 × 1.12
= 0.68

#### 6. 上限处理
final_confidence = min(final_confidence, 0.99)
                = 0.68
```

**简化版（大模型直接判断）**：

由于我们依赖大模型进行预测，实际上不需要精确的数学公式。大模型可以根据以下指令进行综合判断：

```markdown
## 预测置信度评估指令

请综合以下因素评估预测置信度：

### 因素 1：历史概率
- 从统计数据中获取 A→B 的概率
- 概率越高，置信度基础越高

### 因素 2：样本量
- 观察次数越多，统计越可信
- < 5 次：置信度 -20%
- 5-20 次：正常
- > 20 次：置信度 +10%

### 因素 3：上下文支持
- 当前上下文是否支持这个预测？
- 强烈支持：置信度 +20%
- 部分支持：正常
- 不支持：置信度 -30%

### 因素 4：最近行为模式
- 最近 5 次 A 后是否都是 B？
- 全部是 B：置信度 +15%
- 大部分是 B：置信度 +5%
- 很少是 B：置信度 -10%

### 输出
综合以上因素，给出 0-1 之间的置信度，并解释判断理由。
```

##### 三、置信度示例

| 场景 | 历史概率 | 样本量 | 上下文 | 最近模式 | 最终置信度 |
|------|----------|--------|--------|----------|-----------|
| 修改测试文件后预测 run_test | 0.50 | 30 | 强支持 | 4/5 | **0.85** |
| 修改 README 后预测 run_test | 0.50 | 30 | 不支持 | 2/5 | **0.35** |
| 新用户，首次 write_code 后预测 run_test | 0.50 | 2 | 中性 | N/A | **0.40** |
| 老用户，write_code 后预测 run_test | 0.60 | 100 | 中性 | 5/5 | **0.75** |

##### 四、置信度的使用

| 置信度范围 | 系统行为 |
|-----------|----------|
| > 0.9 | 可以自动执行（如果配置允许） |
| 0.7-0.9 | 询问用户确认 |
| 0.5-0.7 | 显示建议，不强调 |
| < 0.5 | 不显示建议 |

#### 5.2.8 实现总结

| 组件 | 职责 | 实现方式 |
|------|------|----------|
| **大模型** | 动作分类（主要） | SKILL.md 指令 |
| **规则** | 兜底分类（辅助） | Python 简单规则 |
| **动作类型** | 可扩展的分类体系 | 大模型可自动扩展 |
| **置信度** | 综合判断 | 大模型根据多因素评估 |

**核心优势**：
- 不需要维护复杂的规则库
- 自动适应新工具/框架
- 结合上下文理解意图
- 随着大模型能力提升自动改进

## 6. 预测算法：大模型驱动

### 6.1 核心理念：让大模型做决策

> **关键洞察**：与其用 Python 实现复杂的预测算法，不如让大模型基于统计数据和上下文做出智能判断。

**传统方案 vs 大模型方案**：

| 步骤 | 传统方案 | 大模型方案 |
|------|----------|-----------|
| 获取候选 | Python 计算概率 | Python 提供统计数据 |
| 排序筛选 | Python 算法 | 大模型综合判断 |
| 上下文调整 | 硬编码规则 | 大模型理解上下文 |
| 生成建议 | 模板填充 | 自然语言生成 |

### 6.2 大模型预测指令（SKILL.md 核心内容）

```markdown
## Behavior Prediction - 预测下一步动作

### 触发时机

当完成一个动作后，执行预测分析。

### 第一步：获取统计数据

执行脚本获取历史行为统计：

```bash
python3 <skills_dir>/behavior-prediction/scripts/get_statistics.py '{"current_action": "write_code"}'
```

输出示例：
```json
{
  "current_action": "write_code",
  "transitions": {
    "run_test": {"count": 30, "probability": 0.50},
    "git_commit": {"count": 15, "probability": 0.25},
    "write_code": {"count": 10, "probability": 0.17}
  },
  "recent_sequence": ["create_file", "write_code", "run_test", "write_code"],
  "context": {
    "last_file": "src/api/user.py",
    "file_type": "python",
    "has_tests_dir": true,
    "uncommitted_changes": 3
  }
}
```

### 第二步：智能分析（大模型核心任务）

基于统计数据和上下文，分析以下问题：

1. **下一步最可能是什么？**
   - 参考历史概率，但不完全依赖
   - 考虑当前上下文（修改了什么文件、项目结构等）
   - 考虑最近的行为序列（是否有明显模式）

2. **置信度是多少？**
   - 高置信度（>0.8）：历史概率高 + 上下文支持 + 样本量足够
   - 中置信度（0.5-0.8）：历史概率中等或上下文部分支持
   - 低置信度（<0.5）：历史数据不足或上下文不支持

3. **是否应该建议？**
   - 考虑用户当前的工作流程
   - 避免在不合适的时机打扰用户
   - 如果用户明显在做其他事情，不建议

4. **如何表达建议？**
   - 使用自然、友好的语言
   - 根据置信度调整语气（高置信度更肯定，低置信度更询问）
   - 可以解释为什么建议这个动作

### 第三步：输出预测结果

```json
{
  "should_suggest": true,
  "prediction": {
    "action": "run_test",
    "confidence": 0.85,
    "reason": "你刚修改了 API 文件，历史上 50% 的情况下会运行测试"
  },
  "suggestion": "要运行测试验证一下修改吗？",
  "auto_execute": false
}
```

### 预测决策示例

**示例 1：高置信度，建议执行**

输入：
- 当前动作：write_code（修改了 tests/test_user.py）
- 历史：write_code → run_test 概率 50%
- 上下文：修改的是测试文件

分析：
- 用户修改了测试文件，下一步运行测试的可能性很高
- 历史概率支持（50%）
- 上下文强烈支持（测试文件修改后通常会运行）

输出：
```json
{
  "should_suggest": true,
  "prediction": {"action": "run_test", "confidence": 0.90},
  "suggestion": "测试文件已修改，要运行测试吗？"
}
```

**示例 2：中置信度，询问用户**

输入：
- 当前动作：write_code（修改了 src/utils/helper.py）
- 历史：write_code → run_test 概率 50%
- 上下文：普通工具函数文件

分析：
- 历史概率支持（50%）
- 上下文中性（不是测试文件，但可能有相关测试）

输出：
```json
{
  "should_suggest": true,
  "prediction": {"action": "run_test", "confidence": 0.65},
  "suggestion": "你可能想运行测试验证修改"
}
```

**示例 3：低置信度，不建议**

输入：
- 当前动作：read_file（查看了 README.md）
- 历史：read_file → 各种动作概率分散
- 上下文：用户在浏览文档

分析：
- 历史概率分散，没有明显的下一步
- 用户可能只是在了解项目

输出：
```json
{
  "should_suggest": false,
  "reason": "用户在浏览文档，没有明显的下一步动作"
}
```
```

### 6.3 Python 脚本：数据支持

Python 脚本只负责数据的读写和简单统计，不做复杂的预测逻辑：

```python
# get_statistics.py - 获取统计数据供大模型分析

def get_statistics(current_action: str) -> dict:
    """
    获取当前动作的统计数据，供大模型分析
    """
    # 读取转移矩阵
    matrix = load_transition_matrix()
    
    # 获取当前动作的转移统计
    transitions = matrix.get(current_action, {})
    
    # 获取最近的行为序列
    recent_sequence = get_recent_actions(limit=10)
    
    # 获取当前上下文
    context = {
        "last_file": get_last_modified_file(),
        "file_type": detect_file_type(get_last_modified_file()),
        "has_tests_dir": check_tests_directory(),
        "uncommitted_changes": count_uncommitted_changes()
    }
    
    return {
        "current_action": current_action,
        "transitions": transitions,
        "recent_sequence": recent_sequence,
        "context": context
    }
```

### 6.4 冷启动处理

```python
# 预置的常见行为模式（作为大模型的参考）
DEFAULT_PATTERNS = {
    "create_file": {
        "write_code": {"count": 10, "probability": 0.70},
        "git_add": {"count": 3, "probability": 0.20},
    },
    "write_code": {
        "run_test": {"count": 8, "probability": 0.50},
        "git_commit": {"count": 4, "probability": 0.25},
    },
    "edit_file": {
        "run_test": {"count": 6, "probability": 0.40},
        "git_add": {"count": 4, "probability": 0.27},
    },
    "run_test": {
        "fix_bug": {"count": 5, "probability": 0.35},
        "git_commit": {"count": 5, "probability": 0.35},
    },
    "fix_bug": {
        "run_test": {"count": 8, "probability": 0.60},
        "git_commit": {"count": 3, "probability": 0.22},
    }
}
```

**冷启动策略**：
1. 首次使用时，加载预置模式
2. 大模型基于预置模式 + 当前上下文做预测
3. 随着用户使用，逐渐用真实数据替换预置模式

### 6.5 大模型 vs 传统算法对比

| 场景 | 传统算法 | 大模型方案 |
|------|----------|-----------|
| 用户修改测试文件后 | 概率 50% 运行测试 | 理解"测试文件修改后应该运行测试"，置信度提升到 90% |
| 用户连续 3 次 write→test | 概率不变 | 识别到模式，置信度提升 |
| 用户在写文档 | 仍然建议运行测试 | 理解上下文，不建议 |
| 新的动作组合 | 无法预测 | 基于语义理解做推断 |

## 7. 工作流程

### 7.1 动作记录流程

> **重要说明**：Skill 无法真正"拦截"工具调用，因为 Cursor 没有提供 Hook 机制。正确的实现方式是**让大模型在执行工具调用后主动记录**。

#### 7.1.1 为什么无法拦截？

| 限制 | 说明 |
|------|------|
| **无 Hook API** | Cursor 没有提供工具调用的拦截/Hook 接口 |
| **Skill 是被动的** | Skill 只能通过 SKILL.md 指令指导大模型，不是后台进程 |
| **执行时机** | Skill 指令在大模型读取 SKILL.md 时才生效 |

#### 7.1.2 正确的实现方式：大模型主动记录

**方案 A：Always Applied Rule（推荐）**

创建一个 Always Applied Rule，让大模型在每次工具调用后自动记录：

```markdown
# Behavior Recording Rule

## 动作记录规则

每次执行以下工具调用后，自动记录动作：

### 需要记录的工具
- Write / StrReplace / Delete（文件操作）
- Shell（命令执行）
- Grep / SemanticSearch / Glob（搜索操作）

### 记录方式

工具调用完成后，执行：
```bash
python3 <skills_dir>/behavior-prediction/scripts/record_action.py '{
  "type": "动作类型",
  "tool": "工具名称",
  "details": {...},
  "timestamp": "ISO时间"
}'
```

### 动作分类
- Write 新文件 → create_file
- Write/StrReplace 已有文件 → edit_file
- Shell + pytest/npm test → run_test
- Shell + git commit → git_commit
- ...
```

**方案 B：会话结束时批量记录**

在会话结束时，回顾本次会话的所有工具调用，批量记录：

```markdown
## 会话结束时

回顾本次会话执行的工具调用，提取动作序列并记录：

```bash
python3 <skills_dir>/behavior-prediction/scripts/record_session.py '{
  "actions": [
    {"type": "create_file", "timestamp": "..."},
    {"type": "write_code", "timestamp": "..."},
    {"type": "run_test", "timestamp": "..."}
  ]
}'
```
```

**方案 C：用户触发记录**

让用户主动说"记录我的行为"来触发记录。

#### 7.1.3 推荐方案：Always Applied Rule

| 方案 | 实时性 | 完整性 | 用户干扰 | 推荐 |
|------|--------|--------|----------|------|
| Always Applied Rule | ✅ 实时 | ✅ 完整 | ⚠️ 每次调用后有额外脚本 | ✅ 推荐 |
| 会话结束批量记录 | ❌ 延迟 | ✅ 完整 | ✅ 无干扰 | ⚠️ 备选 |
| 用户触发 | ❌ 延迟 | ❌ 不完整 | ✅ 无干扰 | ❌ 不推荐 |

#### 7.1.4 实际流程（使用 Always Applied Rule）

```
用户发送消息
    ↓
AI 读取 Behavior Prediction Skill（如果触发条件满足）
    ↓
AI 处理请求
    ↓
执行工具调用（如 Write, Shell 等）
    ↓
[大模型主动] 根据 Rule 指令，调用 record_action.py 记录动作
    ↓
继续处理或返回响应
    ↓
[大模型主动] 根据 Skill 指令，调用 get_statistics.py 获取统计
    ↓
[大模型主动] 分析并决定是否建议下一步
    ↓
返回响应（可能包含建议）
```

### 7.2 预测与建议流程

```
AI 完成响应
    ↓
[Behavior Skill] 获取最后执行的动作
    ↓
查询 transition_matrix 预测下一步
    ↓
计算置信度
    ↓
┌─────────────────────────────────────┐
│ 置信度 > 0.9                         │
│ → 自动执行（如果配置允许）            │
├─────────────────────────────────────┤
│ 置信度 0.7-0.9                       │
│ → 询问用户："要运行测试吗？[Y/n]"    │
├─────────────────────────────────────┤
│ 置信度 0.5-0.7                       │
│ → 提示："你可能想运行测试"           │
├─────────────────────────────────────┤
│ 置信度 < 0.5                         │
│ → 不提示                             │
└─────────────────────────────────────┘
```

### 7.3 用户反馈学习流程

```
预测建议展示给用户
    ↓
用户响应（接受/拒绝/忽略）
    ↓
记录反馈到 user_feedback.json
    ↓
调整转移概率
    ↓
更新模型
```

## 8. 配置选项

### 8.1 配置文件

```json
{
  "version": "1.0",
  "enabled": true,
  "recording": {
    "enabled": true,
    "retention_days": 90
  },
  "prediction": {
    "enabled": true,
    "auto_execute_threshold": 0.95,
    "suggest_threshold": 0.5,
    "max_suggestions": 3
  },
  "learning": {
    "enabled": true,
    "min_samples_for_prediction": 5,
    "feedback_weight": 1.5
  },
  "privacy": {
    "record_file_paths": true,
    "record_command_args": false,
    "record_code_content": false
  }
}
```

### 8.2 配置说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enabled` | `true` | 总开关 |
| `recording.enabled` | `true` | 是否记录动作 |
| `recording.retention_days` | `90` | 动作记录保留天数 |
| `prediction.enabled` | `true` | 是否启用预测 |
| `prediction.auto_execute_threshold` | `0.95` | 自动执行的置信度阈值 |
| `prediction.suggest_threshold` | `0.5` | 显示建议的最低置信度 |
| `learning.min_samples_for_prediction` | `5` | 最少样本数才启用预测 |
| `learning.feedback_weight` | `1.5` | 用户反馈的权重倍数 |

## 9. 用户交互

### 9.1 建议展示格式

```
✨ 基于你的习惯，你可能想要：
1. 运行测试 (置信度: 85%) [Y]
2. 提交代码 (置信度: 60%) [n]

输入数字选择，或直接继续其他操作。
```

### 9.2 用户命令

| 命令 | 描述 |
|------|------|
| `查看我的行为模式` | 显示学习到的行为模式 |
| `清除行为记录` | 删除所有行为记录 |
| `关闭行为预测` | 临时关闭预测功能 |
| `为什么建议这个` | 解释预测原因 |

## 10. 可行性评估总结

### 10.1 技术可行性：✅ 高

| 维度 | 评估 | 说明 |
|------|------|------|
| 数据采集 | ⭐⭐⭐⭐ | 可通过 Skill 记录工具调用 |
| 模式识别 | ⭐⭐⭐⭐⭐ | 马尔可夫链简单有效 |
| 预测准确性 | ⭐⭐⭐⭐ | 需要足够样本，冷启动可用默认模式 |
| 实现复杂度 | ⭐⭐⭐ | 中等，核心逻辑简单 |

### 10.2 用户价值：✅ 高

| 场景 | 价值 |
|------|------|
| 减少重复操作 | 自动执行常见后续动作 |
| 提醒遗漏步骤 | 提醒用户可能忘记的步骤 |
| 学习用户习惯 | 越用越懂用户 |
| 提升效率 | 减少用户思考和输入 |

### 10.3 实现风险：⚠️ 中等

| 风险 | 严重程度 | 缓解措施 |
|------|----------|----------|
| 误预测干扰用户 | ⭐⭐⭐ | 高阈值 + 用户反馈调整 |
| 冷启动不准确 | ⭐⭐ | 预置常见模式 |
| 数据采集不完整 | ⭐⭐ | 只依赖可获取的数据 |
| 隐私顾虑 | ⭐ | 本地存储，用户完全控制 |

### 10.4 与 Memory Skill 的关系

| 维度 | Memory Skill | Behavior Prediction Skill |
|------|--------------|---------------------------|
| 目标 | 记住对话内容 | 学习行为模式 |
| 数据类型 | 对话摘要 | 动作序列 |
| 触发方式 | 用户问题触发检索 | 动作完成后触发预测 |
| 输出 | 历史上下文 | 下一步建议 |

**可以协同工作**：
- Memory Skill 提供历史上下文
- Behavior Prediction Skill 预测下一步动作
- 两者结合让 AI 更懂用户

## 11. 基于 Cursor 大模型的架构设计（核心）

> 本章节详细说明如何充分利用 Cursor 内置大模型的能力，这是本 Skill 的核心设计理念。

### 11.1 架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SKILL.md（指令层）                           │
│  定义大模型的行为：何时记录、如何分类、如何预测、如何建议              │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      Cursor 大模型（智能层）                         │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐ │
│  │ 动作分类   │  │ 模式识别   │  │ 预测决策   │  │ 自然语言生成     │ │
│  │ 语义理解   │  │ 上下文推理 │  │ 综合判断   │  │ 个性化建议       │ │
│  └───────────┘  └───────────┘  └───────────┘  └───────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓↑
┌─────────────────────────────────────────────────────────────────────┐
│                      Python 脚本（数据层）                           │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐ │
│  │ 记录动作   │  │ 统计计算   │  │ 数据读写   │  │ 上下文收集       │ │
│  │ JSON存储   │  │ 频率/转移  │  │ 文件操作   │  │ 项目信息         │ │
│  └───────────┘  └───────────┘  └───────────┘  └───────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓↑
┌─────────────────────────────────────────────────────────────────────┐
│                      本地存储（持久层）                               │
│  actions/*.json  |  patterns/*.json  |  feedback/*.json  |  config  │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.2 大模型负责的核心任务

#### 11.2.1 动作分类（语义理解）

**传统方案的问题**：
```python
# 硬编码，容易遗漏
if "pytest" in command or "npm test" in command:
    return "run_test"
```

**大模型方案**：

```markdown
## 动作分类任务

请分析以下工具调用/用户消息，判断属于哪种动作类型：

### 输入
- 工具：Shell
- 命令：`python -m pytest tests/unit/ -v --tb=short`
- 用户消息：帮我运行一下单元测试

### 动作类型列表
- run_test: 运行测试
- run_build: 构建项目
- git_commit: 提交代码
- ...

### 请输出
```json
{
  "action_type": "run_test",
  "confidence": 0.95,
  "reason": "命令包含 pytest，用户消息提到'单元测试'"
}
```
```

**优势**：
- 能理解各种变体：`pytest`、`python -m pytest`、`py.test`
- 能结合用户消息理解意图
- 能处理从未见过的命令格式

#### 11.2.2 模式识别（上下文推理）

**传统方案的问题**：
```python
# 只能发现简单的 A→B 频率关系
if transitions["write_code"]["run_test"] > 0.5:
    suggest("run_test")
```

**大模型方案**：

```markdown
## 模式识别任务

请分析用户的行为序列，识别潜在的模式：

### 最近 10 次动作序列
1. create_file → write_code → run_test → git_commit
2. edit_file → run_test → fix_bug → run_test → git_commit
3. create_file → write_code → run_test → git_commit
4. edit_file → run_test → git_commit
5. create_file → write_code → run_test → fix_bug → run_test → git_commit

### 请分析
1. 有哪些明显的行为模式？
2. 用户的工作习惯是什么？
3. 哪些动作组合出现频率最高？

### 输出
```json
{
  "patterns": [
    {
      "sequence": ["write_code", "run_test"],
      "frequency": "very_high",
      "description": "用户习惯写完代码后立即运行测试"
    },
    {
      "sequence": ["run_test", "fix_bug", "run_test"],
      "frequency": "high",
      "description": "测试失败后修复再测试的循环"
    }
  ],
  "user_habits": "TDD 风格开发，重视测试"
}
```
```

**优势**：
- 能识别多步序列模式（A→B→C）
- 能理解模式背后的含义（TDD 风格）
- 能发现隐含的工作习惯

#### 11.2.3 预测决策（综合判断）

**传统方案的问题**：
```python
# 纯概率，不考虑上下文
if probability > 0.5:
    suggest(next_action)
```

**大模型方案**：

```markdown
## 预测决策任务

请基于以下信息，判断是否应该建议用户下一步动作：

### 当前状态
- 刚完成的动作：write_code
- 修改的文件：src/api/user.py
- 文件类型：Python API 文件

### 历史统计
- write_code → run_test: 50% (30次)
- write_code → git_commit: 25% (15次)

### 上下文信息
- 项目有 tests/ 目录
- 有 3 个未提交的更改
- 用户最近 5 次 write_code 后都运行了测试

### 请判断
1. 下一步最可能是什么？
2. 置信度是多少？（考虑历史概率、上下文、最近行为）
3. 现在建议合适吗？
4. 如何用自然语言表达建议？

### 输出
```json
{
  "prediction": "run_test",
  "confidence": 0.85,
  "should_suggest": true,
  "reasoning": "历史概率50%，但考虑到：1)用户最近5次都运行测试 2)项目有测试目录 3)修改的是API文件，置信度提升到85%",
  "suggestion": "API 文件已修改，要运行测试验证一下吗？"
}
```
```

**优势**：
- 综合考虑多个因素
- 能解释预测的理由
- 生成自然、个性化的建议

#### 11.2.4 自然语言生成（个性化建议）

**传统方案的问题**：
```python
# 模板化，生硬
suggestions = {
    "run_test": "是否运行测试？",
    "git_commit": "是否提交代码？"
}
```

**大模型方案**：

根据上下文生成自然的建议：

| 场景 | 传统模板 | 大模型生成 |
|------|----------|-----------|
| 修改测试文件后 | "是否运行测试？" | "测试文件已更新，要验证一下吗？" |
| 修改 API 后 | "是否运行测试？" | "API 改动可能影响其他模块，建议跑一下测试" |
| 连续修改多个文件 | "是否提交代码？" | "已经改了 5 个文件了，要先提交一下吗？" |
| 测试失败后 | "是否修复 bug？" | "测试挂了，我来帮你看看哪里出问题？" |

### 11.3 Python 脚本的职责（精简）

Python 脚本只做大模型不擅长或不需要做的事情：

| 职责 | 说明 | 示例 |
|------|------|------|
| **数据存储** | 读写 JSON 文件 | 保存动作记录、读取统计数据 |
| **简单统计** | 计算频率、计数 | 统计 A→B 出现次数 |
| **上下文收集** | 获取项目信息 | 检查是否有 tests 目录、统计未提交更改 |
| **文件操作** | 创建目录、清理过期数据 | 初始化数据目录、删除旧记录 |

**脚本示例**：

```python
# record_action.py - 记录动作（简单的数据存储）
def record_action(action_data: dict):
    """记录一个动作到今日日志"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = DATA_DIR / "actions" / f"{today}.json"
    
    # 读取现有数据
    if log_file.exists():
        data = json.loads(log_file.read_text())
    else:
        data = {"date": today, "actions": []}
    
    # 追加新动作
    data["actions"].append(action_data)
    
    # 保存
    log_file.write_text(json.dumps(data, indent=2))

# get_statistics.py - 获取统计数据（供大模型分析）
def get_statistics(current_action: str) -> dict:
    """获取统计数据，供大模型做预测决策"""
    return {
        "current_action": current_action,
        "transitions": load_transition_matrix().get(current_action, {}),
        "recent_sequence": get_recent_actions(10),
        "context": collect_context()
    }

# update_matrix.py - 更新转移矩阵（简单的频率统计）
def update_transition(from_action: str, to_action: str):
    """更新转移矩阵"""
    matrix = load_transition_matrix()
    
    if from_action not in matrix:
        matrix[from_action] = {}
    
    if to_action not in matrix[from_action]:
        matrix[from_action][to_action] = {"count": 0}
    
    matrix[from_action][to_action]["count"] += 1
    
    # 重新计算概率
    total = sum(t["count"] for t in matrix[from_action].values())
    for action, data in matrix[from_action].items():
        data["probability"] = round(data["count"] / total, 2)
    
    save_transition_matrix(matrix)
```

### 11.4 SKILL.md 设计（指令层）

SKILL.md 是整个 Skill 的核心，它指导大模型如何工作：

```markdown
# Behavior Prediction Skill

为 Cursor 提供用户行为预测能力。当用户执行动作 A 后，自动预测并建议下一个可能的动作 B。

## 工作流程

### 1. 动作记录（每次工具调用后）

当你执行工具调用（Write、Shell、StrReplace 等）后：

1. **分类动作**：判断这个工具调用属于哪种动作类型
   - 文件操作：create_file, edit_file, delete_file, read_file
   - 命令执行：run_test, run_build, install_dep, git_*
   - 代码生成：write_code, write_test, refactor, fix_bug

2. **记录动作**：执行脚本保存动作记录
   ```bash
   python3 <skills_dir>/behavior-prediction/scripts/record_action.py '{
     "type": "动作类型",
     "details": {"file": "文件路径", "command": "命令内容"},
     "timestamp": "ISO时间"
   }'
   ```

### 2. 预测建议（动作完成后）

当完成一个动作后，判断是否需要建议下一步：

1. **获取统计数据**：
   ```bash
   python3 <skills_dir>/behavior-prediction/scripts/get_statistics.py '{"current_action": "动作类型"}'
   ```

2. **分析并决策**：
   - 参考历史转移概率
   - 考虑当前上下文（修改了什么文件、项目结构等）
   - 考虑最近的行为序列
   - 综合判断是否应该建议

3. **生成建议**（如果决定建议）：
   - 使用自然、友好的语言
   - 根据置信度调整语气
   - 可以解释为什么建议这个动作

### 3. 用户反馈学习

当用户接受或拒绝建议时：

```bash
python3 <skills_dir>/behavior-prediction/scripts/record_feedback.py '{
  "prediction": "run_test",
  "response": "accepted|rejected|ignored",
  "actual_action": "实际执行的动作"
}'
```

## 预测决策指南

### 高置信度建议（>0.8）
- 历史概率 > 60%
- 上下文强烈支持（如：修改测试文件后建议运行测试）
- 最近多次出现相同模式

### 中置信度建议（0.5-0.8）
- 历史概率 40-60%
- 上下文部分支持
- 使用询问语气

### 不建议（<0.5）
- 历史概率 < 40%
- 上下文不支持
- 用户明显在做其他事情

## 建议语气示例

| 置信度 | 语气 | 示例 |
|--------|------|------|
| > 0.9 | 肯定 | "我来帮你运行测试" |
| 0.8-0.9 | 建议 | "要运行测试验证一下吗？" |
| 0.6-0.8 | 询问 | "你可能想运行测试？" |
| 0.5-0.6 | 提示 | "顺便说一下，你可以运行测试检查一下" |
```

### 11.5 与 Memory Skill 的协同

Behavior Prediction Skill 可以与 Memory Skill 协同工作：

```
┌─────────────────────────────────────────────────────────────┐
│                    用户发送消息                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Memory Skill: 检索相关历史记忆                               │
│ → "用户之前说过喜欢 TDD 开发方式"                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ AI 处理请求并执行动作                                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Behavior Prediction Skill: 预测下一步                        │
│ → 结合 Memory（用户喜欢 TDD）+ 行为统计 → 提高 run_test 置信度│
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 输出建议: "按照你的 TDD 习惯，要先运行测试吗？"               │
└─────────────────────────────────────────────────────────────┘
```

## 12. 实现建议

### 12.1 MVP 阶段（第一版）

1. **基础动作记录**
   - 记录文件操作、Shell 命令
   - 大模型进行动作分类

2. **简单预测**
   - 大模型基于统计数据预测
   - 只显示建议，不自动执行

3. **用户反馈**
   - 记录接受/拒绝
   - 简单的权重调整

### 12.2 增强阶段（第二版）

1. **智能动作分类**
   - 大模型分类复杂动作
   - 支持更多动作类型

2. **上下文感知预测**
   - 考虑文件类型、项目类型
   - 结合 Memory Skill 的历史记忆

3. **自动执行**
   - 高置信度自动执行
   - 可配置的阈值

### 12.3 高级阶段（第三版）

1. **序列预测**
   - 预测多步动作序列
   - A → B → C 模式

2. **跨项目学习**
   - 全局行为模式
   - 项目类型特定模式

3. **智能建议**
   - 结合 Memory Skill
   - 个性化建议文案

## 13. 关键技术问题：如何记录动作？

> 这是实现 Behavior Prediction Skill 的核心技术挑战。

### 13.1 问题本质

**问题**：Skill 如何知道用户/AI 执行了什么动作？

**挑战**：
- Cursor 没有提供工具调用的 Hook/拦截 API
- Skill 不是后台进程，无法监听事件
- Skill 只能通过 SKILL.md 指令指导大模型

### 13.2 可行的解决方案

#### 方案 1：Always Applied Rule（推荐）

**原理**：创建一个始终生效的规则，指导大模型在每次工具调用后自动记录。

**实现**：

```markdown
# .cursor/rules/behavior-recording.mdc

## 动作记录规则（Always Applied）

### 触发条件
每次执行以下工具后自动触发：
- Write / StrReplace / Delete
- Shell
- Grep / SemanticSearch / Glob

### 执行动作
工具调用完成后，立即执行：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{
  "tool": "工具名称",
  "type": "动作类型",
  "details": {...}
}'
```
```

**优点**：
- 实时记录，数据完整
- 大模型自动执行，无需用户干预

**缺点**：
- 每次工具调用后有额外的脚本执行
- 依赖大模型正确遵循规则

#### 方案 2：会话结束批量记录

**原理**：在会话结束时，大模型回顾本次会话的工具调用历史，批量记录。

**实现**：

```markdown
# SKILL.md 中的指令

## 会话结束时

在对话即将结束时（用户说"谢谢"、"好的"、"结束"等），执行：

1. 回顾本次会话执行的所有工具调用
2. 提取动作序列
3. 调用脚本批量记录

```bash
python3 record_session.py '{
  "actions": [
    {"type": "create_file", "file": "...", "timestamp": "..."},
    {"type": "run_test", "command": "...", "timestamp": "..."}
  ]
}'
```
```

**优点**：
- 不影响正常工作流程
- 一次性记录，效率高

**缺点**：
- 非实时，可能遗漏（如会话异常结束）
- 需要大模型记住整个会话的工具调用

#### 方案 3：利用 Cursor 的对话历史

**原理**：Cursor 会保存对话历史，可以通过分析历史记录提取动作。

**实现**：
- 定期运行脚本分析 Cursor 的对话历史文件
- 提取工具调用记录

**优点**：
- 不依赖大模型主动记录
- 数据完整

**缺点**：
- 需要了解 Cursor 的内部存储格式
- 可能涉及隐私问题
- Cursor 更新可能导致格式变化

### 13.3 推荐方案

**推荐：Always Applied Rule（核心）+ 会话结束处理（可选）+ 下次会话检查（兜底）**

> **重要**：在 Cursor 中，用户说"谢谢"等结束语后，对话可能直接结束，AI 没有机会执行会话结束处理。因此，**实时记录必须是完整的**，不能依赖会话结束处理。

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Always Applied Rule（核心，必须）                          │
│ - 每次工具调用后立即记录                                      │
│ - 立即更新转移矩阵                                           │
│ - 数据实时完整，不依赖会话结束                                │
└─────────────────────────────────────────────────────────────┘
                           +
┌─────────────────────────────────────────────────────────────┐
│ 2. 会话结束处理（可选，如果有机会执行）                        │
│ - 检测结束信号时执行                                         │
│ - 记录会话统计                                               │
│ - 验证数据一致性                                             │
└─────────────────────────────────────────────────────────────┘
                           +
┌─────────────────────────────────────────────────────────────┐
│ 3. 下次会话开始时检查（兜底）                                  │
│ - 检查上次会话是否正常结束                                    │
│ - 如果没有，补充处理                                         │
└─────────────────────────────────────────────────────────────┘
```

**关键设计原则**：
- **实时记录是核心**：每次工具调用后立即记录并更新转移矩阵
- **会话结束是可选的**：即使没有执行，数据也是完整的
- **下次会话检查是兜底**：确保没有遗漏

### 13.4 实现细节

#### Always Applied Rule 示例

```markdown
# .cursor/rules/behavior-recording.mdc

---
description: 自动记录用户行为，用于行为预测
globs: ["**/*"]
alwaysApply: true
---

## 动作记录规则

### 何时记录

在执行以下工具调用**之后**，自动记录动作：

| 工具 | 动作类型 | 记录内容 |
|------|----------|----------|
| Write（新文件） | create_file | 文件路径、文件类型 |
| Write/StrReplace | edit_file | 文件路径、修改行数 |
| Delete | delete_file | 文件路径 |
| Shell | 根据命令分类 | 命令内容、退出码 |

### 如何记录

执行完工具调用后，调用记录脚本：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{
  "type": "动作类型",
  "tool": "工具名称",
  "timestamp": "2026-01-31T10:30:00Z",
  "details": {
    "file_path": "文件路径（如适用）",
    "command": "命令内容（如适用）"
  }
}'
```

### Shell 命令分类

| 命令特征 | 动作类型 |
|----------|----------|
| pytest, npm test, go test | run_test |
| npm build, make, cargo build | run_build |
| git add | git_add |
| git commit | git_commit |
| git push | git_push |
| npm install, pip install | install_dep |
| 其他 | shell_command |

### 注意事项

- 记录失败不应阻塞正常流程
- 只记录关键动作，避免过度记录
- 本地存储，用户完全控制数据
```

### 13.5 可行性评估

| 维度 | 评估 | 说明 |
|------|------|------|
| **技术可行性** | ✅ 高 | Always Applied Rule 是 Cursor 支持的功能 |
| **数据完整性** | ⚠️ 中 | 依赖大模型正确遵循规则 |
| **性能影响** | ✅ 低 | 脚本执行很快（<100ms） |
| **用户体验** | ✅ 好 | 对用户透明，无感知 |

### 13.6 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 大模型不遵循规则 | 在 SKILL.md 中强调记录的重要性 |
| 记录脚本失败 | 脚本内部处理异常，不影响主流程 |
| 数据不完整 | 会话结束时补充记录 |
| 记录过多影响性能 | 只记录关键动作，异步写入 |

### 13.7 组合方案详细实现

> **推荐方案**：Always Applied Rule（实时记录）+ 会话结束批量记录（补充完善）

#### 13.7.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户与 AI 对话                                │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Always Applied Rule: behavior-recording.mdc                          │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 每次工具调用后：                                                  │ │
│ │ 1. 判断是否是需要记录的动作                                       │ │
│ │ 2. 调用 record_action.py 实时记录                                │ │
│ │ 3. 继续正常流程                                                  │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 会话结束时（检测到结束信号）                                          │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 1. 回顾本次会话的所有工具调用                                     │ │
│ │ 2. 与已记录的动作对比，找出遗漏                                   │ │
│ │ 3. 调用 finalize_session.py 补充记录 + 更新统计                  │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

#### 13.7.2 Always Applied Rule 完整实现

**文件位置**：`.cursor/rules/behavior-recording.mdc`

```markdown
---
description: 自动记录用户行为，用于行为预测 Skill
globs: ["**/*"]
alwaysApply: true
---

# 行为记录规则

## 一、触发条件

在执行以下工具调用**完成后**，自动记录动作：

### 必须记录的工具
| 工具 | 条件 | 动作类型 |
|------|------|----------|
| Write | 新文件 | create_file |
| Write | 已有文件 | edit_file |
| StrReplace | - | edit_file |
| Delete | - | delete_file |
| Shell | 命令执行成功 | 根据命令分类 |

### 可选记录的工具（默认不记录）
| 工具 | 说明 |
|------|------|
| Read | 读取文件（太频繁，默认不记录） |
| Grep/Glob | 搜索操作（太频繁，默认不记录） |

## 二、动作分类规则

### Shell 命令分类表

| 命令特征 | 动作类型 | 示例 |
|----------|----------|------|
| pytest, npm test, go test, cargo test | run_test | `pytest tests/ -v` |
| npm build, yarn build, make, cargo build | run_build | `npm run build` |
| npm start, python.*app, flask run, uvicorn | run_server | `npm start` |
| npm install, pip install, yarn add | install_dep | `pip install requests` |
| git add | git_add | `git add .` |
| git commit | git_commit | `git commit -m "msg"` |
| git push | git_push | `git push origin main` |
| git pull | git_pull | `git pull` |
| 其他 | shell_command | - |

### 文件类型识别

| 文件路径特征 | 文件类型 |
|--------------|----------|
| tests/, test_, _test.py, .test.ts | test_file |
| .config., config/, settings | config_file |
| README, .md | doc_file |
| 其他 | source_file |

## 三、记录执行

### 记录脚本调用

工具调用完成后，执行：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{
  "type": "动作类型",
  "tool": "工具名称",
  "timestamp": "ISO8601时间",
  "details": {
    "file_path": "文件路径（如适用）",
    "file_type": "文件类型（如适用）",
    "command": "命令内容（如适用）",
    "exit_code": "退出码（如适用）"
  }
}'
```

### 记录示例

**示例 1：创建文件**
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{
  "type": "create_file",
  "tool": "Write",
  "timestamp": "2026-01-31T10:30:00Z",
  "details": {
    "file_path": "src/utils/helper.py",
    "file_type": "source_file"
  }
}'
```

**示例 2：运行测试**
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{
  "type": "run_test",
  "tool": "Shell",
  "timestamp": "2026-01-31T10:35:00Z",
  "details": {
    "command": "pytest tests/ -v",
    "exit_code": 0
  }
}'
```

## 四、注意事项

1. **记录失败不阻塞**：如果脚本执行失败，继续正常流程
2. **频率控制**：相同动作 5 秒内不重复记录
3. **静默执行**：不向用户显示记录过程
4. **本地存储**：所有数据存储在本地，用户完全控制
```

#### 13.7.3 会话结束批量记录实现

**在 SKILL.md 中添加会话结束处理指令**：

```markdown
## 会话结束处理

### 检测会话结束信号

当检测到以下信号时，认为会话即将结束：
- 用户说"谢谢"、"好的"、"结束"、"拜拜"、"再见"
- 用户说"thanks"、"done"、"bye"、"that's all"
- 用户长时间无响应后的最后一条消息

### 会话结束时执行

1. **回顾本次会话**：列出本次会话执行的所有工具调用
2. **调用结束脚本**：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/finalize_session.py '{
  "session_id": "会话ID（可选）",
  "actions_summary": [
    {"type": "create_file", "tool": "Write", "file": "src/utils/helper.py"},
    {"type": "edit_file", "tool": "StrReplace", "file": "src/api/user.py"},
    {"type": "run_test", "tool": "Shell", "command": "pytest"}
  ],
  "start_time": "会话开始时间",
  "end_time": "会话结束时间"
}'
```

### finalize_session.py 的职责

1. **补充遗漏**：对比 actions_summary 和已记录的动作，补充遗漏的记录
2. **更新转移矩阵**：根据本次会话的动作序列更新转移概率
3. **清理临时数据**：清理本次会话的临时状态
```

#### 13.7.4 Python 脚本实现

**record_action.py**：

```python
#!/usr/bin/env python3
"""实时记录单个动作"""

import json
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / ".cursor" / "skills" / "behavior-prediction-data"

def record_action(action_data: dict) -> dict:
    """记录一个动作到今日日志"""
    try:
        # 确保目录存在
        actions_dir = DATA_DIR / "actions"
        actions_dir.mkdir(parents=True, exist_ok=True)
        
        # 今日日志文件
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = actions_dir / f"{today}.json"
        
        # 读取或创建日志
        if log_file.exists():
            data = json.loads(log_file.read_text())
        else:
            data = {"date": today, "actions": []}
        
        # 频率控制：5秒内相同动作不重复记录
        if data["actions"]:
            last_action = data["actions"][-1]
            if (last_action.get("type") == action_data.get("type") and
                last_action.get("details") == action_data.get("details")):
                last_time = datetime.fromisoformat(last_action["timestamp"].replace("Z", "+00:00"))
                now = datetime.now().astimezone()
                if (now - last_time).total_seconds() < 5:
                    return {"status": "skipped", "reason": "duplicate within 5s"}
        
        # 添加动作
        action_data["id"] = f"{today}-{len(data['actions']) + 1:03d}"
        if "timestamp" not in action_data:
            action_data["timestamp"] = datetime.now().isoformat() + "Z"
        
        data["actions"].append(action_data)
        
        # 保存
        log_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        
        # 更新转移矩阵（如果有前一个动作）
        if len(data["actions"]) >= 2:
            prev_action = data["actions"][-2]["type"]
            curr_action = action_data["type"]
            update_transition(prev_action, curr_action)
        
        return {"status": "success", "action_id": action_data["id"]}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def update_transition(from_action: str, to_action: str):
    """更新转移矩阵"""
    matrix_file = DATA_DIR / "patterns" / "transition_matrix.json"
    matrix_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 读取或创建矩阵
    if matrix_file.exists():
        matrix = json.loads(matrix_file.read_text())
    else:
        matrix = {"version": "1.0", "matrix": {}, "total_transitions": 0}
    
    # 更新计数
    if from_action not in matrix["matrix"]:
        matrix["matrix"][from_action] = {}
    
    if to_action not in matrix["matrix"][from_action]:
        matrix["matrix"][from_action][to_action] = {"count": 0}
    
    matrix["matrix"][from_action][to_action]["count"] += 1
    matrix["total_transitions"] += 1
    
    # 重新计算概率
    total = sum(t["count"] for t in matrix["matrix"][from_action].values())
    for action, data in matrix["matrix"][from_action].items():
        data["probability"] = round(data["count"] / total, 3)
    
    matrix["updated_at"] = datetime.now().isoformat() + "Z"
    
    # 保存
    matrix_file.write_text(json.dumps(matrix, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Missing action data"}))
        sys.exit(1)
    
    try:
        action_data = json.loads(sys.argv[1])
        result = record_action(action_data)
        print(json.dumps(result))
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(1)
```

**finalize_session.py**：

```python
#!/usr/bin/env python3
"""会话结束时的批量处理"""

import json
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / ".cursor" / "skills" / "behavior-prediction-data"

def finalize_session(session_data: dict) -> dict:
    """会话结束时的处理"""
    try:
        actions_summary = session_data.get("actions_summary", [])
        
        if not actions_summary:
            return {"status": "success", "message": "No actions to process"}
        
        # 1. 补充遗漏的动作记录
        补充数 = supplement_missing_actions(actions_summary)
        
        # 2. 更新转移矩阵（基于完整序列）
        update_transitions_from_sequence(actions_summary)
        
        # 3. 记录会话统计
        record_session_stats(session_data)
        
        return {
            "status": "success",
            "actions_count": len(actions_summary),
            "supplemented": 补充数,
            "message": f"Session finalized with {len(actions_summary)} actions"
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def supplement_missing_actions(actions_summary: list) -> int:
    """补充遗漏的动作记录"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = DATA_DIR / "actions" / f"{today}.json"
    
    if log_file.exists():
        existing = json.loads(log_file.read_text())
        existing_types = {a["type"] for a in existing.get("actions", [])}
    else:
        existing = {"date": today, "actions": []}
        existing_types = set()
    
    补充数 = 0
    for action in actions_summary:
        # 简单检查：如果类型不在已记录中，补充记录
        # 实际实现可以更精细（比如检查时间戳）
        if action.get("type") not in existing_types:
            action["id"] = f"{today}-{len(existing['actions']) + 1:03d}"
            action["timestamp"] = datetime.now().isoformat() + "Z"
            action["source"] = "session_finalize"  # 标记来源
            existing["actions"].append(action)
            补充数 += 1
    
    if 补充数 > 0:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    
    return 补充数


def update_transitions_from_sequence(actions: list):
    """根据动作序列更新转移矩阵"""
    if len(actions) < 2:
        return
    
    matrix_file = DATA_DIR / "patterns" / "transition_matrix.json"
    matrix_file.parent.mkdir(parents=True, exist_ok=True)
    
    if matrix_file.exists():
        matrix = json.loads(matrix_file.read_text())
    else:
        matrix = {"version": "1.0", "matrix": {}, "total_transitions": 0}
    
    # 遍历序列，更新转移
    for i in range(len(actions) - 1):
        from_action = actions[i].get("type", "unknown")
        to_action = actions[i + 1].get("type", "unknown")
        
        if from_action not in matrix["matrix"]:
            matrix["matrix"][from_action] = {}
        
        if to_action not in matrix["matrix"][from_action]:
            matrix["matrix"][from_action][to_action] = {"count": 0}
        
        # 会话结束时的更新权重较低（避免重复计数）
        matrix["matrix"][from_action][to_action]["count"] += 0.5
        matrix["total_transitions"] += 0.5
    
    # 重新计算所有概率
    for from_action in matrix["matrix"]:
        total = sum(t["count"] for t in matrix["matrix"][from_action].values())
        if total > 0:
            for action, data in matrix["matrix"][from_action].items():
                data["probability"] = round(data["count"] / total, 3)
    
    matrix["updated_at"] = datetime.now().isoformat() + "Z"
    matrix_file.write_text(json.dumps(matrix, indent=2, ensure_ascii=False))


def record_session_stats(session_data: dict):
    """记录会话统计信息"""
    stats_file = DATA_DIR / "stats" / "sessions.json"
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    
    if stats_file.exists():
        stats = json.loads(stats_file.read_text())
    else:
        stats = {"sessions": [], "total_sessions": 0}
    
    session_record = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "actions_count": len(session_data.get("actions_summary", [])),
        "action_types": list(set(a.get("type") for a in session_data.get("actions_summary", [])))
    }
    
    stats["sessions"].append(session_record)
    stats["total_sessions"] += 1
    
    # 只保留最近 100 条会话记录
    if len(stats["sessions"]) > 100:
        stats["sessions"] = stats["sessions"][-100:]
    
    stats_file.write_text(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Missing session data"}))
        sys.exit(1)
    
    try:
        session_data = json.loads(sys.argv[1])
        result = finalize_session(session_data)
        print(json.dumps(result, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(1)
```

#### 13.7.5 数据流示意图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         会话开始                                     │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 用户: "帮我创建一个工具函数文件"                                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ AI 执行: Write("src/utils/helper.py", ...)                          │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ [Always Applied Rule 触发]                                           │
│ AI 执行: python3 record_action.py '{"type": "create_file", ...}'    │
│ → 写入 actions/2026-01-31.json                                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 用户: "帮我写一个字符串处理函数"                                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ AI 执行: StrReplace("src/utils/helper.py", ...)                     │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ [Always Applied Rule 触发]                                           │
│ AI 执行: python3 record_action.py '{"type": "edit_file", ...}'      │
│ → 写入 actions/2026-01-31.json                                      │
│ → 更新 transition_matrix.json (create_file → edit_file)             │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 用户: "运行一下测试"                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ AI 执行: Shell("pytest tests/ -v")                                  │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ [Always Applied Rule 触发]                                           │
│ AI 执行: python3 record_action.py '{"type": "run_test", ...}'       │
│ → 写入 actions/2026-01-31.json                                      │
│ → 更新 transition_matrix.json (edit_file → run_test)                │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 用户: "好的，谢谢！"                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ [会话结束信号检测]                                                    │
│ AI 执行: python3 finalize_session.py '{                             │
│   "actions_summary": [                                               │
│     {"type": "create_file", ...},                                    │
│     {"type": "edit_file", ...},                                      │
│     {"type": "run_test", ...}                                        │
│   ]                                                                  │
│ }'                                                                   │
│ → 补充遗漏的记录                                                      │
│ → 更新完整的转移矩阵                                                  │
│ → 记录会话统计                                                        │
└─────────────────────────────────────────────────────────────────────┘
```

#### 13.7.6 数据加载策略

> **核心问题**：每次会话都需要加载之前的行为记录吗？

**答案：不需要全部加载，采用按需加载 + 增量更新策略。**

##### 数据分层

| 数据类型 | 文件 | 大小 | 加载时机 |
|----------|------|------|----------|
| **转移矩阵** | `transition_matrix.json` | ~5-10KB | 预测时加载 |
| **今日动作** | `actions/2026-01-31.json` | ~10-50KB | 记录时追加 |
| **历史动作** | `actions/*.json` | 每天 ~50KB | 几乎不加载 |
| **用户反馈** | `feedback/*.json` | ~5KB | 学习时加载 |

##### 加载策略详解

**1. 转移矩阵（核心数据）**

```
┌─────────────────────────────────────────────────────────────┐
│ 转移矩阵是预测的核心数据                                      │
│ - 已经是聚合后的统计数据                                      │
│ - 文件很小（通常 < 10KB）                                     │
│ - 只在需要预测时加载                                          │
└─────────────────────────────────────────────────────────────┘

加载时机：
- 当完成一个动作后，需要预测下一步时
- 调用 get_statistics.py 时加载

不加载时机：
- 会话开始时（不需要预加载）
- 用户只是问问题，没有执行动作时
```

**2. 今日动作日志（追加写入）**

```
┌─────────────────────────────────────────────────────────────┐
│ 今日动作日志采用追加写入模式                                   │
│ - 每次记录动作时，追加到文件末尾                               │
│ - 不需要读取全部历史                                          │
│ - 只在去重检查时读取最后一条                                   │
└─────────────────────────────────────────────────────────────┘

写入流程：
1. 打开今日日志文件
2. 读取最后一条记录（用于去重）
3. 追加新记录
4. 保存文件
```

**3. 历史动作日志（几乎不加载）**

```
┌─────────────────────────────────────────────────────────────┐
│ 历史动作日志是原始数据，通常不需要加载                          │
│ - 转移矩阵已经包含了统计信息                                   │
│ - 只在以下场景才需要：                                        │
│   - 用户查看历史行为                                          │
│   - 重建转移矩阵                                              │
│   - 数据分析/导出                                             │
└─────────────────────────────────────────────────────────────┘
```

##### 增量更新机制

**关键设计**：每次记录动作时，同时更新转移矩阵，而不是每次预测时重新计算。

```python
# record_action.py 中的增量更新

def record_action(action_data: dict):
    # 1. 追加到今日日志
    append_to_daily_log(action_data)
    
    # 2. 增量更新转移矩阵（如果有前一个动作）
    if has_previous_action():
        prev_action = get_previous_action()
        curr_action = action_data["type"]
        
        # 直接更新矩阵，不需要重新计算全部
        update_transition_count(prev_action, curr_action)
        recalculate_probabilities(prev_action)  # 只重算这一行
```

##### 预测时的数据加载

```python
# get_statistics.py - 预测时加载的数据

def get_statistics(current_action: str) -> dict:
    """获取预测所需的统计数据"""
    
    # 1. 加载转移矩阵（~5KB，很快）
    matrix = load_transition_matrix()
    
    # 2. 获取当前动作的转移统计
    transitions = matrix.get("matrix", {}).get(current_action, {})
    
    # 3. 获取最近的动作序列（只读今日日志的最后 10 条）
    recent_sequence = get_recent_actions(limit=10)
    
    # 4. 收集当前上下文（不涉及历史数据）
    context = collect_current_context()
    
    return {
        "current_action": current_action,
        "transitions": transitions,
        "recent_sequence": recent_sequence,
        "context": context
    }
```

##### 性能分析

| 操作 | 数据量 | 耗时 | 频率 |
|------|--------|------|------|
| 记录动作 | 追加 ~200B | <10ms | 每次工具调用 |
| 更新矩阵 | 读写 ~5KB | <20ms | 每次工具调用 |
| 预测加载 | 读取 ~5KB | <10ms | 预测时 |
| 会话结束 | 读写 ~50KB | <100ms | 每次会话结束 |

**结论**：
- 不需要在会话开始时加载全部历史
- 转移矩阵是轻量级的聚合数据，按需加载
- 增量更新保证数据实时性，避免重复计算

#### 13.7.7 最终数据结构

**actions/2026-01-31.json**：
```json
{
  "date": "2026-01-31",
  "actions": [
    {
      "id": "2026-01-31-001",
      "type": "create_file",
      "tool": "Write",
      "timestamp": "2026-01-31T10:30:00Z",
      "details": {
        "file_path": "src/utils/helper.py",
        "file_type": "source_file"
      }
    },
    {
      "id": "2026-01-31-002",
      "type": "edit_file",
      "tool": "StrReplace",
      "timestamp": "2026-01-31T10:32:00Z",
      "details": {
        "file_path": "src/utils/helper.py",
        "file_type": "source_file"
      }
    },
    {
      "id": "2026-01-31-003",
      "type": "run_test",
      "tool": "Shell",
      "timestamp": "2026-01-31T10:35:00Z",
      "details": {
        "command": "pytest tests/ -v",
        "exit_code": 0
      }
    }
  ]
}
```

**patterns/transition_matrix.json**：
```json
{
  "version": "1.0",
  "updated_at": "2026-01-31T10:35:00Z",
  "total_transitions": 2,
  "matrix": {
    "create_file": {
      "edit_file": {"count": 1, "probability": 1.0}
    },
    "edit_file": {
      "run_test": {"count": 1, "probability": 1.0}
    }
  }
}
```

## 14. 结论

**用户行为预测 Skill 是可行的**，理由如下：

### 14.1 技术可行性

| 维度 | 评估 | 说明 |
|------|------|------|
| **数据采集** | ✅ 高 | 通过 Skill 记录工具调用，数据可获取 |
| **动作分类** | ✅ 高 | 大模型语义理解，比硬编码更准确 |
| **模式识别** | ✅ 高 | 大模型上下文推理，能发现隐含模式 |
| **预测决策** | ✅ 高 | 大模型综合判断，考虑多因素 |
| **实现复杂度** | ✅ 中 | 脚本简单，核心逻辑由大模型处理 |

### 14.2 核心优势：充分利用 Cursor 大模型

1. **零外部依赖**：不需要 sklearn、tensorflow 等机器学习库
2. **语义理解**：大模型能理解各种命令变体和用户意图
3. **上下文感知**：能结合当前上下文做出合理判断
4. **自然交互**：生成个性化、自然的建议文案
5. **持续改进**：随着大模型能力提升，Skill 自动受益

### 14.3 与传统方案对比

| 维度 | 传统 ML 方案 | 大模型方案 |
|------|-------------|-----------|
| 依赖 | sklearn/tensorflow | Cursor 内置 |
| 安装 | 需要 pip install | 零安装 |
| 分类准确度 | 依赖训练数据 | 语义理解，更灵活 |
| 上下文理解 | 需要特征工程 | 自然理解 |
| 维护成本 | 需要重新训练 | 几乎为零 |
| 冷启动 | 需要大量数据 | 可立即使用 |

### 14.4 风险与缓解

| 风险 | 严重程度 | 缓解措施 |
|------|----------|----------|
| 误预测干扰用户 | ⭐⭐⭐ | 置信度阈值 + 用户反馈调整 |
| 大模型理解偏差 | ⭐⭐ | 提供清晰的 Skill 指令 |
| 数据采集不完整 | ⭐⭐ | Always Applied Rule + 会话结束补充 |
| 隐私顾虑 | ⭐ | 本地存储，用户完全控制 |

### 14.5 实施建议

**推荐从 MVP 开始**：

1. **第一周**：实现基础动作记录和统计
2. **第二周**：实现大模型预测决策
3. **第三周**：添加用户反馈机制
4. **后续**：根据使用反馈持续优化

**核心文件**：
- `SKILL.md`：指导大模型如何工作（最重要）
- `scripts/record_action.py`：记录动作
- `scripts/get_statistics.py`：获取统计数据
- `scripts/record_feedback.py`：记录用户反馈

### 14.6 最终结论

**用户行为预测 Skill 是一个高价值、技术可行的项目**。

通过充分利用 Cursor 内置大模型的能力，我们可以用最小的实现成本获得最大的智能效果。大模型负责"思考"（分类、识别、预测、生成），脚本负责"记忆"（数据存储和简单统计），这种分工让整个 Skill 既强大又简洁。

---

*文档版本: 1.0*  
*创建日期: 2026-01-31*  
*更新说明: 优化为基于 Cursor 大模型能力的设计方案*
