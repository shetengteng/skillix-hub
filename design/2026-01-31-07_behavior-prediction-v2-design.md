# 行为预测 Skill V2 设计文档

## 1. 概述

**Skill 名称**: behavior-prediction (V2)  
**版本**: 2.0  
**设计日期**: 2026-01-31

### 1.1 V1 vs V2 对比

| 维度 | V1（当前） | V2（新设计） |
|------|-----------|-------------|
| **记录内容** | 工具调用动作 | 完整会话内容 |
| **记录粒度** | 单个动作 | 整个会话 |
| **模式类型** | 动作转移概率 | 工作流程 + 偏好 + 项目模式 |
| **用途** | 预测下一步 | 预测 + 用户画像 + 优化交互 |
| **数据来源** | Always Applied Rule | 会话结束时总结 |

### 1.2 核心理念

**从"记录指令"到"理解用户"**

V1 关注的是：用户执行了什么动作（create_file, run_test）
V2 关注的是：用户在做什么事情、有什么习惯、喜欢什么方式

```
V1: 记录 → 统计 → 预测
V2: 记录 → 理解 → 画像 → 预测 + 优化
```

### 1.3 设计目标

1. **记录完整会话内容**：用户对话、AI 操作、会话摘要
2. **提取多维度行为模式**：
   - 工作流程模式（设计 → 实现 → 测试 → 提交）
   - 偏好模式（技术栈、编码风格、工具选择）
   - 项目模式（不同项目类型的开发流程）
3. **三大应用场景**：
   - 预测下一步操作
   - 生成用户画像/偏好
   - 优化 AI 的交互方式

## 2. 会话内容记录

### 2.1 记录什么

每次会话结束时，记录以下内容：

```
┌─────────────────────────────────────────────────────────────────────┐
│                        会话记录结构                                   │
├─────────────────────────────────────────────────────────────────────┤
│ 1. 会话元信息                                                        │
│    - 会话ID、开始/结束时间、持续时长                                   │
│    - 项目信息（路径、类型、技术栈）                                    │
│                                                                     │
│ 2. 对话内容                                                          │
│    - 用户消息列表（原始文本）                                         │
│    - AI 响应摘要                                                     │
│                                                                     │
│ 3. 操作记录                                                          │
│    - 文件操作（创建、修改、删除）                                      │
│    - 命令执行（Shell 命令及结果）                                     │
│    - 搜索操作（搜索内容及结果）                                       │
│                                                                     │
│ 4. 会话摘要（AI 生成）                                                │
│    - 主题/目标                                                       │
│    - 完成的任务                                                      │
│    - 使用的技术/工具                                                  │
│    - 工作流程阶段                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 会话记录数据结构

```json
{
  "session_id": "sess_20260131_001",
  "project": {
    "path": "/Users/xxx/my-project",
    "name": "my-project",
    "type": "backend_api",
    "tech_stack": ["python", "fastapi", "postgresql"]
  },
  "time": {
    "start": "2026-01-31T10:00:00Z",
    "end": "2026-01-31T10:45:00Z",
    "duration_minutes": 45
  },
  "conversation": {
    "user_messages": [
      {
        "index": 1,
        "content": "帮我创建一个用户认证 API",
        "timestamp": "2026-01-31T10:00:00Z"
      },
      {
        "index": 2,
        "content": "添加 JWT token 验证",
        "timestamp": "2026-01-31T10:15:00Z"
      },
      {
        "index": 3,
        "content": "写一下单元测试",
        "timestamp": "2026-01-31T10:30:00Z"
      }
    ],
    "message_count": 3
  },
  "operations": {
    "files": {
      "created": ["src/api/auth.py", "src/utils/jwt.py", "tests/test_auth.py"],
      "modified": ["src/main.py", "requirements.txt"],
      "deleted": []
    },
    "commands": [
      {
        "command": "pip install pyjwt",
        "type": "install_dep",
        "exit_code": 0
      },
      {
        "command": "pytest tests/test_auth.py -v",
        "type": "run_test",
        "exit_code": 0
      }
    ],
    "searches": []
  },
  "summary": {
    "topic": "用户认证功能开发",
    "goals": ["创建认证 API", "实现 JWT 验证", "编写测试"],
    "completed_tasks": [
      "创建 auth.py API 文件",
      "实现 JWT token 生成和验证",
      "添加单元测试并通过"
    ],
    "technologies_used": ["FastAPI", "PyJWT", "pytest"],
    "workflow_stage": "implement_and_test",
    "tags": ["#auth", "#api", "#jwt", "#testing"]
  }
}
```

### 2.3 记录时机

**会话结束时记录**（而非实时记录）

| 触发条件 | 说明 |
|----------|------|
| 用户说结束语 | "谢谢"、"好的"、"结束"、"done"、"thanks" |
| 会话自然结束 | 用户长时间无响应 |
| 用户主动保存 | "保存这次会话" |

**为什么选择会话结束时记录？**

| 方案 | 优点 | 缺点 |
|------|------|------|
| 实时记录（V1） | 数据完整 | 频繁 I/O、数据碎片化 |
| 会话结束记录（V2） | 完整上下文、可生成摘要 | 异常结束可能丢失 |

**V2 选择会话结束记录的原因**：
1. 需要完整上下文才能生成有意义的摘要
2. 需要知道整个会话的目标和成果
3. 减少对正常工作流程的干扰
4. 大模型可以回顾整个会话生成高质量摘要

## 3. 行为模式提取

### 3.1 三种模式类型

```
┌─────────────────────────────────────────────────────────────────────┐
│                        行为模式体系                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │  工作流程模式    │  │   偏好模式       │  │   项目模式       │     │
│  │                 │  │                 │  │                 │     │
│  │ 设计 → 实现     │  │ 技术栈偏好       │  │ API 项目流程     │     │
│  │ 实现 → 测试     │  │ 编码风格        │  │ 前端项目流程     │     │
│  │ 测试 → 提交     │  │ 工具选择        │  │ 全栈项目流程     │     │
│  │ ...            │  │ 交互习惯        │  │ ...            │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 工作流程模式

