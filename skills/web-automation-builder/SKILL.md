---
name: web-automation-builder
description: |
  被动录制用户浏览器操作行为。打开浏览器后用户自由操作，系统通过 CDP + DOM 事件注入
  自动记录点击、输入、导航等操作和 API 调用。录制完成后 LLM 分析生成结构化工作流。
  支持参数化重放、生成独立 Skill、导出 Playwright 脚本。依赖 Playwright Skill。
---

# Web Automation Builder

被动录制用户在浏览器中的操作，生成可重放的自动化工作流。

**核心模式**：用户自由操作 + 系统被动录制（非 LLM 驱动）。

## 安装 / 更新

```bash
# 安装（安装依赖 + 构建）
node skills/web-automation-builder/tool.js install

# 全局安装（复制到 ~/.cursor/skills/ + 安装依赖）
node skills/web-automation-builder/tool.js install '{"target":"~/.cursor/skills/web-automation-builder"}'

# 更新（从源码覆盖 + 清理重装）
node skills/web-automation-builder/tool.js update '{"target":"~/.cursor/skills/web-automation-builder"}'
```

## 前置依赖

| 依赖 | 说明 | 安装方式 |
|------|------|----------|
| **Playwright Skill** | 浏览器启动和操作命令 | `~/.cursor/skills/playwright/` |
| **playwright-core** | CDP 连接库 | `npm install`（package.json 已声明） |

## CLI 命令

```bash
node skills/web-automation-builder/tool.js <command> '<JSON参数>'
```

### 录制控制

```bash
# 开始被动录制（启动浏览器 + 注入 DOM 监听 + 启动网络监听）
node tool.js record '{"name":"部署后端代码"}'

# 查看录制状态（已收集的事件数量）
node tool.js status '{}'

# 停止录制（返回原始录制数据：DOM 事件 + API 请求）
node tool.js stop '{}'

# 保存 LLM 分析后的结构化工作流
node tool.js save '{"id":"wf-xxx","workflow":{...}}'
```

### 工作流管理

```bash
node tool.js list '{}'
node tool.js show '{"id":"wf-xxx"}'
node tool.js delete '{"id":"wf-xxx"}'
```

### 重放

```bash
# 批量重放（快速路径）
node tool.js replay '{"id":"wf-xxx"}'
node tool.js replay '{"id":"wf-xxx","params":{"username":"admin","password":"123"}}'

# 从指定步骤恢复
node tool.js replay '{"id":"wf-xxx","startFrom":3,"params":{...}}'
```

### LLM-First 逐步重放（推荐）

```bash
# 获取步骤列表（含 intent、locators），LLM 阅读后决定每步执行策略
node tool.js replaySteps '{"id":"wf-xxx"}'

# 执行单个步骤（1-based）
node tool.js replayStep '{"id":"wf-xxx","step":1,"params":{"key":"value"}}'
```

LLM 根据每步的 intent 和置信度，选择用 `replayStep` 工具执行或直接用 playwright 手动操作。

### 录制期间辅助操作（Phase 4）

Agent 在录制期间可以通过 `exec` 命令直接调用 Playwright 辅助用户操作：

```bash
# 导航到特定 URL
node tool.js exec '{"command":"navigate","args":{"url":"https://example.com"}}'

# 点击元素
node tool.js exec '{"command":"click","args":{"selector":"#some-button"}}'

# 填写表单
node tool.js exec '{"command":"type","args":{"selector":"#input","text":"value"}}'
```

### 生成独立 Skill

```bash
# 默认：生成 Skill（SKILL.md + tool.js + workflow.json + package.json）
node tool.js generate '{"id":"wf-xxx","skillName":"deploy-staging","target":"~/.cursor/skills/deploy-staging"}'

# 同时生成 Playwright 脚本（Skill 产物 + deploy-staging.js）
node tool.js generate '{"id":"wf-xxx","skillName":"deploy-staging","target":"~/.cursor/skills/deploy-staging","includePlaywright":true}'

# 仅生成 Playwright 脚本（不生成 Skill 产物）
node tool.js generate '{"id":"wf-xxx","skillName":"deploy-staging","target":"./scripts","format":"playwright"}'
```

### 导出 Playwright 脚本（单文件）

```bash
node tool.js export '{"id":"wf-xxx","output":"./my-automation.js"}'
```

## 自主决策指南

LLM 在录制流程中的行为协议：

### 录制流程（LLM 必须严格按此顺序执行）

