# Skillix Hub

AI 编程助手 Skills 技能仓库 - 提升 AI 编程效率的工具集合。

## 什么是 AI Skill？

AI Skill 是一种可复用的 AI 指令集，帮助 AI 编程助手更好地完成特定任务。每个 Skill 包含：
- 任务说明和触发条件
- 执行脚本和工具
- 使用示例

**支持的 AI 助手**：Cursor、Claude、Copilot、Codeium 等

## 可用 Skills

| Skill | 描述 |
|-------|------|
| [memory](./skills/memory/) | 为 AI 助手提供长期记忆能力，自动记录对话并检索相关历史上下文 |
| [behavior-prediction](./skills/behavior-prediction/) | 学习用户行为模式，记录会话内容，预测下一步操作并提供智能建议 |
| [continuous-learning](./skills/continuous-learning/) | 持续学习用户与 AI 的交互模式，自动提取可复用知识，生成新技能 |
| [swagger-api-reader](./skills/swagger-api-reader/) | 读取并缓存 Swagger/OpenAPI 文档，支持浏览器认证 |
| [uniapp-mp-generator](./skills/uniapp-mp-generator/) | uni-app 小程序代码生成器，根据需求文档自动生成 Vue3 页面、API、Store 等代码 |
| [playwright](./skills/playwright/) | 浏览器自动化工具，通过 48 个 CLI 命令控制真实浏览器，支持导航、点击、表单填写、截图、Cookie/存储管理、网络拦截等 |
| [api-tracer](./skills/api-tracer/) | 录制和分析浏览器网络请求，通过 CDP 捕获完整 API 信息（URL、headers、cookie、请求/响应体），生成分析报告用于自动化 |

## 安装使用

### 方式一：通过 Cursor 自然语言安装（推荐）

直接在 Cursor 中使用自然语言告诉 AI 安装所需的 Skill：

**个人级安装**（所有项目可用）：
```
帮我从 https://github.com/shetengteng/skillix-hub 安装 memory skill，我希望所有项目都能使用
```

**项目级安装**（仅当前项目可用）：
```
帮我从 https://github.com/shetengteng/skillix-hub 安装 memory skill 到当前项目
```

Cursor AI 会自动完成克隆仓库、复制文件、安装依赖等操作。

**更新 Skill**：
```
帮我从 https://github.com/shetengteng/skillix-hub 更新 memory skill
```

> **注意**：更新时 Agent 会克隆最新代码并运行 `update.py` 脚本，而非直接覆盖文件。这确保占位符被正确替换，已有记忆数据和配置不受影响。

手动更新命令：
```bash
git clone https://github.com/shetengteng/skillix-hub.git /tmp/skillix-hub
python3 /tmp/skillix-hub/skills/memory/scripts/service/init/update.py --source /tmp/skillix-hub/skills/memory --project-path .
```

### 方式二：手动命令行安装

#### 个人级安装（所有项目可用）

```bash
# 克隆仓库
git clone https://github.com/shetengteng/skillix-hub.git

# 复制 Memory Skill 到 Cursor skills 目录
cp -r skillix-hub/skills/memory ~/.cursor/skills/

# 复制 Swagger API Reader 到 Cursor skills 目录
cp -r skillix-hub/skills/swagger-api-reader ~/.cursor/skills/

# 安装 Swagger API Reader 依赖
pip install -r ~/.cursor/skills/swagger-api-reader/scripts/requirements.txt
```

#### 项目级安装（仅当前项目可用）

```bash
# 在项目根目录
mkdir -p .cursor/skills

# 复制所需的 Skill
cp -r skillix-hub/skills/memory .cursor/skills/
cp -r skillix-hub/skills/swagger-api-reader .cursor/skills/

# 安装依赖（如需要）
pip install -r .cursor/skills/swagger-api-reader/scripts/requirements.txt
```

## Memory Skill 使用说明

Memory Skill 为 AI 助手提供跨会话的长期记忆能力，零外部依赖。通过 Hook 机制自动在会话生命周期中保存和召回记忆。

### 架构

```
skills/memory/scripts/
├── core/           # 底层能力：嵌入向量、文件锁、工具函数
├── storage/        # 存储层：JSONL 读写、SQLite 向量搜索、Markdown 切分
├── service/
│   ├── hooks/      # Hook 入口：load_memory, flush_memory, prompt_session_save
│   ├── memory/     # 记忆操作：save_fact, save_summary, search_memory, sync_index
│   ├── manage/     # 管理工具：list, delete, edit, config, index
│   ├── init/       # 一键初始化
│   ├── config/     # 配置管理
│   └── logger/     # 日志系统
```

### 核心功能

