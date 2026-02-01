/**
 * Skillix Hub - Skills Data
 * 技能数据配置文件
 */

const SKILLS_DATA = [
    {
        id: 'memory',
        name: 'memory',
        icon: 'lightbulb',
        description: {
            zh: '为 Cursor 提供长期记忆能力，自动记录对话并检索相关历史上下文，零外部依赖',
            en: 'Long-term memory for Cursor, auto-record conversations and retrieve relevant history, zero external dependencies'
        },
        tags: [
            { zh: '记忆', en: 'Memory' },
            { zh: '上下文', en: 'Context' },
            { zh: '检索', en: 'Retrieval' }
        ],
        features: [
            { zh: '保存记忆', en: 'Save Memory' },
            { zh: '搜索记忆', en: 'Search Memory' },
            { zh: '查看记忆', en: 'View Memory' },
            { zh: '删除记忆', en: 'Delete Memory' }
        ],
        scripts: ['save_memory.py', 'search_memory.py', 'view_memory.py', 'delete_memory.py', 'utils.py'],
        version: '1.0',
        author: 'shetengteng',
        repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/memory'
    },
    {
        id: 'behavior-prediction',
        name: 'behavior-prediction',
        icon: 'chart',
        description: {
            zh: '学习用户行为模式，记录会话内容，预测下一步操作并提供智能建议',
            en: 'Learn user behavior patterns, record sessions, predict next actions and provide smart suggestions'
        },
        tags: [
            { zh: '预测', en: 'Prediction' },
            { zh: '行为', en: 'Behavior' },
            { zh: '智能', en: 'Smart' }
        ],
        features: [
            { zh: '会话记录', en: 'Session Recording' },
            { zh: '模式学习', en: 'Pattern Learning' },
            { zh: '智能预测', en: 'Smart Prediction' },
            { zh: '用户画像', en: 'User Profile' }
        ],
        scripts: ['hook.py', 'get_predictions.py', 'extract_patterns.py', 'user_profile.py', 'utils.py'],
        version: '2.0',
        author: 'shetengteng',
        repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/behavior-prediction'
    },
    {
        id: 'continuous-learning',
        name: 'continuous-learning',
        icon: 'brain',
        description: {
            zh: '持续学习用户与 AI 的交互模式，自动提取可复用知识，生成新技能文件',
            en: 'Continuously learn from user-AI interactions, extract reusable knowledge, generate new skill files'
        },
        tags: [
            { zh: '学习', en: 'Learning' },
            { zh: '知识', en: 'Knowledge' },
            { zh: '演化', en: 'Evolution' }
        ],
        features: [
            { zh: '观察记录', en: 'Observation Recording' },
            { zh: '模式检测', en: 'Pattern Detection' },
            { zh: '本能生成', en: 'Instinct Generation' },
            { zh: '技能演化', en: 'Skill Evolution' }
        ],
        scripts: ['observe.py', 'analyze.py', 'instinct.py', 'setup_rule.py', 'utils.py'],
        version: '1.0',
        author: 'shetengteng',
        repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/continuous-learning'
    },
    {
        id: 'swagger-api-reader',
        name: 'swagger-api-reader',
        icon: 'document',
        description: {
            zh: '读取并缓存 Swagger/OpenAPI 文档，支持浏览器认证，自动生成结构化 API 文档',
            en: 'Read and cache Swagger/OpenAPI docs with browser auth support, auto-generate structured API documentation'
        },
        tags: [
            { zh: 'API', en: 'API' },
            { zh: 'Swagger', en: 'Swagger' },
            { zh: '文档', en: 'Docs' }
        ],
        features: [
            { zh: '读取 Swagger 文档', en: 'Read Swagger Docs' },
            { zh: '生成 API 文档', en: 'Generate API Docs' },
            { zh: '浏览器认证', en: 'Browser Auth' }
        ],
        scripts: ['swagger_reader.py', 'doc_generator.py'],
        version: '1.0',
        author: 'shetengteng',
        repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/swagger-api-reader'
    },
    {
        id: 'uniapp-mp-generator',
        name: 'uniapp-mp-generator',
        icon: 'code',
        description: {
            zh: 'uni-app 小程序代码生成器，根据需求文档自动生成 Vue3 页面、API、Store 等代码',
            en: 'uni-app mini-program code generator, auto-generate Vue3 pages, API, Store from requirements'
        },
        tags: [
            { zh: '代码生成', en: 'Code Gen' },
            { zh: 'uni-app', en: 'uni-app' },
            { zh: 'Vue3', en: 'Vue3' }
        ],
        features: [
            { zh: '页面生成', en: 'Page Generation' },
            { zh: 'API 生成', en: 'API Generation' },
            { zh: 'Store 生成', en: 'Store Generation' },
            { zh: '组件生成', en: 'Component Generation' }
        ],
        scripts: [],
        version: '1.0',
        author: 'shetengteng',
        repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/uniapp-mp-generator'
    }
];

// 图标 SVG 路径映射
const ICON_PATHS = {
    lightbulb: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    document: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    plus: 'M12 6v6m0 0v6m0-6h6m-6 0H6',
    globe: 'M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    folder: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z',
    info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    chart: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    brain: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    code: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4'
};

// 导出供 Vue 使用
if (typeof window !== 'undefined') {
    window.SKILLS_DATA = SKILLS_DATA;
    window.ICON_PATHS = ICON_PATHS;
}
