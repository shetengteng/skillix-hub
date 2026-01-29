# Memory Skill 测试案例文档

## 1. 概述

本文档描述 Memory Skill 的测试案例，用于验证其核心功能是否正常工作。

## 2. 测试环境准备

### 2.1 全局安装

Memory Skill 已安装到全局目录：

```
~/.cursor/skills/memory/
├── SKILL.md
├── default_config.json
└── scripts/
    ├── save_memory.py
    ├── search_memory.py
    └── utils.py
```

### 2.2 数据存储位置

- **项目级数据**：`<project>/.cursor/skills/memory-data/`
- **全局级数据**：`~/.cursor/skills/memory-data/`

## 3. 功能测试案例

### 3.1 保存记忆测试

#### 测试案例 1：基本保存

**操作**：
```bash
python3 ~/.cursor/skills/memory/scripts/save_memory.py '{"topic": "API 设计讨论", "key_info": ["使用 FastAPI 框架", "RESTful 风格"], "tags": ["#api", "#design"]}'
```

**预期结果**：
- 返回成功消息，包含 `memory_id`
- 在 `memory-data/daily/` 目录下创建当日 Markdown 文件
- 在 `memory-data/index/keywords.json` 中添加索引条目

#### 测试案例 2：多会话保存

**操作**：连续执行三次保存命令

**预期结果**：
- 三次保存的 `session` 分别为 1、2、3
- `memory_id` 格式为 `YYYY-MM-DD-001`、`YYYY-MM-DD-002`、`YYYY-MM-DD-003`

#### 测试案例 3：无标签保存

**操作**：
```bash
python3 ~/.cursor/skills/memory/scripts/save_memory.py '{"topic": "测试主题", "key_info": ["信息1"]}'
```

**预期结果**：保存成功，标签字段为空数组

---

### 3.2 搜索记忆测试

#### 测试案例 4：基本搜索

**前置条件**：已保存包含 "API" 关键词的记忆

**操作**：
```bash
python3 ~/.cursor/skills/memory/scripts/search_memory.py "API 设计"
```

**预期结果**：
- 返回包含 "API" 相关的候选记忆
- 结果按分数降序排列
- 包含 `matched_keywords` 字段

#### 测试案例 5：无匹配搜索

**操作**：
```bash
python3 ~/.cursor/skills/memory/scripts/search_memory.py "完全不存在的关键词 xyz123"
```

**预期结果**：
- `candidates_count` 为 0
- `candidates` 为空数组

#### 测试案例 6：时间衰减验证

**前置条件**：有不同日期的记忆

**预期结果**：
- 近期记忆分数更高
- 7 天前的记忆分数约为今天的 70%（衰减率 0.95）

---

### 3.3 配置测试

#### 测试案例 7：禁用 Memory Skill

**操作**：
1. 在 `memory-data/config.json` 中设置 `"enabled": false`
2. 尝试保存和搜索

**预期结果**：
- 保存返回 `"success": false`
- 搜索返回空结果，消息包含 "禁用"

#### 测试案例 8：自定义检索范围

**操作**：
1. 在配置中设置 `"search_scope_days": 7`
2. 搜索记忆

**预期结果**：只返回最近 7 天的记忆

---

## 4. 集成测试案例

### 4.1 Cursor 对话测试

#### 测试案例 9：自动检索触发

**操作**：在 Cursor 中输入 "继续昨天的 API 重构工作"

**预期结果**：
- Memory Skill 识别到延续性意图
- 自动执行搜索并返回相关记忆
- 记忆内容被注入到 AI 响应上下文

#### 测试案例 10：手动保存命令

**操作**：在 Cursor 中输入 "记住这个"

**预期结果**：
- 当前对话被保存为记忆
- 返回保存成功的确认消息

#### 测试案例 11：跳过保存命令

**操作**：在 Cursor 中输入 "不要保存"

**预期结果**：当前对话不会被自动保存

---

### 4.2 意图识别测试

#### 测试案例 12：延续性意图

**输入示例**：
- "继续昨天的工作"
- "上次我们讨论到哪了"
- "接着做那个功能"

**预期结果**：触发记忆检索

#### 测试案例 13：偏好相关意图

**输入示例**：
- "帮我写一个函数"（需要了解用户编码偏好）
- "按照我的风格来"

**预期结果**：触发记忆检索

#### 测试案例 14：独立问题（不触发检索）

**输入示例**：
- "Python 怎么读文件"
- "async/await 用法是什么"

**预期结果**：不触发记忆检索，直接回答

#### 测试案例 15：新话题信号

**输入示例**：
- "换个话题"
- "新问题"

**预期结果**：不触发记忆检索

---

### 3.4 查看记忆测试

#### 测试案例 20：查看今日记忆

**操作**：
```bash
python3 ~/.cursor/skills/memory/scripts/view_memory.py today
```