**定义**：用户在开发过程中的典型步骤序列

**示例**：
```
模式 1: 设计优先
  设计文档 → 实现代码 → 编写测试 → 代码审查 → 提交

模式 2: TDD 风格
  编写测试 → 实现代码 → 重构 → 提交

模式 3: 快速迭代
  实现代码 → 手动测试 → 修复 → 提交

模式 4: 文档驱动
  阅读文档 → 设计方案 → 讨论确认 → 实现
```

**数据结构**：
```json
{
  "workflow_patterns": [
    {
      "pattern_id": "wf_001",
      "name": "设计优先开发",
      "sequence": ["design", "implement", "test", "review", "commit"],
      "frequency": 15,
      "confidence": 0.75,
      "contexts": ["new_feature", "api_development"],
      "description": "用户习惯先写设计文档，再实现代码"
    },
    {
      "pattern_id": "wf_002",
      "name": "TDD 开发",
      "sequence": ["write_test", "implement", "refactor", "commit"],
      "frequency": 8,
      "confidence": 0.60,
      "contexts": ["bug_fix", "refactoring"],
      "description": "用户在修复 bug 时倾向于先写测试"
    }
  ]
}
```

### 3.3 偏好模式

**定义**：用户在技术选择、编码风格、工具使用等方面的偏好

**偏好维度**：

| 维度 | 示例 |
|------|------|
| **技术栈** | Python > JavaScript, FastAPI > Flask, PostgreSQL > MySQL |
| **编码风格** | 函数式 > 面向对象, 类型注解 > 无类型 |
| **测试习惯** | 单元测试优先, 喜欢 pytest, 测试覆盖率要求高 |
| **文档习惯** | 喜欢详细注释, 习惯写 README, 偏好中文文档 |
| **Git 习惯** | 小步提交, commit message 用英文, 喜欢用 conventional commits |
| **交互习惯** | 喜欢详细解释, 偏好代码示例, 习惯确认后再执行 |

