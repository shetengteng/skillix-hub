---
id: "{{topic-slug}}"
title: "{{主题标题}}"
tags: [{{标签1}}, {{标签2}}]
sources:
  - {{source/path/to/file.md}}
relations:
  related: []
  depends_on: []
created: "{{YYYY-MM-DD}}"
updated: "{{YYYY-MM-DD}}"
compile_count: 1
---

# {{主题标题}}

> 一句话定义或概述。

## 概要
<!-- coverage: ? -->

全面概述（5-10 句）。涵盖：是什么、为什么重要、在系统中的定位、关键特征。
保留源材料中的具体细节（字段名、路径、数据格式）。

<!-- mermaid: 每篇文章至少 1 个 mermaid 图表。放在最能帮助理解的位置。 -->
<!-- 适用场景：流程用 flowchart，组件关系用 graph，状态转换用 stateDiagram-v2 -->

## 关键决策
<!-- coverage: ? -->

从源材料中提取所有设计决策、权衡和架构选择。
每条决策：做出的选择 + 理由 + 考虑过的替代方案。目标 3-8 条。

- **决策:** 选择理由。
  [source: source/path/to/file.md]

## 当前状态
<!-- coverage: ? -->

完整的当前实现状态。包含数据模型、API 端点、配置、数据库 schema。
不要过度概括——保留字段名、类型、端点路径、SQL schema、代码示例等具体信息。

## 注意事项
<!-- coverage: ? -->

所有陷阱、边界情况、非直觉行为。逐条列出。

## 待解决问题
<!-- coverage: ? -->

仅列出源材料中真正未解决的问题。不要编造。

## 相关概念
- [[related-concept-slug]]

## 来源
{{#each sources}}
- [source: {{this}}]
{{/each}}
