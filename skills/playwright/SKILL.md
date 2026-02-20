---
name: playwright
description: 通过 Playwright 实现浏览器自动化。导航页面、点击元素、填写表单、截图、执行 JavaScript、管理 Cookie/存储、拦截网络请求等。当用户需要自动化浏览器、测试网页、抓取内容或与任何 Web UI 交互时使用。
---

# Playwright 浏览器自动化

通过 48 个工具控制真实浏览器（Chrome/Chromium）。每个工具通过 CLI 调用。

## 安装

首次使用前，在 skill 目录下执行一次：

```bash
cd skills/playwright && npm install && npx playwright install chromium
```

## 使用方式

所有命令遵循以下格式：

```bash
node skills/playwright/tool.js <命令> '<JSON参数>'
```

## 核心工作流

### 1. 导航到页面

```bash
node skills/playwright/tool.js navigate '{"url":"https://example.com"}'
```

返回页面快照，包含元素引用（如 `[ref=e3]`）。

### 2. 获取快照

```bash
node skills/playwright/tool.js snapshot '{}'
```

快照是无障碍树。每个可交互元素都有一个 `ref`（如 `[ref=e42]`）。使用这些 ref 来定位元素。

### 3. 与元素交互

```bash
node skills/playwright/tool.js click '{"ref":"e42","element":"提交按钮"}'
node skills/playwright/tool.js type '{"ref":"e10","text":"hello@example.com"}'
node skills/playwright/tool.js fillForm '{"fields":[{"name":"邮箱","type":"textbox","ref":"e10","value":"hello@example.com"}]}'
```

### 4. 截图

```bash
node skills/playwright/tool.js screenshot '{"type":"png"}'
```

## 浏览器管理

```bash
node skills/playwright/tool.js start    # 启动浏览器
node skills/playwright/tool.js stop     # 关闭浏览器
node skills/playwright/tool.js status   # 检查浏览器状态
```

浏览器在多次调用之间保持运行。首次调用工具时会自动启动。

## 工具参考

完整的 48 个工具 API 参数说明，请查看 [references/tools-api.md](references/tools-api.md)。

### 快速参考

| 命令 | 说明 |
|------|------|
| `navigate` | 导航到 URL |
| `snapshot` | 获取页面无障碍树（含 ref） |
| `click` | 通过 ref 点击元素 |
| `type` | 向元素输入文本 |
| `fillForm` | 批量填写表单字段 |
| `pressKey` | 按下键盘按键 |
| `screenshot` | 截图 |
| `evaluate` | 在页面执行 JavaScript |
| `waitFor` | 等待文本/时间 |
| `tabs` | 管理浏览器标签页 |
| `consoleMessages` | 获取控制台输出 |
| `networkRequests` | 获取网络活动 |
| `handleDialog` | 接受/关闭对话框 |
| `cookieList` | 列出 Cookie |
| `route` | 模拟网络请求 |
| `runCode` | 执行 Playwright 代码片段 |

## 输出格式

每个命令返回 JSON 到 stdout：

```json
{
  "result": "...",
  "snapshot": "- generic [ref=e2]: ...",
  "tabs": ["0: (current) [标题](url)"],
  "code": "await page.goto('...');",
  "error": null
}
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PLAYWRIGHT_SKILL_BROWSER` | `chromium` | 浏览器引擎 |
| `PLAYWRIGHT_SKILL_HEADLESS` | `false`（桌面）/ `true`（Linux 无显示器） | 无头模式 |
| `PLAYWRIGHT_SKILL_CHANNEL` | `chrome` | 浏览器通道 |
