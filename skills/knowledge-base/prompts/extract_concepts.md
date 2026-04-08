你是知识库编译器。请分析以下资料，提取关键概念并建立关系。

## 待分析资料

{{pending_list}}

## 已有概念（避免重复）

{{existing_concepts}}

## 编译规则

1. **概念粒度**：每个概念是一个可独立理解的知识单元
   - 避免过于宏观（如"软件工程"）
   - 避免过于微观（如"某个变量名"）
   - 好的粒度示例：Memory 四层架构、渐进式披露模式、Hook 触发机制

2. **概念提取**：从资料中识别核心概念，为每个概念创建条目
   - 同一概念在多个资料中出现时，合并为一个条目
   - 标注该概念来自哪些资料（sources 字段）
   - 识别概念间的关系（related 字段）

3. **条目格式**：每个概念写一个 Markdown 文件，写入 `skills/knowledge-base-data/wiki/concepts/` 目录

```markdown
---
id: concept-简短英文ID
title: 概念名称（中文）
category: 所属分类
tags: [标签1, 标签2]
sources: [来源ID1, 来源ID2]
related: [concept-关联ID1, concept-关联ID2]
updated_at: 当前ISO时间
---

# 概念名称

一段话概要（50-100字）。

## 核心要点

- 要点 1
- 要点 2
- 要点 3

## 关联概念

- [[关联概念名]] — 关系说明

## 来源资料

- [资料标题](source://来源ID)
```

4. **控制篇幅**：每个条目 200-500 字，聚焦核心信息
5. **内部链接**：用 `[[概念名]]` 语法引用其他概念

## 输出

逐个创建概念条目文件。完成后执行：
```bash
python3 skills/knowledge-base/main.py compile --finalize
```
