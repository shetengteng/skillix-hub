/**
 * Skillix Hub - Agent Interact Skill Data
 */
window.SKILL_DATA_AGENT_INTERACT = {
    id: 'agent-interact',
    name: 'agent-interact',
    icon: 'chart',
    description: {
        zh: 'AI Agent 与用户之间的可视化交互桥梁，支持确认选择、等待操作、图表展示',
        en: 'Visual interaction bridge between AI Agent and user, supporting confirm dialogs, wait-for-action, and chart display'
    },
    tags: [
        { zh: '交互', en: 'Interaction' },
        { zh: '弹框', en: 'Dialog' },
        { zh: '可视化', en: 'Visualization' },
        { zh: 'Vue', en: 'Vue' }
    ],
    features: [
        { zh: '确认选择弹框 — Agent 需要用户从选项中选择', en: 'Confirm dialog — Agent needs user to choose from options' },
        { zh: '等待操作弹框 — Agent 等待用户完成外部操作', en: 'Wait dialog — Agent waits for user to complete external action' },
        { zh: '图表展示弹框 — Agent 可视化展示数据', en: 'Chart dialog — Agent visualizes data for user' },
        { zh: 'HTTP API — 任何 Agent 都可通过 REST API 调用', en: 'HTTP API — Any agent can call via REST API' },
        { zh: 'WebSocket 实时通信', en: 'WebSocket real-time communication' }
    ],
    scripts: ['tool.js'],
    version: '1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/agent-interact',
    useCases: [
        {
            title: { zh: '确认选择', en: 'Confirm Selection' },
            userInput: { zh: '弹个框让我选择部署环境', en: 'Show me a dialog to choose deployment environment' },
            aiResponse: { zh: '已弹出选择框，请在浏览器中选择部署环境', en: 'Dialog shown, please select deployment environment in browser' }
        },
        {
            title: { zh: '等待操作', en: 'Wait for Action' },
            userInput: { zh: '等我完成指纹验证', en: 'Wait for me to complete fingerprint verification' },
            aiResponse: { zh: '已弹出等待框，请完成验证后点击确认', en: 'Wait dialog shown, please confirm after verification' }
        },
        {
            title: { zh: '图表展示', en: 'Chart Display' },
            userInput: { zh: '画个图展示 API 响应时间', en: 'Show a chart of API response times' },
            aiResponse: { zh: '已在浏览器中展示响应时间折线图', en: 'Response time line chart displayed in browser' }
        }
    ]
};
