# 行为模式提取方案对比

> **日期**: 2026-01-31
> **目标**: 设计 AI 友好的行为模式格式，以及定期提取行为模式的方案

## 一、问题背景

### 1.1 核心问题

1. **如何让 AI 方便读懂行为模式**：格式设计需要考虑 AI 的理解能力
2. **何时提取行为模式**：定期提取 vs 实时提取
3. **提取什么内容**：哪些信息对 AI 预测最有价值

### 1.2 设计原则

根据之前的设计文档，核心原则是：
- **大模型驱动**：充分利用 AI 的语义理解能力
- **数据存储用脚本**：Python 脚本负责数据读写和简单统计
- **智能分析用大模型**：复杂的分类、识别、预测交给大模型

## 二、AI 友好的行为模式格式

### 2.1 设计目标

| 目标 | 说明 |
|------|------|
| **易读性** | AI 能快速理解用户习惯 |
| **结构化** | 便于 AI 提取关键信息 |
| **上下文丰富** | 提供足够的背景信息 |
| **可操作** | AI 能直接用于预测和建议 |

### 2.2 格式对比：JSON vs Markdown

| 维度 | JSON 格式 | Markdown 格式 |
|------|-----------|---------------|
| **机器可读性** | ⭐⭐⭐⭐⭐ 完美 | ⭐⭐⭐ 需要解析 |
| **人类可读性** | ⭐⭐⭐ 一般 | ⭐⭐⭐⭐⭐ 优秀 |
| **AI 理解能力** | ⭐⭐⭐⭐⭐ 结构清晰 | ⭐⭐⭐⭐ 需要推断结构 |
| **数据提取** | ⭐⭐⭐⭐⭐ 直接访问 | ⭐⭐⭐ 需要正则/解析 |
| **扩展性** | ⭐⭐⭐⭐⭐ 易于添加字段 | ⭐⭐⭐ 格式不固定 |
| **存储效率** | ⭐⭐⭐⭐ 较紧凑 | ⭐⭐⭐ 有格式开销 |

**推荐：JSON 格式 + 自然语言描述字段**

理由：
1. **AI 可以直接解析**：JSON 结构清晰，AI 可以直接访问字段
2. **自然语言增强理解**：在 JSON 中嵌入 `description` 字段，提供自然语言解释
3. **程序可处理**：脚本可以直接读写 JSON，无需复杂解析
4. **版本兼容**：JSON 易于添加新字段，保持向后兼容

### 2.3 推荐格式：自然语言 + 结构化数据

```json
{
  "summary": {
    "description": "这是一个活跃了 15 天的用户，主要从事 API 开发和测试工作",
    "total_sessions": 50,
    "total_actions": 500,
    "main_activities": ["API 开发", "单元测试", "文档编写"]
  },
  
  "behavior_patterns": {
    "description": "用户的典型工作流程是：设计 → 实现 → 测试 → 提交",
    "common_sequences": [
      {
        "pattern": "创建设计文档 → 创建 API 文件 → 运行测试",
        "frequency": "高（出现 12 次）",
        "suggestion": "当用户创建设计文档后，可以主动询问是否需要创建 API 文件"
      },
      {
        "pattern": "修改 API → 运行测试 → Git 提交",
        "frequency": "高（出现 8 次）",
        "suggestion": "当用户修改 API 后，可以主动运行测试"
      }
    ]
  },
  
  "predictions": {
    "description": "基于历史数据的预测规则",
    "rules": [
      {
        "when": "用户创建 API 文件后",
        "then": "85% 概率会运行测试",
        "action": "主动询问：要运行测试验证一下吗？"
      },
      {
        "when": "用户运行测试通过后",
        "then": "68% 概率会提交代码",
        "action": "建议：测试通过了，要提交代码吗？"
      }
    ]
  },
  
  "preferences": {
    "description": "用户的偏好设置",
    "file_types": ["Python (.py)", "JavaScript (.js)", "Markdown (.md)"],
    "work_style": "先设计后实现",
    "testing_habit": "每次修改后都会运行测试"
  }
}
```

### 2.4 格式特点

| 特点 | 说明 |
|------|------|
| **自然语言描述** | 每个部分都有 `description` 字段，用自然语言总结 |
| **可操作建议** | 直接给出 AI 应该如何行动的建议 |
| **频率标注** | 使用"高/中/低"而非纯数字，更易理解 |
| **上下文完整** | 包含用户画像、行为模式、预测规则 |

### 2.5 为什么不用 Markdown

虽然 Markdown 对人类更友好，但对于行为预测场景，JSON 更合适：

