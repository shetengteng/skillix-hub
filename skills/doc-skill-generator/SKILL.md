---
name: doc-skill-generator
description: |
  从文档（网页、PDF、本地文件）中提取内容，自动生成 Cursor Skill。
  使用 Playwright BFS 深度采集网页（含 SPA/Vue/React），支持 Tab 展开、折叠区域、懒加载、多页面遍历。
  两阶段流程：先提取到临时文件 → 确认后生成 Skill。
---

# Doc Skill Generator

从文档中提取内容，自动生成可用的 Cursor Skill。支持网页（含 SPA）、PDF、本地 Markdown/文本文件。

## 安装 / 更新

```bash
# 安装依赖
cd skills/doc-skill-generator && npm install

# 全局安装
node skills/doc-skill-generator/tool.js install '{"target":"~/.cursor/skills/doc-skill-generator"}'

# 更新
node skills/doc-skill-generator/tool.js update-self '{"target":"~/.cursor/skills/doc-skill-generator"}'
```

## 前置依赖

| 依赖 | 说明 |
|------|------|
| **Playwright Skill** | 网页深度采集引擎（BFS 遍历、Tab 展开、SPA 渲染） |
| **pdf-parse** | PDF 文件解析（npm 依赖，install 时自动安装） |

## 核心流程

```
1. fetch         → 采集文档，保存到临时文件
2. show          → 检查提取内容是否完整
3. analyze       → 分析文档类型，输出 Skill 规格建议
4. generate      → 生成到暂存目录（data/generated/）
5. install-skill → 从暂存目录安装到目标路径
```

## CLI 命令

```bash
node skills/doc-skill-generator/tool.js <command> '<JSON参数>'
```

### 采集

```bash
# 从网页采集（Playwright BFS 深度采集）
node tool.js fetch '{"sources":[{"type":"url","value":"https://docs.example.com"}]}'

# 从 PDF 采集
node tool.js fetch '{"sources":[{"type":"pdf","value":"./manual.pdf"}]}'

# 多文档源
node tool.js fetch '{"sources":[{"type":"url","value":"https://docs.example.com"},{"type":"pdf","value":"./guide.pdf"}]}'

# 单页面模式（不遍历子页面）
node tool.js fetch '{"sources":[{"type":"url","value":"https://example.com/api"}],"singlePage":true}'

# 控制采集深度和页面数
node tool.js fetch '{"sources":[{"type":"url","value":"https://docs.example.com"}],"maxDepth":2,"maxPages":20}'
```

### 管理提取结果

```bash
# 列出所有提取结果
node tool.js list-extracts '{}'

# 查看提取详情
node tool.js show-extract '{"id":"ext-xxx"}'

# 导出为 Markdown
node tool.js show-extract '{"id":"ext-xxx","format":"markdown"}'

# 追加采集（补充遗漏页面）
node tool.js append '{"id":"ext-xxx","sources":[{"type":"url","value":"https://docs.example.com/advanced"}]}'

# 删除提取结果
node tool.js delete-extract '{"id":"ext-xxx"}'
```

### 分析与生成

```bash
# 分析文档类型，输出 Skill 规格建议
node tool.js analyze '{"id":"ext-xxx"}'

# 预览将生成的 Skill 结构（不写文件）
node tool.js preview '{"id":"ext-xxx","skillName":"my-api-client"}'

# 生成 Skill（输出到暂存目录 data/generated/my-api-client/）
node tool.js generate '{"id":"ext-xxx","skillName":"my-api-client"}'

# 从暂存目录安装到目标路径
node tool.js install-skill '{"skillName":"my-api-client","target":"~/.cursor/skills/my-api-client"}'

# 更新已生成的 Skill（重新读取文档源 → 生成 → 安装）
node tool.js update '{"target":"~/.cursor/skills/my-api-client"}'
```

## 自主决策指南

| 场景 | 操作 |
|------|------|
| 用户给出文档 URL 或 PDF | 执行 `fetch` 采集 |
| 采集完成后 | 执行 `show-extract` 展示摘要，询问是否完整 |
| 用户确认内容完整 | 执行 `analyze` + `generate` |
| `generate` 完成后 | **读取 `skillMdPrompt`，在暂存目录创建 SKILL.md** |
| SKILL.md 创建完成 | 执行 `install-skill` 安装到目标路径 |
| 用户说"遗漏了某个页面" | 执行 `append` 追加采集 |
| 用户说"生成 Skill" | 执行 `generate` |
| 用户说"更新 Skill" | 执行 `update`（重新读取文档源） |

### generate → install-skill 两阶段流程

`generate` 命令将结果输出到暂存目录（`data/generated/{skillName}/`），**不会** 直接写到目标路径。
返回结果中的 `skillMdPrompt` 字段包含 SKILL.md 创建指引，Agent 需要：

1. 读取 `skillMdPrompt` 中提到的关键文档文件（在暂存目录的 `docs/` 下）
2. 理解文档内容后，在暂存目录撰写高质量的 SKILL.md
3. 执行 `install-skill` 将暂存目录安装到最终目标路径

## 数据存储

数据存在 Skill 安装目录的同级 `doc-skill-generator-data/` 下：

```
~/.cursor/skills/
├── doc-skill-generator/           # Skill 代码
└── doc-skill-generator-data/      # 数据目录
    ├── extracts/                  # 提取结果（临时文件）
    ├── cache/                     # 文档缓存
    ├── specs/                     # Skill 规格
    └── generated/                 # 生成暂存（generate 输出）
```

## 自然语言使用示例

### 示例 1：从 API 文档生成 Skill

```
用户: 帮我读一下 https://docs.stripe.com/api 生成一个 Skill

Agent:
  1. fetch → Playwright BFS 采集（snapshot → LLM 分析导航 → 遍历子页面）
  2. show-extract → 展示摘要："共 45 页，128 个代码块"
  3. 用户确认 → analyze + generate（输出到暂存目录）
  4. 根据 skillMdPrompt 创建 SKILL.md
  5. install-skill → 安装到 ~/.cursor/skills/stripe-api/
```

### 示例 2：从 PDF 生成 Skill

```
用户: 这个 PDF 是设备控制手册，帮我生成 Skill
     [附件: device-manual.pdf]

Agent:
  1. fetch → PDF 解析，提取 120 页内容
  2. show-extract → 展示摘要
  3. analyze → 识别为 CLI Reference
  4. generate → 生成到暂存目录
  5. install-skill → 安装 device-controller Skill
```

### 示例 3：追加采集

```
用户: 好像少了高级配置那部分

Agent:
  1. append → 追加采集 https://docs.example.com/advanced
  2. show-extract → 更新后的摘要
  3. 用户确认 → generate + install-skill
```

## 触发词

- 读取文档、从文档生成 Skill
- 采集网页、抓取页面内容
- 从 PDF 生成、解析 PDF
- 生成 API 客户端、生成 CLI 封装
- 更新 Skill、重新读取文档
