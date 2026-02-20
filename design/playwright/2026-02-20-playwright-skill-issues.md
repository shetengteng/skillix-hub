# Playwright Skill 问题报告

> 测试日期：2026-02-20
> 测试环境：macOS, Chrome 145.0.7632.76, playwright-core 1.52.0
> 测试目标：验证 Playwright CLI Skill 能否替代 Playwright MCP

---

## 问题汇总

| # | 问题 | 严重程度 | 文件 | 状态 |
|---|------|---------|------|------|
| 1 | Chrome 进程启动后立即退出 | 严重 | `lib/server.js` | 已临时修复 |
| 2 | CDP 端口就绪检测缺失 | 严重 | `lib/server.js` | 已临时修复 |
| 3 | CDP 连接超时时间太短 | 中等 | `lib/browser-manager.js` | 已临时修复 |
| 4 | screenshot filename 不支持相对路径 | 低 | `lib/config.js` / 截图相关 | 未修复 |
| 5 | waitFor 默认超时太短 | 低 | `tools/wait.js` | 未修复 |
| 6 | click 无法触发 Vue 自定义组件事件 | 严重 | `tools/click.js` | 未修复 |
| 7 | fillForm combobox 不支持自定义下拉组件 | 中等 | `tools/fill-form.js` | 未修复 |
| 8 | type/fillForm 不支持自定义 input 组件 | 中等 | `tools/type.js` / `tools/fill-form.js` | 未修复 |
| 9 | screenshot filename 目录不存在时报错 | 低 | 截图相关 | 未修复 |

---

## 问题详情

### 问题 1：Chrome 进程启动后立即退出（严重）

**现象**：`start` 或首次 `navigate` 时，server.js 启动 Chrome 进程，但进程很快退出，导致 CDP 连接失败。

**错误信息**：
```
browserType.connectOverCDP: connect ECONNREFUSED 127.0.0.1:XXXXX
```

**根因**：`server.js` 中 `spawn` 启动 Chrome 时没有指定 `--user-data-dir`，Chrome 检测到已有实例运行时会委托给已有实例然后退出。同时缺少 `--no-startup-window` 参数。

**临时修复**（已应用到本地）：

```javascript
// server.js - 添加 user-data-dir 和 no-startup-window
const userDataDir = path.join(stateDir, 'chrome-profile');
await ensureDir(userDataDir);

const args = [
  `--remote-debugging-port=${cdpPort}`,
  `--user-data-dir=${userDataDir}`,  // 新增：独立用户数据目录
  '--no-first-run',
  '--no-default-browser-check',
  '--disable-background-networking',
  '--disable-default-apps',
  '--disable-sync',
  '--no-startup-window',  // 新增：防止无窗口时退出
];
```

**建议源码修复**：
- 在 `server.js` 中为 Chrome 指定独立的 `--user-data-dir`（基于 `stateDir`）
- 添加 `--no-startup-window` 防止 Chrome 因无初始窗口而退出
- 这个 user-data-dir 的好处是可以保留登录态（Cookie/Session），避免每次都需要重新登录

---

### 问题 2：CDP 端口就绪检测缺失（严重）

**现象**：Chrome 启动后，server.js 只等待固定 1.5 秒就输出 wsEndpoint，但 Chrome 的 CDP 端口可能还没准备好。

**根因**：`server.js` 中使用 `setTimeout(1500)` 硬编码等待，没有实际检测 CDP 端口是否可用。

**临时修复**（已应用到本地）：

```javascript
// server.js - 增加等待时间 + CDP 端口就绪检测
await new Promise(r => setTimeout(r, 3000));  // 从 1500 增加到 3000

// 轮询检测 CDP 端口
for (let i = 0; i < 10; i++) {
  try {
    const res = await fetch(`http://127.0.0.1:${cdpPort}/json/version`);
    if (res.ok) break;
  } catch {}
  await new Promise(r => setTimeout(r, 500));
}
```

**建议源码修复**：
- 将固定等待改为轮询 `http://127.0.0.1:${cdpPort}/json/version` 直到返回 200
- 设置合理的超时上限（如 15 秒）
- 如果超时仍未就绪，kill 子进程并报错

---

### 问题 3：CDP 连接超时时间太短（中等）

**现象**：`browser-manager.js` 中 `connectOverCDP` 的超时时间为 5000ms，在 Chrome 启动较慢时可能不够。

**临时修复**（已应用到本地）：

```javascript
// browser-manager.js
// 连接前等待从 500ms 增加到 1500ms
await new Promise(r => setTimeout(r, 1500));
// 连接超时从 5000ms 增加到 10000ms
this._browser = await playwright.chromium.connectOverCDP(serverInfo.wsEndpoint, { timeout: 10000 });
```