```
1. 用户请求录制 → 调用 record 命令
2. record 返回成功（包含 id、pid）→ 立即执行步骤 3
3. 弹出 agent-interact wait 对话框（见下方代码）
   - 浏览器窗口会自动打开，用户可直接操作
   - 用户点击对话框"确认"按钮表示操作完成
4. 用户确认后 → 调用 stop 命令 → 获取 rawEvents
5. LLM 分析 rawEvents → 生成分析报告
6. 弹出 agent-interact custom 对话框展示分析报告（见下方代码）
   - 展示操作流程摘要、事件统计、可参数化的值
   - 提供文本输入区域让用户补充说明
   - 用户选择"生成并保存"或"不需要"
7. 用户确认后 → 生成结构化工作流 JSON → 调用 save 保存
8. 弹出 agent-interact custom 对话框询问产物生成（见下方代码）
   - 提供生成模式选择（Skill / Skill+Playwright / 仅Playwright）
   - 提供 Skill 名称和目标路径输入
   - 用户选择"生成"或"跳过"
9. 用户确认后 → 调用 generate 命令生成产物
```

**重要**：步骤 8 必须通过 agent-interact 弹框交互，禁止在对话文本中提问。所有需要用户选择或输入的环节都应使用 agent-interact。

### agent-interact 强制交互规则

**核心原则**：在整个录制流程中，所有需要用户选择、确认或输入的环节，**必须**通过 agent-interact 弹框完成。**禁止**在对话文本中提问或列出选项让用户回复。

违反此规则的典型错误：
- ❌ 在对话中写"需要我生成 Skill 吗？请选择：1. Skill 2. Playwright"
- ❌ 在对话中写"请告诉我 Skill 名称和目标路径"
- ✅ 调用 agent-interact dialog 弹出选择/输入对话框

**必须使用 agent-interact 的环节**：
- 步骤 3：录制等待（wait 类型）
- 步骤 6：分析报告展示 + 确认（custom 类型）
- 步骤 8：产物选择 + 参数输入（custom 类型）

**调用方式**（选择一种可用的路径）：

```bash
# 方式 1：项目内 skill
node skills/agent-interact/tool.js dialog '<JSON>'

# 方式 2：全局安装的 skill
node ~/.cursor/skills/agent-interact/tool.js dialog '<JSON>'
```

**降级策略**：仅当 agent-interact skill 完全不存在时，才降级为对话模式。

**注意**：
- LLM 不应在 record 和 agent-interact 之间插入任何其他操作或对话。
- agent-interact dialog 命令是阻塞的（等用户点击才返回），应设置足够长的超时等待（如 `block_until_ms: 3600000`），**不要**用 `sleep + 轮询` 方式。

### 录制等待对话框（步骤 3）

record 命令返回成功后，**必须立即**弹出等待对话框：

```bash
node skills/agent-interact/tool.js dialog '{"type":"wait","title":"🔴 正在录制浏览器操作","message":"浏览器已打开，请在浏览器中完成所有操作。\n操作完成后点击下方按钮停止录制。","confirmText":"✅ 操作完成，停止录制","timeout":3600}'
```

### 分析报告对话框（步骤 6）

stop 命令返回后，LLM 分析 rawEvents 并通过 agent-interact custom 对话框展示报告：

```bash
node skills/agent-interact/tool.js dialog '{"type":"custom","schemaVersion":"1.0","title":"📊 录制分析报告","timeout":1200,"content":[{"kind":"kv","items":[{"key":"录制名称","value":"<name>"},{"key":"时长","value":"<duration>"},{"key":"DOM 事件","value":"<domCount>"},{"key":"网络请求","value":"<networkCount>"}]},{"kind":"divider"},{"kind":"heading","value":"操作流程","level":3},{"kind":"text","value":"<步骤列表>"},{"kind":"divider"},{"kind":"heading","value":"可参数化的值","level":3},{"kind":"text","value":"<参数列表>"},{"kind":"divider"},{"kind":"textarea","id":"notes","label":"补充说明（可选）","placeholder":"如有需要补充的信息请在此输入..."}],"actions":[{"id":"save","label":"✅ 生成并保存","submit":true},{"id":"cancel","label":"❌ 不需要"}]}'
```

用户点击"生成并保存"后，LLM 根据 rawEvents + 用户补充信息生成工作流 JSON 并保存。

### 产物选择对话框（步骤 8）

