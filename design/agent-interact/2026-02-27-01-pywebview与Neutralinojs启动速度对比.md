# pywebview vs Neutralinojs 启动速度对比

> 日期：2026-02-27  
> 背景：当前 agent-interact 使用 pywebview 方案，dialog 关闭后后端服务仍在运行，导致其他软件点击时出现卡顿。本文对比 pywebview 和 Neutralinojs 两种方案的启动速度，为后续架构调整提供依据。

---

## 测试环境

- 机器：macOS arm64（Apple Silicon）
- pywebview：系统 WKWebView（macOS 原生）
- Neutralinojs：v2.x，二进制 `neutralino-mac_arm64`（2.1MB）
- 测量方式：从进程启动 → 窗口/ready 事件触发，Python subprocess 计时

---

## 实测结果

### 方案一：pywebview

测量指标：从 `python3 window.py` 进程启动 → `window.events.loaded` 事件触发

| 次数 | 窗口加载完成 | 进程总耗时（含 Python 启动） |
|------|------------|--------------------------|
| 1    | 588ms      | 748ms                    |
| 2    | 424ms      | 530ms                    |
| 3    | 449ms      | 588ms                    |
| 4    | 484ms      | 591ms                    |
| 5    | 423ms      | 544ms                    |
| **均值** | **474ms** | **600ms**             |

> **注**：进程总耗时包含 Python 解释器启动（约 70~100ms）+ import webview（约 60~100ms）+ WKWebView 初始化。

### 方案二：Neutralinojs

测量指标：从二进制进程启动 → `Neutralino.events.on("ready")` 事件触发

| 次数 | ready 事件触发 |
|------|--------------|
| 1    | 594ms        |
| 2    | 480ms        |
| 3    | 482ms        |
| **均值** | **519ms** |

> **注**：直接运行 `neutralino-mac_arm64` 二进制，不含 `neu` CLI 工具的启动开销（CLI 约额外增加 200~400ms）。

---

## 对比汇总

| 指标 | pywebview | Neutralinojs |
|------|-----------|--------------|
| 窗口可见时间（均值） | **474ms** | **519ms** |
| 进程总启动时间（均值） | 600ms | 519ms（含 CLI 约 900ms） |
| 二进制/包大小 | ~5MB（pywebview pip 包） | **2.1MB**（单个二进制） |
| 安装方式 | `pip install pywebview` | 下载预编译二进制 |
| 语言依赖 | Python 3（macOS 自带） | 无（纯二进制） |
| 与现有架构集成难度 | **低**（已实现，仅需改进关闭逻辑） | 中（需重写 window 管理层） |
| WebSocket 通信 | 已实现 | 需通过 Neutralino.js 客户端库 |
| 跨平台 | macOS/Windows/Linux | macOS/Windows/Linux |

---

## 结论

**两者启动速度基本相当**，差距在 50ms 以内（均值 474ms vs 519ms），在用户感知层面无明显区别。

### 推荐：继续使用 pywebview，修复关闭逻辑

切换到 Neutralinojs **不能解决**当前的卡顿问题，因为：

1. **启动速度无显著差异**：两者都在 500ms 左右，Neutralinojs 并不更快
2. **卡顿根因不在启动速度**：问题是 dialog 关闭后，Express/WebSocket 后端服务进程仍在运行，持续占用资源
3. **切换成本高**：需要重写整个 window 管理层，放弃已经稳定运行的 pywebview 实现

### 真正的修复方案：dialog 关闭后停止服务

当所有 dialog 关闭后，主动终止后端服务进程：

```
dialog:close 事件 → 检查是否还有活跃 dialog → 无则 process.exit()
```

具体实现：在 `tool.js` 的 `dialog:close` 处理逻辑中，当 `activeDialogs` 数量归零时，调用 `server.close()` 并退出进程。

---

## 附：Neutralinojs 方案的适用场景

如果未来需要**完全脱离 Python 依赖**（例如分发给没有 Python 环境的用户），Neutralinojs 是合理选择：

- 单个 2.1MB 二进制，无需安装任何运行时
- 启动速度与 pywebview 相当
- 前端 HTML/JS 代码完全兼容

但当前场景下，macOS 自带 Python 3，pywebview 方案更简单，无需切换。
