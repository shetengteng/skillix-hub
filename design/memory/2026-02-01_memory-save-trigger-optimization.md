# Memory Skill 保存触发机制优化方案

## 一、问题分析

### 当前机制

当前 Memory Skill 的保存触发依赖于：
1. **AI 主动判断** - AI 需要主动识别"值得保存"的内容
2. **用户手动触发** - 用户说"记住这个"
3. **会话结束信号** - 用户说"谢谢"、"done"等

### 存在的问题

| 问题 | 描述 | 影响 |
|------|------|------|
| **依赖 AI 主动性** | AI 可能忘记判断是否需要保存 | 重要信息丢失 |
| **触发条件模糊** | "值得保存"的判断标准不够明确 | 保存不一致 |
| **会话结束不可靠** | 用户可能直接关闭窗口 | 整个会话丢失 |
| **无实时保存** | 只在会话结束时保存 | 中途关闭丢失 |

## 二、优化方案

### 方案 A：关键词触发保存（推荐）

**原理**：检测用户消息中的关键词，自动触发保存。

**触发关键词：**

| 类型 | 关键词 | 示例 |
|------|--------|------|
| **决策类** | 决定、选择、使用、采用、确定 | "我们决定使用 FastAPI" |
| **偏好类** | 喜欢、习惯、偏好、风格、方式 | "我喜欢函数式风格" |
| **配置类** | 配置、设置、规范、约定、前缀 | "API 前缀是 /api/v2" |
| **计划类** | 下一步、待办、TODO、计划、接下来 | "下一步要实现认证" |
| **重要类** | 重要、记住、注意、关键、核心 | "这个很重要" |

**实现方式**：
```python
# 在 memory-auto-retrieve.mdc 规则中添加
SAVE_TRIGGER_KEYWORDS = {
    "zh": ["决定", "选择", "使用", "采用", "喜欢", "习惯", "偏好", 
           "配置", "设置", "规范", "下一步", "待办", "重要", "记住"],
    "en": ["decide", "choose", "use", "prefer", "like", "habit",
           "config", "setting", "convention", "next step", "todo", "important"]
}
```

**优点**：
- 自动化程度高
- 不依赖 AI 主动判断
- 实时保存，不怕中途关闭

**缺点**：
- 可能产生误触发
- 需要维护关键词列表

---

### 方案 B：会话 Hook 机制

**原理**：类似 Behavior Prediction 的 hook 机制，在会话开始和结束时自动执行。

**实现方式**：

```bash
# 会话开始时
python3 memory/scripts/hook.py --init

# 会话结束时（或下次 --init 时自动触发）
python3 memory/scripts/hook.py --finalize '{
  "topic": "会话主题",
  "key_info": ["要点1", "要点2"],
  "tags": ["#tag1"]
}'
```

**工作流程**：
1. 每次会话开始时调用 `--init`
2. `--init` 自动 finalize 上一个未完成的会话
3. AI 在会话过程中收集信息
4. 会话结束时调用 `--finalize`（可选）

**优点**：
- 与 Behavior Prediction 机制一致
- 自动 finalize 保证数据不丢失
- 结构化的会话数据

**缺点**：
- 需要 AI 收集会话信息
- 实现复杂度较高

---

### 方案 C：实时保存 + 去重

**原理**：每次有价值的对话后立即保存，通过去重机制避免重复。

**触发条件**：
1. 用户消息长度 > 50 字符
2. AI 回复包含代码或配置
3. 对话涉及决策或配置

**去重机制**：
- 基于内容相似度去重
- 同一主题只保留最新版本
- 使用关键词哈希快速比对

**实现方式**：
```python
def should_save(user_msg, ai_response):
    # 长度检查
    if len(user_msg) < 50:
        return False
    
    # 关键词检查
    if not has_save_keywords(user_msg):
        return False
    
    # 去重检查
    if is_duplicate(user_msg, ai_response):
        return False
    
    return True
```

**优点**：
- 实时保存，数据安全
- 自动去重，避免冗余
- 不依赖会话结束

**缺点**：
- 可能产生较多记忆
- 去重逻辑复杂

---

### 方案 D：混合方案（推荐）

**原理**：结合方案 A 和方案 B 的优点。

**实现方式**：

1. **关键词触发实时保存**（方案 A）
   - 检测到关键词时立即保存
   - 保存为"临时记忆"

2. **会话 Hook 汇总**（方案 B）
   - 会话结束时汇总临时记忆
   - 合并相关内容
   - 生成结构化记忆

3. **自动 Finalize 兜底**
   - 下次会话开始时自动处理未完成的会话
   - 保证数据不丢失

**数据流程**：

