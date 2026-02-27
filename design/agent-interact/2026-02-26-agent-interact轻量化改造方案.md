# agent-interact 轻量化改造方案

> 日期：2026-02-26  
> 背景：当前 Electron 方案 node_modules 达 289MB（其中 Electron 本体 275MB），安装耗时长，对于"只展示一个弹框"的需求来说过于重量级。

---

## 当前架构回顾

```
tool.js (CLI 入口)
  └── Express HTTP 服务 (端口 7890)
       └── WebSocket 双向通信
            └── Electron 独立窗口 (加载 Vite 构建的 Vue3 前端)
```

**问题**：
- Electron 本体 275MB，每台机器首次安装需下载
- `npm install` 耗时 1~3 分钟
- 进程常驻内存约 80~120MB
- 仅为了展示一个弹框，代价过高

---

## 核心需求澄清

> 系统浏览器方案（`open` 命令）不满足需求：它只是打开一个浏览器标签页，不会"弹框"，没有置顶效果，用户体验差。

真正的弹框需要满足：
1. **独立窗口**：不是浏览器标签页，是一个独立的 OS 窗口
2. **置顶显示**：出现在所有窗口最前面，用户不会错过
3. **自定义 UI**：支持表格、图表、表单等复杂内容
4. **轻量安装**：安装包小，无需漫长的 npm install

---

## 方案一：pywebview（推荐 ⭐⭐⭐⭐⭐）

**原理**：Python 的 `pywebview` 库直接调用 macOS 系统原生 **WKWebView**（Safari 内核），弹出一个真正的独立置顶窗口，加载本地 HTML 页面。

**架构**：
```
tool.js (CLI 入口)
  └── Express HTTP 服务 (端口 7890)
       └── WebSocket 双向通信
            └── Python pywebview 进程 (调用系统 WKWebView)
                 └── 加载本地 HTML（Vue3 前端不变）
```

**优点**：
- **真正的独立置顶窗口**，不是浏览器标签页
- 使用系统 WKWebView，**无需下载浏览器引擎**
- pywebview 包本体仅 **499KB**，安装极快
- 支持 `on_top=True`、无边框、自定义尺寸
- 前端 Vue3 代码**完全不变**
- macOS 已有 Python3（系统自带 `/usr/bin/python3`）

**缺点**：
- 需要 `pip install pywebview`（首次安装需网络，约 5MB 含依赖）
- 混合了 Node.js + Python 两个进程
- 调试体验不如 Electron 方便

**安装大小对比**：
```
当前 Electron：  node_modules = 289MB
pywebview 方案：node_modules = ~5MB（删除 electron 依赖）
               + pywebview   = ~5MB（含依赖）
总计：~10MB（减少 96%）
```

**示例代码**：
```python
import webview
import sys
import json

data = json.loads(sys.argv[1])  # 接收 dialog JSON
window = webview.create_window(
    data.get('title', 'Agent Dialog'),
    url=f'http://127.0.0.1:7890/dialog?id={data["dialogId"]}',
    width=600,
    height=500,
    on_top=True,
    frameless=False
)
webview.start()
```

**tool.js 改动**：
```javascript
// 之前：启动 Electron
spawn('electron', [electronMain, ...])

// 之后：启动 pywebview
spawn('python3', [pywebviewScript, JSON.stringify(dialogData)])
```

---

## 方案二：Neutralinojs（推荐 ⭐⭐⭐⭐）

**原理**：Neutralinojs 是一个轻量级桌面应用框架，使用系统 WebView（macOS 上是 WKWebView），**核心二进制文件仅约 2~5MB**，无需 Node.js 运行时，直接下载预编译二进制运行。

**架构**：
```
tool.js (CLI 入口)
  └── Express HTTP 服务 (端口 7890)
       └── Neutralino 二进制 (调用系统 WKWebView)
            └── 加载本地 HTML（Vue3 前端不变）
```

**优点**：
- 预编译二进制，**macOS 上约 3~5MB**
- 独立置顶窗口，真正的桌面弹框
- 使用系统 WKWebView，无需下载浏览器引擎
- 前端 HTML/JS 完全兼容
- 跨平台（macOS/Windows/Linux）

**缺点**：
- 需要下载预编译二进制（首次约 3~5MB）
- 与现有 Node.js/Express 架构集成需要一定改造
- 社区相对 Electron 小，文档较少

**安装**：
```bash
npm install -g @neutralinojs/neu
neu create myapp  # 初始化项目
```

**二进制大小**（macOS arm64）：约 3~5MB

---

## 方案三：pkg 打包 Node.js + 系统 WebView（推荐 ⭐⭐⭐）

**原理**：用 `pkg` 将 Node.js 服务打包成单个可执行文件，窗口部分改用 `node-webview`（调用系统 WebView）替代 Electron。

**优点**：
- 打包后单个可执行文件，用户**零安装**
- 使用系统 WebView，体积小