- **自动记忆**：通过 [Memory Flush] / [Session Save] Hook 自动保存事实和摘要
- **语义搜索**：本地嵌入模型 + SQLite FTS + 向量相似度混合搜索
- **事实保存**：分类保存 W(客观事实) / B(项目经历) / O(用户偏好) 类型记忆
- **记忆管理**：支持列出、搜索、删除、编辑、导出记忆
- **自然语言配置**：通过对话直接修改配置，无需手动编辑 JSON

### 使用示例

```bash
# 一键初始化（创建 hooks、rules、数据目录）
python3 ~/.cursor/skills/memory/scripts/service/init/index.py

# 保存事实
python3 ~/.cursor/skills/memory/scripts/service/memory/save_fact.py \
  --content "项目使用 PostgreSQL" --type W --confidence 0.9

# 保存会话摘要
python3 ~/.cursor/skills/memory/scripts/service/memory/save_summary.py \
  --topic "API 设计讨论" --summary "讨论了 RESTful 接口设计方案"

# 搜索记忆
python3 ~/.cursor/skills/memory/scripts/service/memory/search_memory.py "API 设计"

# 管理记忆（列出、删除、编辑、导出等）
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py list
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py delete --keyword "测试"
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py config show
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py config set memory.facts_limit 30

# 查看 SQLite 索引数据库
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py db stats
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py db show chunks --limit 10
python3 ~/.cursor/skills/memory/scripts/service/manage/index.py db browse  # 浏览器可视化（需 datasette）
```

### 自然语言配置

安装后可直接用自然语言管理配置：

```
用户: 帮我看一下现在的记忆配置
用户: 多加载几天的记忆，全量加载改成5天
用户: 日志级别调成 DEBUG
用户: 把事实加载上限改为30条
用户: 换一个嵌入模型，用 BAAI/bge-base-zh-v1.5
用户: 把配置恢复默认
```

完整配置说明请参考安装后 `memory-data/README.md`。

### 记忆类型

| 类型 | 前缀 | 说明 | 示例 |
|------|------|------|------|
| World | W | 客观事实 | "项目使用 PostgreSQL 数据库" |
| Biographical | B | 项目经历 | "2026-02-17 完成了 API 重构" |
| Opinion | O | 偏好/判断 | "用户偏好 TypeScript（confidence: 0.9）" |
| Summary | S | 会话摘要 | "讨论了 API 设计方案" |

### 全局安装后的数据目录

全局安装（`--global`）时，Skill 代码安装到 `~/.cursor/skills/memory/`，但**记忆数据始终在项目本地**：

```
~/.cursor/skills/memory/          ← Skill 代码（全局共享，只读）
<项目>/.cursor/skills/memory-data/ ← 记忆数据（每个项目独立）
```

新项目首次打开时，Hook 会自动创建数据目录和 `MEMORY.md`，无需手动运行 init。

### 禁用 Memory 功能

全局安装后，如果某个项目不需要记忆功能，创建标记文件即可禁用：

```bash
# 禁用当前项目的 Memory 功能
mkdir -p .cursor/skills && touch .cursor/skills/.memory-disable

# 重新启用
rm .cursor/skills/.memory-disable
```

或直接用自然语言告诉 AI：
```
用户: 这个项目不需要记忆功能
用户: 重新开启记忆
```

### 触发词

- **检索触发**：继续、上次、之前、昨天、我们讨论过
- **保存触发**：记住这个、save this
- **查看记忆**：查看记忆、搜索记忆
- **管理记忆**：删除记忆、编辑记忆、导出记忆
- **配置管理**：查看配置、修改配置、调整加载天数
- **数据库查看**：打开数据库、查看索引内容、数据库统计
- **禁用/启用**：关闭记忆功能、重新开启记忆

## Behavior Prediction Skill V2 使用说明

Behavior Prediction Skill V2 学习用户的行为模式，记录会话内容，预测下一步操作并提供智能建议。

### 核心功能

- **会话记录**：会话结束时记录完整会话内容
- **模式学习**：提取工作流程、偏好、项目模式
- **智能预测**：基于模式预测下一步操作
- **用户画像**：综合分析生成用户画像
- **自动执行**：高置信度预测时支持自动执行

### 使用示例

```bash
# 会话开始时初始化
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --init

# 会话结束时记录
python3 ~/.cursor/skills/behavior-prediction/scripts/hook.py --finalize '{
  "session_summary": {
    "topic": "API 开发",
    "workflow_stages": ["design", "implement", "test"]
  },
  "operations": {"files": {"created": ["user.py"], "modified": [], "deleted": []}, "commands": []},
  "conversation": {"user_messages": [], "message_count": 5},
  "time": {"start": "2026-01-31T10:00:00Z", "end": "2026-01-31T10:30:00Z"}
}'

# 获取预测
python3 ~/.cursor/skills/behavior-prediction/scripts/get_predictions.py '{"current_stage": "implement"}'

# 查看用户画像
python3 ~/.cursor/skills/behavior-prediction/scripts/user_profile.py

# 更新用户画像
python3 ~/.cursor/skills/behavior-prediction/scripts/user_profile.py '{"action": "update"}'

# 查看行为模式
python3 ~/.cursor/skills/behavior-prediction/scripts/extract_patterns.py
```