**数据结构**：
```json
{
  "preferences": {
    "tech_stack": {
      "languages": {
        "python": { "count": 45, "preference": 0.85 },
        "typescript": { "count": 20, "preference": 0.65 },
        "javascript": { "count": 10, "preference": 0.35 }
      },
      "frameworks": {
        "fastapi": { "count": 30, "preference": 0.90 },
        "vue": { "count": 15, "preference": 0.70 }
      },
      "databases": {
        "postgresql": { "count": 20, "preference": 0.80 }
      }
    },
    "coding_style": {
      "type_annotations": { "preference": 0.90, "evidence": "几乎所有 Python 代码都有类型注解" },
      "functional_style": { "preference": 0.60, "evidence": "经常使用 map/filter/reduce" },
      "detailed_comments": { "preference": 0.75, "evidence": "习惯为复杂逻辑添加注释" }
    },
    "testing": {
      "test_first": { "preference": 0.40, "evidence": "偶尔先写测试" },
      "preferred_framework": "pytest",
      "coverage_focus": { "preference": 0.70, "evidence": "经常要求测试覆盖率" }
    },
    "git": {
      "commit_style": "conventional",
      "commit_language": "english",
      "commit_frequency": "small_steps"
    },
    "interaction": {
      "explanation_level": "detailed",
      "code_examples": { "preference": 0.85, "evidence": "经常要求代码示例" },
      "confirmation_before_action": { "preference": 0.70, "evidence": "重要操作前习惯确认" }
    }
  }
}
```

### 3.4 项目模式

**定义**：不同类型项目的开发流程和习惯

**示例**：
```
API 项目:
  - 通常先设计 API 接口
  - 使用 FastAPI + PostgreSQL
  - 重视测试覆盖率
  - 习惯写 API 文档

前端项目:
  - 先搭建组件结构
  - 使用 Vue + TypeScript
  - 注重 UI/UX
  - 较少写测试

全栈项目:
  - 先设计数据模型
  - 前后端并行开发
  - 使用 monorepo 结构
```

**数据结构**：
```json
{
  "project_patterns": {
    "backend_api": {
      "count": 25,
      "typical_workflow": ["design_api", "implement", "write_tests", "document", "commit"],
      "common_tech": ["python", "fastapi", "postgresql", "pytest"],
      "characteristics": {
        "test_coverage": "high",
        "documentation": "api_docs",
        "commit_frequency": "medium"
      }
    },
    "frontend_spa": {
      "count": 10,
      "typical_workflow": ["design_ui", "implement_components", "style", "test_manually", "commit"],
      "common_tech": ["vue", "typescript", "tailwind"],
      "characteristics": {
        "test_coverage": "low",
        "documentation": "minimal",
        "commit_frequency": "high"
      }
    },
    "fullstack": {
      "count": 5,
      "typical_workflow": ["design_data_model", "implement_api", "implement_ui", "integrate", "test", "commit"],
      "common_tech": ["python", "vue", "postgresql"],
      "characteristics": {
        "test_coverage": "medium",
        "documentation": "readme",
        "commit_frequency": "medium"
      }
    }
  }
}
```

### 3.5 模式提取流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                        模式提取流程                                   │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 1. 会话结束时，收集完整会话数据                                        │
│    - 用户消息、AI 操作、文件变更、命令执行                              │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. 大模型分析会话，生成结构化摘要                                      │
│    - 识别会话主题和目标                                               │
│    - 识别工作流程阶段                                                 │
│    - 识别使用的技术和工具                                             │
│    - 识别用户偏好信号                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. 保存会话记录到本地                                                 │
│    - sessions/2026-01-31/sess_001.json                              │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. 定期聚合分析（或按需触发）                                          │
│    - 从多个会话中提取工作流程模式                                      │
│    - 统计偏好数据                                                     │
│    - 识别项目类型模式                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 5. 更新用户画像                                                       │
│    - patterns/workflow_patterns.json                                │
│    - patterns/preferences.json                                      │
│    - patterns/project_patterns.json                                 │
│    - profile/user_profile.json                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 4. 用户画像

### 4.1 画像结构