**缺点**：
- `node-webview` npm 包（版本 0.0.1）几乎无维护，不可靠
- `pkg` 打包后文件约 50~80MB（含 Node.js 运行时）
- 开发调试复杂

**不推荐**：node-webview 包太旧，不可靠。

---

## 方案四：macOS osascript（降级方案 ⭐⭐）

**原理**：直接用 macOS 内置 `osascript` 调用系统原生对话框，零依赖。

```bash
osascript -e 'display dialog "即将部署到生产环境" buttons {"取消", "确认"} default button "确认"'
```

**优点**：
- **零安装**，macOS 内置
- 毫秒级弹出，强制置顶
- 原生 macOS 风格

**缺点**：
- **仅支持 macOS**
- UI 极简：只有文字 + 按钮，无法展示表格/图表/表单
- 无法实现 custom/chart/form 等复杂交互类型

**适用场景**：仅作为 pywebview 不可用时的简单 confirm/approval 降级方案。

---

## 方案五：Tauri（长期方向 ⭐⭐⭐）

**原理**：Rust 编写的桌面框架，调用系统 WebView，打包成单个二进制文件。

**优点**：
- 打包后单个二进制，用户零安装
- 内存占用极低（约 10~30MB）
- 前端仍用 Vue3

**缺点**：
- **开发环境需要 Rust 工具链**（约 1.5GB 安装）
- 构建时间长（首次 5~10 分钟）
- 目前项目无 Rust 环境，迁移成本高

**适合场景**：长期规划，将 agent-interact 打包成独立可执行文件分发。

---

## 方案对比总结

| 方案 | 安装大小 | 安装时间 | 真正弹框 | 置顶 | 功能完整性 | 推荐度 |
|------|---------|---------|---------|------|-----------|-------|
| 当前 Electron | 289MB | 1~3 分钟 | ✅ | 强制置顶 | ⭐⭐⭐⭐⭐ | 现状 |
| **方案一：pywebview** | **~10MB** | **10 秒** | **✅** | **强制置顶** | **⭐⭐⭐⭐⭐** | **⭐⭐⭐⭐⭐** |
| 方案二：Neutralinojs | ~5MB 二进制 | 5 秒 | ✅ | 强制置顶 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 方案三：pkg+node-webview | 打包后 ~60MB | 构建需时 | ✅ | 强制置顶 | ⭐⭐ | ⭐ |
| 方案四：osascript | 0MB | 0 秒 | ✅ | 强制置顶 | ⭐（仅简单确认） | ⭐⭐ |
| 方案五：Tauri | 0MB（打包后） | 需 Rust 环境 | ✅ | 强制置顶 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐（长期） |
| ~~系统浏览器~~ | ~5MB | 5 秒 | ❌ 标签页 | ❌ | ⭐⭐⭐⭐⭐ | ❌ |

---

## 推荐路径

### 短期（立即可做）：方案一 — pywebview

**最优选择**，改动最小，收益最大：

1. 删除 `electron` npm 依赖（释放 275MB）
2. 安装 `pywebview`（约 5MB）
3. 新增 `dialog_window.py` 脚本（替代 `electron/main.js`）
4. `tool.js` 中替换 Electron 启动逻辑为 `python3 dialog_window.py`
5. 前端 Vue3 代码**完全不变**

**预计工作量**：约 2~4 小时  
**风险**：低，pywebview 成熟稳定，macOS WKWebView 支持完整

### 中期（可选）：方案二 — Neutralinojs

如果希望完全脱离 Python 依赖，可以用 Neutralinojs 的预编译二进制替代。

### 长期（规划）：方案五 — Tauri

将整个 agent-interact 打包成单个可执行文件，彻底解决安装问题。

---

## 方案一详细实施步骤

**文件改动**：

| 文件 | 操作 | 说明 |
|------|------|------|
| `package.json` | 删除 `electron` 依赖 | 释放 275MB |
| `electron/` 目录 | 整体删除 | 不再需要 |
| `dialog_window.py` | 新增 | pywebview 窗口脚本 |
| `tool.js` | 修改 start/stop/dialog 命令 | 替换 Electron 调用为 python3 |
| `lib/server.js` | 移除 Electron IPC 代码 | 改为纯 HTTP/WebSocket |
| `ui/` 前端 | 基本不变 | 只调整 WebSocket 连接方式 |

**pywebview 安装**（一次性）：
```bash
pip3 install pywebview
```

**dialog_window.py 核心逻辑**：
```python
import webview
import sys
import json

args = json.loads(sys.argv[1])
window = webview.create_window(
    title=args.get('title', 'Agent'),
    url=f"http://127.0.0.1:{args['port']}/dialog?id={args['dialogId']}",
    width=args.get('width', 640),
    height=args.get('height', 520),
    on_top=True,
    resizable=True
)
webview.start()
```
