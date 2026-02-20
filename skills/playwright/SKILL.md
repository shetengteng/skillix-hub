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

## 自然语言交互指南

当用户用自然语言描述浏览器操作时，按以下规则映射到工具调用：

### 页面导航

| 用户说 | 执行 |
|--------|------|
| "打开 xxx 网站" / "访问 xxx" / "去 xxx 页面" | `navigate '{"url":"xxx"}'` |
| "返回上一页" / "后退" | `goBack '{}'` |
| "前进" | `goForward '{}'` |
| "刷新页面" / "重新加载" | `reload '{}'` |

### 页面观察

| 用户说 | 执行 |
|--------|------|
| "看看页面上有什么" / "页面内容是什么" | `snapshot '{}'` |
| "截个图" / "看看页面长什么样" | `screenshot '{"type":"png"}'` |
| "截整个页面" / "完整截图" | `screenshot '{"type":"png","fullPage":true}'` |
| "控制台有什么输出" / "看看日志" | `consoleMessages '{"level":"info"}'` |
| "有什么网络请求" / "看看 API 调用" | `networkRequests '{"includeStatic":false}'` |

### 元素交互

先通过 `snapshot` 获取元素 ref，然后：

| 用户说 | 执行 |
|--------|------|
| "点击 xxx 按钮" / "点一下 xxx" | `click '{"ref":"eN","element":"xxx"}'` |
| "在 xxx 输入框输入 yyy" | `type '{"ref":"eN","text":"yyy"}'` |
| "填写表单" / "把 xxx 填成 yyy" | `fillForm '{"fields":[...]}'` |
| "选择 xxx 选项" | `selectOption '{"ref":"eN","values":["xxx"]}'` |
| "按回车" / "按 Esc" | `pressKey '{"key":"Enter"}'` / `pressKey '{"key":"Escape"}'` |

### 标签页管理

| 用户说 | 执行 |
|--------|------|
| "打开新标签页" | `tabs '{"action":"new"}'` |
| "切换到第 N 个标签" | `tabs '{"action":"select","index":N}'` |
| "关闭当前标签" | `tabs '{"action":"close"}'` |
| "有哪些标签页" | `tabs '{"action":"list"}'` |

### 数据操作

| 用户说 | 执行 |
|--------|------|
| "查看 Cookie" / "有哪些 Cookie" | `cookieList '{}'` |
| "设置 Cookie xxx" | `cookieSet '{"name":"xxx","value":"yyy","domain":"..."}'` |
| "清除 Cookie" | `cookieClear '{}'` |
| "在页面执行 JS" / "运行脚本 xxx" | `evaluate '{"function":"() => { xxx }"}'` |

### 等待与验证

| 用户说 | 执行 |
|--------|------|
| "等页面出现 xxx" / "等 xxx 加载完" | `waitFor '{"text":"xxx"}'` |
| "等 xxx 消失" | `waitFor '{"textGone":"xxx"}'` |
| "等 3 秒" | `waitFor '{"time":3}'` |
| "验证页面有 xxx" | `verifyText '{"text":"xxx"}'` |
| "验证 xxx 元素存在" | `verifyElement '{"ref":"eN"}'` |

### 典型工作流示例

**示例 1：用户说"帮我登录 xxx 网站"**

```bash
# 1. 打开网站
node skills/playwright/tool.js navigate '{"url":"https://xxx.com/login"}'
# 2. 查看页面结构，找到输入框和按钮的 ref
node skills/playwright/tool.js snapshot '{}'
# 3. 填写用户名和密码（根据 snapshot 中的 ref）
node skills/playwright/tool.js fillForm '{"fields":[{"name":"用户名","type":"textbox","ref":"e5","value":"user@example.com"},{"name":"密码","type":"textbox","ref":"e8","value":"password123"}]}'
# 4. 点击登录按钮
node skills/playwright/tool.js click '{"ref":"e12","element":"登录按钮"}'
# 5. 验证登录成功
node skills/playwright/tool.js waitFor '{"text":"欢迎"}'
node skills/playwright/tool.js screenshot '{"type":"png"}'
```

**示例 2：用户说"帮我看看这个页面的商品价格"**

```bash
# 1. 导航到页面
node skills/playwright/tool.js navigate '{"url":"https://shop.example.com/product/123"}'
# 2. 获取页面内容
node skills/playwright/tool.js snapshot '{}'
# 3. 如果需要滚动加载更多内容
node skills/playwright/tool.js evaluate '{"function":"() => window.scrollTo(0, document.body.scrollHeight)"}'
node skills/playwright/tool.js snapshot '{}'
```

**示例 3：用户说"监控这个 API 的请求和响应"**

```bash
# 1. 打开页面
node skills/playwright/tool.js navigate '{"url":"https://app.example.com"}'
# 2. 执行触发 API 的操作
node skills/playwright/tool.js click '{"ref":"e5","element":"加载数据按钮"}'
# 3. 查看网络请求
node skills/playwright/tool.js networkRequests '{"includeStatic":false}'
# 4. 查看控制台日志
node skills/playwright/tool.js consoleMessages '{"level":"info"}'
```

### 关键规则

1. **先 snapshot 再交互**：任何点击、输入操作前，必须先执行 `snapshot` 获取元素 ref
2. **ref 是动态的**：页面变化后 ref 会失效，需要重新 `snapshot`
3. **浏览器自动管理**：首次调用工具时浏览器自动启动，无需手动 `start`
4. **JSON 输出**：所有工具返回 JSON，从 `result` 字段读取主要结果
5. **错误处理**：检查返回 JSON 的 `error` 字段，非 null 表示执行失败

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PLAYWRIGHT_SKILL_BROWSER` | `chromium` | 浏览器引擎 |
| `PLAYWRIGHT_SKILL_HEADLESS` | `false`（桌面）/ `true`（Linux 无显示器） | 无头模式 |
| `PLAYWRIGHT_SKILL_CHANNEL` | `chrome` | 浏览器通道 |
