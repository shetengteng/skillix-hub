# Behavior Prediction Skill

为 AI 助手提供用户行为预测能力。学习用户的行为模式，当用户执行动作 A 后，自动预测并建议下一个可能的动作 B。当用户问题包含行为预测相关词汇（预测下一步、我的行为模式、行为习惯）或需要查看/管理行为记录时自动触发。

## 兼容性

本 Skill 支持多种 AI 助手：
- Cursor (.cursor)
- Claude (.claude)
- GitHub Copilot (.copilot)
- Codeium (.codeium)
- 通用 AI (.ai)

系统会自动检测当前使用的 AI 助手，并使用对应的目录存储数据。

## 功能概述

1. **行为记录**：自动记录用户在 AI 助手中执行的动作
2. **模式学习**：分析行为序列，发现 A → B 的关联模式
3. **智能预测**：当用户执行动作 A 时，预测并建议动作 B

## 使用方式

### 自动模式

启用 Always Applied Rule 后，系统会自动：
- 记录每次工具调用
- 在适当时机提供预测建议

### 手动命令

| 命令 | 描述 |
|------|------|
| `查看我的行为模式` | 显示学习到的行为模式 |
| `预测下一步` | 手动触发预测 |
| `查看行为统计` | 显示统计数据概览 |
| `清除行为记录` | 删除所有行为记录 |

## 预测建议

当完成一个动作后，如果系统有高置信度的预测，会显示建议：

```
✨ 基于你的习惯，你可能想要：
→ 运行测试 (置信度: 85%)

要执行吗？[Y/n]
```

## 脚本说明

### record_action.py

记录单个动作到今日日志，并更新转移矩阵。

```bash
python3 <skill_dir>/scripts/record_action.py '{
  "type": "动作类型",
  "tool": "工具名称",
  "timestamp": "ISO8601时间",
  "details": {...},
  "classification": {
    "confidence": 0.95,
    "is_new_type": false,
    "description": "类型描述（新类型时）"
  }
}'
```

### get_statistics.py

获取预测所需的统计数据。

```bash
# 获取特定动作的统计
python3 <skill_dir>/scripts/get_statistics.py '{"current_action": "动作类型"}'

# 获取所有统计概览
python3 <skill_dir>/scripts/get_statistics.py
```

### finalize_session.py

会话结束时的批量处理（可选）。

```bash
python3 <skill_dir>/scripts/finalize_session.py '{
  "actions_summary": [...],
  "start_time": "...",
  "end_time": "..."
}'
```

### check_last_session.py

会话开始时检查数据完整性（兜底）。

```bash
# 检查上次会话
python3 <skill_dir>/scripts/check_last_session.py

# 获取数据摘要
python3 <skill_dir>/scripts/check_last_session.py '{"action": "summary"}'

# 手动重新计算转移矩阵
python3 <skill_dir>/scripts/check_last_session.py '{"action": "recalculate"}'
```

## 动作分类指南

### 常见动作类型（参考，不限于此）

**文件操作**：
- `create_file`: 创建新文件
- `edit_file`: 修改已有文件
- `delete_file`: 删除文件

**代码相关**：
- `write_code`: 编写代码
- `write_test`: 编写测试
- `refactor`: 重构代码
- `fix_bug`: 修复 bug

**命令执行**：
- `run_test`: 运行测试
- `run_build`: 构建项目
- `run_server`: 启动服务
- `install_dep`: 安装依赖

**Git 操作**：
- `git_add`: 暂存文件
- `git_commit`: 提交代码
- `git_push`: 推送代码
- `git_pull`: 拉取代码

### 分类要求

1. **理解语义**：不只看命令关键词，要理解实际意图
2. **结合上下文**：参考用户消息理解意图
3. **可以创建新类型**：如 `train_model`、`deploy_app`
4. **输出置信度**：评估分类的确信程度

## 预测决策指南

### 获取统计数据后的分析步骤

1. **查看历史概率**：从 transitions 中获取各动作的概率
2. **考虑样本量**：count 越大，统计越可信
3. **检查最近模式**：recent_sequence 中是否有明显模式
4. **结合上下文**：当前操作的文件类型、项目结构等

### 置信度评估

| 置信度 | 条件 | 建议方式 |
|--------|------|----------|
| > 0.9 | 历史概率高 + 上下文支持 + 样本量大 | 肯定语气 |
| 0.7-0.9 | 历史概率中等或上下文部分支持 | 建议语气 |
| 0.5-0.7 | 历史概率较低或样本量小 | 询问语气 |
| < 0.5 | 数据不足或上下文不支持 | 不建议 |

## 会话开始检查

每次新会话开始时，建议执行检查确保数据完整：

```bash
python3 <skill_dir>/scripts/check_last_session.py
```

这个脚本会：
1. 检查上次会话是否正常结束
2. 如果转移矩阵需要更新，自动重新计算
3. 每天只执行一次，避免重复检查

## 配置选项

配置文件位于数据目录的 `config.json`。

```json
{
  "enabled": true,
  "prediction": {
    "enabled": true,
    "suggest_threshold": 0.5,
    "auto_execute_threshold": 0.95,
    "max_suggestions": 3
  },
  "recording": {
    "enabled": true,
    "retention_days": 90
  },
  "learning": {
    "enabled": true,
    "min_samples_for_prediction": 3
  }
}
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enabled` | `true` | 总开关 |
| `prediction.suggest_threshold` | `0.5` | 显示建议的最低置信度 |
| `prediction.auto_execute_threshold` | `0.95` | 自动执行的置信度阈值（后续功能） |
| `recording.retention_days` | `90` | 动作记录保留天数 |
| `learning.min_samples_for_prediction` | `3` | 最少样本数才启用预测 |

## 数据存储

数据存储位置会根据使用的 AI 助手自动选择：

**项目级（优先）**：
- `<project>/.cursor/skills/behavior-prediction-data/`
- `<project>/.claude/skills/behavior-prediction-data/`
- `<project>/.ai/skills/behavior-prediction-data/`
- 等等...

**全局级（备选）**：
- `~/.cursor/skills/behavior-prediction-data/`
- `~/.claude/skills/behavior-prediction-data/`
- 等等...

```
behavior-prediction-data/
├── actions/                    # 动作记录
│   └── YYYY-MM-DD.json         # 每日动作日志
├── patterns/
│   ├── transition_matrix.json  # 转移概率矩阵
│   └── types_registry.json     # 动作类型注册表
├── stats/
│   └── sessions.json           # 会话统计
└── config.json                 # 用户配置
```

## 隐私说明

- 所有数据存储在本地
- 不上传任何信息到服务器
- 用户可以随时删除数据
- 完整记录命令和参数，便于准确预测
