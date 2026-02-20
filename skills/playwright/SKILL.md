---
name: playwright
description: 通过 Playwright 实现浏览器自动化。导航页面、点击元素、填写表单、截图、执行 JavaScript、管理 Cookie/存储、拦截网络请求等。当用户需要自动化浏览器、测试网页、抓取内容或与任何 Web UI 交互时使用。
---

# Playwright 浏览器自动化

通过 48 个工具控制真实浏览器（Chrome/Chromium）。支持两种调用方式：CLI 命令和 MCP Tools。

## MCP Tools 映射（Playwright MCP Server）

当环境中启用了 `@playwright/mcp` 服务时，以下 22 个 MCP tools 与 Skill CLI 命令的映射关系。**优先使用 Skill CLI 命令**，MCP tools 作为补充。

| 功能 | 对应 CLI 命令 |
|------|--------------|
| `browser_navigate` → 导航到 URL | `navigate` |
| `browser_navigate_back` → 返回上一页 | `goBack` |
| `browser_snapshot` → 获取页面无障碍树 | `snapshot` |
| `browser_click` → 点击元素 | `click` |
| `browser_drag` → 拖拽元素 | `drag` |
| `browser_hover` → 悬停元素 | `hover` |
| `browser_type` → 输入文本 | `type` |
| `browser_select_option` → 选择下拉选项 | `selectOption` |
| `browser_fill_form` → 批量填写表单 | `fillForm` |
| `browser_press_key` → 按下键盘按键 | `pressKey` |
| `browser_take_screenshot` → 截图 | `screenshot` |
| `browser_evaluate` → 执行 JavaScript | `evaluate` |
| `browser_run_code` → 执行 Playwright 代码 | `runCode` |
| `browser_wait_for` → 等待文本/时间 | `waitFor` |
| `browser_tabs` → 管理标签页 | `tabs` |
| `browser_console_messages` → 控制台输出 | `consoleMessages` |
| `browser_network_requests` → 网络请求 | `networkRequests` |
| `browser_handle_dialog` → 处理对话框 | `handleDialog` |
| `browser_file_upload` → 上传文件 | `fileUpload` |
| `browser_close` → 关闭浏览器 | `close` |
| `browser_resize` → 调整窗口大小 | `resize` |
| `browser_install` → 安装浏览器 | `install` |

### 仅 CLI 可用的扩展工具

以下 26 个工具无对应 MCP tool，通过 CLI 调用（`node skills/playwright/tool.js <命令>`）：

| 类别 | CLI 命令 |
|------|----------|
| 导航扩展 | `goForward`, `reload` |
| 复选框 | `check`, `uncheck` |
| 键盘扩展 | `pressSequentially`, `keydown`, `keyup` |
| 鼠标坐标 | `mouseMove`, `mouseClick`, `mouseDrag`, `mouseDown`, `mouseUp`, `mouseWheel` |
| Cookie | `cookieList`, `cookieGet`, `cookieSet`, `cookieDelete`, `cookieClear` |
| 存储状态 | `storageState`, `setStorageState` |
| Web 存储 | `localStorageList/Get/Set/Delete/Clear`, `sessionStorageList/Get/Set/Delete/Clear` |
| 网络拦截 | `route`, `routeList`, `unroute` |
| 控制台扩展 | `consoleClear`, `networkClear` |
| 测试验证 | `verifyElement`, `verifyText`, `verifyList`, `verifyValue`, `generateLocator` |
| 高级功能 | `pdf`, `tracingStart`, `tracingStop`, `startVideo`, `stopVideo`, `devtoolsStart`, `getConfig` |

## 安装

首次使用前，在 skill 目录下执行一次：

```bash
cd skills/playwright && npm install && npx playwright install chromium
```

## 更新

自然语言更新：
```
帮我从 https://github.com/shetengteng/skillix-hub 更新 playwright skill
```

手动更新：
```bash
git clone https://github.com/shetengteng/skillix-hub.git /tmp/skillix-hub
cp -r /tmp/skillix-hub/skills/playwright/{SKILL.md,tool.js,lib,tools,references,package.json} skills/playwright/
cd skills/playwright && npm install
rm -rf /tmp/skillix-hub
```

> Playwright Skill 无用户数据目录，更新时直接覆盖文件即可。

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
