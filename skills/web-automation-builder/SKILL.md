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
# 安装依赖
cd skills/web-automation-builder && npm install

# 安装到全局
node skills/web-automation-builder/tool.js install '{"target":"~/.cursor/skills/web-automation-builder"}'
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
node tool.js replay '{"id":"wf-xxx"}'
node tool.js replay '{"id":"wf-xxx","params":{"username":"admin","password":"123"}}'
```

### 生成独立 Skill

```bash
node tool.js generate '{"id":"wf-xxx","skillName":"deploy-staging","target":"~/.cursor/skills/deploy-staging"}'
```

### 导出 Playwright 脚本

```bash
node tool.js export '{"id":"wf-xxx","output":"./my-automation.js"}'
```

## 自主决策指南

LLM 在录制流程中的行为协议：

### 录制流程

```
1. 用户请求录制 → 调用 record
2. record 返回成功 → 使用 agent-interact 的 wait 弹框通知用户
   （降级：在对话中告知用户"浏览器已打开，操作完成后告诉我"）
3. 等待用户通知操作完成
4. 调用 stop → 获取 rawEvents
5. LLM 分析 rawEvents → 生成结构化工作流 JSON
6. 调用 save 保存工作流
7. 向用户报告录制结果
```

### agent-interact 交互（优先使用）

录制开始后，优先使用 agent-interact skill 的 wait 弹框：

```bash
node agent-interact/tool.js dialog '{"type":"wait","title":"正在录制","message":"浏览器已打开，请完成操作后点击确认。","confirmText":"操作完成，停止录制"}'
```

如果 agent-interact 不可用，降级为对话模式等待用户输入。

### 何时建议录制

| 场景 | 操作 |
|------|------|
| 用户要求执行重复性浏览器操作 | 主动建议录制 |
| 用户说"录制"、"记录操作"、"学习操作" | 执行录制流程 |
| 录制完成后 | 询问是否生成 Skill |
| 用户说"重放"、"再执行一次" | 执行 replay |

### LLM 分析 rawEvents 的要求

stop 返回的 rawEvents 包含 DOM 事件和网络请求的原始数据。LLM 需要：

1. **过滤噪音**：去除无关点击（空白区域）、无意义滚动
2. **合并输入**：连续的 input 事件合并为单次填写操作
3. **识别意图**：为每步操作添加语义描述（"登录"、"选择分支"）
4. **识别参数**：将可变输入值替换为 `{{paramName}}`
5. **关联 API**：将 DOM 操作与触发的 API 请求关联
6. **推断等待**：根据导航和 API 响应推断步骤间的等待条件

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
| Playwright 脚本 | `export` | 脱离 Cursor 使用 |

## 数据存储

```
~/.cursor/skills/
├── web-automation-builder/           # Skill 代码
└── web-automation-builder-data/      # 数据目录
    ├── workflows/                    # 已保存的结构化工作流 JSON
    ├── recordings/                   # 原始录制数据（按日期归档）
    │   ├── 2026-02-23-wf-xxx.json   # 包含完整 rawEvents
    │   └── ...
    └── .recording.json               # 录制中的临时状态（stop 后删除）
```

## 触发词

- 录制浏览器操作、开始录制、帮我录制
- 重放工作流、再执行一次、用新参数执行
- 生成 Skill、做成 Skill、以后直接用
- 导出脚本、导出为 JS
- 查看录制、工作流列表
