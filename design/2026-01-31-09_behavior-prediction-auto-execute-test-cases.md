# Behavior Prediction Skill V2 - 完整测试案例

## 1. 概述

本文档描述 Behavior Prediction Skill V2 的完整测试案例，包括：
- 核心功能测试（hook.py、record_session.py、extract_patterns.py、user_profile.py、get_predictions.py）
- 工具函数测试（utils.py）
- 自动执行功能测试
- 集成测试
- Cursor 对话交互测试示例

## 2. 测试环境准备

### 2.1 配置文件

确保 `default_config.json` 包含完整配置：

```json
{
  "version": "2.0",
  "enabled": true,
  "recording": {
    "enabled": true,
    "retention_days": 90
  },
  "patterns": {
    "extraction_enabled": true,
    "min_sessions_for_pattern": 3
  },
  "profile": {
    "auto_update": true,
    "update_interval_sessions": 10
  },
  "prediction": {
    "enabled": true,
    "suggest_threshold": 0.5,
    "max_suggestions": 3,
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

### 2.2 测试数据准备

为了测试功能，需要先建立足够的历史数据：

```bash
# 模拟多次 implement → test 的转移
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --finalize '{
  "session_summary": {
    "topic": "测试数据准备",
    "workflow_stages": ["implement", "test"]
  },
  "operations": {"files": {"created": ["test.py"], "modified": [], "deleted": []}, "commands": []},
  "conversation": {"user_messages": [], "message_count": 1},
  "time": {"start": "2026-01-31T10:00:00Z", "end": "2026-01-31T10:30:00Z"}
}'
```

## 3. Hook 功能测试案例

### 3.1 初始化测试（--init）

#### 测试案例 1：新用户初始化

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --init
```

**预期结果**：
```json
{
  "status": "success",
  "user_profile": {
    "stats": {
      "total_sessions": 0,
      "active_days": 0
    }
  },
  "behavior_patterns": {
    "common_sequences": [],
    "top_transitions": []
  },
  "ai_summary": {
    "summary": {
      "description": "新用户，暂无历史数据"
    }
  },
  "suggestions": []
}
```

#### 测试案例 2：有历史数据的用户初始化

**前置条件**：已有多次会话记录

**预期结果**：
- `user_profile.stats.total_sessions` > 0
- `behavior_patterns.common_sequences` 非空
- `ai_summary.predictions.rules` 包含预测规则
- `suggestions` 包含基于历史的建议

---

### 3.2 会话结束测试（--finalize）

#### 测试案例 3：正常会话结束

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --finalize '{
  "session_summary": {
    "topic": "API 开发",
    "goals": ["实现用户接口"],
    "completed_tasks": ["创建 user.py"],
    "technologies_used": ["Python", "FastAPI"],
    "workflow_stages": ["design", "implement", "test"],
    "tags": ["#api", "#backend"]
  },
  "operations": {
    "files": {"created": ["user.py"], "modified": [], "deleted": []},
    "commands": ["pytest"]
  },
  "conversation": {
    "user_messages": ["帮我创建用户 API"],
    "message_count": 5
  },
  "time": {
    "start": "2026-01-31T10:00:00Z",
    "end": "2026-01-31T10:30:00Z"
  }
}'
```

**预期结果**：
```json
{
  "status": "success",
  "session_id": "sess_20260131_001",
  "patterns_updated": true,
  "message": "会话 sess_20260131_001 已记录"
}
```

#### 测试案例 4：空会话处理

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --finalize '{
  "session_summary": {},
  "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
  "conversation": {"user_messages": [], "message_count": 0},
  "time": {}
}'
```

**预期结果**：
- `status` 为 `success`
- 空会话也能正常处理

---

## 4. 会话记录测试案例

### 4.1 record_session.py 测试

#### 测试案例 5：会话 ID 生成

**预期结果**：
- 格式为 `sess_YYYYMMDD_NNN`
- 同一天的会话序号递增

#### 测试案例 6：会话文件创建

**预期结果**：
- 文件保存在 `sessions/YYYY-MM/` 目录
- 包含完整的会话数据

#### 测试案例 7：会话索引更新

**预期结果**：
- `index/sessions_index.json` 被更新
- 索引包含会话摘要信息

---

## 5. 模式提取测试案例

### 5.1 extract_patterns.py 测试