```
用户消息 → 关键词检测 → 临时保存
                ↓
         会话结束/下次开始
                ↓
         汇总临时记忆 → 结构化保存
```

**优点**：
- 实时保存 + 结构化汇总
- 自动化程度高
- 数据不丢失

**缺点**：
- 实现复杂度最高
- 需要管理临时记忆

## 三、方案对比

| 方案 | 实时性 | 可靠性 | 复杂度 | 推荐度 |
|------|--------|--------|--------|--------|
| A. 关键词触发 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| B. 会话 Hook | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| C. 实时保存+去重 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| D. 混合方案 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 四、推荐实施路径

### 第一阶段：方案 A（关键词触发）

**目标**：快速提升保存触发率

**实施内容**：
1. 在规则文件中添加关键词列表
2. 检测到关键词时自动调用 `save_memory.py`
3. 保存格式与现有一致

**预计工作量**：1-2 小时

### 第二阶段：方案 B（会话 Hook）

**目标**：增加结构化保存能力

**实施内容**：
1. 创建 `hook.py` 脚本
2. 实现 `--init` 和 `--finalize` 功能
3. 更新规则文件

**预计工作量**：2-3 小时

### 第三阶段：方案 D（混合方案）

**目标**：完整的保存机制

**实施内容**：
1. 实现临时记忆存储
2. 实现会话汇总逻辑
3. 实现去重机制

**预计工作量**：3-4 小时

## 五、规则文件修改示例

### 方案 A 的规则修改

```markdown
## 二、保存触发（实时）

### 关键词自动保存

当用户消息包含以下关键词时，**立即**触发保存：

**决策类**：决定、选择、使用、采用、确定
**偏好类**：喜欢、习惯、偏好、风格
**配置类**：配置、设置、规范、约定
**计划类**：下一步、待办、TODO、计划
**重要类**：重要、记住、注意、关键

### 保存执行

检测到关键词后：

1. 提取当前对话的主题和关键信息
2. 立即执行保存：
   ```bash
   python3 /path/to/save_memory.py '{"topic": "主题", "key_info": ["要点"], "tags": ["#tag"]}'
   ```

### 示例

用户: "我们决定使用 FastAPI 替换 Flask"
→ 检测到"决定"、"使用"
→ 自动保存: {"topic": "技术选型", "key_info": ["使用 FastAPI 替换 Flask"], "tags": ["#decision", "#api"]}
```

## 六、方案 D 详细设计

### 6.1 关键词列表（完整版）

```python
SAVE_TRIGGER_KEYWORDS = {
    "zh": {
        "decision": ["决定", "选择", "使用", "采用", "确定", "选用", "改用", "换成", "替换"],
        "preference": ["喜欢", "习惯", "偏好", "风格", "方式", "倾向", "常用", "一般"],
        "config": ["配置", "设置", "规范", "约定", "前缀", "后缀", "命名", "格式", "路径"],
        "plan": ["下一步", "待办", "TODO", "计划", "接下来", "之后", "后续", "安排"],
        "important": ["重要", "记住", "注意", "关键", "核心", "必须", "一定", "务必"],
        "project": ["项目", "模块", "功能", "接口", "API", "数据库", "表", "字段"],
        "tech": ["框架", "库", "工具", "语言", "版本", "依赖", "环境", "部署"]
    },
    "en": {
        "decision": ["decide", "choose", "use", "adopt", "select", "switch to", "replace"],
        "preference": ["prefer", "like", "habit", "style", "way", "usually", "always"],
        "config": ["config", "setting", "convention", "prefix", "suffix", "naming", "format", "path"],
        "plan": ["next step", "todo", "plan", "then", "after", "later", "schedule"],
        "important": ["important", "remember", "note", "key", "core", "must", "critical"],
        "project": ["project", "module", "feature", "api", "database", "table", "field"],
        "tech": ["framework", "library", "tool", "language", "version", "dependency", "deploy"]
    }
}
```

### 6.2 自定义关键词配置

用户可以在 `memory-data/config.json` 中添加自定义关键词：

```json
{
  "save_trigger": {
    "enabled": true,
    "custom_keywords": {
      "zh": ["自定义词1", "自定义词2"],
      "en": ["custom1", "custom2"]
    },
    "excluded_keywords": {
      "zh": ["排除词1"],
      "en": ["exclude1"]
    }
  }
}
```

### 6.3 临时记忆机制

**存储位置**：`memory-data/temp/`

**文件格式**：
```
memory-data/temp/
├── 2026-02-01_sess_001.jsonl    # 会话 1 的临时记忆
├── 2026-02-01_sess_002.jsonl    # 会话 2 的临时记忆
└── ...
```