```json
{
  "user_profile": {
    "version": "2.0",
    "updated_at": "2026-01-31T12:00:00Z",
    "stats": {
      "total_sessions": 50,
      "total_hours": 120,
      "active_days": 30,
      "first_seen": "2026-01-01",
      "last_seen": "2026-01-31"
    },
    "identity": {
      "role": "backend_developer",
      "experience_level": "senior",
      "primary_languages": ["python", "typescript"],
      "primary_domains": ["api_development", "data_processing"]
    },
    "work_style": {
      "planning_tendency": 0.75,
      "test_driven": 0.40,
      "documentation_focus": 0.65,
      "iteration_speed": "medium",
      "risk_tolerance": "low"
    },
    "interaction_preferences": {
      "explanation_detail": "high",
      "code_example_preference": "high",
      "confirmation_preference": "medium",
      "language": "chinese"
    },
    "time_patterns": {
      "most_active_hours": [10, 11, 14, 15, 16],
      "most_active_days": ["monday", "tuesday", "wednesday"],
      "avg_session_duration_minutes": 35
    }
  }
}
```

### 4.2 画像生成

**大模型分析指令**：

```markdown
## 用户画像生成任务

基于以下会话历史数据，生成/更新用户画像：

### 输入数据
- 最近 30 天的会话记录
- 当前用户画像（如果有）

### 分析维度

1. **身份识别**
   - 用户的主要角色（前端/后端/全栈/DevOps...）
   - 经验水平（初级/中级/高级）
   - 主要使用的语言和技术

2. **工作风格**
   - 是否倾向于先规划再执行
   - 是否习惯测试驱动开发
   - 对文档的重视程度
   - 迭代速度（快速迭代 vs 谨慎开发）

3. **交互偏好**
   - 喜欢详细解释还是简洁回答
   - 是否需要代码示例
   - 重要操作前是否需要确认
   - 使用的语言（中文/英文）

4. **时间模式**
   - 最活跃的时间段
   - 平均会话时长

### 输出格式
生成 JSON 格式的用户画像，包含以上所有维度。
```

## 5. 三大应用场景

### 5.1 预测下一步操作

**基于工作流程模式预测**：

```
当前状态：用户刚完成 "implement" 阶段
历史模式：implement → test (75%), implement → commit (20%)
上下文：项目有测试目录，用户偏好测试驱动

预测：下一步可能是 "编写/运行测试"
置信度：0.80
建议："代码写完了，要运行测试验证一下吗？"
```

### 5.1.1 自动执行功能

**设计目标**：当预测置信度足够高时，自动执行安全的操作，减少用户确认步骤。

**自动执行判断逻辑**：

```
┌─────────────────────────────────────────────────────────────────────┐
│                        自动执行决策流程                               │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 1. 检查自动执行是否启用                                               │
│    - enabled = false → 不自动执行                                    │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. 检查动作是否在禁止列表中                                           │
│    - 在禁止列表 → 永不自动执行                                        │
│    - 禁止列表：delete_file, git_push, git_reset, deploy, rm, drop   │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. 检查动作是否在允许列表中                                           │
│    - 不在允许列表 → 不自动执行                                        │
│    - 允许列表：run_test, run_lint, git_status, git_add              │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. 检查置信度                                                        │
│    - confidence >= 0.95 → 直接执行，无需确认                          │
│    - confidence >= 0.85 → 询问确认后执行                              │
│    - confidence < 0.85  → 仅提供建议                                 │
└─────────────────────────────────────────────────────────────────────┘
```

**配置选项**：

```json
{
  "prediction": {
    "auto_execute": {
      "enabled": true,
      "threshold": 0.85,
      "allowed_actions": ["run_test", "run_lint", "git_status", "git_add"],
      "forbidden_actions": ["delete_file", "git_push", "git_reset", "deploy", "rm", "drop"],
      "require_confirmation_below": 0.95
    }
  }
}
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| enabled | true | 是否启用自动执行 |
| threshold | 0.85 | 最低置信度阈值 |
| allowed_actions | [...] | 允许自动执行的动作 |
| forbidden_actions | [...] | 禁止自动执行的动作 |
| require_confirmation_below | 0.95 | 低于此值需要确认 |

**自动执行示例**：

```
场景 1：高置信度直接执行
─────────────────────────
当前阶段：implement（刚创建了 API 文件）
预测：run_test，置信度 96%
判断：96% >= 95%，且 run_test 在允许列表中
结果：直接执行 pytest
输出："根据你的习惯，我已自动运行测试 ✓"