save 命令成功后，**必须立即**弹出 agent-interact custom 对话框让用户选择产物形态：

```bash
node skills/agent-interact/tool.js dialog '{"type":"custom","schemaVersion":"1.0","title":"🎯 生成产物选择","timeout":300,"content":[{"kind":"kv","items":[{"key":"工作流名称","value":"<name>"},{"key":"工作流 ID","value":"<id>"},{"key":"步骤数","value":"<stepCount>"}]},{"kind":"divider"},{"kind":"heading","value":"选择生成方式","level":3},{"kind":"select","id":"generateMode","label":"生成模式","options":["Skill 产物（SKILL.md + tool.js + workflow.json + package.json）","Skill + Playwright 脚本（两者兼有）","仅 Playwright 脚本（不生成 Skill）"],"default":"Skill + Playwright 脚本（两者兼有）"},{"kind":"divider"},{"kind":"input","id":"skillName","label":"Skill 名称","placeholder":"例如：deploy-staging"},{"kind":"input","id":"targetPath","label":"目标路径","placeholder":"例如：~/.cursor/skills/deploy-staging"}],"actions":[{"id":"generate","label":"✅ 生成","submit":true},{"id":"skip","label":"⏭️ 跳过","variant":"outline","submit":false}]}'
```

用户选择后，LLM 根据 `generateMode` 字段调用 generate 命令：
- "Skill 产物..." → `generate '{"id":"<id>","skillName":"<name>","target":"<path>"}'`
- "Skill + Playwright..." → `generate '{"id":"<id>","skillName":"<name>","target":"<path>","includePlaywright":true}'`
- "仅 Playwright..." → `generate '{"id":"<id>","skillName":"<name>","target":"<path>","format":"playwright"}'`

如果用户未填写 skillName 或 targetPath，LLM 应根据工作流名称自动生成合理的默认值。

### custom dialog schema 强制约束

调用 agent-interact custom 对话框时，**必须严格遵守以下规则**：

1. **必须包含** `"schemaVersion":"1.0"`
2. **content 数组中每个节点使用 `kind` 字段**（不是 `type`），值的字段用 `value`（不是 `text`）
3. **按钮使用 `actions` 数组**（不是 `buttons`），每个 action 包含 `id`、`label`，可选 `submit`、`variant`
4. **可用的 kind 值**：`text`、`heading`、`divider`、`alert`、`badge`、`kv`、`progress`、`chart`、`code`、`image`、`table`、`input`、`select`、`checkbox`、`textarea`、`row`、`column`、`grid`、`section`、`group`

**错误处理**：调用 agent-interact dialog 后，**必须检查返回结果**。如果返回 `"error": "Invalid custom schema"` 或 exit code 非 0，LLM 应：
1. 读取 `details` 中的错误信息
2. 根据错误修正 JSON schema（常见错误：`type` → `kind`，`text` → `value`，`buttons` → `actions`，缺少 `schemaVersion`）
3. 重新调用 dialog 命令

### 何时建议录制

| 场景 | 操作 |
|------|------|
| 用户要求执行重复性浏览器操作 | 主动建议录制 |
| 用户说"录制"、"记录操作"、"学习操作" | 执行录制流程 |
| 录制完成后 | 弹出产物选择对话框 |
| 用户说"重放"、"再执行一次" | 执行 replay |

### LLM 分析 rawEvents 的要求

stop 返回的 rawEvents 包含 DOM 事件和网络请求的原始数据。LLM 需要：

1. **过滤噪音**：去除无关点击（空白区域）、无意义滚动
2. **合并输入**：连续的 input 事件合并为单次填写操作；同一输入框的多次 change/input 事件只保留最终值
3. **捕获操作意图**（关键，影响 LLM 自愈能力）：
   - 每步必须包含 `intent` 字段，格式：「[在什么上下文中] + 操作目标 + [期望产生的页面变化]」
   - 示例（正确）：「在部署任务列表第一行，点击 Deploy 按钮，以打开部署配置对话框」
   - 示例（不足）：「点击 Deploy」（缺少上下文和期望结果，LLM 无法用于自愈）
   - `description` 字段保留简短描述，`intent` 字段承载完整语义
