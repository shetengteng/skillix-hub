---
name: api-tracer
description: 录制和分析浏览器网络请求。通过 CDP 连接 Playwright 浏览器实例，捕获所有 API 请求的完整信息（URL、headers、cookie、请求体、响应体），生成分析报告用于后期自动化。
---

# API Tracer

录制浏览器中的网络请求，分析 API 端点，生成可用于自动化的报告。

## 安装

首次使用前，在 skill 目录下执行：

```bash
cd skills/api-tracer && npm install
```

## 前置条件

需要 Playwright Skill 已启动浏览器。API Tracer 通过 CDP 连接到同一浏览器实例。

## 使用方式

所有命令格式：

```bash
node skills/api-tracer/tool.js <命令> '<JSON参数>'
```

## 核心工作流

### 1. 启动录制

```bash
node skills/api-tracer/tool.js start '{"name": "my-session"}'
```

可选参数：
- `name`：会话名称（默认自动生成）
- `filter`：URL 过滤关键词，只录制包含此关键词的请求
- `wsEndpoint`：手动指定浏览器 WebSocket 地址

### 2. 操作页面

录制启动后，通过 Playwright Skill 操作页面或手动在浏览器中操作：

```bash
node skills/playwright/tool.js navigate '{"url":"https://example.com"}'
node skills/playwright/tool.js click '{"ref":"e5","element":"登录按钮"}'
```

所有网络请求会被自动捕获。

### 3. 查看录制状态

```bash
node skills/api-tracer/tool.js status '{}'
```

### 4. 停止录制

```bash
node skills/api-tracer/tool.js stop '{}'
```

停止后数据自动保存。

### 5. 查看录制结果

列出所有请求：
```bash
node skills/api-tracer/tool.js detail '{"name": "my-session"}'
```

按 URL 过滤：
```bash
node skills/api-tracer/tool.js detail '{"name": "my-session", "filter": "api/"}'
```

查看单个请求详情（含 headers、body）：
```bash
node skills/api-tracer/tool.js detail '{"name": "my-session", "index": 0}'
```

### 6. 生成分析报告

JSON 格式：
```bash
node skills/api-tracer/tool.js report '{"name": "my-session"}'
```

Markdown 格式：
```bash
node skills/api-tracer/tool.js report '{"name": "my-session", "format": "markdown"}'
```

curl 命令导出：
```bash
node skills/api-tracer/tool.js report '{"name": "my-session", "format": "curl"}'
```

## 命令参考

| 命令 | 说明 |
|------|------|
| `start` | 启动录制（后台 daemon） |
| `stop` | 停止录制并保存 |
| `status` | 查看录制状态 |
| `sessions` | 列出所有历史会话 |
| `detail` | 查看会话的请求列表或单个请求详情 |
| `report` | 生成分析报告（json/markdown/curl） |
| `delete` | 删除历史会话 |

## 自然语言交互指南

| 用户说 | 执行 |
|--------|------|
| "开始录制网络请求" | `start '{"name": "session-name"}'` |
| "只录制 API 请求" | `start '{"name": "session-name", "filter": "api/"}'` |
| "停止录制" | `stop '{}'` |
| "录制状态" / "在录制吗" | `status '{}'` |
| "看看录制了什么" | `detail '{"name": "session-name"}'` |
| "看看第 3 个请求的详情" | `detail '{"name": "session-name", "index": 2}'` |
| "生成 API 报告" | `report '{"name": "session-name", "format": "markdown"}'` |
| "导出为 curl" | `report '{"name": "session-name", "format": "curl"}'` |
| "有哪些录制" | `sessions '{}'` |
| "删除这个录制" | `delete '{"name": "session-name"}'` |

## 报告内容

分析报告包含：
- API 端点列表（自动去重）
- 每个端点的 HTTP 方法、URL 模式
- 请求头（重要字段）
- Cookie 列表
- 请求体格式和 schema
- 响应体格式和 schema
- 认证方式自动识别（Bearer Token / API Key 等）

## 典型场景

**场景：分析一个网站的 API 接口**

```bash
# 1. 用 Playwright 打开网站
node skills/playwright/tool.js navigate '{"url":"https://app.example.com"}'

# 2. 启动 API 录制
node skills/api-tracer/tool.js start '{"name": "example-api", "filter": "api/"}'

# 3. 通过 Playwright 操作页面（登录、浏览等）
node skills/playwright/tool.js fillForm '{"fields":[...]}'
node skills/playwright/tool.js click '{"ref":"e5","element":"登录"}'

# 4. 停止录制
node skills/api-tracer/tool.js stop '{}'

# 5. 生成报告
node skills/api-tracer/tool.js report '{"name": "example-api", "format": "markdown"}'
```