场景 2：中置信度确认执行
─────────────────────────
当前阶段：implement
预测：run_test，置信度 88%
判断：88% >= 85% 但 < 95%
结果：询问确认
输出："代码写完了，要运行测试验证一下吗？（置信度 88%）"

场景 3：低置信度仅建议
─────────────────────────
当前阶段：implement
预测：commit，置信度 60%
判断：60% < 85%
结果：仅显示建议
输出："你可能想要提交代码"

场景 4：禁止动作不执行
─────────────────────────
当前阶段：test
预测：deploy，置信度 98%
判断：deploy 在禁止列表中
结果：不自动执行
输出："测试通过了，是否需要部署？（需要手动确认）"
```

**返回数据结构**：

```json
{
  "predictions": [
    {
      "next_stage": "test",
      "probability": 0.85,
      "confidence": 0.96,
      "suggestion": "根据你的习惯，接下来应该是运行测试"
    }
  ],
  "auto_execute": {
    "enabled": true,
    "should_auto_execute": true,
    "should_confirm": false,
    "action": "run_test",
    "command": "pytest",
    "reason": "auto_execute_approved: confidence=0.96"
  }
}
```

**预测决策流程**：

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. 识别当前工作流程阶段                                               │
│    - 根据最近的操作判断当前阶段                                        │
│    - 例如：刚创建了多个文件 → "implement" 阶段                         │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. 查询工作流程模式                                                   │
│    - 找到匹配的工作流程模式                                           │
│    - 获取下一阶段的概率分布                                           │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. 结合上下文调整                                                     │
│    - 项目类型（API 项目更可能需要测试）                                │
│    - 用户偏好（测试驱动倾向）                                         │
│    - 当前状态（是否有未提交的更改）                                    │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. 生成预测和建议                                                     │
│    - 计算最终置信度                                                   │
│    - 生成自然语言建议                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 生成用户画像/偏好

**用途**：

| 场景 | 应用 |
|------|------|
| **新会话开始** | 加载用户画像，了解用户背景和偏好 |
| **技术选择** | 根据偏好推荐技术方案 |
| **代码生成** | 按照用户的编码风格生成代码 |
| **交互调整** | 根据偏好调整解释详细程度 |

**示例**：

```
场景：用户说"帮我写一个 API"

无画像时：
  AI: "你想用什么语言和框架？"

有画像时：
  AI: "好的，我用 FastAPI 来实现，这是你常用的框架。
       需要我先写设计文档吗？（根据你的习惯）"
```

### 5.3 优化 AI 的交互方式

**基于用户偏好调整交互**：

| 偏好维度 | 低偏好时 | 高偏好时 |
|----------|----------|----------|
| **解释详细度** | 简洁回答，直接给代码 | 详细解释原理和选择理由 |
| **代码示例** | 文字描述为主 | 附带完整代码示例 |
| **确认偏好** | 直接执行 | 重要操作前先确认 |
| **语言** | 英文 | 中文 |

**交互优化指令**：

```markdown
## 交互风格调整

基于用户画像，调整你的交互方式：

### 用户偏好
- 解释详细度：高（喜欢详细解释）
- 代码示例：高（经常需要代码示例）
- 确认偏好：中（重要操作需要确认）
- 语言：中文

### 调整规则

1. **回答风格**
   - 先解释思路和原因，再给出代码
   - 代码要有详细注释
   - 使用中文回答

2. **操作确认**
   - 删除文件、修改配置等操作前先确认
   - 简单的代码修改可以直接执行

3. **建议方式**
   - 提供多个方案时，解释各自优缺点
   - 给出推荐方案及理由
