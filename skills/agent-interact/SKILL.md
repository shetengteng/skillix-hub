---
name: agent-interact
description: |
  AI Agent 与用户之间的可视化交互桥梁。通过 Electron 独立窗口 + shadcn-vue 前端，
  支持 7 种预定义交互 + custom 通用渲染。Agent 发起交互时自动弹出置顶窗口，用户无需切换应用。
---

# Agent Interact

为 AI Agent 提供可视化的用户交互能力。交互弹框通过 Electron 独立窗口弹出，置顶显示在屏幕最前面。

## 快速开始

```bash
# 首次使用：安装依赖 + 构建前端
cd skills/agent-interact && npm install
cd ui && npm install && npm run build && cd ..

# 启动服务（同时启动 Electron）
node skills/agent-interact/tool.js start

# 发送弹框（Electron 窗口自动弹出）
node skills/agent-interact/tool.js dialog '{"type":"confirm","title":"选择环境","options":[{"id":"dev","label":"开发"},{"id":"prod","label":"生产"}]}'
```

## CLI 命令

```bash
node skills/agent-interact/tool.js start          # 启动服务 + Electron
node skills/agent-interact/tool.js stop           # 停止服务 + Electron
node skills/agent-interact/tool.js status         # 检查服务和 Electron 状态
node skills/agent-interact/tool.js dialog '<JSON>' # 发送弹框（Electron 窗口自动弹出）
```

## 交互类型（7 种预定义 + custom 通用渲染）

### confirm — 确认选择

```bash
node skills/agent-interact/tool.js dialog '{"type":"confirm","title":"请选择","options":[{"id":"a","label":"选项A"},{"id":"b","label":"选项B"}]}'
```

### wait — 等待操作

```bash
node skills/agent-interact/tool.js dialog '{"type":"wait","title":"等待验证","message":"请完成指纹验证后点击确认","confirmText":"已完成"}'
```

### chart — 图表展示

支持 line/bar/pie/doughnut/radar。

```bash
node skills/agent-interact/tool.js dialog '{"type":"chart","title":"分析","chartType":"line","data":{"labels":["Mon","Tue","Wed"],"datasets":[{"label":"P99","data":[120,150,90]}]}}'
```

### notification — 通知提醒（非阻塞）

推送通知后立即返回，不等待用户响应。

```bash
node skills/agent-interact/tool.js dialog '{"type":"notification","level":"success","title":"部署完成","message":"v2.0 已部署","autoClose":5}'
```

### form — 表单输入

Agent 需要用户填写结构化数据。

```bash
node skills/agent-interact/tool.js dialog '{"type":"form","title":"数据库配置","fields":[{"id":"host","label":"主机","type":"text","default":"localhost"},{"id":"port","label":"端口","type":"number","default":5432},{"id":"db","label":"数据库","type":"select","options":["postgres","mysql"]}]}'
```

### approval — 审批门控

Agent 执行敏感操作前需要用户审批。

```bash
node skills/agent-interact/tool.js dialog '{"type":"approval","title":"确认删除","message":"即将删除 production 数据库","severity":"critical","details":{"action":"DROP TABLE","database":"production"}}'
```

### progress — 进度展示

展示多步骤任务的实时进度。

```bash
node skills/agent-interact/tool.js dialog '{"type":"progress","title":"部署进度","steps":[{"id":"build","label":"构建","status":"completed"},{"id":"test","label":"测试","status":"running"},{"id":"deploy","label":"部署","status":"pending"}],"percent":45}'
```

### custom — 通用渲染（自由编排）

当预定义类型无法满足需求时，使用 `custom` 类型自由编排弹框内容。通过 JSON 描述 `content` 数组，前端动态递归渲染。

**可用组件**：

| 分类 | kind | 说明 |
|------|------|------|
| 展示 | `text`, `heading`, `divider`, `alert`, `badge`, `code`, `image`, `kv`, `progress` | 纯展示，无交互 |
| 数据 | `table`, `chart` | 表格和图表 |
| 输入 | `input`, `textarea`, `select`, `checkbox` | 表单字段，数据随 action 提交 |
| 布局 | `row`, `column`, `grid`, `section`, `group` | 嵌套布局容器 |

```bash
node skills/agent-interact/tool.js dialog '{"type":"custom","title":"部署确认","content":[{"kind":"alert","value":"即将部署到生产环境","level":"error"},{"kind":"kv","items":[{"key":"版本","value":"v2.3.1"},{"key":"分支","value":"release/2.3.1"}]},{"kind":"input","id":"reason","label":"部署原因","required":true}],"actions":[{"id":"deploy","label":"确认部署","variant":"destructive","submit":true,"requireValid":true},{"id":"cancel","label":"取消","variant":"outline","submit":false}]}'
```

**actions 字段**：

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `submit` | `true` | 是否提交表单数据 |
| `requireValid` | `false` | 是否要求校验通过才能提交 |
| `closeOnSubmit` | `true` | 提交后是否关闭弹框 |

**Schema 校验**：服务端使用 Ajv 严格校验，未知 `kind` 或格式错误直接返回 400 + 错误路径。收到 400 时仅修正报错路径字段，不重写整份 JSON。

**性能限制**：`content` 最多 40 项，嵌套深度 ≤ 4，表格 ≤ 200 行，图表 ≤ 1000 点。

## HTTP API

Agent 也可以直接调用 REST API：

- `POST http://127.0.0.1:7890/api/dialog` — 创建弹框（阻塞直到用户响应）
- `GET http://127.0.0.1:7890/api/status` — 服务状态
- `GET http://127.0.0.1:7890/api/dialogs` — 活跃弹框列表
- `DELETE http://127.0.0.1:7890/api/dialog/:id` — 取消弹框

## 自主决策指南

LLM 在任务执行中应**自主判断**何时需要用户介入，主动选择合适的交互类型。用户不需要指定弹框类型。

### 何时弹什么框

| 任务上下文 | 使用类型 | 示例 |
|------------|----------|------|
| 存在多个可行方案，无法自动判断 | confirm | 检测到 3 个环境，让用户选 |
| 即将执行不可逆/高风险操作 | approval | 删除数据库、修改生产配置 |
| 缺少必要的结构化信息 | form | 需要数据库连接参数 |
| 需要用户完成外部操作才能继续 | wait | 等待用户在另一系统中审批 |
| 需要可视化展示数据分析结果 | chart | 性能分析完成，展示趋势图 |
| 任务状态变更需通知用户（不阻塞） | notification | 部署完成、构建失败 |
| 长时间多步骤任务展示进度 | progress | 多步部署流程进行中 |
| 需要混合展示（表格+图表+输入） | custom | 分析报告、部署确认、数据对比 |

### 不应弹框的情况

- 能自动判断的不要问用户（如只有一个选项）
- 不要每一步都弹框确认（过度交互）
- 低风险操作不要用 approval（用 confirm 或直接执行）
- 需要多字段输入时不要用 confirm（用 form）

## 窗口行为

- **弹出方式**：Electron 独立窗口，置顶显示（`alwaysOnTop`）
- **关闭行为**：用户操作后窗口自动关闭
- **notification**：走系统原生通知，不弹窗口
- **Fallback**：Electron 不可用时自动降级为浏览器模式

## 技术栈

- **窗口**：Electron（独立置顶窗口）
- **后端**：Node.js + Express + ws
- **前端**：Vite + Vue 3 + TypeScript + shadcn-vue + Tailwind CSS v4
- **图表**：Chart.js + vue-chartjs
