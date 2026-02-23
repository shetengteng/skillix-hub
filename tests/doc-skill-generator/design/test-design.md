# Doc Skill Generator 测试设计

## 测试范围

| 模块 | 文件 | 说明 |
|------|------|------|
| response | lib/response.js | 标准 JSON 输出格式 |
| extractor | lib/extractor.js | 内容结构化 + Markdown 导出 + token 估算 |
| analyzer | lib/analyzer.js | 文档类型识别 + API/CLI 端点提取 |
| generator | lib/generator.js | Skill 代码生成（tool.js/SKILL.md/package.json/doc-source.json） |
| fetcher | lib/fetcher.js | 文档采集调度 + 提取结果管理（本地文件部分） |
| pdf-reader | lib/pdf-reader.js | PDF 解析 |
| crawler | lib/crawler.js | Playwright BFS 深度采集 |

## 测试用例

### 模块：response

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| success 包装数据 | `{msg:'ok'}` | `{result:{msg:'ok'}, error:null}` | unit |
| error 包装消息 | `'fail'` | `{result:null, error:'fail'}` | unit |

### 模块：extractor

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| estimateTokens 基础 | `'hello world'` | 3 | unit |
| estimateTokens 空值 | `''`, `null` | 0 | unit |
| summarizeExtract | extract 对象 | 包含 id、title、heading | unit |
| extractToMarkdown | extract 对象 | 包含标题、代码块、表格 | unit |
| extractToMarkdown token 限制 | maxTokens=5 | 截断或更短 | unit |

### 模块：analyzer

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| 识别 API Reference | 含 GET/POST/endpoint 的文档 | primary='api-reference' | unit |
| 识别 CLI Reference | 含 command/flag/option 的文档 | primary='cli-reference' | unit |
| 提取 API endpoints | 含 `GET /api/users` 的文档 | endpoints 数组 | unit |
| 提取 CLI commands | 含 bash 代码块的文档 | commands 数组 | unit |
| 去重 endpoints | 重复的 GET /api/users | 只保留 1 个 | unit |

### 模块：generator

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| sanitizeName 替换连字符 | `'hello-world'` | `'hello_world'` | unit |
| sanitizeName 数字开头 | `'123abc'` | `'_123abc'` | unit |
| 生成 SKILL.md | extract + analysis | 包含 skill name 和 doc type | unit |
| 生成 tool.js | API analysis | 包含命令名和 API 路径 | unit |
| 生成 package.json | skillName | name 字段正确 | unit |
| 生成 doc-source.json | extract | 包含 sources 和 generatedAt | unit |

### 模块：fetcher（本地文件）

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| fetchAll 本地文件 | .md 文件路径 | extract 对象，status=completed | unit |
| loadExtract | 已保存的 id | 完整 extract 对象 | unit |
| listExtracts | 已保存 1 个 | [{id, status, summary}] | unit |
| deleteExtract | 已保存的 id | true | unit |
| deleteExtract 不存在 | 不存在的 id | false | unit |

### 模块：pdf-reader

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| readPdf 本地文件 | 有效 PDF 路径 | {text, pages, title} | integration |
| readPdf 不存在 | 无效路径 | 抛出错误 | unit |

### 模块：crawler

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| crawlBFS | 真实 URL | pages 数组 | integration |
| crawlSinglePage | 真实 URL | {url, title, sections} | integration |

## 测试策略

- 沙箱隔离：所有文件操作在 `testdata/runtime/` 下，测试后自动清理
- 模块隔离：通过修改 `config` 模块的 `EXTRACTS_DIR` 路径实现
- 无网络依赖：单元测试只测试本地文件采集，不测试 URL 采集
- 无 Playwright 依赖：单元测试不调用 crawler.js

## 不测试的范围

- `crawler.js` 的 Playwright 操作（需要浏览器）→ 集成测试
- `pdf-reader.js` 的 URL 下载 → 集成测试
- `fetcher.js` 的 URL 采集 → 集成测试
- `install`/`update-self` 的全局安装 → 手动验证