**临时记忆格式**：
```json
{
  "id": "temp_20260201_001",
  "timestamp": "2026-02-01T10:30:45",
  "trigger_keyword": "决定",
  "trigger_category": "decision",
  "user_message": "我们决定使用 FastAPI",
  "ai_response": "好的，FastAPI 是一个很好的选择...",
  "extracted_info": {
    "topic": "技术选型",
    "key_info": ["使用 FastAPI"],
    "tags": ["#decision", "#api"]
  }
}
```

**保留时间**：默认 30 天，可在配置中调整

```json
{
  "temp_memory": {
    "retention_days": 30,
    "max_per_session": 50
  }
}
```

### 6.4 汇总机制

#### 触发时机

1. **会话结束时**（检测到结束信号）
2. **下次会话开始时**（自动 finalize 上一个会话）
3. **手动触发**（用户说"汇总记忆"）

#### 汇总流程

```
临时记忆列表
    ↓
┌─────────────────────────────────────┐
│  1. 按类别分组                       │
│     - decision: [temp_001, temp_003] │
│     - config: [temp_002]             │
│     - plan: [temp_004, temp_005]     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  2. 合并相同主题                     │
│     - 相似度 > 80% 的合并            │
│     - 保留最新的 key_info            │
│     - 合并 tags                      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  3. 生成结构化记忆                   │
│     - 按主题生成 Session             │
│     - 添加会话元数据                 │
│     - 写入每日记忆文件               │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  4. 清理临时记忆                     │
│     - 删除已汇总的临时记忆           │
│     - 保留未汇总的（如果有）         │
└─────────────────────────────────────┘
```

#### 汇总示例

**输入：临时记忆**

```json
[
  {"trigger_keyword": "决定", "extracted_info": {"topic": "技术选型", "key_info": ["使用 FastAPI"]}},
  {"trigger_keyword": "配置", "extracted_info": {"topic": "API 配置", "key_info": ["前缀 /api/v2"]}},
  {"trigger_keyword": "使用", "extracted_info": {"topic": "技术选型", "key_info": ["数据库用 PostgreSQL"]}}
]
```

**输出：结构化记忆**

```markdown
# 2026-02-01 对话记忆

## Session 1 - 10:30:45

### 主题
技术选型与配置

### 关键信息
- 使用 FastAPI 框架
- 数据库用 PostgreSQL
- API 前缀 /api/v2

### 标签
#decision #config #api #database

---
```

#### 合并规则

| 规则 | 说明 | 示例 |
|------|------|------|
| **主题相似** | 相似度 > 80% 合并 | "技术选型" + "框架选择" → "技术选型" |
| **时间接近** | 10 分钟内的合并 | 10:30 + 10:35 → 同一 Session |
| **类别相同** | 同类别优先合并 | decision + decision → 合并 |
| **去重** | 完全相同的去重 | 重复的 key_info 只保留一个 |

#### 相似度计算

```python
def calculate_similarity(topic1, topic2):
    """
    计算两个主题的相似度
    使用关键词重叠率
    """
    words1 = set(jieba.cut(topic1))
    words2 = set(jieba.cut(topic2))
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union) if union else 0
```

### 6.5 配置选项

```json
{
  "save_trigger": {
    "enabled": true,
    "min_message_length": 10,
    "custom_keywords": {},
    "excluded_keywords": {}
  },
  "temp_memory": {
    "enabled": true,
    "retention_days": 30,
    "max_per_session": 50
  },
  "summarize": {
    "enabled": true,
    "similarity_threshold": 0.8,
    "time_window_minutes": 10,
    "auto_on_session_end": true,
    "auto_on_next_session": true
  }
}
```

## 七、实施计划

### 第一步：关键词触发（1-2 小时）

1. 更新 `memory-auto-retrieve.mdc` 规则文件
2. 添加关键词检测逻辑
3. 实现实时保存到临时记忆

### 第二步：临时记忆存储（1-2 小时）

1. 创建 `temp/` 目录结构
2. 实现临时记忆的读写
3. 实现保留时间清理

### 第三步：汇总机制（2-3 小时）

1. 实现主题相似度计算
2. 实现合并逻辑
3. 实现结构化记忆生成

### 第四步：会话 Hook（1-2 小时）

1. 创建 `hook.py` 脚本
2. 实现 `--init` 和 `--finalize`
3. 更新规则文件

## 八、确认事项

- [x] 方案选择：方案 D（混合方案）
- [x] 关键词列表：使用完整版
- [x] 自定义关键词：支持
- [x] 临时记忆保留时间：30 天
- [x] 汇总机制：已说明

是否开始实施？
