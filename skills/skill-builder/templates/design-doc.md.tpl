# {{Name}} — 设计文档

## 1. 需求

### 1.1 背景

TODO: 描述背景和动机。

### 1.2 目标

TODO: 列出核心目标。

### 1.3 使用场景

| 场景 | 触发方式 | 说明 |
|------|----------|------|
| TODO | TODO | TODO |

## 2. 整体流程

```mermaid
flowchart TD
    Start[开始] --> TODO[TODO]
    TODO --> End_[结束]
```

## 3. 技术方案

### 3.1 方案 A：TODO（推荐）

**原理**：TODO

**优点**：
- TODO

**缺点**：
- TODO

### 3.2 方案对比

| 维度 | A | B |
|------|---|---|
| TODO | TODO | TODO |

## 4. 推荐方案

### 4.1 架构

TODO: 架构图和说明。

### 4.2 CLI 命令设计

```bash
node skills/{{name}}/tool.js <命令> '<JSON参数>'
```

### 4.3 输出格式

```json
{
  "result": {},
  "error": null
}
```

### 4.4 目录结构

```
skills/{{name}}/
├── SKILL.md
├── tool.js
├── package.json
└── lib/
    └── TODO.js
```

## 5. 实现计划

### Phase 1：核心功能（MVP）

- TODO

### Phase 2：增强功能

- TODO

## 6. 风险与注意事项

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| TODO | TODO | TODO |
