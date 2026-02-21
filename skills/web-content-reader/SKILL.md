---
name: web-content-reader
description: 读取网页内容，支持 SPA 页面自动检测与浏览器渲染降级。当普通 HTTP fetch 无法获取 Vue/React 等 SPA 页面的渲染数据时，自动通过 Playwright 浏览器获取完整内容。当用户需要读取网页数据、提取页面内容、或 WebFetch 工具返回空内容时使用。
---

# Web Content Reader

读取任意网页的渲染后内容。自动检测 SPA 页面，在 HTTP fetch 失败时降级到浏览器渲染。

## 安装

首次使用前，在 skill 目录下执行：

```bash
cd skills/web-content-reader && npm install
```

浏览器渲染模式需要系统已安装 Chrome/Chromium。如果未安装，可通过 Playwright 安装：

```bash
npx playwright install chromium
```

本 Skill 完全独立，不依赖其他 Skill。如果系统已有 Playwright Skill 启动的浏览器实例，会自动复用以节省资源。

## 使用方式

所有命令格式：

```bash
node skills/web-content-reader/tool.js <命令> '<JSON参数>'
```

## 核心工作流

### 自动模式（推荐）

先尝试 HTTP fetch，检测到 SPA 空壳时自动降级到浏览器渲染：

```bash
node skills/web-content-reader/tool.js read '{"url":"https://example.com"}'
```

### 强制浏览器模式

已知是 SPA 页面时，跳过 fetch 直接用浏览器渲染：

```bash
node skills/web-content-reader/tool.js read '{"url":"https://spa-app.com","mode":"browser"}'
```

### 仅 fetch 模式

只需要静态 HTML 内容时：

```bash
node skills/web-content-reader/tool.js read '{"url":"https://example.com","mode":"fetch"}'
```

### 提取特定区域

使用 CSS 选择器提取页面局部内容：

```bash
node skills/web-content-reader/tool.js read '{"url":"https://example.com","selector":".main-content"}'
```

### 输出格式控制

```bash
# 纯文本（默认）
node skills/web-content-reader/tool.js read '{"url":"https://example.com","output":"text"}'

# 含 HTML
node skills/web-content-reader/tool.js read '{"url":"https://example.com","output":"html"}'

# 全部数据（含表格、链接、元信息）
node skills/web-content-reader/tool.js read '{"url":"https://example.com","output":"json"}'
```

### 自定义等待条件

浏览器模式下等待特定元素出现：

```bash
node skills/web-content-reader/tool.js read '{"url":"https://spa-app.com","mode":"browser","waitSelector":".data-loaded"}'
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | string | 必填 | 目标页面 URL |
| `mode` | string | `auto` | `auto`：自动检测 / `fetch`：仅 HTTP / `browser`：仅浏览器 |
| `selector` | string | - | CSS 选择器，提取页面特定区域 |
| `output` | string | `text` | `text`：标题+文本 / `html`：含 HTML / `json`：全部数据 |
| `waitSelector` | string | - | 浏览器模式下等待此选择器出现 |
| `timeout` | number | `15000` | 浏览器渲染超时（ms） |

## 输出格式

所有命令返回 JSON：

```json
{
  "result": {
    "title": "页面标题",
    "content": "提取的纯文本内容",
    "html": "<div>...</div>",
    "tables": [{"headers": ["列1"], "rows": [["值1"]]}],
    "links": [{"text": "链接文本", "href": "https://..."}],
    "meta": {"description": "...", "ogTitle": "...", "ogImage": "..."}
  },
  "method": "fetch|browser",
  "url": "https://example.com",
  "elapsed": 1234,
  "error": null
}
```

`output` 参数控制 `result` 中返回的字段：
- `text`：`title` + `content` + `meta`
- `html`：以上 + `html`
- `json`：以上 + `tables` + `links`

## 自然语言交互指南

| 用户说 | 执行 |
|--------|------|
| "读取这个页面的内容" / "帮我看看这个网页" | `read '{"url":"..."}'` |
| "这个页面 fetch 读不到数据" / "这是个 Vue 页面" | `read '{"url":"...","mode":"browser"}'` |
| "提取页面的表格数据" | `read '{"url":"...","output":"json"}'` |
| "只看 .content 区域的内容" | `read '{"url":"...","selector":".content"}'` |
| "获取页面的所有链接" | `read '{"url":"...","output":"json"}'` → 从 `links` 字段读取 |

## Agent 自动降级说明

当 Agent 使用 WebFetch 工具获取 URL 内容时，如果返回结果为空或明显是 SPA 空壳，应自动调用此 Skill：

```bash
node skills/web-content-reader/tool.js read '{"url":"<目标URL>","mode":"browser"}'
```

判断 WebFetch 结果需要降级的信号：
- 返回内容几乎为空
- 内容仅包含 `<div id="app"></div>` 等框架占位符
- 用户明确说"这个页面需要打开浏览器才能看到数据"

## 工作原理

1. **HTTP Fetch**：发送 HTTP 请求获取原始 HTML
2. **SPA 检测**：分析 HTML 特征（空 body、框架占位符、noscript 提示等）
3. **浏览器渲染**：通过 playwright-core 打开页面，等待 JS 渲染完成（优先复用已有浏览器实例）
4. **内容提取**：使用 cheerio 解析 HTML，提取文本、表格、链接、元信息
