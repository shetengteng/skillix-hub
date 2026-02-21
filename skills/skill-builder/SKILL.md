---
name: skill-builder
description: |
  skillix-hub 项目标准化 Skill 开发流程指南和脚手架工具。当用户要求创建新 Skill、
  初始化 Skill 目录结构、或询问 Skill 开发规范时使用。提供 8 阶段完整生命周期：
  需求命名、设计文档、讨论迭代、代码开发、单元测试、测试报告、README 同步、docs 同步。
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
- `tech`：`node`（默认）或 `python`
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

## 开发流程（8 阶段）

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

2. 与用户确认以下信息：
   - Skill 名称（从推荐中选择或自定义）
   - 技术栈（Node.js 或 Python）
   - 核心功能描述
   - 使用场景（Agent 内部 / 用户手动 / 两者）

3. 命名规范：
   - 全小写，单词用连字符分隔
   - 描述性名称，避免 `helper`、`utils` 等模糊词
   - 示例：`web-content-reader`、`api-tracer`、`swagger-api-reader`

3. 运行脚手架初始化目录：
   ```bash
   node skills/skill-builder/scaffold.js init '{"name":"<name>","tech":"<tech>","description":"<desc>"}'
   ```

---

### Phase 2：设计文档

**目标**：编写设计文档，明确技术方案。

**路径规范**：`design/<name>/YYYY-MM-DD-NN-描述.md`
- `YYYY-MM-DD`：当前日期
- `NN`：当天序号（01 起步）
- 示例：`design/web-content-reader/2026-02-21-01-Web内容读取Skill设计文档.md`

**文档结构**（参考 `templates/design-doc.md.tpl`）：

1. **需求**：背景、目标、使用场景表格
2. **整体流程**：Mermaid flowchart
3. **技术方案**：至少 2 个方案对比，含优缺点和对比表
4. **推荐方案**：架构图、CLI 命令设计、输出格式、目录结构
5. **实现计划**：分 Phase 列出任务
6. **风险与注意事项**：风险表格

---

### Phase 3：讨论迭代

**目标**：与用户确认设计方案。

**执行步骤**：

1. 切换到 Plan 模式，展示设计方案
2. 等待用户确认或提出修改意见
3. 迭代修改直到用户满意
4. 确认后进入代码开发阶段

---

### Phase 4：代码开发

**目标**：实现 Skill 源码。

**目录规范**：

```
skills/<name>/
├── SKILL.md          # Skill 文档（Phase 完成后编写）
├── tool.js           # CLI 入口（Node.js）或 main.py（Python）
├── package.json      # Node.js 依赖
└── lib/              # 核心模块
    ├── config.js
    └── ...
```

**CLI 入口规范**（Node.js）：

```bash
node skills/<name>/tool.js <command> '<json_params>'
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
- 使用 `'use strict'`
- 模块化：每个功能一个文件放在 `lib/` 下
- 不添加无意义注释
- 错误处理：所有命令 catch 异常返回 JSON error

---

### Phase 5：单元测试

**目标**：编写并运行单元测试。

**路径规范**：
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

**覆盖要求**：
- 每个 `lib/` 模块至少一个测试文件
- 覆盖正常路径和边界情况

---

### Phase 6：测试报告

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

### Phase 7：README 同步

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

### Phase 8：docs 同步

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