```markdown
# 不推荐：Markdown 格式

## 用户画像
- 活跃天数：15 天
- 总动作数：500

## 行为模式
1. 创建文件 → 运行测试（出现 12 次）
2. 修改 API → 运行测试 → 提交（出现 8 次）
```

**问题**：
1. AI 需要解析 Markdown 结构，可能出错
2. 数据提取不可靠（格式可能变化）
3. 无法直接用于程序处理

**结论**：使用 JSON 格式，在 `description` 字段中嵌入自然语言，兼顾机器可读性和人类可读性。

## 三、行为模式提取方案对比

### 方案 A：会话结束时提取（推荐）

```
┌─────────────────────────────────────────────────────────────┐
│                     方案 A：会话结束时提取                    │
├─────────────────────────────────────────────────────────────┤
│  会话开始 → 加载已有模式                                      │
│  会话过程 → 累积动作                                          │
│  会话结束 → 写入动作 + 重新计算模式 + 保存                     │
└─────────────────────────────────────────────────────────────┘
```

**优点**：
- 模式始终是最新的
- 实现简单，复用现有 hook
- 不需要额外的定时任务

**缺点**：
- 会话结束时计算量较大
- 如果会话很长，可能有延迟

**实现方式**：
```python
# hook.py --finalize 时
def finalize_hook(session_data):
    # 1. 写入动作
    batch_record_actions(session_data["actions"])
    
    # 2. 重新计算行为模式
    patterns = extract_behavior_patterns()
    
    # 3. 更新用户画像
    profile = update_user_profile()
    
    # 4. 保存到文件
    save_patterns(patterns)
    save_profile(profile)
```

### 方案 B：定时提取（每日/每周）

```
┌─────────────────────────────────────────────────────────────┐
│                     方案 B：定时提取                          │
├─────────────────────────────────────────────────────────────┤
│  会话开始 → 加载已有模式（可能是昨天的）                       │
│  会话过程 → 累积动作                                          │
│  会话结束 → 只写入动作                                        │
│  每日凌晨 → 定时任务重新计算所有模式                           │
└─────────────────────────────────────────────────────────────┘
```

**优点**：
- 会话结束时响应快
- 可以做更复杂的分析（全量数据）
- 不影响用户体验

**缺点**：
- 需要配置定时任务（cron）
- 模式可能不是最新的
- 实现复杂度高

**实现方式**：
```bash
# crontab 配置
0 2 * * * python3 ~/.cursor/skills/behavior-prediction/scripts/extract_patterns.py --full
```

### 方案 C：增量提取（混合方案）

```
┌─────────────────────────────────────────────────────────────┐
│                     方案 C：增量提取                          │
├─────────────────────────────────────────────────────────────┤
│  会话开始 → 加载已有模式                                      │
│  会话过程 → 累积动作                                          │
│  会话结束 → 写入动作 + 增量更新模式（只更新变化的部分）         │
│  每周一次 → 全量重新计算（修正累积误差）                       │
└─────────────────────────────────────────────────────────────┘
```

**优点**：
- 会话结束时响应快
- 模式基本是最新的
- 定期全量计算保证准确性

**缺点**：
- 实现最复杂
- 需要维护增量更新逻辑

**实现方式**：
```python
# hook.py --finalize 时
def finalize_hook(session_data):
    # 1. 写入动作
    batch_record_actions(session_data["actions"])
    
    # 2. 增量更新模式（只更新本次会话涉及的转移）
    incremental_update_patterns(session_data["actions"])

# 每周定时任务
def full_recalculate():
    # 全量重新计算所有模式
    patterns = extract_behavior_patterns_full()
    save_patterns(patterns)
```

### 方案对比表

| 维度 | 方案 A（会话结束） | 方案 B（定时） | 方案 C（增量） |
|------|-------------------|----------------|----------------|
| **实时性** | ⭐⭐⭐⭐⭐ 最新 | ⭐⭐⭐ 可能滞后 | ⭐⭐⭐⭐ 基本最新 |
| **性能** | ⭐⭐⭐ 会话结束时较慢 | ⭐⭐⭐⭐⭐ 会话结束快 | ⭐⭐⭐⭐ 会话结束较快 |
| **实现复杂度** | ⭐⭐⭐⭐⭐ 简单 | ⭐⭐⭐ 需要 cron | ⭐⭐ 最复杂 |
| **准确性** | ⭐⭐⭐⭐⭐ 高 | ⭐⭐⭐⭐⭐ 高 | ⭐⭐⭐⭐ 可能有累积误差 |
| **维护成本** | ⭐⭐⭐⭐⭐ 低 | ⭐⭐⭐ 需要维护定时任务 | ⭐⭐ 需要维护两套逻辑 |

