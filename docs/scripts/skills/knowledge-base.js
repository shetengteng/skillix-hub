/**
 * Skillix Hub - knowledge-base Skill Data
 */
window.SKILL_DATA_KNOWLEDGE_BASE = {
    id: 'knowledge-base',
    name: 'knowledge-base',
    icon: 'folder',
    description: {
        zh: '本地知识资料索引与 Wiki 编译，管理设计文档、代码仓库、数据集等资料，通过 LLM 编译成结构化 Wiki（含反向链接、概念归类、知识图谱）',
        en: 'Local knowledge asset index and Wiki compilation, managing design docs, code repos, datasets, and compiling them into structured Wiki with backlinks, concept categorization, and knowledge graph'
    },
    tags: [
        { zh: '知识管理', en: 'Knowledge Management' },
        { zh: 'Wiki 编译', en: 'Wiki Compilation' },
        { zh: '知识图谱', en: 'Knowledge Graph' },
        { zh: '渐进式披露', en: 'Progressive Disclosure' }
    ],
    features: [
        { zh: '索引任意文件类型，只索引不复制，支持自动类型检测', en: 'Index any file type, reference-only (no copy), with automatic type detection' },
        { zh: 'Agent 即编译器：利用 LLM 提取概念、编写条目、构建关系', en: 'Agent as Compiler: leverages LLM to extract concepts, write entries, and build relations' },
        { zh: '增量编译：通过 content_hash 只处理新增/修改的内容', en: 'Incremental compilation: processes only new/changed content via content_hash' },
        { zh: '渐进式浏览：知识地图 → 分类 → 概念 → 来源 → 原始文件', en: 'Progressive browsing: map → category → concept → source → raw file' },
        { zh: '知识图谱输出（JSON + Mermaid），支持子图提取', en: 'Knowledge graph output (JSON + Mermaid) with subgraph extraction' }
    ],
    scripts: ['main.py'],
    version: '0.1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/knowledge-base',
    useCases: [
        {
            title: { zh: '导入项目设计文档', en: 'Import project design docs' },
            description: { zh: '一键导入项目 design/ 目录下的所有 Markdown 文件', en: 'One-click import of all Markdown files from the project design/ directory' }
        },
        {
            title: { zh: '编译 Wiki', en: 'Compile Wiki' },
            description: { zh: 'LLM 分析索引内容，提取概念并生成结构化 Wiki 条目', en: 'LLM analyzes indexed content, extracts concepts and generates structured Wiki entries' }
        },
        {
            title: { zh: '搜索知识库', en: 'Search knowledge base' },
            description: { zh: '通过关键词搜索索引和已编译的概念条目', en: 'Search indexed items and compiled concept entries by keyword' }
        }
    ]
};