4. **识别参数**：将可变输入值替换为 `{{paramName}}`
5. **关联 API**：将 DOM 操作与触发的 API 请求关联
6. **生成等待条件**（`waitAfter` 字段，优先于固定时间等待）：
   - 导航后：等待目标页面关键元素出现 `{ "type": "selector", "value": ".some-key-element" }`
   - 点击触发 modal：等待 modal 容器出现 `{ "type": "selector", "value": ".modal-container" }`
   - 提交后等待完成：等待加载状态消失 `{ "type": "selectorGone", "value": ".loading-spinner" }`
   - 页面跳转：等待 URL 变化 `{ "type": "url", "value": "/target-path" }`
7. **识别 UI 容器模式**：
   - 点击按钮 → 弹出 modal：后续步骤的 intent 和 locator 应说明「在弹出对话框中」
   - 下拉菜单展开：选项的 intent 应说明「在展开的下拉菜单中」
   - 表格行操作：intent 应包含行锚定信息，如「在显示 job-name-xxx 的那一行中」
8. **事件去重**：同一元素连续多次 click 合并为一次；导航后 500ms 内的误触点击丢弃
9. **保留 locator 元数据**：
   - `roleName`：录制脚本自动提取的 accessible name（aria-label / label[for] / aria-labelledby），生成 workflow 时必须保留
   - `context`：录制脚本自动检测的容器上下文（modal / dropdown / table-row / form），生成 workflow 时必须保留在 locators 中
   - 这两个字段是 `buildLocatorChain` 作用域限定和精确匹配的关键输入

分析后生成的工作流 JSON 通过 save 命令保存。

## 录制数据说明

### DOM 事件类型

| type | 说明 | 关键字段 |
|------|------|----------|
| click | 用户点击 | locators |
| input | 文本输入 | locators, value |
| select | 下拉选择 | locators, value, selectedText |
| check | 勾选复选框 | locators, checked |
| submit | 表单提交 | locators |
| keydown | 特殊按键（Enter/Tab/Escape） | key, modifiers |
| navigation | 页面导航 | url / fromUrl, toUrl |

### 网络请求

| 字段 | 说明 |
|------|------|
| request.url | 请求 URL |
| request.method | HTTP 方法 |
| request.body | 请求体（已解析 JSON） |
| response.status | 响应状态码 |
| response.body | 响应体（文本类 MIME，≤512KB） |

自动过滤静态资源（.js/.css/.png 等）和 tracking 请求。

## 参数化语法

工作流中的可变值使用 `{{paramName}}` 标记：

```json
{
  "command": "fill",
  "args": { "text": "{{username}}" },
  "locators": { "css": "#username", "placeholder": "Username" }
}
```

重放时通过 params 注入：

```bash
node tool.js replay '{"id":"wf-xxx","params":{"username":"admin"}}'
```

导出为 Playwright 脚本时，参数通过环境变量注入：

```bash
USERNAME=admin PASSWORD=secret node deploy-staging.js
```

## 产物形态

| 形态 | 命令 | 适合场景 |
|------|------|----------|
| JSON 工作流 | `save` | 临时或低频操作 |
| 独立 Skill | `generate` | 高频复用、跨项目 |
| Skill + Playwright 脚本 | `generate` + `includePlaywright` | 两种方式都需要 |
| 仅 Playwright 脚本 | `generate` + `format:"playwright"` | 只需脚本，不需要 Skill |
| 单文件 Playwright 脚本 | `export` | 快速导出到指定路径 |

Playwright 脚本特性：
- 可直接 `node script.js` 运行，不依赖 Cursor 或 Playwright Skill
- 与 replayer.js 一致的 locator 链（testId > ariaLabel > placeholder > text > role > id > css）
- 支持 context 作用域（modal/dropdown）
- 支持 waitAfter 条件
- 每步 try-catch + 失败截图
- 参数通过环境变量注入

## 数据存储

```
~/.cursor/skills/
├── web-automation-builder/           # Skill 代码
└── web-automation-builder-data/      # 数据目录
    ├── workflows/                    # 已保存的结构化工作流 JSON
    ├── recordings/                   # 录制数据（按日期归档）
    │   ├── 2026-02-23-wf-xxx.json   # 精简 summary（DOM事件+导航+API请求）
    │   └── ...
    ├── chrome-profile/                # Chrome 用户数据（认证缓存持久化）
    └── .recording.json               # 录制中的临时状态（stop 后删除）
```

## 触发词

- 录制浏览器操作、开始录制、帮我录制
- 重放工作流、再执行一次、用新参数执行
- 生成 Skill、做成 Skill、以后直接用
- 导出脚本、导出为 JS
- 查看录制、工作流列表