#### 测试案例 8：工作流程模式提取

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/extract_patterns.py '{
  "session_summary": {
    "workflow_stages": ["design", "implement", "test", "commit"]
  }
}'
```

**预期结果**：
- `workflow_patterns.json` 被更新
- `stage_transitions` 包含 design→implement, implement→test, test→commit
- 转移概率被正确计算

#### 测试案例 9：偏好数据提取

**预期结果**：
- `preferences.json` 被更新
- 技术栈被正确分类（languages/frameworks/tools）
- 工作流程阶段频率被统计

#### 测试案例 10：项目模式推断

**操作**：
```python
from extract_patterns import infer_project_type

# 测试后端项目识别
result = infer_project_type(["#api", "#backend"], ["fastapi", "python"])
assert result == "backend_api"

# 测试前端项目识别
result = infer_project_type(["#frontend"], ["vue", "typescript"])
assert result == "frontend"
```

---

## 6. 用户画像测试案例

### 6.1 user_profile.py 测试

#### 测试案例 11：默认画像生成

**操作**：
```python
from user_profile import get_default_profile

profile = get_default_profile()
```

**预期结果**：
- `version` 为 `2.0`
- `stats.total_sessions` 为 0
- `preferences` 包含空列表

#### 测试案例 12：画像更新

**前置条件**：已有多次会话记录

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/user_profile.py '{"action": "update"}'
```

**预期结果**：
- 统计数据被正确计算
- 工作风格被分析
- 偏好被提取

#### 测试案例 13：AI 摘要生成

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/user_profile.py '{"action": "summary"}'
```

**预期结果**：
- 返回结构化的 AI 可用摘要
- 包含预测规则
- 包含行为模式描述

---

## 7. 预测功能测试案例

### 7.1 get_predictions.py 测试

#### 测试案例 14：基于当前阶段的预测

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/get_predictions.py '{"current_stage": "implement"}'
```

**预期结果**：
- 返回下一阶段的预测列表
- 包含概率和置信度
- 包含自然语言建议

#### 测试案例 15：无当前阶段的通用建议

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/get_predictions.py '{}'
```

**预期结果**：
- 返回通用建议列表
- `predictions` 为空
- `suggestions` 非空

---

## 8. 自动执行功能测试案例

### 8.1 配置加载测试

#### 测试案例 16：自动执行配置正确加载

**操作**：
```python
from utils import load_config
config = load_config()
auto_exec = config.get("prediction", {}).get("auto_execute", {})
```

**预期结果**：
- `enabled` 为 `True`
- `threshold` 为 `0.85`
- `allowed_actions` 包含 `["run_test", "run_lint", "git_status", "git_add"]`
- `forbidden_actions` 包含 `["delete_file", "git_push", "git_reset", "deploy", "rm", "drop"]`
- `require_confirmation_below` 为 `0.95`

---

### 8.2 自动执行判断测试

#### 测试案例 17：高置信度直接执行

**前置条件**：
- 历史数据中 `implement → test` 的置信度 >= 95%

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/get_predictions.py '{"current_stage": "implement"}'
```

**预期结果**：
```json
{
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

#### 测试案例 18：中置信度需要确认

**前置条件**：
- 历史数据中 `implement → test` 的置信度在 85%-95% 之间

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/get_predictions.py '{"current_stage": "implement"}'
```

**预期结果**：
```json
{
  "auto_execute": {
    "enabled": true,
    "should_auto_execute": false,
    "should_confirm": true,
    "action": "run_test",
    "command": "pytest",
    "reason": "confidence_requires_confirmation: 0.88 < 0.95"
  }
}
```

#### 测试案例 19：低置信度不自动执行

**前置条件**：
- 历史数据中 `implement → commit` 的置信度 < 85%

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/get_predictions.py '{"current_stage": "implement"}'
```

**预期结果**：
- `should_auto_execute` 为 `false`
- `should_confirm` 为 `false`
- `reason` 包含 `"confidence_below_threshold"`

---

### 8.3 动作过滤测试

#### 测试案例 20：允许列表中的动作

**操作**：
```python
from get_predictions import evaluate_auto_execute

config = {
    "enabled": True,
    "threshold": 0.85,
    "allowed_actions": ["run_test"],
    "forbidden_actions": [],
    "require_confirmation_below": 0.95
}

prediction = {
    "next_stage": "test",
    "probability": 0.90,
    "confidence": 0.96
}

result = evaluate_auto_execute(prediction, config)
```

**预期结果**：
- `should_auto_execute` 为 `true`
- `action` 为 `"run_test"`

#### 测试案例 21：不在允许列表中的动作

**操作**：
```python
prediction = {
    "next_stage": "deploy",
    "probability": 0.95,
    "confidence": 0.98
}

