# Memory Skill v2.0 Cursor 对话测试方案

## 测试准备

### 1. 确保规则已启用

```
启用自动记忆检索
```

### 2. 验证规则文件存在

```bash
cat ~/.cursor/rules/memory-auto-retrieve.mdc
```

### 3. 验证 Skill 已安装

```bash
ls ~/.cursor/skills/memory/
```

---

## 测试场景

### 场景 1：会话开始初始化

**目的**：验证会话开始时的初始化

**测试对话**：

```
用户: 开始新的会话
期望: AI 自动调用 hook.py --init，初始化会话
```

**验证命令**：

```bash
python3 ~/.cursor/skills/memory/scripts/hook.py --init
```

**期望输出**：

```json
{
  "status": "success",
  "session_start": "2026-02-01T10:00:00",
  "save_trigger_enabled": true,
  "temp_memory_enabled": true
}
```

---

### 场景 2：关键词触发保存

**目的**：验证关键词检测和自动保存

**测试对话**：

```
用户: 我们决定使用 FastAPI 替换 Flask
期望: AI 检测到"决定"、"使用"关键词，自动保存临时记忆

用户: 我喜欢函数式编程风格
期望: AI 检测到"喜欢"、"风格"关键词，自动保存临时记忆

用户: API 前缀配置为 /api/v2
期望: AI 检测到"配置"关键词，自动保存临时记忆

用户: 下一步要实现用户认证功能
期望: AI 检测到"下一步"关键词，自动保存临时记忆
```

**手动验证**：

```bash
# 保存临时记忆
python3 ~/.cursor/skills/memory/scripts/hook.py --save '{
  "user_message": "我们决定使用 FastAPI 替换 Flask",
  "topic": "技术选型",
  "key_info": ["使用 FastAPI 替换 Flask"],
  "tags": ["#decision", "#api"]
}'
```

**期望输出**：

```json
{
  "status": "success",
  "message": "临时记忆已保存",
  "trigger_keyword": "决定",
  "trigger_category": "decision"
}
```

---

### 场景 3：无触发关键词

**目的**：验证普通对话不会触发保存

**测试对话**：

```
用户: 今天天气不错
期望: 正常回复，不触发保存

用户: Python 怎么读取文件
期望: 正常回复，不触发保存（通用问答）
```

**验证命令**：

```bash
python3 ~/.cursor/skills/memory/scripts/hook.py --save '{"user_message": "今天天气不错"}'
```

**期望输出**：

```json
{
  "status": "skipped",
  "reason": "no_trigger_keyword",
  "message": "未检测到保存触发关键词"
}
```

---

### 场景 4：查看会话状态

**目的**：验证临时记忆是否正确保存

**测试对话**：

```
用户: 查看会话状态
期望: 显示当前会话的临时记忆数量和最近记忆列表
```

**验证命令**：

```bash
python3 ~/.cursor/skills/memory/scripts/hook.py --status
```

**期望输出**：

```json
{
  "status": "active",
  "session_start": "2026-02-01T10:00:00",
  "temp_memory_count": 3,
  "recent_memories": [
    {
      "id": "temp_20260201_100100_001",
      "trigger_keyword": "决定",
      "timestamp": "2026-02-01T10:01:00"
    }
  ]
}
```

---

### 场景 5：手动保存

**目的**：验证强制保存功能

**测试对话**：

```
用户: 记住这个：项目使用 MIT 许可证
期望: 强制保存，即使没有触发关键词
```

**验证命令**：

```bash
python3 ~/.cursor/skills/memory/scripts/hook.py --save '{
  "user_message": "项目使用 MIT 许可证",
  "force": true
}'
```

---

### 场景 6：汇总记忆

**目的**：验证汇总功能

**测试对话**：

```
用户: 汇总记忆
期望: 汇总当前会话的临时记忆，显示合并结果
```

**验证命令**：

```bash
python3 ~/.cursor/skills/memory/scripts/summarize.py --session
```

**期望输出**：

```json
{
  "status": "success",
  "original_count": 5,
  "merged_count": 3,
  "file_path": "~/.cursor/skills/memory-data/daily/2026-02-01.md",
  "date": "2026-02-01"
}
```

---

### 场景 7：会话结束

**目的**：验证会话结束时的自动汇总

**测试对话**：

```
用户: 谢谢，今天就到这里
期望: AI 调用 hook.py --finalize，汇总保存会话记忆
```

**验证命令**：

```bash
python3 ~/.cursor/skills/memory/scripts/hook.py --finalize '{"topic": "技术讨论"}'
```

**期望输出**：

```json
{
  "status": "success",
  "message": "会话已保存",
  "memory_count": 3,
  "summarize_result": {
    "status": "success",
    "original_count": 3,
    "merged_count": 2,
    "file_path": "~/.cursor/skills/memory-data/daily/2026-02-01.md"
  }
}
```

---

### 场景 8：检索历史记忆

**目的**：验证检索功能

