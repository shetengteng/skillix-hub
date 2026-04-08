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
            title: { zh: '导入项目设计文档到知识库', en: 'Import project design docs to KB' },
            userInput: { zh: '把项目的设计文档都导入知识库', en: 'Import all design docs into the knowledge base' },
            aiResponse: {
                zh: '正在导入项目设计文档...\n\n执行：python3 skills/knowledge-base/main.py import-project\n\n✅ 项目导入完成: 80 个新条目, 0 个已存在跳过\n   来源目录: /path/to/project/design\n   匹配模式: *.md\n\n💡 下一步：\n  - `kb list` — 查看已导入的资料\n  - `kb compile --dry-run` — 预览待编译清单',
                en: 'Importing project design docs...\n\nRunning: python3 skills/knowledge-base/main.py import-project\n\n✅ Import complete: 80 new entries, 0 skipped\n   Source: /path/to/project/design\n   Pattern: *.md\n\n💡 Next:\n  - `kb list` — view imported items\n  - `kb compile --dry-run` — preview compilation list'
            }
        },
        {
            title: { zh: '添加代码文件到知识库', en: 'Add code files to KB' },
            userInput: { zh: '把 src/indexer.py 加到知识库，标签是 indexer, core', en: 'Add src/indexer.py to KB with tags indexer, core' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-base/main.py add src/indexer.py --tags "indexer,core"\n\n✅ 已添加: kb-20260408-123456-001\n   标题: indexer.py\n   类型: code\n   分类: uncategorized\n   标签: indexer, core\n\n知识库支持任意文件类型：code、config、markdown、dataset、image、binary 等，LLM 能读的都能索引。',
                en: 'Running: python3 skills/knowledge-base/main.py add src/indexer.py --tags "indexer,core"\n\n✅ Added: kb-20260408-123456-001\n   Title: indexer.py\n   Type: code\n   Category: uncategorized\n   Tags: indexer, core\n\nKB supports any file type: code, config, markdown, dataset, image, binary, etc.'
            }
        },
        {
            title: { zh: '编译知识库 Wiki', en: 'Compile KB Wiki' },
            userInput: { zh: '编译知识库', en: 'Compile the knowledge base' },
            aiResponse: {
                zh: '执行编译流程...\n\n1. python3 skills/knowledge-base/main.py compile\n   → 待编译: 40 个条目，已有概念: 16 个\n   → 分析内容，提取概念...\n\n2. 创建概念条目（wiki/concepts/*.md）\n   → 提取了 5 个新概念\n\n3. python3 skills/knowledge-base/main.py compile --finalize\n   → 更新反向链接、知识图谱、知识地图\n\n✅ 编译完成\n   概念条目: 21 个\n   知识图谱: 68 节点 / 95 边',
                en: 'Running compilation...\n\n1. python3 skills/knowledge-base/main.py compile\n   → Pending: 40 entries, existing concepts: 16\n   → Analyzing content, extracting concepts...\n\n2. Creating concept entries (wiki/concepts/*.md)\n   → Extracted 5 new concepts\n\n3. python3 skills/knowledge-base/main.py compile --finalize\n   → Updated backlinks, knowledge graph, index map\n\n✅ Compilation complete\n   Concepts: 21\n   Graph: 68 nodes / 95 edges'
            }
        },
        {
            title: { zh: '搜索之前的设计资料', en: 'Search previous design docs' },
            userInput: { zh: '找找之前关于 pywebview 的设计', en: 'Find previous design docs about pywebview' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-base/main.py search "pywebview"\n\n=== Knowledge Base: 搜索结果 ===\n\n  📄 ✅ kb-20260408-024455-006 | 轻量化改造方案\n      分类: agent-interact\n\n  📄 ✅ kb-20260408-024455-007 | pywebview vs Neutralinojs 对比\n      分类: agent-interact\n\n  💡 agent-interact-visual-bridge | Agent Interact 可视化桥梁\n\n共 3 个结果\n\n💡 执行 `kb read agent-interact-visual-bridge` 查看概念详情',
                en: 'Running: python3 skills/knowledge-base/main.py search "pywebview"\n\n=== Knowledge Base: Search Results ===\n\n  📄 ✅ kb-20260408-024455-006 | Lightweight Migration Plan\n      Category: agent-interact\n\n  📄 ✅ kb-20260408-024455-007 | pywebview vs Neutralinojs Comparison\n      Category: agent-interact\n\n  💡 agent-interact-visual-bridge | Agent Interact Visual Bridge\n\n3 results found'
            }
        },
        {
            title: { zh: '渐进式浏览知识库', en: 'Progressive browsing' },
            userInput: { zh: '浏览一下知识库，看看 memory 分类', en: 'Browse the KB, show me the memory category' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-base/main.py browse memory\n\n# memory\n\n- [Memory 四层存储架构](../concepts/memory-four-layer-architecture.md) [memory, architecture, hooks, storage]\n- [Hooks + Agent 协作模式](../concepts/hooks-agent-collaboration-pattern.md) [hooks, agent, pattern]\n- [本地嵌入模型](../concepts/local-embedding-model.md) [embedding, semantic-search, local]\n- [记忆质量优化](../concepts/memory-quality-optimization.md) [memory, quality, distill]\n\n💡 执行 `kb read memory-four-layer-architecture` 查看概念全文',
                en: 'Running: python3 skills/knowledge-base/main.py browse memory\n\n# memory\n\n- [Memory Four-Layer Architecture](../concepts/memory-four-layer-architecture.md)\n- [Hooks + Agent Collaboration Pattern](../concepts/hooks-agent-collaboration-pattern.md)\n- [Local Embedding Model](../concepts/local-embedding-model.md)\n- [Memory Quality Optimization](../concepts/memory-quality-optimization.md)\n\n💡 Run `kb read memory-four-layer-architecture` for full concept'
            }
        },
        {
            title: { zh: '查看知识图谱', en: 'View knowledge graph' },
            userInput: { zh: '以 memory-four-layer-architecture 为中心看关联', en: 'Show relations centered on memory-four-layer-architecture' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-base/main.py graph --center memory-four-layer-architecture --depth 2 --format mermaid\n\n```mermaid\ngraph LR\n  memory-four-layer-architecture["Memory 四层存储架构"]\n  hooks-agent-collaboration-pattern["Hooks + Agent 协作模式"]\n  local-embedding-model["本地嵌入模型"]\n  memory-quality-optimization["记忆质量优化"]\n  memory-four-layer-architecture --> hooks-agent-collaboration-pattern\n  memory-four-layer-architecture --> local-embedding-model\n  memory-four-layer-architecture --> memory-quality-optimization\n```\n\n该概念关联了 3 个直接相关概念和 5 个来源资料。',
                en: 'Running: python3 skills/knowledge-base/main.py graph --center memory-four-layer-architecture --depth 2 --format mermaid\n\n```mermaid\ngraph LR\n  memory-four-layer-architecture --> hooks-agent-collaboration-pattern\n  memory-four-layer-architecture --> local-embedding-model\n  memory-four-layer-architecture --> memory-quality-optimization\n```\n\n3 directly related concepts and 5 source materials.'
            }
        }
    ]
};