result = evaluate_auto_execute(prediction, config)
```

**预期结果**：
- `should_auto_execute` 为 `false`
- `reason` 包含 `"action_not_in_allowed_list"`

#### 测试案例 22：禁止列表中的动作

**操作**：
```python
config = {
    "enabled": True,
    "threshold": 0.85,
    "allowed_actions": ["run_test", "delete_file"],
    "forbidden_actions": ["delete_file"],
    "require_confirmation_below": 0.95
}

prediction = {
    "next_stage": "delete_file",
    "probability": 0.99,
    "confidence": 0.99
}

result = evaluate_auto_execute(prediction, config)
```

**预期结果**：
- `should_auto_execute` 为 `false`
- `reason` 包含 `"action_forbidden"`
- 即使置信度 99%，禁止列表中的动作也不会自动执行

---

### 8.4 命令生成测试

#### 测试案例 23：基础命令生成

**操作**：
```python
from get_predictions import generate_auto_command

# 测试各种动作的命令生成
actions = ["run_test", "run_lint", "git_status", "git_add"]
for action in actions:
    cmd = generate_auto_command(action)
    print(f"{action}: {cmd}")
```

**预期结果**：
| 动作 | 命令 |
|------|------|
| run_test | pytest |
| run_lint | ruff check . |
| git_status | git status |
| git_add | git add -A |

#### 测试案例 24：带上下文的命令生成

**操作**：
```python
context = {"test_file": "tests/test_auth.py"}
cmd = generate_auto_command("run_test", context)
print(cmd)
```

**预期结果**：
- 命令为 `"pytest tests/test_auth.py"`

#### 测试案例 25：未知动作的命令生成

**操作**：
```python
cmd = generate_auto_command("unknown_action")
print(cmd)
```

**预期结果**：
- 返回 `None`

---

### 8.5 禁用测试

#### 测试案例 26：自动执行功能禁用

**操作**：
```python
config = {
    "enabled": False,
    "threshold": 0.85,
    "allowed_actions": ["run_test"],
    "forbidden_actions": [],
    "require_confirmation_below": 0.95
}

prediction = {
    "next_stage": "test",
    "probability": 0.99,
    "confidence": 0.99
}

result = evaluate_auto_execute(prediction, config)
```

**预期结果**：
- `should_auto_execute` 为 `false`
- `reason` 为 `"auto_execute_disabled"`

---

### 8.6 边界条件测试

#### 测试案例 27：置信度恰好等于阈值

**操作**：
```python
config = {
    "enabled": True,
    "threshold": 0.85,
    "allowed_actions": ["run_test"],
    "forbidden_actions": [],
    "require_confirmation_below": 0.95
}

# 置信度恰好等于 0.85
prediction = {"next_stage": "test", "probability": 0.85, "confidence": 0.85}
result = evaluate_auto_execute(prediction, config)
```

**预期结果**：
- `should_auto_execute` 为 `false`
- `should_confirm` 为 `true`
- 置信度恰好等于阈值时，需要确认

#### 测试案例 28：置信度恰好等于确认阈值

**操作**：
```python
# 置信度恰好等于 0.95
prediction = {"next_stage": "test", "probability": 0.95, "confidence": 0.95}
result = evaluate_auto_execute(prediction, config)
```

**预期结果**：
- `should_auto_execute` 为 `true`
- `should_confirm` 为 `false`
- 置信度恰好等于确认阈值时，直接执行

#### 测试案例 29：空配置处理

**操作**：
```python
result = evaluate_auto_execute(prediction, {})
```

**预期结果**：
- `should_auto_execute` 为 `false`
- `reason` 为 `"auto_execute_disabled"`

---

## 9. 集成测试案例

### 9.1 完整工作流测试

#### 测试案例 30：完整会话生命周期

**操作**：
```bash
# 步骤 1：初始化会话
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --init

# 步骤 2：执行工作（AI 助手执行各种操作）

