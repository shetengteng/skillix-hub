# Behavior Prediction Skill 测试案例文档

## 1. 概述

本文档描述 Behavior Prediction Skill 的测试案例，用于验证其核心功能是否正常工作。

## 2. 测试环境准备

### 2.1 安装位置

Behavior Prediction Skill 可以安装到项目级或全局目录：

**项目级**：
```
<project>/.cursor/skills/behavior-prediction/
├── SKILL.md
├── default_config.json
├── rules/
│   └── behavior-recording.mdc
└── scripts/
    ├── record_action.py
    ├── get_statistics.py
    ├── finalize_session.py
    ├── check_last_session.py
    └── utils.py
```

**全局级**：
```
~/.cursor/skills/behavior-prediction/
└── (同上)
```

### 2.2 数据存储位置

- **项目级数据**：`<project>/.cursor/skills/behavior-prediction-data/`
- **全局级数据**：`~/.cursor/skills/behavior-prediction-data/`

### 2.3 兼容性

支持多种 AI 助手目录：`.cursor`, `.claude`, `.ai`, `.copilot`, `.codeium`

## 3. 功能测试案例

### 3.1 动作记录测试

#### 测试案例 1：基本记录

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{
  "type": "create_file",
  "tool": "Write",
  "details": {"file_path": "src/test.py"}
}'
```

**预期结果**：
- 返回成功消息，包含 `action_id`
- 在 `behavior-prediction-data/actions/` 目录下创建当日 JSON 文件
- `total_actions_today` 递增

#### 测试案例 2：连续记录更新转移矩阵

**操作**：连续执行两次记录命令（不同类型）
```bash
# 第一次
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{"type": "create_file", "tool": "Write", "details": {}}'

# 等待 1 秒后
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{"type": "edit_file", "tool": "StrReplace", "details": {}}'
```

**预期结果**：
- 两次都返回成功
- 转移矩阵中 `create_file → edit_file` 的计数增加
- 概率重新计算

#### 测试案例 3：重复动作去重

**操作**：5 秒内连续执行两次相同的记录命令
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{"type": "create_file", "tool": "Write", "details": {}}'
# 立即再次执行
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{"type": "create_file", "tool": "Write", "details": {}}'
```

**预期结果**：
- 第一次返回 `"status": "success"`
- 第二次返回 `"status": "skipped", "reason": "duplicate within 5s"`

#### 测试案例 4：新类型注册

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{
  "type": "train_model",
  "tool": "Shell",
  "details": {"command": "python train.py"},
  "classification": {
    "confidence": 0.85,
    "is_new_type": true,
    "description": "训练机器学习模型"
  }
}'
```

**预期结果**：
- 返回成功
- `types_registry.json` 中添加新类型 `train_model`
- 新类型的 `source` 为 `"auto_generated"`

#### 测试案例 5：缺少动作类型

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{"tool": "Write", "details": {}}'
```

**预期结果**：
- 返回 `"status": "error"`
- 错误消息包含 "Missing" 或 "invalid"

---

### 3.2 统计数据测试

#### 测试案例 6：获取特定动作统计

**前置条件**：已记录多个动作，包括 `edit_file → run_test` 的转移

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/get_statistics.py '{"current_action": "edit_file"}'
```

**预期结果**：
- `status` 为 `"success"`
- `transitions` 包含 `run_test` 及其概率
- `recent_sequence` 包含最近的动作序列

#### 测试案例 7：获取所有统计概览

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/get_statistics.py
```

**预期结果**：
- 返回 `total_transitions`、`action_types_count`、`today_actions`
- 包含 `top_actions` 和 `top_transitions` 列表

#### 测试案例 8：空数据统计

**前置条件**：清空所有数据

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/get_statistics.py '{"current_action": "unknown_action"}'
```

**预期结果**：
- `status` 为 `"success"`
- `transitions` 为空对象 `{}`
- `total_samples` 为 0

#### 测试案例 9：Top 预测

**前置条件**：记录足够多的 `write_code → run_test` 转移（至少 3 次）

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/get_statistics.py '{"current_action": "write_code"}'
```

**预期结果**：
- 包含 `top_prediction` 字段
- `top_prediction.action` 为 `"run_test"`
- `top_prediction.probability` 接近 1.0

---

### 3.3 会话结束处理测试

#### 测试案例 10：基本会话结束

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/finalize_session.py '{
  "actions_summary": [
    {"type": "create_file", "tool": "Write"},
    {"type": "edit_file", "tool": "StrReplace"},
    {"type": "run_test", "tool": "Shell"}
  ],
  "start_time": "2026-01-31T10:00:00Z",
  "end_time": "2026-01-31T11:00:00Z"
}'
```

**预期结果**：
- `status` 为 `"success"`
- `actions_count` 为 3
- 会话统计记录到 `stats/sessions.json`

#### 测试案例 11：空会话结束

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/finalize_session.py '{"actions_summary": []}'
```

**预期结果**：
- `status` 为 `"success"`
- `actions_count` 为 0
- 不创建会话统计记录

#### 测试案例 12：会话统计限制

