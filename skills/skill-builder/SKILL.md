---
name: skill-builder
description: |
  skillix-hub 项目标准化 Skill 开发流程指南和脚手架工具。当用户要求创建新 Skill、
  初始化 Skill 目录结构、或询问 Skill 开发规范时使用。提供 10 阶段完整生命周期：
  需求命名、可行性分析、设计文档、讨论迭代、代码开发、单元测试、测试报告、技术文档、README 同步、docs 同步。
---

# Skill Builder

skillix-hub 项目中创建新 Skill 的标准化流程和脚手架工具。

## 脚手架工具

初始化新 Skill 的完整目录结构和模板文件：

```bash
node skills/skill-builder/scaffold.js init '{"name":"my-skill","tech":"node","description":"简短描述"}'
```

参数：
- `name`（必填）：小写字母+数字+连字符，如 `web-content-reader`
- `tech`：`node`（默认）、`python` 或其他（根据 Skill 需求选择最合适的技术栈）
- `description`：简短描述

生成的目录结构：

```
skills/<name>/          # Skill 源码
  SKILL.md, tool.js, package.json, lib/
design/<name>/          # 设计文档
  YYYY-MM-DD-01-设计文档.md
tests/<name>/           # 测试
  run_tests.js, src/unit/test_example.js, reports/
```

## 开发流程（10 阶段）

当用户要求创建新 Skill 时，严格按以下顺序执行每个阶段。

---

### Phase 1：需求命名

**目标**：确认 Skill 名称、技术栈、使用场景。

**执行步骤**：

1. 根据用户描述的功能需求，**给出 3-5 个命名推荐**，每个附带简要理由：
   ```
   推荐命名：
   1. data-analyzer — 强调数据分析能力
   2. data-insight  — 强调洞察输出
   3. csv-parser    — 强调具体输入格式
   推荐：方案 1，最准确描述核心功能
   ```

2. **命名讨论（必须）**：使用 AskQuestion 工具让用户从推荐中选择或自定义，同时确认：
   - Skill 名称
   - 技术栈（Node.js、Python 或其他，根据需求选择）
   - 核心功能描述
   - 使用场景（Agent 内部 / 用户手动 / 两者）

3. **命名规范（强制）**：
   - 全小写，单词用连字符分隔
   - 描述性名称，避免 `helper`、`utils` 等模糊词
   - 名称应准确反映核心功能，不要太宽泛也不要太狭窄
   - 考虑未来扩展性：如 `agent-interact` 比 `agent-dialog` 更通用
   - 示例：`web-content-reader`、`api-tracer`、`swagger-api-reader`、`agent-interact`

4. **命名记录**：将所有候选方案、选择理由记录在设计文档的 Phase 1 章节中

5. 运行脚手架初始化目录：
   ```bash
   node skills/skill-builder/scaffold.js init '{"name":"<name>","tech":"<tech>","description":"<desc>"}'
   ```

---

### Phase 2：可行性分析

**目标**：在投入设计之前，快速验证 Skill 的技术可行性和实现路径。

**路径规范**：`design/<name>/YYYY-MM-DD-NN-可行性分析.md`

**文档结构**：

1. **需求摘要**：一段话描述 Skill 要解决的核心问题
2. **技术可行性**：
   - 关键技术点逐一分析（是否有成熟方案、是否需要外部依赖）
   - 已知限制和约束（平台、权限、性能等）
   - 原型验证（如有必要，附上关键代码片段或 PoC 结果）
3. **方案对比**：至少 2 种实现路径，含优缺点对比表
4. **推荐方案**：选定路径及理由
5. **风险评估**：技术风险、依赖风险、维护风险
6. **结论**：可行 / 有条件可行 / 不可行，附建议

**执行要求**：
- 一次性输出完整文档，不在对话中碎片化讨论
- 用户确认可行后再进入设计文档阶段
- 如果结论为"不可行"，与用户讨论替代方案

---

### Phase 3：设计文档

**目标**：编写完整设计文档，包含技术方案和待讨论问题。

**重要原则**：
- **设计文档优先**：不要在 Plan 模式下讨论方案，直接将所有方案、对比、问题写入设计文档
- **问题驱动**：在文档末尾添加"待讨论问题"章节，列出需要用户确认的关键决策
- **一次性输出**：先完成完整文档，再让用户审阅，避免碎片化讨论

