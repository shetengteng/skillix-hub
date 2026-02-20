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
| 元素点击 | `click` | 通过 |
| 等待时间 | `waitFor {time}` | 通过 |
| 控制台消息 | `consoleMessages` | 通过 |
| 网络请求 | `networkRequests` | 通过 |
| 多次调用间状态保持 | CDP 复用 | 通过 |
| 登录态保持 | user-data-dir | 通过（修复后） |

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