**建议源码修复**：
- 将 `connectOverCDP` 超时增加到 10000ms
- 连接前等待增加到 1500ms
- 或者更好的方案：在 `_launch()` 中也加入 CDP 端口就绪检测

---

### 问题 4：screenshot filename 不支持相对路径（低）

**现象**：`screenshot` 命令的 `filename` 参数如果传相对路径，会相对于 `outputDir`（默认 `/tmp/playwright-skill-output/`）而不是当前工作目录。

**复现**：
```bash
# 失败 - 相对路径
node tool.js screenshot '{"type":"png","filename":"测试/screenshots/test.png"}'
# 报错：ENOENT: /tmp/playwright-skill-output/测试/screenshots/test.png

# 成功 - 绝对路径
node tool.js screenshot '{"type":"png","filename":"/absolute/path/test.png"}'
```

**建议源码修复**：
- 如果 `filename` 是相对路径，应该相对于 `process.cwd()` 而不是 `outputDir`
- 或者在 `outputFile()` 函数中检测：如果 `suggestedFilename` 是绝对路径则直接使用，否则拼接 `outputDir`
- 当前 `lib/config.js` 的 `outputFile()` 函数总是 `path.resolve(dir, baseName)`，需要判断

---

### 问题 5：waitFor 默认超时太短（低）

**现象**：`waitFor` 的 `textGone` 等待文本消失时，默认超时 5000ms，对于首次加载的 SPA 应用可能不够。

**复现**：
```bash
# 超时失败
node tool.js waitFor '{"textGone":"Content loading..."}'
# 报错：Timeout 5000ms exceeded
```

**建议源码修复**：
- `waitFor` 的默认超时应该使用 `config.timeouts.navigation`（60000ms）而不是 `config.timeouts.action`（5000ms）
- 或者允许用户通过参数指定超时时间：`{"textGone":"...", "timeout": 30000}`

---

### 问题 6：click 无法触发 Vue 自定义组件事件（严重）

**现象**：Playwright 的 `click` 命令可以成功点击元素（无报错），但 Vue 自定义组件（如 `zoom-button`、`zoom-dialog` 内的按钮）上的 `@click` 事件不会被触发。需要通过 `evaluate` + JS `element.click()` 才能触发。

**复现**：
```bash
# Playwright click - 点击成功但事件不触发
node tool.js click '{"ref":"e632","element":"Create 按钮"}'
# 返回成功，但弹窗不关闭，表单不提交

# JS evaluate click - 事件正常触发
node tool.js evaluate '{"function":"() => { document.querySelector(\".zoom-dialog__footer .zoom-button--primary\").click(); return \"clicked\"; }"}'
# 表单提交成功，弹窗关闭
```

**影响范围**：
- Dialog 内的 Create/Save/Submit 按钮
- MessageBox 内的 Confirm/Delete 按钮
- 使用 `zoom-button` 组件的所有按钮

**可能原因**：Playwright 的 `click` 使用 `locator.click()` 触发的是原生 DOM 事件，而 Vue 自定义组件可能监听的是通过 Vue 事件系统绑定的事件，或者组件内部有事件拦截/冒泡阻止。

**建议源码修复**：
- 在 `click` 工具中增加 fallback 机制：如果 Playwright `locator.click()` 后页面无变化，自动尝试 `page.evaluate(el => el.click(), element)`
- 或者提供 `forceJsClick` 参数选项，让用户可以选择使用 JS click
- 需要深入调查 Playwright `locator.click()` 与 Vue 3 事件系统的兼容性问题

---

### 问题 7：fillForm combobox 不支持自定义下拉组件（中等）

**现象**：`fillForm` 的 `combobox` 类型使用 `locator.selectOption()`，只支持原生 `<select>` 元素，不支持 Vue 自定义下拉组件（如 `zoom-virtual-filter-select`）。

**错误信息**：
```
Element is not a <select> element
```

**复现**：
```bash
node tool.js fillForm '{"fields":[{"name":"Tenant","type":"combobox","ref":"e582","value":"meetings"}]}'
# 报错：Element is not a <select> element
```

**当前 workaround**：
```bash
# 1. 点击 combobox 展开下拉列表
node tool.js click '{"ref":"e582","element":"Tenant combobox"}'
# 2. 从 snapshot 中找到 option 的 ref
# 3. 点击目标 option
node tool.js click '{"ref":"e640","element":"meetings option"}'
```

**建议源码修复**：
- 检测元素是否为原生 `<select>`，如果不是，改用 click 展开 → 查找 option → click 选择的流程
- 或者增加 `type: "custom-combobox"` 类型，自动执行 click → waitFor listbox → click option 的流程
- 参考 Playwright 的 `getByRole('combobox')` + `getByRole('option')` 模式

---

### 问题 8：type/fillForm 不支持自定义 input 组件（中等）

