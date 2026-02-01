# 行为预测 Cursor 对话测试方案

## 测试准备

### 1. 确保规则已启用

```
启用行为预测规则
```

### 2. 验证规则文件存在

```bash
cat ~/.cursor/rules/behavior-prediction.mdc
```

---

## 测试场景

### 场景 1：会话开始初始化

**目的**：验证会话开始时加载用户画像和行为模式

**测试对话**：

```
用户: 开始新的会话
期望: AI 自动调用 hook.py --init，返回用户画像和行为模式
```

**验证命令**：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --init
```

**期望输出**：

```json
{
  "status": "success",
  "user_profile": {
    "stats": {
      "total_sessions": 4,
      "active_days": 1
    }
  },
  "behavior_patterns": {
    "common_sequences": [...]
  },
  "ai_summary": {...},
  "suggestions": [...]
}
```

---

### 场景 2：记录动作

**目的**：验证动作记录到 pending session

**测试对话**：

```
用户: 帮我创建一个 test.py 文件
期望: 
1. AI 创建文件
2. AI 调用 hook.py --record 记录动作

用户: 运行 pytest
期望:
1. AI 执行命令
2. AI 调用 hook.py --record 记录动作
```

**手动验证**：

```bash
# 手动记录动作
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --record '{
  "type": "create_file",
  "tool": "Write",
  "details": {"file_path": "test.py"},
  "context": {"task_stage": "implement"}
}'

# 查看 pending session
cat ~/.cursor/skills/behavior-prediction-data/pending_session.json
```

**期望输出**：

```json
{
  "start_time": "2026-02-01T10:00:00",
  "actions": [
    {
      "timestamp": "2026-02-01T10:01:00",
      "type": "create_file",
      "tool": "Write",
      "details": {"file_path": "test.py"},
      "context": {"task_stage": "implement"}
    }
  ],
  "stages": ["implement"]
}
```

---

### 场景 3：智能预测

**目的**：验证完成某阶段后的预测建议

**测试对话**：

```
用户: 我刚完成了代码实现
期望: AI 根据行为模式预测下一步，如"你可能想要运行测试"

用户: 查看预测建议
期望: 显示基于历史行为的预测
```

**验证命令**：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/get_predictions.py '{"current_stage": "implement"}'
```

**期望输出**：

```json
{
  "predictions": [
    {
      "next_stage": "test",
      "probability": 0.85,
      "suggestion": "运行测试验证代码"
    }
  ],
  "auto_execute": {
    "enabled": true,
    "should_auto_execute": false,
    "should_confirm": true,
    "action": "run_test",
    "command": "pytest"
  }
}
```

---

### 场景 4：会话结束

**目的**：验证会话结束时的记录和模式更新

**测试对话**：

```
用户: 谢谢，今天的工作完成了
期望: AI 调用 hook.py --finalize，记录会话并更新模式
```

**手动验证**：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --finalize '{
  "session_summary": {
    "topic": "测试会话",
    "goals": ["测试行为预测"],
    "completed_tasks": ["创建文件", "运行测试"],
    "technologies_used": ["Python", "pytest"],
    "workflow_stages": ["implement", "test"],
    "tags": ["#test"]
  },
  "operations": {
    "files": {"created": ["test.py"], "modified": [], "deleted": []},
    "commands": [{"command": "pytest", "type": "run_test", "exit_code": 0}]
  },
  "conversation": {"user_messages": [], "message_count": 3},
  "time": {"start": "2026-02-01T10:00:00", "end": "2026-02-01T10:30:00"}
}'
```

**期望输出**：

```json
{
  "status": "success",
  "session_id": "sess_20260201_005",
  "patterns_updated": true,
  "message": "会话 sess_20260201_005 已记录"
}
```

---

### 场景 5：查看用户画像

**目的**：验证用户画像更新

**测试对话**：

```
用户: 查看我的行为模式
期望: 显示用户画像和行为模式分析
```

**验证命令**：

```bash
# 查看用户画像
python3 ~/.cursor/skills/behavior-prediction/scripts/user_profile.py

# 查看行为模式
python3 ~/.cursor/skills/behavior-prediction/scripts/extract_patterns.py
```

---

### 场景 6：自动 Finalize

**目的**：验证下次会话开始时自动保存上次会话

**测试步骤**：

1. 先记录一些动作（不调用 finalize）
2. 开始新会话（调用 init）
3. 验证上次会话被自动保存

```bash
# 1. 记录动作
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --record '{
  "type": "create_file",
  "tool": "Write",
  "details": {"file_path": "auto_test.py"},
  "context": {"task_stage": "implement"}
}'

# 2. 开始新会话（会自动 finalize 上次）
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --init

# 3. 检查输出中是否有 auto_finalized_session 字段
```

**期望输出**：

```json
{
  "status": "success",
  "auto_finalized_session": {
    "status": "success",
    "session_id": "sess_20260201_006",
    "message": "上一个会话已自动保存"
  },
  "user_profile": {...}
}
```

---

### 场景 7：自动执行

**目的**：验证高置信度时的自动执行

**测试对话**：

```
用户: 帮我实现一个简单的函数
（AI 创建文件后）
期望: 如果置信度 >= 95%，AI 自动运行测试
      如果置信度 >= 85%，AI 询问是否运行测试
```

**验证命令**：

```bash
python3 ~/.cursor/skills/behavior-prediction/scripts/get_predictions.py '{"current_stage": "implement"}'
```

---

## 完整测试流程

1. **开始会话**：说"开始"或任何话
2. **执行任务**：让 AI 创建文件、运行命令等
3. **查看预测**：说"查看预测建议"
4. **结束会话**：说"谢谢"或"完成了"
5. **验证记录**：检查会话是否被记录

---

## 常见问题排查

### 问题 1：--init 返回 total_sessions: 0

**原因**：用户画像文件不存在或未更新

**解决**：

```bash
# 强制更新用户画像
python3 ~/.cursor/skills/behavior-prediction/scripts/user_profile.py '{"action": "update"}'
```

### 问题 2：--record 没有被调用

**原因**：AI 没有遵循规则文件中的指令

**解决**：检查规则文件是否正确加载，确保 `alwaysApply: true`

### 问题 3：预测不准确

**原因**：历史数据不足

**解决**：多进行几次会话，积累更多数据

---

## 数据文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| 用户画像 | `~/.cursor/skills/behavior-prediction-data/profile/user_profile.json` | 用户统计和偏好 |
| 会话索引 | `~/.cursor/skills/behavior-prediction-data/index/sessions_index.json` | 所有会话列表 |
| 行为模式 | `~/.cursor/skills/behavior-prediction-data/patterns/workflow_patterns.json` | 工作流程模式 |
| Pending Session | `~/.cursor/skills/behavior-prediction-data/pending_session.json` | 当前会话状态 |
