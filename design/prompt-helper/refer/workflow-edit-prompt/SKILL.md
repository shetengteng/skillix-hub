---
name: workflow-edit-prompt
description: Prompt 编辑指南。诊断→读取指南→设计方案→修改→自检的完整流程。当修改、修复或优化 prompt 文件时使用。
---

# Prompt 编辑指南

## 硬约束

此工作流依赖 `.cursor/skills/` 中的专业方法论知识。你自带的 prompt engineering 知识**不能替代** skill 文件。

- 每个阶段必须通过 Read 工具加载对应的 skill 文件，不允许凭记忆操作
- 向用户汇报方案时，必须引用 skill 中的具体原则
- 不确定该读哪个 skill 时，根据 `available_skills` 列表中各 skill 的 description 判断

---

按以下流程修改 `prompt/` 目录下的 Prompt 文件。每个阶段完成后再进入下一阶段，不允许跳过。

## 阶段 0：确认是否需要先诊断

向用户确认：当前的修改需求是否源于**行为问题**（如模型做错了、输出不对、走错分支）。

- 如果用户确认是行为问题，先读取 `guide-diagnose/SKILL.md`，按其流程诊断并向用户报告结论，确认后进入阶段 1
- 如果用户确认不是行为问题（需求明确），直接进入阶段 1

## 阶段 1：读取 Skill + 设计方案

1. 读取目标 Prompt 文件
2. 读取 `guide-skeleton/SKILL.md` 和 `guide-placement/SKILL.md`（任何修改都涉及结构和布局，必读）
3. 根据修改类型，读取对应的 guide skill
4. 基于 skill 中的原则设计修改方案，方案需包含：
   - 修改内容和理由（引用 skill 原则）
   - 影响范围评估：修改会影响哪些 section、引用关系、功能链条
5. 向用户说明方案并等待确认

## 阶段 2：执行修改

按确认的方案执行修改。

## 阶段 3：修改后自检

修改完成后**自动执行**，不需要用户要求，不允许跳过：

1. 读取 `workflow-review-edit/SKILL.md`，按其清单逐项检查，发现问题立即修正
2. 向用户报告评审结果

---

## 与其他 Skill 的关系

- `@guide-diagnose` — 阶段 0 行为诊断
- `@guide-skeleton` — 阶段 1 必读，整体结构设计
- `@guide-placement` — 阶段 1 必读，信息布局设计
- `@guide-scenario` / `@guide-output` / `@guide-example` / `@guide-info-passing` — 阶段 1 按需读取
- `@workflow-review-edit` — 阶段 3 修改评审
- `@workflow-audit-prompt` — 全面质量检查（由 audit-prompt command 触发）
