---
name: guide-info-passing
description: 指导设计 Prompt 之间传递信息的标准化机制（如 Agent 链、Skill 互引用）。涉及规范型（输出格式）、策略型（提取/转发逻辑）、知识型（接口规范）Facet。当设计 Prompt 间信息传递、优化通信流程、调试信息丢失问题时使用。
---

# Agent 信息传递机制

## 核心理念

**Sub Agent 之间不直接通信，所有信息通过 Super Agent 中转。**

这种模式确保：
- 信息流向清晰可控
- 便于调试和追踪
- 保持 Agent 职责单一

---

## Facet 定位

信息传递涉及**三个角色**和**多种 Facet 类型的协作**：

- **Producer（生产者）**：输出结构化信息的 Agent
- **Coordinator（协调者）**：提取、整理、转发信息的 Super Agent
- **Consumer（消费者）**：接收并使用信息的 Agent

三个角色分别关联不同的 Facet：

**Producer**：
- **规范型** facet — 定义输出格式（JSON 结构、标记格式）
- **边界型** facet — 数据完整性约束（必需字段、空值处理）

**Coordinator**：
- **策略型** facet — 提取、整理、转发的执行逻辑
- **知识型** facet — 理解 Sub Agent 的接口规范（知道从哪里提取什么）
- **边界型** facet — 转发约束（保持 JSON 不变、不修改内容）

**Consumer**：
- **知识型** facet — 理解输入格式（知道会收到什么、怎么解析）
- **策略型** facet — 根据接收的信息做决策

**共享 Facet**：
- **知识型** — 标记规范、命名约定（所有角色共享）

---

## 信息传递的三种方式

### 方式 1: 标记化 JSON 传递

**适用场景**：结构化数据

**标记格式**：
```
--- [信息类型] (JSON) ---
[JSON 数组或对象]
```


**关键要点**：
- 标记使用清晰的描述性名称
- JSON 必须完整可解析
- 通常放在 Agent 输出末尾

### 方式 2: 特殊代码块传递

**适用场景**：Agent 间的内部通信数据

**标记格式**：
````
```Remote_Agent_Request Inner
[JSON 结构]
```
````

**关键要点**：
- 用于 Sub Agent 需要传递给另一个 Sub Agent 的数据
- Super Agent 提取后传递给目标 Agent

### 方式 3: 自然语言提取

**适用场景**：执行结果总结、操作建议、纯文本输出

**工作方式**：
- Sub Agent 用自然语言输出结果
- Super Agent 从输出中提取关键信息
- 重新组织后传递给下一个 Agent

**示例**：
```
Sample_Data_Agent 输出：
"[1/15] user_email (varchar): john@example.com
 [2/15] phone (varchar): 1234567890"

Super Agent 提取：
- 字段列表：user_email, phone
- 示例值：john@example.com, 1234567890

传递给 Modify_Agent：
"字段: user_email, sampleValue: john@example.com"
```

## Producer Agent 设计规范

### 输出格式设计

**JSON 结构原则**：
- 使用清晰的字段名
- 区分必需字段和可选字段
- 保持结构一致性

**数据完整性**：
- 必需字段不能缺失
- 空值用 `null` 或空字符串明确表示
- 避免半成品数据

### 标记使用

**何时使用标记**：
- 数据需要被另一个 Agent 使用
- 需要与自然语言输出区分
- 格式固定且结构化

**标记命名约定**：
- 使用描述性名称（如 `Quality Issues`）
- 统一大小写风格（每个单词首字母大写）
- 避免歧义（说明是什么类型的数据）


### 在 Prompt 中说明

Producer Agent 的 prompt 应该明确说明：
- 使用什么标记格式
- JSON 结构的字段定义

**示例**：
```markdown
## 输出格式

检测完成后，输出质量问题的汇总 JSON：

```Remote_Agent_Request Inner
[
  {
    "logicalTableId": "表ID",
    "fieldName": "字段名",
    "issues": {
      "description": "描述问题（如果有）",
      "sampleValue": "示例值问题（如果有）"
    }
  }
]
```

**说明**：
- 只包含有问题的字段（无问题字段不输出）
```

---

## Coordinator (Super Agent) 设计规范

### 信息提取

**识别标记化信息**：
- 查找特定标记（如 `--- Quality Issues (JSON) ---`）
- 提取标记后的 JSON 内容
- 验证 JSON 格式完整性

**解析 JSON 结构**：
- 理解 JSON 的结构和字段含义
- 保存完整的 JSON 数据（不修改）

**提取自然语言关键点**：
- 从文本输出中识别关键信息
- 提取统计数据、状态、问题等
- 组织为结构化上下文

### 信息组织

**整理多源信息**：
- 合并来自不同 Agent 的信息
- 保持信息的完整性和准确性
- 按目标 Agent 的需求组织

**精简冗余数据**：
- 只传递目标 Agent 需要的信息
- 保持传递内容简洁

### 信息转发

**调用模板格式**：
```markdown
请使用中文回复。

--- Quality Issues (JSON) ---
{Quality_Checker 输出的 JSON}

用户意图: {具体请求}
```