**测试对话**：

```
用户: 继续昨天的 API 工作
期望: AI 检索相关历史记忆并显示

用户: 我们之前讨论过什么
期望: AI 检索相关历史记忆并显示
```

**验证命令**：

```bash
python3 ~/.cursor/skills/memory/scripts/search_memory.py "API 设计"
```

---

### 场景 9：查看今日记忆

**目的**：验证记忆是否正确保存到每日文件

**测试对话**：

```
用户: 查看今日记忆
期望: 显示今天保存的所有记忆
```

**验证命令**：

```bash
python3 ~/.cursor/skills/memory/scripts/view_memory.py today
```

---

### 场景 10：清空临时记忆

**目的**：验证清空临时记忆功能

**测试对话**：

```
用户: 清空临时记忆
期望: 清除当前会话的临时记忆
```

**验证命令**：

```bash
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{"clear_temp": true}'
```

**期望输出**：

```json
{
  "success": true,
  "cleared_count": 3,
  "message": "已清空 3 条临时记忆"
}
```

---

### 场景 11：清空所有记忆

**目的**：验证清空所有记忆功能

**测试对话**：

```
用户: 清空所有记忆
期望: AI 询问确认

用户: 确认清空
期望: 清空所有记忆
```

**验证命令**：

```bash
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{"clear_all": true, "confirm": true}'
```

---

### 场景 12：删除日期范围记忆

**目的**：验证删除日期范围内的记忆

**测试对话**：

```
用户: 删除 1 月份的所有记忆
期望: 删除指定范围内的记忆
```

**验证命令**：

```bash
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{
  "start_date": "2026-01-01",
  "end_date": "2026-01-31"
}'
```

---

## 完整测试流程

1. **开始会话**：说"开始"
2. **触发保存**：说包含关键词的话（决定、喜欢、配置等）
3. **查看状态**：说"查看会话状态"
4. **手动保存**：说"记住这个：xxx"
5. **汇总记忆**：说"汇总记忆"
6. **结束会话**：说"谢谢"
7. **检索记忆**：说"继续昨天的工作"
8. **查看记忆**：说"查看今日记忆"

---

## 触发词参考

### 保存触发关键词

| 类型 | 中文关键词 | 英文关键词 |
|------|-----------|-----------|
| 决策类 | 决定、选择、使用、采用、确定 | decide, choose, use, adopt, select |
| 偏好类 | 喜欢、习惯、偏好、风格、方式 | prefer, like, habit, style, way |
| 配置类 | 配置、设置、规范、约定、命名 | config, setting, convention, naming |
| 计划类 | 下一步、待办、TODO、计划 | next step, todo, plan |
| 重要类 | 重要、记住、注意、关键、核心 | important, remember, note, key, core |

### 检索触发词

- 继续、上次、之前、昨天、我们讨论过
- continue, last time, before, yesterday

### 用户控制命令

| 命令 | 效果 |
|------|------|
| 记住这个 / save this | 强制保存当前对话 |
| 不要保存 / don't save | 跳过本次对话保存 |
| 搜索记忆: xxx | 主动搜索历史记忆 |
| 查看今日记忆 | 查看今天的记忆 |
| 汇总记忆 | 手动触发汇总 |
| 查看会话状态 | 查看当前会话的临时记忆数量 |
| 清空临时记忆 | 清空当前会话临时记忆 |
| 清空所有记忆 | 清空所有记忆（需确认） |

---

## 数据文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| 每日记忆 | `~/.cursor/skills/memory-data/daily/` | 每日记忆文件 |
| 关键词索引 | `~/.cursor/skills/memory-data/index/keywords.json` | 关键词索引 |
| 配置文件 | `~/.cursor/skills/memory-data/config.json` | 用户配置 |
| Pending Session | `~/.cursor/skills/memory-data/pending_session.json` | 当前会话状态 |

---

## 常见问题排查

### 问题 1：关键词没有触发保存

**原因**：消息太短或关键词不在列表中

**解决**：

```bash
# 检查关键词列表
python3 -c "from utils import SAVE_TRIGGER_KEYWORDS; print(SAVE_TRIGGER_KEYWORDS)"

# 添加自定义关键词到配置
```

### 问题 2：临时记忆没有被汇总

**原因**：会话没有正常结束

**解决**：

```bash
# 手动汇总
python3 ~/.cursor/skills/memory/scripts/summarize.py --session

# 或下次 --init 会自动汇总
```

### 问题 3：检索结果为空

**原因**：没有相关记忆或关键词不匹配

**解决**：

```bash
# 查看所有记忆
python3 ~/.cursor/skills/memory/scripts/view_memory.py all

# 检查索引
cat ~/.cursor/skills/memory-data/index/keywords.json
```

### 问题 4：配置没有生效

**原因**：使用了旧的配置文件

**解决**：

```bash
# 删除旧配置，使用默认配置
rm ~/.cursor/skills/memory-data/config.json
```
