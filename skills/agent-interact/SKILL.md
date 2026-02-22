---
name: agent-interact
description: |
  AI Agent 与用户之间的可视化交互桥梁。通过本地 Web Server + shadcn-vue 前端，
  支持确认选择、等待操作、图表展示三种弹框场景。任何 Agent 都可通过 HTTP API 调用。
---

# Agent Interact

为 AI Agent 提供可视化的用户交互能力。

## 快速开始

```bash
# 首次使用：安装依赖 + 构建前端
cd skills/agent-interact && npm install
cd ui && npm install && npm run build && cd ..

# 启动服务
node skills/agent-interact/tool.js start

# 发送弹框
node skills/agent-interact/tool.js dialog '{"type":"confirm","title":"选择环境","options":[{"id":"dev","label":"开发"},{"id":"prod","label":"生产"}]}'
```

## CLI 命令

```bash
node skills/agent-interact/tool.js start          # 启动服务（默认端口 7890）
node skills/agent-interact/tool.js stop           # 停止服务
node skills/agent-interact/tool.js status         # 检查服务状态
node skills/agent-interact/tool.js dialog '<JSON>' # 发送弹框（阻塞等待结果）
```

## 交互类型（7 种）

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

## HTTP API

Agent 也可以直接调用 REST API：

- `POST http://127.0.0.1:7890/api/dialog` — 创建弹框（阻塞直到用户响应）
- `GET http://127.0.0.1:7890/api/status` — 服务状态
- `GET http://127.0.0.1:7890/api/dialogs` — 活跃弹框列表
- `DELETE http://127.0.0.1:7890/api/dialog/:id` — 取消弹框

## 自然语言触发

| 用户说 | 执行 |
|--------|------|
| "弹个框让我选" / "让我确认一下" | 使用 confirm 类型 |
| "等我操作完" / "等我验证" | 使用 wait 类型 |
| "画个图" / "展示数据" / "可视化" | 使用 chart 类型 |
| "通知一下" / "提醒我" | 使用 notification 类型 |
| "让我填个表" / "需要我输入信息" | 使用 form 类型 |
| "需要我审批" / "确认这个操作" | 使用 approval 类型 |
| "展示进度" / "看看进展" | 使用 progress 类型 |
| "启动交互服务" | 执行 start 命令 |

## 技术栈

- **后端**：Node.js + Express + ws
- **前端**：Vite + Vue 3 + TypeScript + shadcn-vue + Tailwind CSS v4
- **图表**：Chart.js + vue-chartjs
