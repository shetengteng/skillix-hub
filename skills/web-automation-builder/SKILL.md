---
name: web-automation-builder
description: |
  学习用户浏览器操作行为，录制为可重放的参数化工作流。
  支持生成独立 Skill、导出 Playwright 脚本。依赖 Playwright Skill。
---

# Web Automation Builder

录制浏览器操作序列，保存为可重放的工作流。支持参数化（相同流程不同输入值）、生成独立 Skill、导出 Playwright 脚本。

## 安装 / 更新

```bash
# 从 skillix-hub 仓库安装到全局（自动安装依赖 Playwright Skill）
node skills/web-automation-builder/tool.js install '{"target":"~/.cursor/skills/web-automation-builder"}'

# 更新（删除旧版 → 重新安装）
node skills/web-automation-builder/tool.js update '{"target":"~/.cursor/skills/web-automation-builder"}'
```

## 前置依赖

| 依赖 | 说明 | 安装方式 |
|------|------|----------|
| **Playwright Skill** | 浏览器自动化引擎，提供 48 个操作命令 | `skills/playwright/` 或 `~/.cursor/skills/playwright/` |

`install` 命令会自动检查 Playwright Skill 是否存在，未安装时给出提示。

## CLI 命令

```bash
node skills/web-automation-builder/tool.js <command> '<JSON参数>'
```

### 录制控制

```bash
# 开始录制
node skills/web-automation-builder/tool.js record '{"name":"登录后台"}'

# 录制模式下执行浏览器操作（代理转发到 Playwright）
node skills/web-automation-builder/tool.js exec '{"command":"navigate","args":{"url":"https://example.com"}}'
node skills/web-automation-builder/tool.js exec '{"command":"click","args":{"ref":"e5","element":"登录"}}'
node skills/web-automation-builder/tool.js exec '{"command":"type","args":{"ref":"e10","text":"admin"}}'

# 停止录制（自动保存工作流）
node skills/web-automation-builder/tool.js stop '{}'

# 查看录制状态
node skills/web-automation-builder/tool.js status '{}'
```

### 工作流管理

```bash
node skills/web-automation-builder/tool.js list '{}'
node skills/web-automation-builder/tool.js show '{"id":"wf-xxx"}'
node skills/web-automation-builder/tool.js delete '{"id":"wf-xxx"}'
```

### 重放

```bash
# 基础重放
node skills/web-automation-builder/tool.js replay '{"id":"wf-xxx"}'

# 带参数重放
node skills/web-automation-builder/tool.js replay '{"id":"wf-xxx","params":{"username":"admin","password":"123"}}'
```

### 参数化分析

```bash
# 分析工作流，输出参数化建议
node skills/web-automation-builder/tool.js analyze '{"id":"wf-xxx"}'
```

LLM 根据 analyze 输出，将工作流中的输入值替换为 `{{paramName}}` 模板变量。

### 生成独立 Skill

```bash
# 生成到全局 Skill 目录
node skills/web-automation-builder/tool.js generate '{"id":"wf-xxx","skillName":"deploy-staging","target":"~/.cursor/skills/deploy-staging"}'
```

生成的 Skill 包含 `SKILL.md`、`tool.js`、`workflow.json`、`package.json`，可被 Cursor 自动识别。

### 导出 Playwright 脚本

```bash
node skills/web-automation-builder/tool.js export '{"id":"wf-xxx","output":"./my-automation.js"}'
```

## 自主决策指南

LLM 在任务执行中应自主判断何时使用录制功能：

| 场景 | 操作 |
|------|------|
| 用户要求执行重复性浏览器操作 | 主动建议录制 |
| 用户说"录制"、"记录操作" | 执行 `record` + `exec` 代理模式 |
| 录制完成后 | 执行 `analyze` 分析参数，询问是否生成 Skill |
| 用户说"部署到 staging"且已有对应 Skill | 直接调用生成的 Skill |
| 用户说"重放"、"再执行一次" | 执行 `replay` |

## 产物形态

| 形态 | 命令 | 适合场景 |
|------|------|----------|
| JSON 工作流 | `stop`（自动保存） | 临时或低频操作 |
| 独立 Skill | `generate` | 高频复用、跨项目 |
| Playwright 脚本 | `export` | 脱离 Cursor 使用 |

## 数据存储

工作流数据存储在 Skill 安装目录的**同级** `web-automation-builder-data/` 目录下：