**关键原则**：
- 使用相同的标记格式传递
- 保持 JSON 结构不变
- 添加必要的上下文说明

---

## Consumer Agent 设计规范

### 接收说明

在 Consumer Agent 的 prompt 中明确说明：
- 会接收什么类型的信息
- 信息的用途和如何使用

**示例**：
```markdown
## 输入格式

Super Agent 会以自然语言描述的方式提供信息，包含：
- 质量问题 JSON（`--- Quality Issues (JSON) ---` 部分）
```

### 解析处理

**识别标记信息**：
```markdown
如果收到质量 JSON：
- 遍历数组中的每个对象：`{"logicalTableId": "xxx", "fieldName": "xxx", "issues": {...}}`
- 根据 `issues.description` 判断该字段的描述是否有质量问题
- 根据 `issues.sampleValue` 判断该字段的示例值是否有质量问题
```

**缺失数据处理**：
```markdown
如果没有质量 JSON：不进行质量评估
```

### 使用方式

**根据信息做决策**：
- 质量问题存在 → 标记为 ⚠️（有质量问题）
- 字段缺失 → 标记为 ☐（未完成）
- 全部完成 → 标记为 ☑（已完成）

**与其他数据整合**：
- 结合字段的填写情况（是否有值）
- 结合质量检测结果（是否有问题）
- 综合判断字段状态

---

## 标记规范和命名约定

### 标记格式标准

**三横线标记**：
```
--- [信息类型] (JSON) ---
```

**代码块标记**：
````
```Remote_Agent_Request Inner
```
````

### 命名规则

**使用清晰描述**：
- ✅ `Quality Issues (JSON)` - 清楚知道是质量问题
- ❌ `Issues` - 太模糊，什么问题？

**统一大小写**：
- ✅ `Quality Issues (JSON)` - 每个单词首字母大写
- ❌ `quality issues (JSON)` - 不一致

**避免歧义**：
- ✅ `Field Statistics (JSON)` - 明确是字段统计
- ❌ `Statistics (JSON)` - 统计什么？

---

## 调试和优化指南

### 常见问题

**信息丢失**：
- 检查 Producer 是否输出了标记
- 检查 Coordinator 是否正确提取
- 检查 Consumer 是否正确解析

**格式不匹配**：
- Producer 输出的 JSON 结构与 Consumer 期望不一致
- 标记名称拼写错误
- JSON 格式不完整（缺少引号、逗号）

**解析失败**：
- JSON 语法错误
- 标记位置不正确（被文本截断）
- Consumer 的解析逻辑有误

### 调试技巧

**追踪信息流**：
1. 检查 Producer 的输出日志
2. 检查 Coordinator 是否提取到数据
3. 检查 Consumer 接收到的参数

**验证数据完整性**：
- Producer 输出的 JSON 是否完整
- Coordinator 转发时是否修改了内容
- Consumer 解析后的数据是否正确

**处理边界情况**：
- 数据为空时如何处理
- 数据格式异常时如何处理
- 部分字段缺失时如何处理

### 优化建议

**减少冗余传递**：
- 只传递必要的信息
- 删除已经提取的 extraData
- 精简 JSON 结构

**简化数据结构**：
- 扁平化嵌套过深的 JSON
- 使用清晰的字段名
- 避免冗余字段

**提升可读性**：
- 使用有意义的标记名称
- 添加注释说明数据用途
- 保持格式一致

---

## 设计检查清单

### Producer 设计检查

- [ ] JSON 结构清晰，字段命名合理
- [ ] 必需字段和可选字段明确区分
- [ ] 使用了正确的标记格式
- [ ] 在 prompt 中说明了输出会被传递给谁
- [ ] JSON 格式完整，可被解析

### Coordinator 设计检查

- [ ] 正确识别和提取标记化信息
- [ ] 保持 JSON 内容不变（不修改）
- [ ] 精简了冗余数据（如 extraData）
- [ ] 使用相同标记格式转发
- [ ] 添加了必要的上下文说明

### Consumer 设计检查

- [ ] 在 prompt 中说明会接收什么信息
- [ ] 正确识别标记化信息
- [ ] 处理了数据缺失的情况
- [ ] 根据接收的信息做出正确决策
- [ ] 与其他数据源正确整合

---

## 总结

**核心原则**：
1. Sub Agent 之间通过 Super Agent 中转信息
2. 使用标记化格式传递结构化数据
3. Producer 输出完整信息，Coordinator 原样转发，Consumer 正确解析

**Facet 协作关系**：
- Producer 的规范型 facet 定义输出格式
- Coordinator 的策略型 + 知识型 facet 驱动提取和转发
- Consumer 的知识型 facet 驱动解析和使用
- 标记规范是共享的知识型 facet

**三种传递方式**：
- 标记化 JSON（结构化数据）
- 特殊代码块（内部通信）
- 自然语言提取（文本输出）

**记住**：信息传递机制的目的是让 Agent 之间高效协作，保持信息流清晰可控。
