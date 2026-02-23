# Web Automation Builder 测试设计

## 测试范围

| 模块 | 文件 | 说明 |
|------|------|------|
| response | lib/response.js | 标准 JSON 输出格式 |
| store | lib/store.js | 工作流 CRUD（save/load/list/remove） |
| recorder | lib/recorder.js | 录制状态管理（start/stop/addStep/isRecording） |
| replayer | lib/replayer.js | 模板渲染（renderTemplate/renderArgs） |
| generator | lib/generator.js | Skill 目录生成（SKILL.md/tool.js/workflow.json/package.json） |
| exporter | lib/exporter.js | Playwright 脚本导出（toPlaywrightScript/exportScript） |

## 测试用例

### 模块：response

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| success 包装数据 | `{msg:'ok'}` | `{result:{msg:'ok'}, error:null}` | unit |
| error 包装消息 | `'fail'` | `{result:null, error:'fail'}` | unit |

### 模块：store

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| save 创建文件 | workflow 对象 | 文件存在于 workflows/ | unit |
| load 返回数据 | 已保存的 id | 完整 workflow 对象 | unit |
| load 不存在返回 null | 不存在的 id | null | unit |
| list 返回列表 | 已保存 1 个 | [{id, stepCount}] | unit |
| remove 删除文件 | 已保存的 id | true + 文件不存在 | unit |
| remove 不存在返回 false | 不存在的 id | false | unit |

### 模块：recorder

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| 初始状态 | - | isRecording=false, getState=null | unit |
| start 开始录制 | name | started=true, id 以 wf- 开头 | unit |
| 重复 start | - | started=false | unit |
| addStep 添加步骤 | command, args | step 对象（seq 递增） | unit |
| addStep 提取 locators | click + ref/element | locators.ref, locators.text | unit |
| stop 返回 workflow | - | 完整 workflow，steps 正确 | unit |
| stop 清理录制文件 | - | .recording.json 不存在 | unit |
| 未录制时 stop | - | null | unit |

### 模块：replayer

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| renderTemplate 替换参数 | `'{{name}}'`, `{name:'world'}` | `'world'` | unit |
| renderTemplate 多参数 | `'{{a}} {{b}}'`, `{a:'1',b:'2'}` | `'1 2'` | unit |
| renderTemplate 无占位符 | `'no params'`, `{}` | `'no params'` | unit |
| renderTemplate 未知参数 | `'{{missing}}'`, `{}` | `'{{missing}}'` | unit |
| renderArgs 替换对象值 | `{url:'{{host}}/api'}` | `{url:'https://x/api'}` | unit |

### 模块：generator

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| 生成 SKILL.md | workflow + params | 包含 skill name 和参数 | unit |
| 生成 tool.js | workflow | 包含 findPlaywright 和 renderArgs | unit |
| 生成 workflow.json | workflow | 步骤数正确 | unit |
| 生成 package.json | skillName | name 字段正确 | unit |

### 模块：exporter

| 用例 | 输入 | 预期输出 | 类型 |
|------|------|----------|------|
| navigate 转换 | step | `page.goto(url)` | unit |
| type + placeholder | step + locators | `getByPlaceholder().fill()` | unit |
| click + text | step + locators | `getByText().click()` | unit |
| screenshot 转换 | step | `page.screenshot()` | unit |
| 参数引用 | `{{query}}` | `params.query` | unit |
| exportScript 创建文件 | workflow + path | 文件存在 | unit |

## 测试策略

- 沙箱隔离：所有文件操作在 `testdata/runtime/` 下，测试后自动清理
- 模块隔离：通过修改 `config` 模块的 `WORKFLOWS_DIR` 和 `RECORDING_FILE` 路径实现
- 无网络依赖：所有单元测试不需要 Playwright 或网络

## 不测试的范围

- `exec` 命令（需要 Playwright 运行环境）→ 集成测试
- `replay` 命令的实际浏览器操作 → 集成测试
- `install`/`update` 的全局安装 → 手动验证