```
~/.cursor/skills/                          # 全局安装时
├── web-automation-builder/                # Skill 代码
└── web-automation-builder-data/           # 数据目录
    ├── workflows/                         # 已录制的工作流 JSON
    └── .recording.json                    # 录制中的临时状态

<项目>/.cursor/skills/                     # 项目级安装时
├── web-automation-builder/
└── web-automation-builder-data/
    └── workflows/
```

Skill 在哪里安装，数据就在哪个 skills 目录下。

## 参数化语法

工作流中的可变值使用 `{{paramName}}` 标记：

```json
{
  "command": "type",
  "args": { "ref": "e10", "text": "{{username}}" }
}
```

重放时通过 `params` 注入：

```bash
node tool.js replay '{"id":"wf-xxx","params":{"username":"admin"}}'
```

## 自然语言使用示例

以下展示用户如何通过自然语言与 Agent 交互完成录制、重放和生成 Skill 的完整流程。

### 示例 1：录制登录流程

```
用户: 帮我录制一下登录公司后台的操作

Agent 内部执行:
  1. record '{"name":"登录公司后台"}'
  2. exec '{"command":"navigate","args":{"url":"https://admin.company.com"}}'
  3. exec '{"command":"snapshot","args":{}}'  → 获取页面元素
  4. exec '{"command":"type","args":{"ref":"e10","text":"zhangsan"}}'
  5. exec '{"command":"type","args":{"ref":"e12","text":"password123"}}'
  6. exec '{"command":"click","args":{"ref":"e15","element":"登录"}}'
  7. stop '{}'

Agent: 录制完成！已保存工作流「登录公司后台」，共 4 个操作步骤。
      要不要我分析一下哪些值可以参数化？
```

### 示例 2：参数化 + 重放

```
用户: 分析一下刚才的录制，把用户名和密码参数化

Agent 内部执行:
  1. analyze '{"id":"wf-xxx"}'  → 识别出 step 2 和 step 3 的 text 是可变输入
  2. 修改 workflow.json，将 "zhangsan" → "{{username}}"，"password123" → "{{password}}"

Agent: 已参数化！现在工作流有 2 个参数：username 和 password。
      下次可以用不同账号重放。

用户: 用 lisi 的账号登录一下

Agent 内部执行:
  replay '{"id":"wf-xxx","params":{"username":"lisi","password":"lisi@2026"}}'

Agent: 已用 lisi 账号完成登录。
```

### 示例 3：生成独立 Skill

```
用户: 把这个登录流程做成一个 Skill，以后直接用

Agent 内部执行:
  generate '{"id":"wf-xxx","skillName":"login-company-admin","target":"~/.cursor/skills/login-company-admin"}'

Agent: 已生成独立 Skill「login-company-admin」，安装到 ~/.cursor/skills/login-company-admin/。
      以后你只需要说「登录公司后台」，我就会自动执行。

--- 下次新会话 ---

用户: 用 wangwu 的账号登录公司后台

Agent: （识别到已安装的 login-company-admin Skill）
  执行: node ~/.cursor/skills/login-company-admin/tool.js run '{"username":"wangwu","password":"wangwu@2026"}'

Agent: 已用 wangwu 账号登录公司后台。
```

### 示例 4：录制部署流程并生成 Skill

```
用户: 帮我录制一下部署到 staging 环境的操作

Agent: 好的，开始录制。请告诉我 CI/CD 平台的地址。

用户: https://ci.company.com

Agent 内部执行:
  1. record '{"name":"部署到 staging"}'
  2. exec navigate → ci.company.com
  3. exec snapshot → 获取页面
  4. exec click → 选择项目
  5. exec click → 选择分支
  6. exec click → 触发部署
  7. stop

Agent: 录制完成！共 4 步操作。检测到「分支选择」是可变参数，已自动标记为 {{branch}}。
      要生成 Skill 吗？

用户: 生成

Agent 内部执行:
  generate '{"id":"wf-xxx","skillName":"deploy-staging","target":"~/.cursor/skills/deploy-staging"}'

Agent: 已生成 Skill「deploy-staging」。以后说「部署 release/2.3 到 staging」我就自动执行。
```

### 示例 5：导出为脚本

```
用户: 把登录流程导出为 JS 脚本，我要在 CI 里用

Agent 内部执行:
  export '{"id":"wf-xxx","output":"./scripts/login-automation.js"}'

Agent: 已导出到 ./scripts/login-automation.js。
      运行方式：USERNAME=admin PASSWORD=xxx node scripts/login-automation.js
```

## 触发词

- 录制浏览器操作、开始录制、帮我录制
- 重放工作流、再执行一次、用新参数执行
- 生成 Skill、做成 Skill、以后直接用
- 导出脚本、导出为 JS
- 查看录制、工作流列表、有哪些录制