**路径规范**：`design/<name>/YYYY-MM-DD-NN-描述.md`
- `YYYY-MM-DD`：当前日期
- `NN`：当天序号（01 起步）
- 示例：`design/web-content-reader/2026-02-21-01-Web内容读取Skill设计文档.md`

**文档结构**（参考 `templates/design-doc.md.tpl`）：

1. **Phase 1 记录**：命名候选方案、选择结果和理由
2. **需求**：背景、目标、使用场景表格
3. **整体流程**：Mermaid flowchart
4. **技术方案**：至少 2 个方案对比，含优缺点和对比表
5. **推荐方案**：架构图、CLI 命令设计、输出格式、目录结构
6. **实现计划**：分 Phase 列出任务
7. **风险与注意事项**：风险表格
8. **待讨论问题**：列出需要用户确认的关键决策点（如技术选型、架构取舍等）

---

### Phase 4：讨论迭代

**目标**：基于设计文档与用户确认方案。

**执行步骤**：

1. **不要切换到 Plan 模式**，直接在对话中基于设计文档讨论
2. 使用 AskQuestion 工具让用户对"待讨论问题"逐一确认
3. 根据用户反馈直接修改设计文档
4. 迭代修改直到用户满意
5. 确认后进入代码开发阶段

---

### Phase 5：代码开发

**目标**：实现 Skill 源码。

**目录规范**：

```
skills/<name>/
├── SKILL.md          # Skill 文档（Phase 完成后编写）
├── tool.js           # CLI 入口（Node.js）
├── main.py           # CLI 入口（Python）
├── package.json      # Node.js 依赖（Node.js 项目）
├── requirements.txt  # Python 依赖（Python 项目）
└── lib/              # 核心模块
    └── ...
```

> 根据选择的技术栈保留对应的入口文件和依赖文件。

**CLI 入口规范**：

```bash
# Node.js
node skills/<name>/tool.js <command> '<json_params>'

# Python
python3 skills/<name>/main.py <command> [--param value]
```

**输出格式规范**：所有命令返回 JSON 到 stdout：

```json
{
  "result": { ... },
  "error": null
}
```

错误时：

```json
{
  "result": null,
  "error": "error message"
}
```

**编码规范**：
- 模块化：每个功能一个文件放在 `lib/` 下
- 不添加无意义注释
- 错误处理：所有命令 catch 异常返回 JSON error
- **长文本模板**：代码中的长文本字符串（如生成的脚本、注入的 JS、Markdown 模板）必须提取到 `templates/` 目录下，通过文件读取后替换占位符。不要在代码中内联大段模板字符串
- Node.js 项目使用 `'use strict'`
- Python 项目遵循 PEP 8 规范

**install / update / uninstall 命令（强制）**：

每个 Skill **必须实现** `install`、`update` 和 `uninstall` 命令，支持用户通过自然语言管理：

```bash
# Node.js
node skills/<name>/tool.js install '{"target":"~/.cursor/skills/<name>"}'
node skills/<name>/tool.js update '{"target":"~/.cursor/skills/<name>"}'
node skills/<name>/tool.js uninstall '{"target":"~/.cursor/skills/<name>"}'

# Python
python3 skills/<name>/main.py install --target ~/.cursor/skills/<name>
python3 skills/<name>/main.py update --target ~/.cursor/skills/<name>
python3 skills/<name>/main.py uninstall --target ~/.cursor/skills/<name>
```

**install 命令要求**：
1. 接受 `target` 参数，指定安装目标目录
2. 复制源码文件到目标目录（包括 `SKILL.md`、`tool.js`、`package.json`、`lib/`、`templates/`，排除 `node_modules`、`dist`、运行时数据）
3. 在目标目录执行依赖安装（如 `npm install`、`pip install` 等）
4. 如有前端构建（如 UI 目录），执行构建
5. 检查前置依赖是否存在，给出提示
6. 如有 rules/ 目录，安装规则文件到 `~/.cursor/rules/`
7. 返回安装路径和依赖状态

**update 命令要求**：
1. 接受 `target` 参数
2. 备份用户数据（如工作流、配置、记忆数据等）
3. 删除旧版源码
4. 执行 install 逻辑
5. 恢复用户数据
6. 返回更新结果

