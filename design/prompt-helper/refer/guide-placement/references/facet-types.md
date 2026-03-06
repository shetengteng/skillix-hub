# Facet 类型定义

本文件是 Facet 概念的权威定义，被 `guide-placement` 和 `guide-diagnose` 共同引用。

---

## Facet：核心概念

**Facet（任务侧面）是 prompt 设计的基本单位。**

Facet = 模型需要理解的任务的一个独立方面。缺少某个 facet，模型就会在对应类型的输入上犯错。

**设计 prompt 的流程**：

1. 识别任务需要哪些 facet
2. 决定 facet 如何打包成 section
3. 决定 section 在 prompt 中的布局

**Facet 独立性原则**（UniPrompt, ACL Findings 2025 实证）：

- 每个 facet 对模型效果有**相对独立的贡献**——移除任一 facet，对应类型的准确率下降
- 将所有 facet 合并为一段摘要，准确率显著下降
- **推论**：facet 应保持为可识别的独立单元。合并不等于简化，合并等于丢信息

---

## Facet 功能型分类

**分类依据**：去掉这段信息，模型会犯什么类型的错？

### 六种功能类型

**定义型（Definition）**

模型需要理解自己是谁、做什么。缺失导致角色偏移、职责越界。

- 典型内容：角色定位、核心职责、职责边界、关键理解
- 实例：每个 Agent 的开头章节（角色定位、核心能力）

**知识型（Knowledge）**

模型需要领域背景才能正确处理。缺失导致领域错误、参数错误。

- 典型内容：术语对照、索引字段参考、数据格式、Agent 接口规范、Widget Schema
- 实例：Data_Discovery_Scout 的字段参考；Super Agent 的 Agent 接口规范

**场景型（Scenario）**

模型需要区分不同情况采取不同行动。缺失导致错误路由、场景混淆。

- 典型内容：意图识别、场景分支、处理方式判断（互斥逻辑）
- 实例：Super Agent V6 的场景 A-F；Suggestion Agent 的方式 1 vs 方式 2

**策略型（Strategy）**

模型需要知道具体怎么执行。缺失导致步骤遗漏、顺序错误。

- 典型内容：工作流程、执行步骤、处理逻辑、决策流程
- 实例：Classifier 的 5 步工作流程；Validator 的步骤 3.1-3.5

**边界型（Edge Case）**

模型需要避免在特定情况犯错。缺失导致边界处理错误、违规行为。

- 典型内容：禁止行为、特殊规则、空值处理、跳过规则、核心原则中的约束项
- 实例：Quality Checker 的空值处理；Classifier 的前缀匹配特殊规则

**规范型（Specification）**

模型需要知道输出长什么样。缺失导致格式错误、输出不可解析。

- 典型内容：输出格式、JSON 模板、进度格式、调用模板格式
- 实例：Validator 的 async_cui_callback JSON 格式；Guide Agent 的 Widget JSON Schema

### 关键说明

- 不是每个 prompt 都必须包含全部六种类型。单任务 Agent 可能没有显式场景型 facet
- 知识密集型 Agent 的知识型 facet 可能占 60-70%，这是正常的

### 归属维度

功能类型和归属是两个正交的维度：

- **专属 facet**：只和特定场景/Agent 相关。例：场景 A 的执行流程、Classifier 的跳过规则
- **共享 facet**：跨多个场景/Agent 通用。例：数据解析逻辑、JSON 精简步骤、语言传递规则

### 识别 facet 的方法

问自己：如果去掉这段内容，模型会在哪种情况下犯错？

- 去掉后模型角色偏移 → 定义型
- 去掉后模型领域知识错误 → 知识型
- 去掉后模型走错分支 → 场景型
- 去掉后模型步骤遗漏 → 策略型
- 去掉后模型在边界 case 犯错 → 边界型
- 去掉后模型输出格式错误 → 规范型