# 步骤 3：结束会话
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --finalize '{
  "session_summary": {
    "topic": "用户管理功能开发",
    "workflow_stages": ["design", "implement", "test"]
  },
  "operations": {"files": {"created": ["user.py"], "modified": [], "deleted": []}, "commands": ["pytest"]},
  "conversation": {"user_messages": [], "message_count": 5},
  "time": {"start": "2026-01-31T10:00:00Z", "end": "2026-01-31T10:30:00Z"}
}'
```

**预期结果**：
- 初始化返回用户画像和行为模式
- 会话被正确记录
- 模式被更新

#### 测试案例 31：模式学习和预测

**操作**：
```bash
# 记录多次相同的工作流程
for i in {1..5}; do
  python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --finalize '{
    "session_summary": {"topic": "测试'$i'", "workflow_stages": ["implement", "test"]},
    "operations": {"files": {"created": [], "modified": [], "deleted": []}, "commands": []},
    "conversation": {"user_messages": [], "message_count": 1},
    "time": {"start": "2026-01-31T10:00:00Z", "end": "2026-01-31T10:30:00Z"}
  }'
done

# 获取预测
python3 ~/.cursor/skills/behavior-prediction/scripts/get_predictions.py '{"current_stage": "implement"}'
```

**预期结果**：
- 预测结果中 `test` 的概率应该很高
- 建议文本包含 "测试" 相关内容

#### 测试案例 32：模拟禁止动作场景

**操作**：
1. 记录多次 `test → deploy` 的会话
2. 调用预测
3. 验证不会自动执行

**预期结果**：
- 即使 `deploy` 的置信度很高
- `auto_execute.should_auto_execute` 为 `false`
- `reason` 包含 `"action_forbidden"` 或 `"action_not_in_allowed_list"`

---

## 10. 安全性测试

### 10.1 危险操作防护

#### 测试案例 33：删除操作不自动执行

**操作**：
```python
prediction = {"next_stage": "delete_file", "probability": 1.0, "confidence": 1.0}
config = {
    "enabled": True,
    "threshold": 0.85,
    "allowed_actions": ["run_test", "delete_file"],  # 即使在允许列表
    "forbidden_actions": ["delete_file"],  # 但也在禁止列表
    "require_confirmation_below": 0.95
}
result = evaluate_auto_execute(prediction, config)
```

**预期结果**：
- `should_auto_execute` 为 `false`
- 禁止列表优先级高于允许列表

#### 测试案例 34：Git push 不自动执行

**操作**：
```python
prediction = {"next_stage": "git_push", "probability": 1.0, "confidence": 1.0}
result = evaluate_auto_execute(prediction, default_config)
```

**预期结果**：
- `should_auto_execute` 为 `false`
- `git_push` 在默认禁止列表中

---

## 11. 性能测试

#### 测试案例 35：评估函数性能

**操作**：
```python
import time

config = {
    "enabled": True,
    "threshold": 0.85,
    "allowed_actions": ["run_test"],
    "forbidden_actions": [],
    "require_confirmation_below": 0.95
}
prediction = {"next_stage": "test", "probability": 0.95, "confidence": 0.96}

start = time.time()
for _ in range(1000):
    evaluate_auto_execute(prediction, config)
elapsed = time.time() - start
print(f"1000 次评估耗时: {elapsed:.3f}s")
```

**预期结果**：
- 1000 次评估耗时 < 100ms
- 单次评估耗时 < 0.1ms

---

## 12. Cursor 对话交互测试示例

### 12.1 安装和初始化

#### 示例 1：安装 Behavior Prediction Skill

**用户输入**：
```
帮我从 https://github.com/shetengteng/skillix-hub 安装 behavior-prediction skill
```

**AI 响应**：
```
✅ Behavior Prediction Skill V2 安装成功！

这个 Skill 会：
• 记录你的会话内容（会话结束时）
• 学习你的工作流程和偏好
• 在适当时机提供智能建议

无需额外配置，开始使用即可！

其他命令：
• 查看我的行为模式
• 更新用户画像
• 查看行为统计
```

---

### 12.2 会话过程中的预测

#### 示例 2：完成代码后的预测

**场景**：用户刚完成了一个 Python 文件的编写

**AI 主动建议**：
```
✨ 基于你的习惯，你可能想要：
→ 运行测试 (置信度: 85%)

要执行 pytest 吗？
```

**用户输入**：
```
好的
```

**AI 响应**：
```
正在运行测试...

$ pytest tests/
========================= test session starts =========================
collected 5 items

tests/test_user.py .....                                          [100%]

========================= 5 passed in 0.32s =========================

✅ 所有测试通过！
```

---

### 12.3 查看行为模式

#### 示例 3：查看我的行为模式

**用户输入**：
```
查看我的行为模式
```

**AI 响应**：
```
📊 你的行为模式分析

**基本统计：**
- 活跃天数: 15 天
- 总会话数: 42 次
- 平均会话时长: 25 分钟

