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
            zh: '为 AI 助手提供长期记忆能力，自动记录对话并检索相关历史上下文，支持 Cursor、Claude 等多种 AI 助手',
            en: 'Long-term memory for AI assistants, auto-record conversations and retrieve relevant history, supports Cursor, Claude and more'
        },
        tags: [
            { zh: '记忆', en: 'Memory' },
            { zh: '上下文', en: 'Context' },
            { zh: '检索', en: 'Retrieval' },
            { zh: '通用', en: 'Universal' }
        ],
        features: [
            { zh: '保存记忆', en: 'Save Memory' },
            { zh: '搜索记忆', en: 'Search Memory' },
            { zh: '查看记忆', en: 'View Memory' },
            { zh: '删除记忆', en: 'Delete Memory' },
            { zh: '导出记忆', en: 'Export Memory' },
            { zh: '导入记忆', en: 'Import Memory' },
            { zh: '自动记忆规则', en: 'Auto Memory Rules' }
        ],
        scripts: ['save_memory.py', 'search_memory.py', 'view_memory.py', 'delete_memory.py', 'export_memory.py', 'import_memory.py', 'setup_auto_retrieve.py', 'utils.py'],
        version: '1.2',
        author: 'shetengteng',
        repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/memory'
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
    }
];

// 图标 SVG 路径映射
const ICON_PATHS = {
    lightbulb: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    document: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    plus: 'M12 6v6m0 0v6m0-6h6m-6 0H6',
    globe: 'M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    folder: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z',
    info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
};

// 导出供 Vue 使用
if (typeof window !== 'undefined') {
    window.SKILLS_DATA = SKILLS_DATA;
    window.ICON_PATHS = ICON_PATHS;
}