**uninstall 命令要求**：
1. 接受 `target` 参数
2. 删除已安装的规则文件（如 `~/.cursor/rules/` 下的 `.mdc` 文件）
3. 询问是否保留用户数据（data 目录）
4. 删除安装目录
5. 返回卸载结果

**SKILL.md 中必须包含安装/更新/卸载说明**（根据技术栈选择对应命令）：

```markdown
## 安装 / 更新 / 卸载

\`\`\`bash
# Node.js Skill
node skills/<name>/tool.js install '{"target":"~/.cursor/skills/<name>"}'
node skills/<name>/tool.js update '{"target":"~/.cursor/skills/<name>"}'
node skills/<name>/tool.js uninstall '{"target":"~/.cursor/skills/<name>"}'

# Python Skill
python3 skills/<name>/main.py install --target ~/.cursor/skills/<name>
python3 skills/<name>/main.py update --target ~/.cursor/skills/<name>
python3 skills/<name>/main.py uninstall --target ~/.cursor/skills/<name>
\`\`\`
```

**自然语言管理示例**（用户只需说）：

```
帮我从 https://github.com/shetengteng/skillix-hub 安装 <name> skill
帮我更新 <name> skill
帮我卸载 <name> skill
```

Agent 会自动克隆仓库并执行 install/update/uninstall 命令。

---

### Phase 5.5：测试设计文档

**目标**：在编写测试代码之前，先编写测试设计文档，明确测试范围、用例和验证策略。

**路径规范**：
- `tests/<name>/design/test-design.md`

**文档模板**：

```markdown
# <Name> Skill 测试设计

## 测试范围

| 模块 | 文件 | 说明 |
|------|------|------|
| response | lib/response.js | 标准输出格式 |
| ... | ... | ... |

## 测试用例

### 模块：<module>

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| 正常路径 | ... | ... | unit |
| 边界情况 | ... | ... | unit |
| 错误处理 | ... | ... | unit |

## 测试策略

- 沙箱隔离：所有文件操作在 testdata/runtime/ 下
- 模块覆盖：每个 lib/ 模块至少一个测试文件
- 依赖隔离：通过修改 config 模块路径实现

## 不测试的范围

- 需要真实浏览器的 Playwright 操作（集成测试阶段覆盖）
- 需要网络的 URL 采集（集成测试阶段覆盖）
```

**要求**：
- 在编写测试代码之前完成
- 列出所有需要测试的模块和用例
- 明确哪些是单元测试、哪些是集成测试
- 标注不测试的范围和原因

---

### Phase 6：单元测试

**目标**：编写并运行单元测试。

**路径规范**：
- 测试设计：`tests/<name>/design/test-design.md`
- 测试文件：`tests/<name>/src/unit/test_<module>.js`
- 运行器：`tests/<name>/run_tests.js`

**测试风格**：

```javascript
let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

// 每个用例为独立 async function test_xxx()
// main() 依次调用，最后打印结果
// 失败时 process.exit(1)
```

**沙箱测试要求**（强制）：

测试必须在沙箱环境中运行，**绝不能在项目根目录下创建/修改文件**。

- 测试目录下必须有 `testdata/` 目录，用于存放测试数据和运行时沙箱
- 运行时沙箱创建在 `tests/<name>/testdata/runtime/` 下，每次测试自动创建、测试后自动清理
- 如果被测代码使用硬编码路径（如 `__dirname` 推算项目根目录），必须支持通过环境变量（如 `PROJECT_ROOT`）覆盖，以便测试指向沙箱目录
- 测试中添加 `.gitkeep` 到 `testdata/` 目录以确保 git 跟踪

```javascript
const TESTDATA_DIR = path.resolve(__dirname, '../../testdata/runtime');

function makeSandbox(label) {
  const id = `${label}-${Date.now()}`;
  const dir = path.join(TESTDATA_DIR, id);
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

// 在 finally 中清理
fs.rmSync(sandbox, { recursive: true, force: true });
```

**文件组织要求**（强制）：
- **每个测试文件只测试一个模块**：`test_response.js` 只测 `response.js`，`test_store.js` 只测 `store.js`
- 不要将多个模块的测试合并到一个文件中（如 `test_example.js` 测试所有模块）
- 文件命名：`test_<module>.js`，与被测模块名一一对应

**覆盖要求**：
- 每个 `lib/` 模块至少一个测试文件
- 覆盖正常路径和边界情况