```

## 6. 数据存储架构

### 6.1 目录结构

```
<project>/.cursor/skills/behavior-prediction-data/
├── sessions/                      # 会话记录
│   ├── 2026-01/                   # 按月份组织
│   │   ├── sess_20260131_001.json
│   │   ├── sess_20260131_002.json
│   │   └── ...
│   └── 2026-02/
│       └── ...
│
├── patterns/                      # 行为模式
│   ├── workflow_patterns.json     # 工作流程模式
│   ├── preferences.json           # 偏好数据
│   └── project_patterns.json      # 项目模式
│
├── profile/                       # 用户画像
│   └── user_profile.json          # 综合用户画像
│
├── index/                         # 索引（加速查询）
│   ├── sessions_index.json        # 会话索引
│   └── tags_index.json            # 标签索引
│
└── config.json                    # 配置文件
```

### 6.2 数据生命周期

```
┌─────────────────────────────────────────────────────────────────────┐
│                        数据生命周期                                   │
└─────────────────────────────────────────────────────────────────────┘

会话记录（sessions/）:
  - 保留期限：90 天（可配置）
  - 过期后：删除原始记录，保留聚合数据

行为模式（patterns/）:
  - 保留期限：永久
  - 更新频率：每次会话结束后增量更新

用户画像（profile/）:
  - 保留期限：永久
  - 更新频率：每周全量更新，或手动触发
```

### 6.3 数据加载策略

| 数据类型 | 大小 | 加载时机 |
|----------|------|----------|
| **用户画像** | ~5KB | 会话开始时 |
| **工作流程模式** | ~10KB | 预测时 |
| **偏好数据** | ~5KB | 需要时按需加载 |
| **会话记录** | 每个 ~5KB | 几乎不加载（只在分析时） |

## 7. 实现方案

### 7.1 核心脚本

| 脚本 | 功能 | 调用时机 |
|------|------|----------|
| `record_session.py` | 记录完整会话 | 会话结束时 |
| `extract_patterns.py` | 提取行为模式 | 会话记录后 |
| `update_profile.py` | 更新用户画像 | 定期/手动 |
| `get_predictions.py` | 获取预测建议 | 需要预测时 |
| `get_profile.py` | 获取用户画像 | 会话开始时 |

### 7.2 会话记录流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                        会话记录流程                                   │
└─────────────────────────────────────────────────────────────────────┘

1. 会话开始
   ↓
   [加载用户画像，了解用户偏好]
   
2. 会话进行中
   ↓
   [正常对话和操作，不做额外记录]
   
3. 检测到会话结束信号
   ↓
   [大模型回顾整个会话，生成结构化摘要]
   
4. 调用 record_session.py
   ↓
   输入：会话摘要 JSON
   输出：保存到 sessions/YYYY-MM/sess_xxx.json
   
5. 调用 extract_patterns.py
   ↓
   输入：新会话记录
   输出：增量更新 patterns/*.json
```

### 7.3 大模型任务

**任务 1：会话摘要生成**

```markdown
## 会话摘要生成任务

回顾本次会话，生成结构化摘要：

### 需要提取的信息

1. **会话主题**：这次会话主要在做什么？
2. **完成的任务**：列出完成的具体任务
3. **使用的技术**：用到了哪些语言、框架、工具
4. **工作流程阶段**：
   - design: 设计、规划、讨论方案
   - implement: 编写代码、创建文件
   - test: 编写测试、运行测试
   - debug: 调试、修复问题
   - refactor: 重构、优化代码
   - document: 编写文档
   - deploy: 部署、发布
   - review: 代码审查
   - commit: 提交代码
5. **用户偏好信号**：观察到的用户偏好（如果有）
6. **标签**：给会话打标签

### 输出格式

```json
{
  "topic": "主题",
  "goals": ["目标1", "目标2"],
  "completed_tasks": ["任务1", "任务2"],
  "technologies_used": ["tech1", "tech2"],
  "workflow_stages": ["implement", "test"],
  "preference_signals": {
    "observed": "观察到的偏好",
    "evidence": "证据"
  },
  "tags": ["#tag1", "#tag2"]
}
```
```

**任务 2：模式提取**

```markdown
## 行为模式提取任务

基于最近的会话记录，提取/更新行为模式：

### 输入
- 最近 N 个会话的摘要
- 当前的模式数据

### 提取内容

1. **工作流程模式**
   - 识别重复出现的工作流程序列
   - 计算各模式的频率和置信度
   - 识别模式适用的上下文

2. **偏好更新**
   - 统计技术栈使用频率
   - 识别编码风格偏好
   - 更新交互偏好

3. **项目模式**
   - 按项目类型分组
   - 识别各类项目的典型流程

### 输出
更新后的模式 JSON
```

