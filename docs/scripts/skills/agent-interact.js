/**
 * Skillix Hub - Agent Interact Skill Data
 */
window.SKILL_DATA_AGENT_INTERACT = {
    id: 'agent-interact',
    name: 'agent-interact',
    icon: 'chart',
    description: {
        zh: 'AI Agent 与用户之间的可视化交互桥梁，通过 Electron 独立窗口支持 8 种交互场景，所有交互由 LLM 自主发起',
        en: 'Visual interaction bridge between AI Agent and user via Electron standalone windows, supporting 8 interaction types, all initiated autonomously by LLM'
    },
    tags: [
        { zh: '交互', en: 'Interaction' },
        { zh: 'Electron', en: 'Electron' },
        { zh: '可视化', en: 'Visualization' },
        { zh: 'Vue', en: 'Vue' },
        { zh: '通用渲染', en: 'Custom Rendering' }
    ],
    features: [
        { zh: 'Electron 独立置顶窗口 — 自动弹出，无需切换应用', en: 'Electron standalone window — auto-pops, no app switching needed' },
        { zh: '8 种交互类型 — 确认、等待、图表、通知、表单、审批、进度、自定义通用渲染', en: '8 interaction types — confirm, wait, chart, notification, form, approval, progress, custom rendering' },
        { zh: 'LLM 自主决策 — Agent 在任务执行中自动判断何时需要用户介入', en: 'LLM autonomous decision — Agent decides when user input is needed during task execution' },
        { zh: 'custom 通用渲染 — 21 种组件自由编排，LLM 通过 JSON 描述即可生成任意弹框', en: 'Custom rendering — 21 component types freely composable, LLM generates any dialog via JSON' },
        { zh: 'HTTP API — 任何 Agent 都可通过 REST API 调用', en: 'HTTP API — Any agent can call via REST API' }
    ],
    scripts: ['tool.js'],
    version: '3.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/agent-interact',
    useCases: [
        {
            title: { zh: '安装 / 更新', en: 'Install / Update' },
            userInput: { zh: 'node skills/agent-interact/tool.js install', en: 'node skills/agent-interact/tool.js install' },
            aiResponse: { zh: '安装依赖并构建 UI；更新使用 update 命令（先删除再重装）', en: 'Install deps and build UI; use update command to clean reinstall' }
        },
        {
            title: { zh: 'LLM 检测到多环境 → 自动弹出确认框', en: 'LLM detects multiple environments → auto-pops confirm dialog' },
            userInput: { zh: '用户说"帮我部署"，LLM 发现有 dev/staging/prod 三个环境', en: 'User says "deploy for me", LLM finds dev/staging/prod environments' },
            aiResponse: { zh: 'LLM 自动弹出 confirm 选择框，用户选择后继续部署', en: 'LLM auto-pops confirm dialog, continues deployment after user selection' }
        },
        {
            title: { zh: 'LLM 即将执行高危操作 → 自动弹出审批框', en: 'LLM about to execute risky operation → auto-pops approval dialog' },
            userInput: { zh: '用户说"清理过期数据"，LLM 判断这是不可逆操作', en: 'User says "clean expired data", LLM determines this is irreversible' },
            aiResponse: { zh: 'LLM 自动弹出 approval 审批框，显示影响范围，等待用户确认', en: 'LLM auto-pops approval dialog showing impact scope, waits for user confirmation' }
        },
        {
            title: { zh: 'LLM 完成分析 → 自动弹出 custom 报告', en: 'LLM completes analysis → auto-pops custom report' },
            userInput: { zh: '用户说"分析 API 性能"，LLM 收集了指标、表格、图表数据', en: 'User says "analyze API performance", LLM collects metrics, tables, charts' },
            aiResponse: { zh: 'LLM 自动弹出 custom 弹框，混合渲染 alert + kv + table + chart + input', en: 'LLM auto-pops custom dialog, rendering alert + kv + table + chart + input' }
        }
    ]
};
