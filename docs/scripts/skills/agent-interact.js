/**
 * Skillix Hub - Agent Interact Skill Data
 */
window.SKILL_DATA_AGENT_INTERACT = {
    id: 'agent-interact',
    name: 'agent-interact',
    icon: 'chart',
    description: {
        zh: 'AI Agent 与用户之间的可视化交互桥梁，通过 Electron 独立窗口支持 7 种交互场景',
        en: 'Visual interaction bridge between AI Agent and user via Electron standalone windows, supporting 7 interaction types'
    },
    tags: [
        { zh: '交互', en: 'Interaction' },
        { zh: 'Electron', en: 'Electron' },
        { zh: '可视化', en: 'Visualization' },
        { zh: 'Vue', en: 'Vue' }
    ],
    features: [
        { zh: 'Electron 独立置顶窗口 — 自动弹出，无需切换应用', en: 'Electron standalone window — auto-pops, no app switching needed' },
        { zh: '7 种交互类型 — 确认、等待、图表、通知、表单、审批、进度', en: '7 interaction types — confirm, wait, chart, notification, form, approval, progress' },
        { zh: 'LLM 自主决策 — Agent 自动判断何时需要用户介入', en: 'LLM autonomous decision — Agent decides when user input is needed' },
        { zh: 'HTTP API — 任何 Agent 都可通过 REST API 调用', en: 'HTTP API — Any agent can call via REST API' },
        { zh: '浏览器 Fallback — Electron 不可用时自动降级', en: 'Browser fallback — auto-degrades when Electron unavailable' }
    ],
    scripts: ['tool.js'],
    version: '2.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/agent-interact',
    useCases: [
        {
            title: { zh: '确认选择', en: 'Confirm Selection' },
            userInput: { zh: 'Agent 检测到多个环境，自动弹出选择框', en: 'Agent detects multiple environments, auto-pops selection dialog' },
            aiResponse: { zh: 'Electron 窗口弹出，用户选择后 Agent 继续执行', en: 'Electron window pops up, Agent continues after user selection' }
        },
        {
            title: { zh: '审批门控', en: 'Approval Gate' },
            userInput: { zh: 'Agent 即将执行高危操作，自动弹出审批框', en: 'Agent about to execute risky operation, auto-pops approval dialog' },
            aiResponse: { zh: '用户审批后 Agent 继续，拒绝则中止', en: 'Agent continues after approval, aborts on rejection' }
        },
        {
            title: { zh: '表单输入', en: 'Form Input' },
            userInput: { zh: 'Agent 缺少配置信息，自动弹出表单', en: 'Agent needs config info, auto-pops form dialog' },
            aiResponse: { zh: '用户填写表单后 Agent 获取数据继续执行', en: 'Agent gets data and continues after form submission' }
        }
    ]
};