**任务 3：预测生成**

```markdown
## 预测生成任务

基于当前状态和历史模式，预测下一步：

### 输入
- 当前会话的操作历史
- 工作流程模式
- 用户偏好
- 项目类型

### 分析步骤

1. 识别当前所处的工作流程阶段
2. 查询匹配的工作流程模式
3. 结合用户偏好和项目类型调整
4. 生成预测和建议

### 输出

```json
{
  "current_stage": "implement",
  "predictions": [
    {
      "next_stage": "test",
      "confidence": 0.75,
      "reason": "根据你的习惯，实现后通常会运行测试"
    }
  ],
  "suggestion": "代码写完了，要运行测试验证一下吗？"
}
```
```

## 8. Hook 设计

### 8.1 会话生命周期 Hook

```
┌─────────────────────────────────────────────────────────────────────┐
│                        会话生命周期                                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 会话开始     │ ──→ │ 会话进行中   │ ──→ │ 会话结束     │
│             │     │             │     │             │
│ [init hook] │     │ [无 hook]   │     │ [finalize   │
│             │     │             │     │  hook]      │
└─────────────┘     └─────────────┘     └─────────────┘
      ↓                                       ↓
 加载用户画像                            记录会话 + 更新模式
 返回预测建议
```

### 8.2 Init Hook

**触发时机**：每次新会话开始时

**功能**：
1. 加载用户画像
2. 返回用户偏好和预测建议

**调用方式**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --init
```

**返回数据**：
```json
{
  "status": "success",
  "user_profile": {
    "role": "backend_developer",
    "primary_languages": ["python"],
    "work_style": {
      "planning_tendency": 0.75,
      "test_driven": 0.40
    },
    "interaction_preferences": {
      "explanation_detail": "high",
      "language": "chinese"
    }
  },
  "suggestions": [
    "根据你的习惯，新功能开发时通常先写设计文档",
    "你常用的技术栈：Python + FastAPI + PostgreSQL"
  ]
}
```

### 8.3 Finalize Hook

**触发时机**：检测到会话结束信号时

**功能**：
1. 接收会话摘要
2. 保存会话记录
3. 增量更新行为模式

**调用方式**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --finalize '{
  "session_summary": {
    "topic": "用户认证功能开发",
    "goals": ["创建认证 API"],
    "completed_tasks": ["创建 auth.py", "实现 JWT 验证"],
    "technologies_used": ["FastAPI", "PyJWT"],
    "workflow_stages": ["implement", "test"],
    "tags": ["#auth", "#api"]
  },
  "operations": {
    "files_created": ["src/api/auth.py"],
    "files_modified": ["src/main.py"],
    "commands": [{"command": "pytest", "type": "run_test"}]
  },
  "conversation": {
    "user_messages": ["帮我创建认证 API", "添加 JWT", "写测试"],
    "message_count": 3
  },
  "time": {
    "start": "2026-01-31T10:00:00Z",
    "end": "2026-01-31T10:45:00Z"
  }
}'
```

**返回数据**：
```json
{
  "status": "success",
  "session_id": "sess_20260131_001",
  "patterns_updated": true,
  "new_insights": [
    "检测到新的工作流程模式：implement → test"
  ]
}
```

### 8.4 Always Applied Rule

```markdown
---
description: 行为预测 V2 - 会话生命周期管理
globs: ["**/*"]
alwaysApply: true
---

# 行为预测规则

## 一、会话开始时

每次新会话开始时（用户发送第一条消息），执行：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --init
```

根据返回的用户画像调整交互方式。

## 二、会话结束时

当检测到以下信号时，执行会话结束处理：

### 结束信号
- 中文："谢谢"、"好的"、"结束"、"拜拜"、"再见"
- 英文："thanks"、"done"、"bye"、"that's all"

### 执行步骤

