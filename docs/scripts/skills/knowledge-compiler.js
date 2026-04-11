/**
 * Skillix Hub - knowledge-compiler Skill Data
 */
window.SKILL_DATA_KNOWLEDGE_COMPILER = {
    id: 'knowledge-compiler',
    name: 'knowledge-compiler',
    icon: 'document',
    description: {
        zh: 'AI 即编译器 — 将知识材料编译为结构化 Wiki。纯 Markdown Skill，零代码零依赖，覆盖度追踪，增量编译，Hard/Soft Gate 质量检查，中英文输出，多轮交互式确认',
        en: 'AI is the compiler — compile knowledge materials into structured Wiki. Pure Markdown Skill, zero code, coverage tracking, incremental compilation, Hard/Soft Gate quality checks, zh/en output, interactive confirmation'
    },
    tags: [
        { zh: '知识编译', en: 'Knowledge Compilation' },
        { zh: 'AI 即编译器', en: 'AI as Compiler' },
        { zh: '覆盖度追踪', en: 'Coverage Tracking' },
        { zh: '质量门禁', en: 'Quality Gates' },
        { zh: '跨平台', en: 'Cross-platform' },
        { zh: '交互式', en: 'Interactive' }
    ],
    features: [
        { zh: 'AI 即编译器：AI 读取 Markdown 指令自行执行，纯 Markdown，零代码，零依赖', en: 'AI is the compiler: reads Markdown instructions and executes directly, zero code, zero deps' },
        { zh: '5 阶段编译管道：Scan → Classify → Compile → Schema+Index+Verify → State', en: '5-phase pipeline: Scan → Classify → Compile → Schema+Index+Verify → State' },
        { zh: '覆盖度追踪：每个章节标记 high/medium/low，AI 据此决定是否回查源文件', en: 'Coverage tracking: each section tagged high/medium/low, AI decides when to consult source files' },
        { zh: 'Hard/Soft Gate 质量检查：frontmatter 完整性、来源有效性、schema 一致性', en: 'Hard/Soft Gate quality checks: frontmatter completeness, source validity, schema consistency' },
        { zh: '中英文输出：language 配置控制生成语言，默认中文，模板中文骨架 + en 映射表', en: 'zh/en output: language config controls output, default zh, Chinese template skeleton + en mapping table' },
        { zh: '交互式确认：编译过程中不确定时暂停向用户确认，初始化多轮对话', en: 'Interactive confirmation: pauses for user confirmation when uncertain, multi-round init dialog' },
        { zh: '自定义源目录：支持 doc/、design/ 等已有目录，raw/ 仅为可选默认结构', en: 'Custom source dirs: supports existing dirs like doc/, design/; raw/ is optional default' },
        { zh: '人机共维：编译器保留用户手动编辑，Schema 由人和 AI 共同维护', en: 'Human-AI co-maintenance: compiler preserves manual edits, schema co-maintained' },
        { zh: '会话模式：staging / recommended / primary 三种模式自动注入上下文', en: 'Session modes: staging / recommended / primary for automatic context injection' },
        { zh: '跨平台兼容：支持 Cursor、Claude Code、Codex', en: 'Cross-platform: supports Cursor, Claude Code, Codex' }
    ],
    scripts: [],
    version: '0.3.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/knowledge-compiler',
    useCases: [
        {
            title: { zh: '初始化知识库（多轮交互）', en: 'Initialize knowledge base (multi-round)' },
            userInput: { zh: '帮我初始化一个知识库', en: 'Help me initialize a knowledge base' },
            aiResponse: {
                zh: 'AI 扫描项目目录后展示结果并逐步确认：\n\n第 1 轮 — 选择源目录：\n扫描到以下目录：\n| 目录 | .md 文件数 |\n| doc/ | 12 |\n| design/ | 5 |\n[1] 使用 doc/, design/（推荐）\n[2] 自定义选择\n[3] 使用默认 raw/ 结构\n\n第 2 轮 — 语言：zh（默认）\n第 3 轮 — 模式：recommended（默认）\n\n知识库初始化完成。\n源目录: doc/, design/\n语言: zh\n模式: recommended',
                en: 'AI scans project dirs and confirms step by step:\n\nRound 1 — Choose sources:\nFound dirs with .md files:\n| Dir | Count |\n| doc/ | 12 |\n| design/ | 5 |\n[1] Use doc/, design/ (recommended)\n\nRound 2 — Language: zh (default)\nRound 3 — Mode: recommended (default)\n\nKB initialized.\nSources: doc/, design/\nLanguage: zh\nMode: recommended'
            }
        },
        {
            title: { zh: '编译知识库', en: 'Compile knowledge base' },
            userInput: { zh: '编译一下', en: 'Compile the wiki' },
            aiResponse: {
                zh: 'AI 读取 commands/kc-compile.md → 调用 5 阶段管道：\n\nPhase 1: Scan — 对比源文件 mtime\n  发现 3 新增, 1 变更\n\nPhase 2: Classify — 推断 topic slug\n  （发现不确定归属时暂停询问用户）\n\nPhase 3: Compile — 生成中文 wiki 文章\n  （源文件矛盾时暂停确认）\n\nPhase 4: Index + Verify\n  Hard Gates: 全部通过\n  Soft Gates: 1 个警告\n\n编译完成: 1 新建, 1 更新, 5 未变',
                en: 'AI reads commands/kc-compile.md → invokes 5-phase pipeline:\n\nPhase 1: Scan — 3 new, 1 changed\nPhase 2: Classify — infers topics (pauses if uncertain)\nPhase 3: Compile — generates articles (pauses on conflicts)\nPhase 4: Verify — Hard Gates passed, 1 Soft Gate warning\n\nCompiled: 1 new, 1 updated, 5 unchanged'
            }
        },
        {
            title: { zh: '查询知识', en: 'Query knowledge' },
            userInput: { zh: 'API 网关的设计取舍是什么？', en: 'What are the API gateway design trade-offs?' },
            aiResponse: {
                zh: 'AI 按覆盖度分级处理：\n\n1. 概要 (high) → 直接引用 [wiki: api-gateway-design]\n2. 关键决策 (medium) → 引用并标注"基于单一来源，可能需补充"\n   [source: design/api-gateway.md]\n3. 注意事项 (low) → 回查源文件验证后回答\n\n注：覆盖度较低的章节已从原始文档补充验证。',
                en: 'AI processes by coverage level:\n\n1. Summary (high) → cite directly [wiki: api-gateway-design]\n2. Key Decisions (medium) → cite with caveat\n3. Gotchas (low) → verify from source files first\n\nNote: Low coverage sections verified from source docs.'
            }
        },
        {
            title: { zh: '健康检查', en: 'Health check' },
            userInput: { zh: '检查一下知识库质量', en: 'Check knowledge base quality' },
            aiResponse: {
                zh: 'kc lint 报告 — 2026-04-10\n─────────────\nHard Gates: 5 通过, 1 失败\n  [失败] wiki/concepts/old-topic.md — 缺少覆盖度标记\n\nSoft Gates: 3 个警告\n  [过期] auth-flow.md — 源文件 12 天前有变更\n  [孤立] old-topic.md — 无入站链接\n  [低覆盖] cache-strategy.md — 所有章节为低覆盖\n\n1 个可自动修复。运行 `kc lint --fix` 修复。\n\n注：kc lint 只读报告，不修改文件。',
                en: 'kc lint report — 2026-04-10\n─────────────\nHard Gates: 5 passed, 1 failed\n  [FAIL] missing coverage tag\n\nSoft Gates: 3 warnings\n  [STALE] sources changed 12 days ago\n  [ORPHAN] no inbound links\n\n1 auto-fixable. Run `kc lint --fix` to resolve.\n\nNote: kc lint is read-only.'
            }
        },
        {
            title: { zh: '浏览知识地图', en: 'Browse knowledge map' },
            userInput: { zh: '看看知识库有什么', en: 'Browse knowledge map' },
            aiResponse: {
                zh: '知识地图\n─────────────\n## 架构 (3 个主题)\n  api-gateway-design      [high]   API 网关设计决策\n  event-driven-arch       [medium] 事件驱动架构模式\n  microservice-patterns   [medium] 微服务通信模式\n\n## 数据层 (2 个主题)\n  database-sharding       [high]   数据库分片策略\n  cache-strategy          [low]    缓存层设计\n\n总计: 5 个主题 | 高: 2 | 中: 2 | 低: 1',
                en: 'Knowledge Map\n─────────────\nArchitecture (3): api-gateway [high], event-driven [medium], microservice [medium]\nData (2): db-sharding [high], cache [low]\n\nTotal: 5 topics | High: 2 | Medium: 2 | Low: 1'
            }
        }
    ]
};