**常见工作流程：**
1. design → implement (78%)
2. implement → test (85%)
3. test → commit (65%)

**技术偏好：**
- 语言: Python, TypeScript
- 框架: FastAPI, Vue
- 工具: pytest, ruff

**工作风格：**
- 测试驱动 (35%)
- 注重规划 (25%)
- 持续重构 (15%)
```

---

### 12.4 预测下一步

#### 示例 4：手动请求预测

**用户输入**：
```
预测下一步
```

**AI 响应**：
```
基于当前上下文预测：

你刚刚完成了 **实现** 阶段。

**最可能的下一步：**
✅ 运行测试 (置信度: 85%)

**其他可能：**
- 继续编辑 (10%)
- 提交代码 (3%)
- 查看文档 (2%)

需要我帮你运行测试吗？
```

---

### 12.5 会话结束

#### 示例 5：会话结束时的自动记录

**用户输入**：
```
谢谢，今天就到这里
```

**AI 响应**：
```
好的！已记录本次会话。

📝 会话摘要：
- 主题: API 用户模块开发
- 工作流程: design → implement → test → commit
- 技术: Python, FastAPI, pytest

基于你的习惯，下次你可能想要：
→ 继续完善文档 (60%)

再见！👋
```

---

## 13. 自动化测试

### 13.1 运行所有测试

```bash
python3 ~/.cursor/skills/behavior-prediction/tests/run_all_tests.py
```

### 13.2 运行单个测试文件

```bash
# 测试 hook 功能
python3 ~/.cursor/skills/behavior-prediction/tests/test_hook.py

# 测试自动执行功能
python3 ~/.cursor/skills/behavior-prediction/tests/test_auto_execute.py

# 测试工具函数
python3 ~/.cursor/skills/behavior-prediction/tests/test_utils.py
```

### 13.3 测试覆盖范围

| 测试文件 | 测试内容 | 测试数量 |
|----------|----------|----------|
| test_hook.py | Hook 初始化和结束 | 10 |
| test_auto_execute.py | 自动执行评估 | 20 |
| test_utils.py | 工具函数 | 18 |
| **总计** | | **48** |

---

## 14. 测试数据清理

```bash
# 清理测试数据
rm -rf ~/.cursor/skills/behavior-prediction-data/sessions/
rm -rf ~/.cursor/skills/behavior-prediction-data/patterns/
rm -rf ~/.cursor/skills/behavior-prediction-data/profile/
rm -rf ~/.cursor/skills/behavior-prediction-data/index/
```

---

## 15. 工具函数测试案例

### 15.1 utils.py 测试

#### 测试案例 36：数据目录创建

```python
from utils import ensure_data_dirs, DATA_DIR

ensure_data_dirs()
assert (DATA_DIR / "sessions").exists()
assert (DATA_DIR / "patterns").exists()
assert (DATA_DIR / "profile").exists()
assert (DATA_DIR / "index").exists()
```

#### 测试案例 37：JSON 文件操作

```python
from utils import load_json, save_json
from pathlib import Path

# 测试保存
test_file = Path("/tmp/test.json")
save_json(test_file, {"key": "value"})
assert test_file.exists()

# 测试加载
data = load_json(test_file)
assert data == {"key": "value"}

# 测试默认值
data = load_json(Path("/tmp/not_exists.json"), {"default": True})
assert data == {"default": True}
```

#### 测试案例 38：日期时间函数

```python
from utils import get_today, get_month, get_timestamp
from datetime import datetime

today = get_today()
assert today == datetime.now().strftime("%Y-%m-%d")

month = get_month()
assert month == datetime.now().strftime("%Y-%m")

timestamp = get_timestamp()
assert "T" in timestamp  # ISO8601 格式
```

#### 测试案例 39：项目信息检测

```python
from utils import detect_project_info

info = detect_project_info()
assert "path" in info
assert "name" in info
assert "type" in info
assert "tech_stack" in info
```

#### 测试案例 40：支持的 AI 助手目录

```python
from utils import SUPPORTED_AI_DIRS

assert ".cursor" in SUPPORTED_AI_DIRS
assert ".claude" in SUPPORTED_AI_DIRS
assert ".ai" in SUPPORTED_AI_DIRS
assert ".copilot" in SUPPORTED_AI_DIRS
assert ".codeium" in SUPPORTED_AI_DIRS
```

---

*文档版本: 2.0*  
*创建日期: 2026-01-31*
*更新日期: 2026-01-31*
