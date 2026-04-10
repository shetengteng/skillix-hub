# 概念文章编译 Prompt

你需要基于一组来源文件，合成一篇结构化的概念文章。

## 输出格式

YAML frontmatter + Markdown 正文，包含以下 Section：
- Summary（概述）
- Key Decisions（关键决策和取舍）
- Current State（当前状态）
- Gotchas（常见陷阱）
- Open Questions（未解决问题）
- Related（相关概念）
- Sources（来源列表）

## 覆盖度标记

在每个 Section 标题下一行添加 HTML 注释：
- `<!-- coverage: high -->` — 多个来源一致描述
- `<!-- coverage: medium -->` — 单一来源或部分覆盖
- `<!-- coverage: low -->` — 推断，来源无直接论述

## 来源引用

引用具体信息时标注：`[source: raw/path/to/file.md]`

## 保留用户编辑

如果已有文章中存在没有 `[source: ...]` 标注的段落，这些是用户手动添加的内容，必须原样保留。