**预期结果**：
- 返回今日所有记忆
- 包含 `count` 和 `memories` 字段
- 每条记忆包含 `id`、`summary`、`content` 等信息

#### 测试案例 21：查看指定日期记忆

**操作**：
```bash
python3 ~/.cursor/skills/memory/scripts/view_memory.py "2026-01-29"
```

**预期结果**：
- 返回指定日期的所有记忆
- 日期不存在时返回空列表

#### 测试案例 22：查看最近记忆

**操作**：
```bash
python3 ~/.cursor/skills/memory/scripts/view_memory.py recent 7
```

**预期结果**：
- 返回最近 7 天的记忆
- 按日期分组，最近的在前

#### 测试案例 23：列出所有日期

**操作**：
```bash
python3 ~/.cursor/skills/memory/scripts/view_memory.py list
```

**预期结果**：
- 返回所有有记忆的日期列表
- 包含每个日期的记忆数量

---

### 3.5 删除记忆测试

#### 测试案例 24：删除指定记忆

**前置条件**：已保存记忆 `2026-01-29-001`

**操作**：
```bash
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{"id": "2026-01-29-001"}'
```

**预期结果**：
- 返回成功消息
- 索引中删除该条目
- 每日文件中标记为已删除

#### 测试案例 25：删除不存在的记忆

**操作**：
```bash
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{"id": "2099-01-01-999"}'
```

**预期结果**：
- 返回 `"success": false`
- 消息包含 "未找到"

#### 测试案例 26：删除指定日期的所有记忆

**前置条件**：2026-01-29 有多条记忆

**操作**：
```bash
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{"date": "2026-01-29"}'
```

**预期结果**：
- 返回成功消息，包含删除数量
- 索引中删除该日期所有条目
- 删除对应的每日文件

#### 测试案例 27：清空所有记忆（无确认）

**操作**：
```bash
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{"clear_all": true}'
```

**预期结果**：
- 返回 `"success": false`
- 消息要求确认

#### 测试案例 28：清空所有记忆（有确认）

**操作**：
```bash
python3 ~/.cursor/skills/memory/scripts/delete_memory.py '{"clear_all": true, "confirm": true}'
```

**预期结果**：
- 返回成功消息
- 索引清空
- 所有每日文件删除

---

## 5. 边界测试案例

### 5.1 数据边界

#### 测试案例 16：空数据库搜索

**前置条件**：`memory-data` 目录为空

**预期结果**：搜索返回空结果，不报错

#### 测试案例 17：大量关键词

**操作**：保存包含 50 个关键词的记忆

**预期结果**：只保存前 20 个关键词

### 5.2 错误处理

#### 测试案例 18：无效 JSON 输入

**操作**：
```bash
python3 save_memory.py 'invalid json'
```

**预期结果**：返回 JSON 解析错误消息

#### 测试案例 19：缺少必需参数

**操作**：
```bash
python3 save_memory.py '{"key_info": ["信息"]}'
```

**预期结果**：返回缺少 `topic` 参数的错误消息

---

## 6. 自动化测试

### 6.1 运行测试套件

```bash
cd ~/.cursor/skills/memory/tests
python3 run_all_tests.py
```

### 6.2 测试覆盖

| 测试文件 | 测试数量 | 覆盖功能 |
|----------|---------|---------|
| test_utils.py | 23 | 关键词提取、时间衰减、分数计算、配置管理 |
| test_save_memory.py | 9 | 保存记忆、索引更新、会话编号 |
| test_search_memory.py | 12 | 搜索记忆、分数排序、禁用状态 |
| test_delete_memory.py | 8 | 删除指定记忆、按日期删除、清空所有记忆 |
| test_view_memory.py | 10 | 查看今日记忆、查看指定日期、查看最近记忆、列出日期 |
| **总计** | **62** | |

---

## 7. 测试检查清单

### 7.1 功能验证

- [ ] 保存记忆成功创建每日文件
- [ ] 保存记忆正确更新索引
- [ ] 搜索返回匹配的记忆
- [ ] 搜索结果按分数排序
- [ ] 时间衰减正确计算
- [ ] 配置文件正确加载

### 7.2 意图识别验证

- [ ] 延续性意图触发检索
- [ ] 偏好意图触发检索
- [ ] 项目相关意图触发检索
- [ ] 独立问题不触发检索
- [ ] 新话题信号不触发检索

### 7.3 错误处理验证

- [ ] 无效输入返回错误消息
- [ ] 禁用状态正确处理
- [ ] 空数据库不报错

---

## 8. 已知限制

1. **中文分词**：当前使用简单的空格分词，对中文支持有限
2. **关键词提取**：依赖停用词列表，可能遗漏重要词汇
3. **语义理解**：依赖大模型进行二次筛选，关键词匹配可能不够精确

---

## 9. 后续改进

1. 添加更完善的中文分词支持
2. ~~实现记忆删除功能~~ ✅ 已完成
3. 添加记忆导出/导入功能
4. 支持记忆标签筛选