**现象**：`type` 和 `fillForm` 的 `textbox` 类型使用 `locator.fill()`，但某些 Vue 自定义组件（如 `async-detail-text`）虽然在 accessibility tree 中显示为 `textbox`，实际 DOM 元素不是 `<input>` 或 `<textarea>`，导致 `fill()` 失败。

**错误信息**：
```
Element is not an <input>, <textarea>, <select> or [contenteditable]
```

**复现场景**：详情页的内联编辑字段（点击编辑图标后出现的输入框），accessibility tree 显示为 `textbox` 但实际是 `<span class="async-detail-text">`。

**当前 workaround**：
```bash
# 使用 evaluate 直接操作 DOM
node tool.js evaluate '{"function":"() => { const input = document.querySelector(\".zoom-input__inner\"); const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, \"value\").set; setter.call(input, \"new value\"); input.dispatchEvent(new Event(\"input\", {bubbles:true})); }"}'
```

**建议源码修复**：
- 在 `type` 工具中，如果 `locator.fill()` 失败，自动 fallback 到查找内部的实际 `<input>` 元素
- 可以尝试 `locator.locator('input, textarea').fill()` 作为 fallback
- 或者使用 `locator.pressSequentially()` 逐字输入作为最终 fallback

---

### 问题 9：screenshot filename 目录不存在时报错（低）

**现象**：`screenshot` 命令的 `filename` 参数指定的路径如果父目录不存在，会直接报 ENOENT 错误，不会自动创建目录。

**复现**：
```bash
node tool.js screenshot '{"filename":"/path/to/new-dir/test.png","type":"png"}'
# 报错：ENOENT: no such file or directory
```

**建议源码修复**：
- 在写入截图文件前，使用 `fs.mkdirSync(path.dirname(filename), { recursive: true })` 自动创建父目录

---

## CRUD 全流程测试结果

| 操作 | 方法 | 结果 | 备注 |
|------|------|------|------|
| 创建 - 打开表单 | `click` | 通过 | 正常弹出 Create dialog |
| 创建 - 下拉选择 Tenant | `click` combobox → `click` option | 通过 | `fillForm combobox` 不支持，需手动 click |
| 创建 - 填写文本字段 | `fillForm textbox` | 通过 | Product name / Description 正常 |
| 创建 - 提交表单 | `evaluate` JS click | 通过 | Playwright `click` 无法触发，需 JS click |
| 查看详情 | 自动跳转 + `snapshot` | 通过 | 创建后自动跳转详情页 |
| 编辑 - 打开编辑模式 | `click` img 图标 | 通过 | |
| 编辑 - 修改值 | `evaluate` JS | 通过 | `type`/`fill` 不支持自定义组件，需 JS |
| 编辑 - 保存 | `evaluate` JS click | 通过 | 同问题 6 |
| 删除 - 点击删除 | `click` | 通过 | 弹出确认框 |
| 删除 - 确认删除 | `evaluate` JS click | 通过 | 同问题 6 |
| 删除 - 验证结果 | `snapshot` | 通过 | 列表中已无该记录 |

---

## 已验证通过的功能

| 功能 | 命令 | 结果 |
|------|------|------|
| 浏览器启动 | `start` / 自动 | 通过（修复后） |
| 浏览器关闭 | `stop` | 通过 |
| 浏览器状态 | `status` | 通过 |
| 页面导航 | `navigate` | 通过 |
| 页面快照 | `snapshot` | 通过 |
| 截图（绝对路径） | `screenshot` | 通过 |
| 文本输入 | `type` | 通过 |
| 表单填写 | `fillForm` | 通过 |
| 元素点击（原生元素） | `click` | 通过 |
| 元素点击（Vue 组件） | `click` | 失败，需 `evaluate` JS click |
| 等待时间 | `waitFor {time}` | 通过 |
| 控制台消息 | `consoleMessages` | 通过 |
| 网络请求 | `networkRequests` | 通过 |
| 多次调用间状态保持 | CDP 复用 | 通过 |
| 登录态保持 | user-data-dir | 通过（修复后） |
| JS 代码执行 | `evaluate` | 通过 |
| Tab 管理 | `tabs` | 通过 |
| 下拉选择（click 方式） | `click` + `click` option | 通过 |
| CRUD 全流程 | 综合 | 通过（部分需 evaluate workaround） |

---

## 临时修复的文件清单

以下文件已在本地做了临时修复，需要同步到源码仓库：

1. **`lib/server.js`**
   - 添加 `--user-data-dir` 和 `--no-startup-window` 参数
   - 增加初始等待时间到 3000ms
   - 添加 CDP 端口就绪轮询检测

2. **`lib/browser-manager.js`**
   - 连接前等待从 500ms 增加到 1500ms
   - `connectOverCDP` 超时从 5000ms 增加到 10000ms