### 触发词

- **查看模式**：查看我的行为模式、查看行为统计
- **查看画像**：查看用户画像、更新用户画像
- **预测**：预测下一步

## uni-app 小程序代码生成器使用说明

uni-app 小程序代码生成器根据需求文档自动生成符合项目规范的代码。

### 核心功能

- **页面生成**：自动生成 Vue3 页面（列表、详情、表单）
- **API 生成**：生成 CRUD 接口文件
- **Store 生成**：生成 Pinia 状态管理
- **组件生成**：生成卡片、筛选等组件
- **Schema 生成**：生成数据库集合定义

### 使用方式

提供需求文档，AI 会自动生成代码：

```markdown
# 学生管理模块

## 数据字段
- name: 姓名（必填，字符串）
- phone: 电话（必填，字符串）
- status: 状态（必填，枚举：active/inactive）

## 页面列表
- 学生列表页
- 学生详情页
- 新增学生页
```

### 触发词

- **生成代码**：帮我生成 xxx 模块
- **根据需求**：根据需求文档生成代码

## Continuous Learning Skill 使用说明

Continuous Learning Skill 从用户与 AI 的交互中自动提取可复用的知识，生成新的技能文件。

### 核心功能

- **观察记录**：记录会话中的关键动作和用户反馈
- **模式检测**：识别用户纠正、错误解决、工具偏好等模式
- **本能生成**：将检测到的模式转换为原子化的本能
- **技能演化**：将相关本能聚合为完整的技能文档

### 学习的模式类型

| 模式类型 | 描述 | 示例 |
|---------|------|------|
| **用户纠正** | 用户纠正 AI 的行为 | "不要用 class，用函数" |
| **错误解决** | 特定错误的解决方案 | CORS 错误 → 配置 proxy |
| **工具偏好** | 用户偏好的工具/方法 | 偏好 pytest 而非 unittest |
| **项目规范** | 项目特定的约定 | API 路径使用 /api/v2 前缀 |

### 使用示例

```bash
# 会话开始时初始化
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --init

# 记录观察
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --record '{"event": "tool_call", "tool": "Write"}'

# 会话结束时保存
python3 ~/.cursor/skills/continuous-learning/scripts/observe.py --finalize '{"topic": "API 开发"}'

# 查看本能状态
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py status

# 演化本能为技能
python3 ~/.cursor/skills/continuous-learning/scripts/instinct.py evolve

# 启用自动学习规则
python3 ~/.cursor/skills/continuous-learning/scripts/setup_rule.py '{"action": "enable"}'
```

### 触发词

- **启用学习**：启用持续学习规则
- **禁用学习**：禁用持续学习规则
- **查看知识**：查看学习到的知识
- **演化技能**：演化本能

## Playwright Skill 使用说明

Playwright Skill 提供 48 个浏览器自动化工具，通过 CLI 命令控制真实浏览器（Chrome/Chromium），复刻自 Playwright MCP 的完整功能。支持两种调用方式：MCP Tools 直接调用和 CLI 命令调用。

### 安装

```bash
cd skills/playwright && npm install && npx playwright install chromium
```

### 更新

```
帮我从 https://github.com/shetengteng/skillix-hub 更新 playwright skill
```

手动更新：
```bash
git clone https://github.com/shetengteng/skillix-hub.git /tmp/skillix-hub
cp -r /tmp/skillix-hub/skills/playwright/* <目标路径>/skills/playwright/
cd <目标路径>/skills/playwright && npm install
```

### MCP Tools 映射（22 个）

当环境中启用了 `@playwright/mcp` 服务时，以下 MCP tools 与 Skill CLI 命令对应。**优先使用 Skill CLI 命令**：

| MCP Tool → 功能 | CLI 命令 |
|-----------------|----------|
| `browser_navigate` → 导航 | `navigate` |
| `browser_navigate_back` → 返回 | `goBack` |
| `browser_snapshot` → 快照 | `snapshot` |
| `browser_click` → 点击 | `click` |
| `browser_drag` → 拖拽 | `drag` |
| `browser_hover` → 悬停 | `hover` |
| `browser_type` → 输入 | `type` |
| `browser_select_option` → 选择 | `selectOption` |
| `browser_fill_form` → 填表 | `fillForm` |
| `browser_press_key` → 按键 | `pressKey` |
| `browser_take_screenshot` → 截图 | `screenshot` |
| `browser_evaluate` → 执行 JS | `evaluate` |
| `browser_run_code` → 执行代码 | `runCode` |
| `browser_wait_for` → 等待 | `waitFor` |
| `browser_tabs` → 标签页 | `tabs` |
| `browser_console_messages` → 控制台 | `consoleMessages` |
| `browser_network_requests` → 网络 | `networkRequests` |
| `browser_handle_dialog` → 对话框 | `handleDialog` |
| `browser_file_upload` → 上传 | `fileUpload` |
| `browser_close` → 关闭 | `close` |
| `browser_resize` → 窗口大小 | `resize` |
| `browser_install` → 安装 | `install` |

