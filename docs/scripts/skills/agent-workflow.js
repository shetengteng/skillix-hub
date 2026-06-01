/**
 * Skillix Hub - agent-workflow Skill Data
 */
window.SKILL_DATA_AGENT_WORKFLOW = {
    id: 'agent-workflow',
    name: 'agent-workflow',
    icon: 'chart',
    description: {
        zh: 'Agent 驱动的跨 IDE / 跨 LLM 工作流引擎。声明式 YAML 描述节点串行 / 用户阻塞 / 条件循环 / 跨 LLM CLI 协作，CLI 状态机持久化、崩溃可恢复。Claude Code / Cursor / Codex / OpenCode 通用，Python 3.10+ 实现。',
        en: 'Agent-driven cross-IDE / cross-LLM workflow engine. Declarative YAML describes serial nodes, user-blocking, conditional loops and cross-LLM CLI collaboration; CLI state machine with disk persistence and crash recovery. Works with Claude Code, Cursor, Codex and OpenCode. Python 3.10+.'
    },
    tags: [
        { zh: '工作流', en: 'Workflow' },
        { zh: '跨 LLM', en: 'Cross-LLM' },
        { zh: '状态机', en: 'State Machine' },
        { zh: 'YAML 配置', en: 'YAML Config' },
        { zh: 'HTML 可视化', en: 'HTML Visualization' }
    ],
    features: [
        { zh: '4 种节点：agent_call / wait_user / loop / sleep', en: '4 node types: agent_call / wait_user / loop / sleep' },
        { zh: '10 个 CLI 命令（create/validate/start/advance/resume/status/list/abort/executors/view）', en: '10 CLI actions (create/validate/start/advance/resume/status/list/abort/executors/view)' },
        { zh: '4 级校验：YAML 语法 / JSON Schema / 引用一致性 / executor PATH', en: '4-layer validation: YAML / JSON Schema / reference / executor PATH' },
        { zh: '长链稳定性：chain_timeout + stall watchdog + caller handoff', en: 'Long-run stability: chain_timeout + stall watchdog + caller handoff' },
        { zh: '$ENV 展开 + _secrets 自动脱敏（events/audit/history）', en: '$ENV expansion + _secrets auto-redact (events/audit/history)' },
        { zh: '运行状态可视化：view 命令一键生成自包含 HTML', en: 'Visualize runs: `view` command generates self-contained HTML' },
        { zh: 'filelock 并发安全 + state.json 原子写盘', en: 'filelock concurrency safe + atomic state.json writes' },
        { zh: '内置 4 个模板（research / cross-llm / code-review / iterative-refine）', en: 'Built-in templates (research / cross-llm / code-review / iterative-refine)' }
    ],
    scripts: [
        'tool.py',
        'lib/engine.py',
        'lib/parser.py',
        'lib/store.py',
        'lib/template.py',
        'lib/logger.py',
        'lib/executors/base.py',
        'lib/executors/registry.py',
        'lib/nodes/agent_call.py',
        'lib/nodes/wait_user.py',
        'lib/nodes/loop.py',
        'lib/nodes/sleep.py',
        'lib/builder/scaffold.py',
        'lib/view/render.py'
    ],
    version: '1.5.3',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/agent-workflow',
    useCases: [
        {
            title: { zh: '安装 agent-workflow', en: 'Install agent-workflow' },
            userInput: {
                zh: '帮我从 https://github.com/shetengteng/skillix-hub 安装 agent-workflow skill',
                en: 'Install agent-workflow skill from https://github.com/shetengteng/skillix-hub'
            },
            aiResponse: {
                zh: '正在安装 agent-workflow...\n\n1. 克隆仓库\n2. 复制 skills/agent-workflow/ 到 ~/.cursor/skills/\n3. 安装依赖：pip3 install -r requirements.txt\n   • PyYAML>=6.0\n   • jsonschema>=4.20\n   • filelock>=3.13\n\n✅ 安装完成！调用约定：\n\npython3 skills/agent-workflow/tool.py <action> \'<JSON params>\'\n\nactions: create / validate / start / advance / resume / status / list / abort / executors / view',
                en: 'Installing agent-workflow...\n\n1. Clone repo\n2. Copy skills/agent-workflow/ to ~/.cursor/skills/\n3. Install dependencies: pip3 install -r requirements.txt\n   • PyYAML>=6.0\n   • jsonschema>=4.20\n   • filelock>=3.13\n\n✅ Done. Invocation:\n\npython3 skills/agent-workflow/tool.py <action> \'<JSON params>\'\n\nactions: create / validate / start / advance / resume / status / list / abort / executors / view'
            }
        },
        {
            title: { zh: '5 分钟跑通第一个 workflow', en: '5-min first workflow' },
            userInput: {
                zh: '我想试一下，跑一个内置示例',
                en: 'Let me try a built-in example'
            },
            aiResponse: {
                zh: '走起：\n\n# 1) 列出内置模板\npython3 skills/agent-workflow/tool.py create \'{"action":"list_templates"}\'\n→ research-and-implement / cross-llm-pipeline / code-review / iterative-refine\n\n# 2) 从模板拷一份\npython3 skills/agent-workflow/tool.py create \'{\n  "action":"from_template",\n  "template":"iterative-refine",\n  "out":".agent-workflow/workflows/demo.yaml"\n}\'\n\n# 3) 校验（L1 语法 + L2 schema + L3 引用 + L4 executor）\npython3 skills/agent-workflow/tool.py validate \'{"workflow":".agent-workflow/workflows/demo.yaml"}\'\n\n# 4) 启动\npython3 skills/agent-workflow/tool.py start \'{"workflow":".agent-workflow/workflows/demo.yaml","caller":"manual"}\'\n→ 返回 action: "execute_agent" / "wait_user" / "continue" / "done"\n\n# 5) 可视化看进度\npython3 skills/agent-workflow/tool.py view \'{}\'   # 浏览器自动打开总览页',
                en: 'Go:\n\n# 1) List built-in templates\npython3 skills/agent-workflow/tool.py create \'{"action":"list_templates"}\'\n→ research-and-implement / cross-llm-pipeline / code-review / iterative-refine\n\n# 2) Copy from template\npython3 skills/agent-workflow/tool.py create \'{\n  "action":"from_template",\n  "template":"iterative-refine",\n  "out":".agent-workflow/workflows/demo.yaml"\n}\'\n\n# 3) Validate (L1 syntax + L2 schema + L3 reference + L4 executor)\npython3 skills/agent-workflow/tool.py validate \'{"workflow":".agent-workflow/workflows/demo.yaml"}\'\n\n# 4) Start\npython3 skills/agent-workflow/tool.py start \'{"workflow":".agent-workflow/workflows/demo.yaml","caller":"manual"}\'\n→ Returns action: "execute_agent" / "wait_user" / "continue" / "done"\n\n# 5) Visualize\npython3 skills/agent-workflow/tool.py view \'{}\'   # opens overview page in browser'
            }
        },
        {
            title: { zh: '声明一个跨 LLM workflow', en: 'Declare a cross-LLM workflow' },
            userInput: {
                zh: '我希望 设计阶段交给 Claude，实现阶段交给 Codex，最后让当前 agent 做 review',
                en: 'I want Claude to design, Codex to implement, then current agent reviews'
            },
            aiResponse: {
                zh: '把下面这份 YAML 存为 .agent-workflow/workflows/cross.yaml：\n\nname: cross-llm-pipeline\nexecutors:\n  claude:\n    kind: spawn\n    cmd: ["claude", "-p"]\n    input_mode: stdin\n    timeout_ms: 60000\n  codex:\n    kind: spawn\n    cmd: ["codex", "exec"]\n    input_mode: stdin\n    timeout_ms: 60000\n\nnodes:\n  - alias: design\n    type: agent_call\n    executor: claude\n    prompt: "设计 {{topic}} 的方案"\n    output: design_doc\n  - alias: implement\n    type: agent_call\n    executor: codex\n    prompt: "按下面的设计实现：\\n{{design_doc}}"\n    output: code\n  - alias: review\n    type: agent_call\n    executor: caller     # 当前 agent\n    prompt: "Review code:\\n{{code}}"\n    output: review_notes\n\n启动：\npython3 skills/agent-workflow/tool.py start \'{"workflow":".agent-workflow/workflows/cross.yaml","vars":{"topic":"OAuth 登录"}}\'',
                en: 'Save the following YAML as .agent-workflow/workflows/cross.yaml:\n\nname: cross-llm-pipeline\nexecutors:\n  claude:\n    kind: spawn\n    cmd: ["claude", "-p"]\n    input_mode: stdin\n    timeout_ms: 60000\n  codex:\n    kind: spawn\n    cmd: ["codex", "exec"]\n    input_mode: stdin\n    timeout_ms: 60000\n\nnodes:\n  - alias: design\n    type: agent_call\n    executor: claude\n    prompt: "Design {{topic}}"\n    output: design_doc\n  - alias: implement\n    type: agent_call\n    executor: codex\n    prompt: "Implement per design:\\n{{design_doc}}"\n    output: code\n  - alias: review\n    type: agent_call\n    executor: caller     # current agent\n    prompt: "Review code:\\n{{code}}"\n    output: review_notes\n\nStart:\npython3 skills/agent-workflow/tool.py start \'{"workflow":".agent-workflow/workflows/cross.yaml","vars":{"topic":"OAuth login"}}\''
            }
        },
        {
            title: { zh: 'wait_user：让 agent 停下来问用户', en: 'wait_user: pause and ask user' },
            userInput: {
                zh: '能不能在某一步让 agent 主动暂停，等用户确认再继续？',
                en: 'Can the agent pause and wait for user confirmation?'
            },
            aiResponse: {
                zh: '可以，用 wait_user 节点。CLI 返回 action: "wait_user"，由调用方（IDE Agent）把 message 渲染给用户，收集到输入后调 resume。\n\nnodes:\n  - alias: ask\n    type: wait_user\n    message: "设计稿是否通过？"\n    schema:\n      type: object\n      required: [approved]\n      properties:\n        approved: { type: boolean }\n        feedback: { type: string, default: "" }\n\n收到用户输入后：\npython3 skills/agent-workflow/tool.py resume \'{\n  "run_id":"wf-...",\n  "input":{"approved":false,"feedback":"需要补错误处理"}\n}\'\n\ninput 会按 schema 校验，失败给统一错误对象（retryable=true）让 caller 改后重试。',
                en: 'Yes — use wait_user. CLI returns action: "wait_user"; caller renders the message, collects input, then calls resume.\n\nnodes:\n  - alias: ask\n    type: wait_user\n    message: "Approve the design?"\n    schema:\n      type: object\n      required: [approved]\n      properties:\n        approved: { type: boolean }\n        feedback: { type: string, default: "" }\n\nAfter user input:\npython3 skills/agent-workflow/tool.py resume \'{\n  "run_id":"wf-...",\n  "input":{"approved":false,"feedback":"need error handling"}\n}\'\n\nInput is validated against the schema; on failure CLI returns a unified error object (retryable=true) so caller can retry.'
            }
        },
        {
            title: { zh: 'loop：评审通过前反复迭代', en: 'loop: iterate until approved' },
            userInput: {
                zh: '希望某段流程反复跑，直到用户说通过为止',
                en: 'Repeat a section until user says approved'
            },
            aiResponse: {
                zh: '用 loop 节点。condition 求值为 true 才继续；max_iterations 兜底防死循环；step_sleep_ms 控制每轮间隔。\n\nnodes:\n  - alias: refine_loop\n    type: loop\n    condition: "{{review.approved}} == false"\n    max_iterations: 5\n    step_sleep_ms: 1000\n    body:\n      - alias: refine\n        type: agent_call\n        executor: caller\n        prompt: "基于反馈优化：{{review.feedback}}"\n        output: design_doc\n      - alias: review\n        type: wait_user\n        message: "再审一遍"\n        schema: { type: object, required: [approved], properties: { approved: {type: boolean}, feedback: {type: string} } }\n\n第一次迭代时 review 还没运行，CLI 自动应用 "do-while" 语义：condition 中未定义变量会被宽松判定为 true，先跑一遍。',
                en: 'Use loop. condition truthy → continue; max_iterations is the safety cap; step_sleep_ms throttles each iteration.\n\nnodes:\n  - alias: refine_loop\n    type: loop\n    condition: "{{review.approved}} == false"\n    max_iterations: 5\n    step_sleep_ms: 1000\n    body:\n      - alias: refine\n        type: agent_call\n        executor: caller\n        prompt: "Refine based on feedback: {{review.feedback}}"\n        output: design_doc\n      - alias: review\n        type: wait_user\n        message: "Re-review"\n        schema: { type: object, required: [approved], properties: { approved: {type: boolean}, feedback: {type: string} } }\n\nOn first iteration `review` has not run; CLI applies do-while semantics — undefined variables in the loop condition are treated as truthy so the body runs once.'
            }
        },
        {
            title: { zh: 'caller 接力：断开会话后继续', en: 'Caller handoff: resume across sessions' },
            userInput: {
                zh: '昨天的 workflow 没跑完，今天 IDE 重启了怎么办？',
                en: 'Last session\'s workflow didn\'t finish; IDE restarted. How to continue?'
            },
            aiResponse: {
                zh: '所有 run 落盘到 .agent-workflow/runs/，今天 caller 启动后做这三步：\n\n# 1) 查未完成 run\npython3 skills/agent-workflow/tool.py list \'{"status":["waiting_user","awaiting_agent"]}\'\n\n# 2) 拿 last_payload 重建上下文\npython3 skills/agent-workflow/tool.py status \'{"run_id":"wf-..."}\'\n→ last_payload 含原 prompt / schema / message，caller 可以直接重建提问\n\n# 3) 推进 / 恢复\npython3 skills/agent-workflow/tool.py resume \'{"run_id":"wf-...","input":{...}}\'\n# 或\npython3 skills/agent-workflow/tool.py advance \'{"run_id":"wf-...","result":{"output":"..."}}\'',
                en: 'All runs persist to .agent-workflow/runs/. New caller does three steps:\n\n# 1) Find unfinished runs\npython3 skills/agent-workflow/tool.py list \'{"status":["waiting_user","awaiting_agent"]}\'\n\n# 2) Get last_payload to rebuild context\npython3 skills/agent-workflow/tool.py status \'{"run_id":"wf-..."}\'\n→ last_payload includes original prompt / schema / message\n\n# 3) advance or resume\npython3 skills/agent-workflow/tool.py resume \'{"run_id":"wf-...","input":{...}}\'\n# or\npython3 skills/agent-workflow/tool.py advance \'{"run_id":"wf-...","result":{"output":"..."}}\''
            }
        },
        {
            title: { zh: '长链稳定性：chain_timeout 自救', en: 'Long-run stability: chain_timeout' },
            userInput: {
                zh: '如果 workflow 太长，IDE shell 调用会不会超时？',
                en: 'For very long workflows, will the IDE shell call time out?'
            },
            aiResponse: {
                zh: '不会。CLI 内部 chain 推进超过 chain_timeout_ms（默认 25s）会主动返回：\n\n{\n  "action": "continue",\n  "run_id": "wf-...",\n  "status": "awaiting_agent"\n}\n\ncaller 收到 "continue" 立刻再调一次 advance（不带 result），CLI 从上次 cursor 继续，直到下一个 wait_user / execute_agent / done。\n\n同时外部 LLM CLI 静默太久（stall_timeout_ms 默认 300s）会被强杀并返回 EXECUTOR_STALLED，避免 hang 死。',
                en: 'No. When internal chain exceeds chain_timeout_ms (default 25s) CLI proactively returns:\n\n{\n  "action": "continue",\n  "run_id": "wf-...",\n  "status": "awaiting_agent"\n}\n\nCaller immediately reissues advance (no result) and CLI resumes from the saved cursor until the next wait_user / execute_agent / done.\n\nExternal LLMs that go silent past stall_timeout_ms (default 300s) are force-killed with EXECUTOR_STALLED, so the caller never hangs.'
            }
        },
        {
            title: { zh: 'secrets：环境变量展开 + 自动脱敏', en: 'Secrets: env expand + auto-redact' },
            userInput: {
                zh: '我 prompt 里要传 API Key，怎么保证日志和事件流里不泄露？',
                en: 'I pass an API key in the prompt — how to keep it out of logs?'
            },
            aiResponse: {
                zh: '在 vars 里用 $ENV 占位 + _secrets 标记：\n\nvars:\n  api_key: "$ENV:OPENAI_API_KEY"   # start 时自动从环境变量读取\n  user: "alice"\n  _secrets: ["api_key"]            # 标记敏感字段\n\nstart 时 CLI 会：\n• 把 $ENV:OPENAI_API_KEY 替换为真实值，注入 prompt\n• 收集 _secrets 中字段的实际值\n• 在 events.ndjson / audit.log / state.json.history 中把这些值替换为 ***REDACTED***\n\nstdin 模式下 prompt 也直接通过管道传给子进程，不会出现在 shell 历史 / ps 输出。',
                en: 'Use $ENV placeholder + _secrets list:\n\nvars:\n  api_key: "$ENV:OPENAI_API_KEY"   # expanded at start from env\n  user: "alice"\n  _secrets: ["api_key"]            # mark sensitive fields\n\nAt start CLI:\n• replaces $ENV:OPENAI_API_KEY with the real value, injects into prompt\n• collects actual values of fields listed in _secrets\n• rewrites those values to ***REDACTED*** in events.ndjson / audit.log / state.json.history\n\nWith stdin input_mode the prompt goes through a pipe, never appears in shell history or ps.'
            }
        },
        {
            title: { zh: 'view 命令：浏览器可视化 run', en: 'view command: visualize runs in browser' },
            userInput: {
                zh: '想在浏览器里看每个 run 跑到哪、节点状态、history 时间线',
                en: 'I want to see each run\'s progress, node status, history timeline in a browser'
            },
            aiResponse: {
                zh: '用 view 命令，零依赖纯 HTML：\n\n# 看所有 run（总览 + 每 run 详情，自动开浏览器）\npython3 skills/agent-workflow/tool.py view \'{}\'\n\n# 看某个 run\npython3 skills/agent-workflow/tool.py view \'{"run_id":"wf-20260527-100647-6d81e3"}\'\n\n# 不自动打开，只生成文件\npython3 skills/agent-workflow/tool.py view \'{"open":false}\'\n\n# 指定输出路径\npython3 skills/agent-workflow/tool.py view \'{"out":"./report.html"}\'\n\n生成的 HTML 是 self-contained（vanilla CSS + inline JS）：节点拓扑 + cursor 高亮 + 状态色块 + history 时间线 + 最近 200 条 events + vars，可离线分享。',
                en: 'Use the view command — zero-dependency HTML:\n\n# Overview + per-run detail pages (auto opens browser)\npython3 skills/agent-workflow/tool.py view \'{}\'\n\n# Single run\npython3 skills/agent-workflow/tool.py view \'{"run_id":"wf-20260527-100647-6d81e3"}\'\n\n# Generate file without opening\npython3 skills/agent-workflow/tool.py view \'{"open":false}\'\n\n# Custom path\npython3 skills/agent-workflow/tool.py view \'{"out":"./report.html"}\'\n\nThe HTML is self-contained (vanilla CSS + inline JS): node topology, cursor highlight, status pills, history timeline, last 200 events, vars — offline-shareable.'
            }
        },
        {
            title: { zh: '错误处理：识别 retryable 错误', en: 'Error handling: detect retryable errors' },
            userInput: {
                zh: '调用 CLI 返回了错误对象，怎么决定要不要重试？',
                en: 'CLI returned an error object — how to decide whether to retry?'
            },
            aiResponse: {
                zh: '所有错误统一为 { code, message, retryable, suggestion, location, ... }。caller 主循环遵守：\n\nif response.error is not None:\n    if response.error.retryable:\n        # 把 message + suggestion 展示给用户，让用户改输入后再 resume\n        show_to_user(response.error.message + "\\n" + response.error.suggestion)\n        new_input = ask_user_again()\n        response = cli(\'resume\', {run_id, input: new_input})\n    else:\n        # 终态错误：直接展示，不再重试\n        show_to_user(\'Workflow 失败：\' + response.error.message)\n        break\n\n常见 retryable 码：SCHEMA_VIOLATION（input 不符 schema）、RUN_BUSY（并发冲突，等 1s 重试）。\n非 retryable：WORKFLOW_INVALID / EXECUTOR_NOT_FOUND / EXECUTOR_STALLED / LOOP_EXCEEDED 等。',
                en: 'All errors share { code, message, retryable, suggestion, location, ... }. Caller main loop:\n\nif response.error is not None:\n    if response.error.retryable:\n        # show message + suggestion, ask user to fix and resume\n        show_to_user(response.error.message + "\\n" + response.error.suggestion)\n        new_input = ask_user_again()\n        response = cli(\'resume\', {run_id, input: new_input})\n    else:\n        # terminal: show and stop\n        show_to_user(\'Workflow failed: \' + response.error.message)\n        break\n\nRetryable examples: SCHEMA_VIOLATION (input fails schema), RUN_BUSY (concurrent advance — wait 1s).\nNon-retryable: WORKFLOW_INVALID / EXECUTOR_NOT_FOUND / EXECUTOR_STALLED / LOOP_EXCEEDED, etc.'
            }
        },
        {
            title: { zh: '调试：events.ndjson + audit.log', en: 'Debugging: events.ndjson + audit.log' },
            userInput: {
                zh: '某次 run 跑挂了，怎么排查？',
                en: 'A run failed — how to debug?'
            },
            aiResponse: {
                zh: '每个 run 都有完整审计：\n\n.agent-workflow/runs/<run_id>/\n├── state.json          # 当前游标 + history + vars + last_payload + error\n├── workflow.yaml       # 启动时的快照（带分配的 _internal_id）\n├── events.ndjson       # 一行一条结构化事件（run_start / node_start / spawn / sleep_* / node_end / error / pause / resume / run_end / abort）\n├── audit.log           # 可读时间线\n└── outputs/            # 单节点 result >10KB 时落盘\n\n常用排查：\n# 1) 看状态\npython3 skills/agent-workflow/tool.py status \'{"run_id":"wf-...","include_events":true,"event_limit":50}\'\n\n# 2) 可视化\npython3 skills/agent-workflow/tool.py view \'{"run_id":"wf-..."}\'\n\n# 3) 直接查事件流\ntail -f .agent-workflow/runs/wf-.../events.ndjson | jq .',
                en: 'Every run has full audit trail:\n\n.agent-workflow/runs/<run_id>/\n├── state.json          # cursor + history + vars + last_payload + error\n├── workflow.yaml       # snapshot at start (with assigned _internal_id)\n├── events.ndjson       # one structured event per line (run_start / node_start / spawn / sleep_* / node_end / error / pause / resume / run_end / abort)\n├── audit.log           # human timeline\n└── outputs/            # for node results >10KB\n\nDebug recipes:\n# 1) status\npython3 skills/agent-workflow/tool.py status \'{"run_id":"wf-...","include_events":true,"event_limit":50}\'\n\n# 2) visualize\npython3 skills/agent-workflow/tool.py view \'{"run_id":"wf-..."}\'\n\n# 3) raw event stream\ntail -f .agent-workflow/runs/wf-.../events.ndjson | jq .'
            }
        },
        {
            title: { zh: '何时该用 / 不该用', en: 'When to use / not to use' },
            userInput: {
                zh: '什么场景适合用 agent-workflow？什么场景不该用？',
                en: 'When is agent-workflow a good fit, and when is it not?'
            },
            aiResponse: {
                zh: '✅ 该用：\n• ≥3 个节点的多步任务\n• 需要用户阻塞确认（wait_user）\n• 需要条件循环（loop）\n• 跨 LLM CLI 协作（设计交 Claude / 实现交 Codex / 评审回当前 agent）\n• 需要可重复执行的 SOP\n• 需要审计 / 进度可见\n\n❌ 不该用：\n• 单次问答 / 2-3 步纯 prompt chain（直接让 agent 推理更快）\n• 临时一次性任务\n• 单一 LLM 内部推理（用 chain-of-thought 即可）\n\n额外提示：CLI 不内嵌 LLM，所有"动脑子"的工作要么交给 caller（你自己），要么 spawn 外部 LLM CLI。',
                en: '✅ Good fit:\n• Multi-step tasks (≥3 nodes)\n• User-blocking confirmation (wait_user)\n• Conditional loops (loop)\n• Cross-LLM CLI collaboration (Claude designs / Codex implements / current agent reviews)\n• Repeatable SOPs\n• Audit / visible progress\n\n❌ Not for:\n• One-shot Q&A or 2-3 step prompt chains (direct reasoning is faster)\n• Disposable tasks\n• Single-LLM internal reasoning (just use chain-of-thought)\n\nNote: CLI does not embed an LLM — all reasoning is delegated to the caller or spawned external LLM CLIs.'
            }
        }
    ]
};