1. **回顾会话**：回顾本次会话的所有对话和操作
2. **生成摘要**：生成结构化的会话摘要
3. **调用 Hook**：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --finalize '{
  "session_summary": {...},
  "operations": {...},
  "conversation": {...},
  "time": {...}
}'
```

## 三、注意事项

- 会话开始时的 init 调用是可选的（如果失败不影响正常对话）
- 会话结束时的 finalize 调用尽量执行（但不强制）
- 所有数据存储在本地，用户完全控制
```

## 9. 与 V1 的兼容性

### 9.1 迁移策略

```
V1 数据结构:
  actions/YYYY-MM-DD.json  (每日动作记录)
  patterns/transition_matrix.json  (转移矩阵)

V2 数据结构:
  sessions/YYYY-MM/sess_xxx.json  (会话记录)
  patterns/workflow_patterns.json  (工作流程模式)
  patterns/preferences.json  (偏好数据)
  profile/user_profile.json  (用户画像)
```

**迁移方案**：

1. **保留 V1 数据**：V1 的动作记录可以作为历史参考
2. **不自动迁移**：V2 从零开始积累，不依赖 V1 数据
3. **可选导入**：提供脚本将 V1 数据转换为 V2 格式（可选）

### 9.2 功能对比

| 功能 | V1 | V2 |
|------|----|----|
| 动作记录 | 实时记录每个动作 | 会话结束时记录摘要 |
| 模式识别 | 动作转移概率 | 工作流程 + 偏好 + 项目模式 |
| 预测 | 基于转移概率 | 基于工作流程模式 + 上下文 |
| 用户画像 | 无 | 完整用户画像 |
| 交互优化 | 无 | 根据偏好调整交互 |

## 10. 实现计划

### 10.1 阶段划分

**阶段 1：基础框架**
- 设计数据结构
- 实现 hook.py（init + finalize）
- 实现 record_session.py
- 创建 Always Applied Rule

**阶段 2：模式提取**
- 实现 extract_patterns.py
- 工作流程模式提取
- 偏好数据统计

**阶段 3：用户画像**
- 实现 update_profile.py
- 用户画像生成
- 画像应用（交互优化）

**阶段 4：预测优化**
- 实现 get_predictions.py
- 基于工作流程的预测
- 预测建议生成

### 10.2 文件清单

```
skills/behavior-prediction/
├── SKILL.md                    # Skill 入口文档
├── default_config.json         # 默认配置
├── rules/
│   └── behavior-prediction.mdc # Always Applied Rule
└── scripts/
    ├── hook.py                 # 统一入口（init/finalize）
    ├── record_session.py       # 记录会话
    ├── extract_patterns.py     # 提取模式
    ├── update_profile.py       # 更新用户画像
    ├── get_predictions.py      # 获取预测
    ├── get_profile.py          # 获取用户画像
    └── utils.py                # 工具函数
```

## 11. 总结

### 11.1 V2 的核心改进

| 维度 | V1 | V2 |
|------|----|----|
| **记录粒度** | 单个动作 | 完整会话 |
| **理解深度** | 动作序列 | 用户意图和习惯 |
| **模式类型** | 转移概率 | 工作流程 + 偏好 + 项目 |
| **应用范围** | 预测下一步 | 预测 + 画像 + 交互优化 + 自动执行 |
| **数据价值** | 统计数据 | 用户洞察 |
| **执行方式** | 仅建议 | 高置信度可自动执行 |

### 11.2 核心价值

1. **更懂用户**：从"记录动作"到"理解用户"
2. **更智能的预测**：基于工作流程和上下文，而非简单概率
3. **个性化交互**：根据用户偏好调整 AI 的交互方式
4. **持续学习**：随着使用积累，越来越了解用户
5. **智能自动化**：高置信度时自动执行安全操作，减少交互成本

### 11.3 设计原则

1. **会话级记录**：完整上下文，高质量摘要
2. **大模型驱动**：复杂分析交给大模型
3. **本地存储**：用户完全控制数据
4. **渐进式学习**：从少量数据开始，逐步完善
5. **安全优先**：危险操作永不自动执行，用户始终有最终控制权

---

*文档版本: 2.0*  
*创建日期: 2026-01-31*
