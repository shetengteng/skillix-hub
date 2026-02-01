# 持续学习 Cursor 对话测试方案

## 测试准备

### 1. 确保规则已启用

```
启用持续学习规则
```

### 2. 验证规则文件存在

```bash
cat ~/.cursor/rules/continuous-learning.mdc
```

### 3. 验证 Skill 已安装

```bash
ls ~/.cursor/skills/continuous-learning/
```

---

## 测试场景

### 场景 1：会话开始初始化

**目的**：验证会话开始时加载本能和建议

**测试对话**：

```
用户: 开始新的会话
期望: AI 自动调用 observe.py --init，返回本能摘要和建议
```

**验证命令**：

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --init
```

**期望输出**：

```json
{
  "status": "success",
  "instincts_loaded": 5,
  "suggestions": [
    "你习惯在 implement 后运行测试",
    "你常用的技术：Python, FastAPI"
  ]
}
```

---

### 场景 2：记录观察

**目的**：验证用户行为被记录为观察

**测试对话**：

```
用户: 帮我创建一个 api.py 文件
期望: 
1. AI 创建文件
2. AI 调用 observe.py --record 记录观察

用户: 运行测试
期望:
1. AI 执行测试
2. AI 调用 observe.py --record 记录观察
```

**手动验证**：

```bash
# 记录观察
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --record '{
  "type": "tool_use",
  "tool": "Write",
  "action": "create_file",
  "details": {"file_path": "api.py"},
  "context": {"task_stage": "implement"}
}'

# 查看观察文件
ls ~/.cursor/skills/continuous-learning-data/observations/
```

**期望**：观察被记录到 JSONL 文件

---

### 场景 3：用户纠正检测

**目的**：验证检测到用户纠正时生成本能

**测试对话**：

```
用户: 不对，应该用 async def 而不是 def
期望: AI 检测到纠正，记录为潜在本能

用户: 这样不行，换成 FastAPI 的方式
期望: AI 检测到纠正，记录为潜在本能
```

**验证命令**：

```bash
# 分析观察，检测纠正
python3 ~/.cursor/skills/continuous-learning/scripts/analyze.py --recent
```

**期望输出**：

```json
{
  "corrections_detected": [
    {
      "type": "user_correction",
      "pattern": "prefer_async_def",
      "confidence": 0.7
    }
  ]
}
```

---

### 场景 4：错误解决检测

**目的**：验证检测到错误解决时生成本能

**测试对话**：

```
用户: 这个报错了，帮我修复
（AI 修复后）
用户: 好了，可以了
期望: AI 检测到错误解决模式，记录为本能
```

**验证命令**：

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/analyze.py --recent
```

---

### 场景 5：查看本能状态

**目的**：验证本能列表和状态

**测试对话**：

```
用户: 查看学习到的本能
期望: 显示所有本能及其置信度
```

**验证命令**：

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py status
```

**期望输出**：

```json
{
  "total_instincts": 5,
  "instincts": [
    {
      "id": "inst_001",
      "pattern": "prefer_async_def",
      "confidence": 0.85,
      "trigger_count": 3
    }
  ]
}
```

---

### 场景 6：创建本能

**目的**：验证手动创建本能

**测试对话**：

```
用户: 记住：我喜欢用 TypeScript 而不是 JavaScript
期望: AI 创建新本能
```

**验证命令**：

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py create '{
  "pattern": "prefer_typescript",
  "description": "用户偏好 TypeScript",
  "trigger": "当用户创建前端文件时",
  "action": "使用 TypeScript 而不是 JavaScript",
  "confidence": 0.9
}'
```

---

### 场景 7：演化本能为技能

**目的**：验证高置信度本能演化为技能

**测试对话**：

```
用户: 将测试相关的本能演化为技能
期望: AI 创建新的 SKILL.md 文件
```

**验证命令**：

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py evolve '{
  "instinct_ids": ["inst_001", "inst_002"],
  "skill_name": "testing-workflow",
  "description": "测试工作流程技能"
}'
```

**期望输出**：

```json
{
  "status": "success",
  "skill_path": "~/.cursor/skills/continuous-learning-data/evolved/skills/testing-workflow/SKILL.md"
}
```

---

### 场景 8：会话结束

**目的**：验证会话结束时的处理

**测试对话**：

```
用户: 谢谢，今天就到这里
期望: AI 调用 observe.py --finalize，保存观察并分析
```

**验证命令**：

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --finalize '{
  "session_summary": {
    "topic": "API 开发",
    "technologies": ["Python", "FastAPI"],
    "stages": ["implement", "test"]
  }
}'
```

---

### 场景 9：删除本能

**目的**：验证删除不需要的本能

**测试对话**：

```
用户: 删除本能 inst_001
期望: AI 删除指定本能
```

**验证命令**：

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py delete inst_001
```

---

### 场景 10：检查演化技能

**目的**：验证演化技能是否被 Cursor 识别

**测试对话**：

```
用户: 查看演化的技能
期望: 显示所有演化的技能列表
```

**验证命令**：

```bash
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py check
```

---

## 完整测试流程

1. **开始会话**：说"开始"
2. **执行任务**：创建文件、修改代码、运行测试
3. **触发纠正**：故意让 AI 做错，然后纠正
4. **查看本能**：说"查看学习到的本能"
5. **创建本能**：说"记住：我喜欢..."
6. **演化技能**：说"将 xxx 本能演化为技能"
7. **结束会话**：说"谢谢"

---

## 触发词参考

| 触发词 | 动作 |
|--------|------|
| 开始、start | 调用 --init |
| 记住、remember | 创建本能 |
| 忘记、forget | 删除本能 |
| 查看本能、list instincts | 显示本能列表 |
| 演化、evolve | 演化本能为技能 |
| 谢谢、done、bye | 调用 --finalize |

---

## 纠正信号词

AI 应该检测以下信号词来识别用户纠正：

**中文**：
- 不对、不是、错了、应该是
- 换成、改成、用 xxx 代替
- 这样不行、不要这样

**英文**：
- no, wrong, incorrect
- should be, use xxx instead
- don't do that, not like this

---

## 数据文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| 观察文件 | `~/.cursor/skills/continuous-learning-data/observations/` | 用户行为观察 |
| 本能文件 | `~/.cursor/skills/continuous-learning-data/instincts/` | 学习到的本能 |
| 演化技能 | `~/.cursor/skills/continuous-learning-data/evolved/skills/` | 演化生成的技能 |
| 技能索引 | `~/.cursor/skills/continuous-learning-data/index/skills_index.json` | 技能索引 |
| Pending Session | `~/.cursor/skills/continuous-learning-data/pending_session.json` | 当前会话状态 |

---

## 常见问题排查

### 问题 1：本能没有被创建

**原因**：置信度阈值太高

**解决**：

```bash
# 查看配置
cat ~/.cursor/skills/continuous-learning/default_config.json

# 调整 instincts.min_confidence 值
```

### 问题 2：演化技能没有被 Cursor 识别

**原因**：符号链接未创建或路径错误

**解决**：

```bash
# 检查符号链接
ls -la ~/.cursor/skills/

# 手动创建符号链接
ln -s ~/.cursor/skills/continuous-learning-data/evolved/skills/xxx ~/.cursor/skills/xxx
```

### 问题 3：观察文件过大

**原因**：长时间未清理

**解决**：

```bash
# 清理旧观察
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --cleanup
```