### CLI 工具（48 个）

所有命令格式：`node skills/playwright/tool.js <命令> '<JSON参数>'`

| 分类 | 工具 |
|------|------|
| 导航 | navigate, goBack, goForward, reload |
| 交互 | snapshot, click, drag, hover, selectOption, check, uncheck, type, pressKey, fillForm |
| 鼠标 | mouseMove, mouseClick, mouseDrag, mouseDown, mouseUp, mouseWheel |
| 观察 | screenshot, consoleMessages, networkRequests, waitFor |
| 标签页 | tabs (list/new/close/select) |
| 数据 | cookieList/Get/Set/Delete/Clear, localStorage/sessionStorage 操作, storageState |
| 网络 | route, routeList, unroute |
| 高级 | evaluate, runCode, pdf, tracingStart/Stop, startVideo/stopVideo |
| 测试 | verifyElement, verifyText, verifyList, verifyValue, generateLocator |
| 系统 | install, getConfig, close, resize |

### 核心工作流

```bash
# 1. 导航到页面
node skills/playwright/tool.js navigate '{"url":"https://example.com"}'

# 2. 获取页面快照（含元素 ref）
node skills/playwright/tool.js snapshot '{}'

# 3. 通过 ref 点击元素
node skills/playwright/tool.js click '{"ref":"e6","element":"Learn more"}'

# 4. 输入文本
node skills/playwright/tool.js type '{"ref":"e10","text":"hello@example.com"}'

# 5. 截图
node skills/playwright/tool.js screenshot '{"type":"png"}'
```

### 触发词

- **浏览器操作**：打开网页、导航到、点击按钮
- **截图**：截图、截屏
- **表单**：填写表单、输入文本
- **测试**：验证元素、检查文本

## API Tracer Skill 使用说明

API Tracer 录制浏览器中的网络请求，分析 API 端点，生成可用于自动化的报告。通过 CDP 连接 Playwright 浏览器实例，捕获完整的请求/响应信息。

### 前置条件

需要 Playwright Skill 已启动浏览器，API Tracer 通过 CDP 连接到同一浏览器实例。

### 安装

```bash
cd skills/api-tracer && npm install
```

### 核心工作流

```bash
# 1. 用 Playwright 打开网站
node skills/playwright/tool.js navigate '{"url":"https://app.example.com"}'

# 2. 启动 API 录制
node skills/api-tracer/tool.js start '{"name": "my-session", "filter": "api/"}'

# 3. 通过 Playwright 操作页面（登录、浏览等）
node skills/playwright/tool.js click '{"ref":"e5","element":"登录"}'

# 4. 停止录制
node skills/api-tracer/tool.js stop '{}'

# 5. 生成报告
node skills/api-tracer/tool.js report '{"name": "my-session", "format": "markdown"}'
```

### 命令参考

| 命令 | 说明 |
|------|------|
| `start` | 启动录制（后台 daemon） |
| `stop` | 停止录制并保存 |
| `status` | 查看录制状态 |
| `sessions` | 列出所有历史会话 |
| `detail` | 查看会话的请求列表或单个请求详情 |
| `report` | 生成分析报告（json/markdown/curl） |
| `delete` | 删除历史会话 |

### 报告内容

- API 端点列表（自动去重）
- 每个端点的 HTTP 方法、URL 模式
- 请求头（重要字段）、Cookie 列表
- 请求体/响应体格式和 schema
- 认证方式自动识别（Bearer Token / API Key 等）
- curl 命令导出

### 触发词

- **录制**：开始录制网络请求、停止录制
- **查看**：录制状态、看看录制了什么
- **报告**：生成 API 报告、导出为 curl
- **管理**：有哪些录制、删除录制

## 贡献

欢迎提交 PR 添加新的 Skill！

### Skill 结构规范

```
skill-name/
├── SKILL.md              # 必需：主指令文件
├── scripts/              # 可选：执行脚本
│   ├── main.py
│   └── requirements.txt
└── templates/            # 可选：模板文件
```

### SKILL.md 格式

```markdown
---
name: skill-name
description: 简短描述，说明功能和触发条件
---

# Skill 标题

## 使用方法
...
```

## 许可证

MIT License