**前置条件**：执行超过 100 次会话结束处理

**预期结果**：
- `sessions.json` 中的 `sessions` 数组最多保留 100 条
- `total_sessions` 正确累计

---

### 3.4 会话检查测试

#### 测试案例 13：首次检查

**前置条件**：清空 `stats/sessions.json` 中的 `last_check`

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/check_last_session.py
```

**预期结果**：
- `status` 为 `"success"`
- `action` 为 `"none"` 或 `"recalculated"`
- `last_check` 更新为今天日期

#### 测试案例 14：今日已检查

**前置条件**：已执行过一次检查

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/check_last_session.py
```

**预期结果**：
- `status` 为 `"success"`
- `action` 为 `"none"`
- `reason` 包含 "Already checked"

#### 测试案例 15：获取数据摘要

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/check_last_session.py '{"action": "summary"}'
```

**预期结果**：
- 返回 `log_files_count`、`total_actions`、`total_transitions`
- 包含 `data_dir` 路径

#### 测试案例 16：手动重新计算

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/check_last_session.py '{"action": "recalculate"}'
```

**预期结果**：
- `status` 为 `"success"`
- `action` 为 `"recalculated"`
- 转移矩阵根据所有日志重新计算

---

### 3.5 配置测试

#### 测试案例 17：默认配置加载

**前置条件**：删除用户配置文件

**操作**：调用任意脚本

**预期结果**：
- 使用 `default_config.json` 中的配置
- `enabled` 为 `true`
- `prediction.suggest_threshold` 为 `0.5`

#### 测试案例 18：用户配置覆盖

**前置条件**：创建用户配置文件
```json
{
  "prediction": {
    "suggest_threshold": 0.7
  }
}
```

**预期结果**：
- `suggest_threshold` 为 `0.7`（用户配置）
- 其他配置使用默认值

---

### 3.6 兼容性测试

#### 测试案例 19：自动检测 AI 助手目录

**前置条件**：项目中存在 `.claude` 目录

**操作**：
```bash
python3 skills/behavior-prediction/scripts/utils.py
```

**预期结果**：
- 输出的数据目录包含 `.claude`
- 不使用 `.cursor`（如果 `.cursor` 不存在）

#### 测试案例 20：全局数据目录

**操作**：
```python
from utils import get_data_dir
print(get_data_dir("global"))
```

**预期结果**：
- 返回用户主目录下的路径
- 路径包含 `behavior-prediction-data`

---

## 4. 集成测试案例

### 4.1 完整工作流测试

#### 测试案例 21：模拟开发会话

**操作**：
1. 记录 `create_file`
2. 记录 `edit_file`
3. 记录 `run_test`
4. 获取 `edit_file` 的统计
5. 执行会话结束处理

**预期结果**：
- 所有操作成功
- 转移矩阵正确更新
- 统计数据正确返回
- 会话统计正确记录

#### 测试案例 22：跨天数据处理

**前置条件**：
- 昨天有动作记录
- 今天首次使用

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/check_last_session.py
```

**预期结果**：
- 自动检测并处理昨天的数据
- 转移矩阵包含昨天的转移记录

---

## 5. 性能测试

### 5.1 大数据量测试

#### 测试案例 23：大量动作记录

**操作**：记录 1000 个动作

**预期结果**：
- 每次记录耗时 < 100ms
- 日志文件大小合理（< 1MB）

#### 测试案例 24：大量转移统计

**前置条件**：转移矩阵包含 100+ 种动作类型

**操作**：获取统计数据

**预期结果**：
- 响应时间 < 500ms
- 正确返回 Top 预测

---

## 6. 错误处理测试

### 6.1 异常输入测试

#### 测试案例 25：无效 JSON

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py 'invalid json'
```

**预期结果**：
- 返回 `"status": "error"`
- 错误消息包含 "Invalid JSON"

#### 测试案例 26：缺少必需参数

**操作**：
```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/record_action.py '{}'
```

**预期结果**：
- 返回 `"status": "error"`
- 错误消息说明缺少的参数

---

## 7. 自动化测试

### 7.1 运行单元测试

```bash
python3 skills/behavior-prediction/tests/run_all_tests.py
```

**预期结果**：
- 所有测试通过
- 输出 "OK"

### 7.2 测试覆盖范围

| 模块 | 测试文件 | 测试数量 |
|------|----------|----------|
| utils.py | test_utils.py | 18 |
| record_action.py | test_record_action.py | 9 |
| get_statistics.py | test_get_statistics.py | 9 |
| finalize_session.py | test_finalize_session.py | 6 |
| check_last_session.py | test_check_last_session.py | 6 |
| **总计** | | **48** |

---

## 8. 测试数据清理

### 8.1 清理测试数据

```bash
# 清理项目级数据
rm -rf .cursor/skills/behavior-prediction-data/

# 清理全局数据
rm -rf ~/.cursor/skills/behavior-prediction-data/
```

### 8.2 重置转移矩阵

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/check_last_session.py '{"action": "recalculate"}'
```

---

*文档版本: 1.0*  
*创建日期: 2026-01-31*