## 四、推荐方案

### 4.1 推荐：方案 A（会话结束时提取）

**理由**：
1. **实现简单**：复用现有 hook，不需要额外配置
2. **实时性好**：每次会话结束都更新，模式始终最新
3. **维护成本低**：不需要维护定时任务
4. **准确性高**：每次都是全量计算，没有累积误差

**性能优化**：
- 如果数据量大，可以只计算最近 30 天的数据
- 使用缓存，只在数据变化时重新计算

### 4.2 实现细节

```python
# hook.py --finalize
def finalize_hook(session_data):
    # 1. 写入动作
    record_result = batch_record_actions(session_data["actions"])
    
    # 2. 提取行为模式（只计算最近 30 天）
    patterns = extract_behavior_patterns(days=30)
    
    # 3. 更新用户画像
    profile = update_user_profile()
    
    # 4. 生成 AI 友好的格式
    ai_friendly = generate_ai_friendly_format(patterns, profile)
    
    # 5. 保存
    save_json(DATA_DIR / "patterns" / "behavior_patterns.json", patterns)
    save_json(DATA_DIR / "patterns" / "user_profile.json", profile)
    save_json(DATA_DIR / "patterns" / "ai_summary.json", ai_friendly)
    
    return {
        "status": "success",
        "recorded_count": record_result["recorded_count"],
        "patterns_updated": True
    }
```

### 4.3 AI 友好格式生成

```python
def generate_ai_friendly_format(patterns, profile):
    """生成 AI 友好的行为模式格式"""
    
    # 生成自然语言描述
    summary_desc = f"这是一个活跃了 {profile['stats']['active_days']} 天的用户"
    
    # 生成常见序列描述
    sequences = []
    for seq in patterns["common_sequences"][:5]:
        freq = "高" if seq["count"] >= 10 else "中" if seq["count"] >= 5 else "低"
        sequences.append({
            "pattern": seq["description"],
            "frequency": f"{freq}（出现 {seq['count']} 次）",
            "suggestion": generate_suggestion(seq)
        })
    
    # 生成预测规则
    rules = []
    for t in patterns["top_transitions"][:5]:
        prob = int(t["probability"] * 100)
        rules.append({
            "when": f"用户执行 {t['from']} 后",
            "then": f"{prob}% 概率会执行 {t['to']}",
            "action": generate_action_suggestion(t, prob)
        })
    
    return {
        "summary": {
            "description": summary_desc,
            "total_sessions": profile["stats"]["total_sessions"],
            "total_actions": profile["stats"]["total_actions"],
            "main_activities": profile["preferences"]["common_purposes"]
        },
        "behavior_patterns": {
            "description": "用户的典型工作流程",
            "common_sequences": sequences
        },
        "predictions": {
            "description": "基于历史数据的预测规则",
            "rules": rules
        },
        "preferences": {
            "description": "用户的偏好设置",
            "file_types": profile["preferences"]["common_file_types"],
            "work_style": infer_work_style(profile)
        }
    }


def generate_suggestion(seq):
    """根据序列生成建议"""
    steps = seq["sequence"]
    if len(steps) >= 2:
        return f"当用户执行 {steps[0]} 后，可以主动询问是否需要执行 {steps[1]}"
    return ""


def generate_action_suggestion(transition, prob):
    """根据转移概率生成行动建议"""
    if prob >= 85:
        return f"主动执行：{transition['to']}"
    elif prob >= 70:
        return f"主动询问：要执行 {transition['to']} 吗？"
    else:
        return f"建议：你可能想执行 {transition['to']}"


def infer_work_style(profile):
    """推断用户的工作风格"""
    task_flow = profile["preferences"]["preferred_task_flow"]
    if "design" in task_flow and task_flow.index("design") < task_flow.index("implement"):
        return "先设计后实现"
    return "边做边改"
```

## 五、总结

### 5.1 推荐方案

**方案 A（会话结束时提取）** + **AI 友好格式**

### 5.2 核心要点

1. **格式设计**：使用自然语言 + 结构化数据的混合格式
2. **提取时机**：每次会话结束时提取，保证实时性
3. **性能优化**：只计算最近 30 天的数据
4. **AI 友好**：生成包含建议的格式，AI 可以直接使用

### 5.3 下一步

1. 实现 `generate_ai_friendly_format()` 函数
2. 更新 `hook.py --finalize` 调用该函数
3. 更新 `hook.py --init` 返回 AI 友好格式
4. 更新规则文件，指导 AI 如何使用这些信息