---

### Phase 7：测试报告

**目标**：运行测试生成 Markdown 报告。

**执行**：

```bash
node tests/<name>/run_tests.js
```

**报告路径**：`tests/<name>/reports/YYYY-MM-DD-NN-test-report.md`

**报告格式**：

```markdown
# <Name> Skill 测试报告

> 时间: YYYY-MM-DD HH:MM:SS
> 结果: PASSED/FAILED
> 耗时: X.XXXs

## 汇总
| 指标 | 数值 |
|---|---:|
| 总用例 | N |
| 通过 | N |
| 失败 | N |

## 单元测试
| 用例 | 状态 | 耗时 |
|---|---|---:|
| `test_xxx` | PASS | 0.XXs |
```

---

### Phase 8：技术文档

**目标**：输出面向开发者的技术文档，详细说明代码结构、模块职责和数据流。

**路径规范**：`design/<name>/YYYY-MM-DD-NN-技术文档.md`

**文档结构**：

1. **概述**：一段话描述 Skill 的技术架构
2. **代码结构**：完整目录树 + 每个文件的职责说明
3. **核心模块**：每个 `lib/` 模块的 API 说明（函数签名、参数、返回值）
4. **数据流**：从输入到输出的完整数据流图（文本或 Mermaid）
5. **配置项**：所有可配置参数及默认值
6. **扩展指南**：如何添加新功能（如新增交互类型、新增命令等）

**执行要求**：
- 代码开发完成后、README 同步前输出
- 内容基于实际代码，不是设计文档的复制
- 如果 Skill 包含前端（如 ui/ 目录），必须单独说明前端结构

---

### Phase 9：README 同步

**目标**：更新项目 README 文件。

**需要更新的文件**：

1. **`README.md`**（中文）：
   - 在"可用 Skills"表格中新增一行
   - 在 Contributing 之前新增使用说明章节

2. **`README_EN.md`**（英文）：
   - 同步翻译上述内容

**Skills 表格格式**：

```markdown
| [<name>](./skills/<name>/) | 简短描述 |
```

**使用说明章节结构**：
- 安装命令
- 核心工作流（代码示例）
- 参数说明表格
- 触发词列表

---

### Phase 10：docs 同步

**目标**：更新 docs 展示页面数据。

每个 Skill 的数据存放在独立文件中，新增 Skill 需要 3 步：

**Step 1**：创建 `docs/scripts/skills/<name>.js`

```javascript
/**
 * Skillix Hub - <Name> Skill Data
 */
window.SKILL_DATA_<NAME_UPPER> = {
    id: '<name>',
    name: '<name>',
    icon: '<icon>',  // lightbulb/document/chart/brain/globe/folder/code
    description: {
        zh: '中文描述',
        en: 'English description'
    },
    tags: [
        { zh: '标签', en: 'Tag' }
    ],
    features: [
        { zh: '功能', en: 'Feature' }
    ],
    scripts: ['tool.js'],
    version: '1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/<name>',
    useCases: [
        {
            title: { zh: '标题', en: 'Title' },
            userInput: { zh: '用户输入', en: 'User input' },
            aiResponse: { zh: 'AI 响应', en: 'AI response' }
        }
    ]
};
```

其中 `<NAME_UPPER>` 是 skill id 的大写+下划线形式（如 `web-content-reader` → `WEB_CONTENT_READER`）。

**Step 2**：在 `docs/index.html` 中添加 script 引用（在 `skills-data.js` 之前）：

```html
<script src="scripts/skills/<name>.js"></script>
```

**Step 3**：在 `docs/scripts/skills-data.js` 的 `SKILL_KEYS` 数组中添加变量名：

```javascript
const SKILL_KEYS = [
    // ... 已有的 ...
    'SKILL_DATA_<NAME_UPPER>',
];
```

---

## 自然语言交互指南

| 用户说 | 执行 |
|--------|------|
| "创建一个新 skill" / "帮我写个 skill" | 从 Phase 1 开始，引导用户完成全流程 |
| "初始化 skill 目录" | 运行 `scaffold.js init` |
| "skill 开发流程是什么" | 展示 8 阶段流程 |
| "skill 命名规范" | 展示命名规范 |
| "设计文档模板" | 展示设计文档结构 |
| "测试怎么写" | 展示测试风格和覆盖要求 |
