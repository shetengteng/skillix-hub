# Web Automation Builder v2 测试设计

## 测试范围

| 模块 | 文件 | 说明 |
|------|------|------|
| response | lib/response.js | 标准 JSON 输出格式 |
| config | lib/config.js | 配置常量、路径、过滤规则 |
| store | lib/store.js | 工作流 CRUD（save/load/list/remove） |
| injector | lib/injector.js | DOM 事件注入脚本生成 |
| network-monitor | lib/network-monitor.js | CDP 网络请求监听（过滤、MIME 判断） |
| recorder | lib/recorder.js | 被动录制核心（状态管理） |
| replayer | lib/replayer.js | 模板渲染（renderTemplate/renderArgs） |
| generator | lib/generator.js | Skill 目录生成 |
| exporter | lib/exporter.js | Playwright 脚本导出 |

## 测试用例

### 模块：response

| 用例 | 预期 | 类型 |
|------|------|------|
| success 包装数据 | `{result:{msg:'ok'}, error:null}` | unit |
| error 包装消息 | `{result:null, error:'fail'}` | unit |

### 模块：config

| 用例 | 预期 | 类型 |
|------|------|------|
| 导出所有必要常量 | SKILL_DIR, DATA_DIR, WORKFLOWS_DIR, RECORDINGS_DIR 等 | unit |
| MAX_BODY_SIZE 为 512KB | 512 * 1024 | unit |
| NETWORK_SKIP_EXTENSIONS 包含静态资源 | .js, .css, .png 等 | unit |
| NETWORK_SKIP_HOSTS 包含 tracking 域名 | google-analytics 等 | unit |
| getBrowserWsEndpoint 是异步函数 | typeof === 'function' | unit |

### 模块：store

| 用例 | 预期 | 类型 |
|------|------|------|
| save 创建文件 | 文件存在于 workflows/ | unit |
| load 返回数据 | 完整 workflow 对象 | unit |
| load 不存在返回 null | null | unit |
| list 返回列表 | [{id, stepCount}] | unit |
| remove 删除文件 | true + 文件不存在 | unit |
| remove 不存在返回 false | false | unit |

### 模块：injector

| 用例 | 预期 | 类型 |
|------|------|------|
| buildInjectionScript 返回字符串 | 包含 __WAB_INJECTED__ 和 __WAB_EVENTS__ | unit |
| 脚本监听 click 事件 | 包含 'click' addEventListener | unit |
| 脚本监听 input 事件 | 包含 'input' addEventListener | unit |
| 脚本监听 change 事件 | 包含 'change' addEventListener | unit |
| 脚本监听 submit 事件 | 包含 'submit' addEventListener | unit |
| 脚本监听 keydown 事件 | 包含 'keydown' addEventListener | unit |
| 脚本监听 SPA 导航 | 包含 popstate 和 hashchange | unit |
| 脚本生成 CSS 选择器 | 包含 cssSelector 函数 | unit |
| 脚本提取定位器属性 | 包含 aria-label, placeholder, data-testid | unit |
| COLLECT_SCRIPT 收集事件 | 包含 __WAB_EVENTS__ 和 JSON.stringify | unit |

### 模块：network-monitor

| 用例 | 预期 | 类型 |
|------|------|------|
| 实例化 NetworkMonitor | instanceof 检查 | unit |
| 暴露所有公共方法 | start, stop, attachToPage, collectRequests, getStats, detachAll | unit |
| 初始状态 | captured=0, pending=0 | unit |
| collectRequests 返回空数组 | [] | unit |
| _shouldSkip 过滤 Image 类型 | true | unit |
| _shouldSkip 过滤 Stylesheet 类型 | true | unit |
| _shouldSkip 过滤 google-analytics | true | unit |
| _shouldSkip 不过滤 API 请求 | false | unit |
| _isTextMime 识别 json | true | unit |
| _isTextMime 识别 html | true | unit |
| _isTextMime 拒绝 image/png | false | unit |

### 模块：recorder

| 用例 | 预期 | 类型 |
|------|------|------|
| 暴露公共方法 | start, stop, isRecording, getState, getStatus | unit |
| 初始状态 | isRecording=false | unit |
| 初始 status | { recording: false } | unit |

注：recorder 的 start/stop 需要浏览器环境，属于集成测试范围。

### 模块：replayer

| 用例 | 预期 | 类型 |
|------|------|------|
| renderTemplate 替换参数 | 'hello world' | unit |
| renderTemplate 多参数 | '1 and 2' | unit |
| renderTemplate 无占位符 | 原样返回 | unit |
| renderTemplate 未知参数 | 保留 {{missing}} | unit |
| renderArgs 替换对象值 | URL 中的模板被替换 | unit |

### 模块：generator

| 用例 | 预期 | 类型 |
|------|------|------|
| 生成 SKILL.md | 包含 skill name 和参数 | unit |
| 生成 tool.js | 包含 findPlaywright 和 renderArgs | unit |
| 生成 workflow.json | 步骤数正确 | unit |
| 生成 package.json | name 字段正确 | unit |

### 模块：exporter

| 用例 | 预期 | 类型 |
|------|------|------|
| navigate 转换 | `page.goto(url)` | unit |
| type + placeholder | `getByPlaceholder().fill()` | unit |
| click + text | `getByText().click()` | unit |
| screenshot 转换 | `page.screenshot()` | unit |
| 参数引用 | `params.query` + 环境变量 `QUERY` | unit |
| exportScript 创建文件 | 文件存在 | unit |

## 测试策略

- 沙箱隔离：所有文件操作在 `testdata/runtime/` 下，测试后自动清理
- 模块隔离：通过修改 `config` 模块的路径实现
- 无网络依赖：所有单元测试不需要 Playwright 或浏览器
- recorder 的 start/stop 涉及 CDP 连接，仅测试接口存在性和初始状态

## 不测试的范围（集成测试）

- `record` 命令的完整流程（需要 Playwright 浏览器）
- `stop` 命令的 rawEvents 收集（需要 CDP 连接）
- `replay` 命令的实际浏览器操作
- DOM 事件注入脚本在真实浏览器中的行为
- 网络监听在真实 CDP 会话中的行为
