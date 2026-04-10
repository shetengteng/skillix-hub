/**
 * Skillix Hub - knowledge-compiler Skill Data
 */
window.SKILL_DATA_KNOWLEDGE_COMPILER = {
    id: 'knowledge-compiler',
    name: 'knowledge-compiler',
    icon: 'document',
    description: {
        zh: 'AI 即编译器 — 将知识材料编译为结构化 Wiki。纯 Markdown Skill，零代码零依赖，覆盖度追踪，增量编译，Hard/Soft Gate 质量检查',
        en: 'AI is the compiler — compile knowledge materials into structured Wiki. Pure Markdown Skill, zero code, coverage tracking, incremental compilation, Hard/Soft Gate quality checks'
    },
    tags: [
        { zh: '知识编译', en: 'Knowledge Compilation' },
        { zh: 'AI 即编译器', en: 'AI as Compiler' },
        { zh: '覆盖度追踪', en: 'Coverage Tracking' },
        { zh: '质量门禁', en: 'Quality Gates' },
        { zh: '跨平台', en: 'Cross-platform' }
    ],
    features: [
        { zh: 'AI 即编译器：AI 读取 Markdown 指令自行执行，纯 Markdown，零代码，零依赖', en: 'AI is the compiler: AI reads Markdown instructions and executes directly, pure Markdown, zero code, zero dependencies' },
        { zh: '5 阶段编译管道：Scan → Classify → Compile → Schema+Index+Verify → State', en: '5-phase pipeline: Scan → Classify → Compile → Schema+Index+Verify → State' },
        { zh: '覆盖度追踪：每个章节标记 high/medium/low，AI 据此决定是否回查原始文件', en: 'Coverage tracking: each section tagged high/medium/low, AI decides when to consult raw files' },
        { zh: 'Hard/Soft Gate 质量检查：frontmatter 完整性、来源有效性、schema 一致性', en: 'Hard/Soft Gate quality checks: frontmatter completeness, source validity, schema consistency' },
        { zh: '人机共维：编译器保留用户手动编辑，Schema 由人和 AI 共同维护', en: 'Human-AI co-maintenance: compiler preserves manual edits, schema co-maintained by both' },
        { zh: '会话模式：staging / recommended / primary 三种模式自动注入上下文', en: 'Session modes: staging / recommended / primary for automatic context injection' },
        { zh: '跨平台兼容：支持 Cursor、Claude Code、Codex', en: 'Cross-platform: supports Cursor, Claude Code, Codex' }
    ],
    scripts: [],
    version: '0.2.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/knowledge-compiler',
    useCases: [
        {
            title: { zh: '初始化知识库', en: 'Initialize knowledge base' },
            userInput: { zh: '帮我初始化一个知识库', en: 'Help me initialize a knowledge base' },
            aiResponse: {
                zh: 'AI 读取 SKILL.md → 路由到 commands/kc-init.md → 按步骤执行：\n\n1. 检查当前目录无 .kc-config.json\n2. 创建目录结构 raw/ + wiki/\n3. 生成 .kc-config.json\n4. 创建 wiki/INDEX.md 和 wiki/log.md\n\nKnowledge base initialized.\n\nSources: raw/designs/, raw/decisions/, raw/research/, raw/notes/\nOutput:  wiki/\nMode:    recommended\n\nNext steps:\n  1. Add materials to raw/ subdirectories\n  2. Run: kc compile',
                en: 'AI reads SKILL.md → routes to commands/kc-init.md → executes steps:\n\n1. Check no .kc-config.json exists\n2. Create raw/ + wiki/ directories\n3. Generate .kc-config.json\n4. Create wiki/INDEX.md and wiki/log.md\n\nKnowledge base initialized.\nSources: raw/designs/, raw/decisions/, raw/research/, raw/notes/\nMode: recommended'
            }
        },
        {
            title: { zh: '编译知识库', en: 'Compile knowledge base' },
            userInput: { zh: '编译一下', en: 'Compile the wiki' },
            aiResponse: {
                zh: 'AI 读取 commands/kc-compile.md → 调用 skills/wiki-compiler.md 5 阶段管道：\n\nPhase 1: Scan — 读取 .compile-state.json，对比 mtime\n  发现 3 new, 1 changed\n\nPhase 2: Classify — 推断 topic slug\n  api-gateway-design: [api-gateway.md]\n  event-driven-arch: [event-driven.md, cqrs.md]\n\nPhase 3: Compile — 读全文，生成概念文章\n  [new] wiki/concepts/api-gateway-design.md\n  [updated] wiki/concepts/event-driven-arch.md\n\nPhase 4: Index + Verify\n  Hard Gates: all passed\n  Soft Gates: 1 warning (orphan page)\n\nPhase 5: State updated\n\nCompiled: 1 new, 1 updated, 5 unchanged',
                en: 'AI reads commands/kc-compile.md → invokes skills/wiki-compiler.md 5-phase pipeline:\n\nPhase 1: Scan — 3 new, 1 changed\nPhase 2: Classify — inferred 2 topics\nPhase 3: Compile — generated/updated articles\nPhase 4: Verify — Hard Gates passed, 1 Soft Gate warning\nPhase 5: State updated\n\nCompiled: 1 new, 1 updated, 5 unchanged'
            }
        },
        {
            title: { zh: '查询知识', en: 'Query knowledge' },
            userInput: { zh: 'API 网关的设计取舍是什么？', en: 'What are the API gateway design trade-offs?' },
            aiResponse: {
                zh: 'AI 读取 commands/kc-query.md → 按步骤执行：\n\n1. 读取 wiki/INDEX.md → 识别相关主题 api-gateway-design\n2. 读取 wiki/concepts/api-gateway-design.md\n3. Key Decisions 章节覆盖度 medium → 引用但标注不确定性\n4. Gotchas 章节覆盖度 low → 回查 raw/designs/api-gateway.md\n\n基于 Wiki 和原始文档：\n\n1. 集中式 vs 分布式网关：选择了集中式... [wiki: api-gateway-design]\n2. 认证策略：在网关层做 JWT 验证... [source: raw/designs/api-gateway.md]\n\n注：Gotchas 章节覆盖度较低，已从原始文档补充验证。',
                en: 'AI reads commands/kc-query.md → executes:\n\n1. Read wiki/INDEX.md → found api-gateway-design\n2. Read concept article → Key Decisions (medium), Gotchas (low)\n3. Low coverage → also read raw source for verification\n\nTrade-offs:\n1. Centralized vs distributed gateway [wiki: api-gateway-design]\n2. JWT at gateway layer [source: raw/designs/api-gateway.md]'
            }
        },
        {
            title: { zh: '健康检查', en: 'Health check' },
            userInput: { zh: '检查一下知识库质量', en: 'Check knowledge base quality' },
            aiResponse: {
                zh: 'AI 读取 commands/kc-lint.md + references/quality-gates.md → 执行检查：\n\nkc lint report — 2026-04-10\n──────────────────────────────────\nHard Gates: 5 passed, 1 failed\n  [FAIL] wiki/concepts/old-topic.md — missing coverage tag on ## Current State\n\nSoft Gates: 3 warnings\n  [STALE]   wiki/concepts/auth-flow.md — sources changed 12 days ago\n  [ORPHAN]  wiki/concepts/old-topic.md — no inbound links\n  [LOW-COV] wiki/concepts/cache-strategy.md — all sections low\n\n1 auto-fixable issue. Fix? (y/n)',
                en: 'AI reads commands/kc-lint.md + references/quality-gates.md → runs checks:\n\nHard Gates: 5 passed, 1 failed\n  [FAIL] missing coverage tag\n\nSoft Gates: 3 warnings\n  [STALE] sources changed 12 days ago\n  [ORPHAN] no inbound links\n  [LOW-COV] all sections low\n\n1 auto-fixable. Fix? (y/n)'
            }
        },
        {
            title: { zh: '浏览知识地图', en: 'Browse knowledge map' },
            userInput: { zh: '看看知识库有什么', en: 'What\'s in the knowledge base?' },
            aiResponse: {
                zh: 'AI 读取 commands/kc-browse.md → 读取 wiki/INDEX.md + wiki/schema.md：\n\nKnowledge Map\n─────────────\n## Architecture (3 topics)\n  api-gateway-design      [high]   API 网关设计决策与实现方案\n  event-driven-arch       [medium] 事件驱动架构模式\n  microservice-patterns   [medium] 微服务通信模式\n\n## Data (2 topics)\n  database-sharding       [high]   数据库分片策略\n  cache-strategy          [low]    缓存层设计\n\nTotal: 5 topics | High: 2 | Medium: 2 | Low: 1',
                en: 'AI reads commands/kc-browse.md → reads wiki/INDEX.md + wiki/schema.md:\n\nKnowledge Map\n─────────────\nArchitecture (3): api-gateway [high], event-driven [medium], microservice [medium]\nData (2): db-sharding [high], cache [low]\n\nTotal: 5 topics | High: 2 | Medium: 2 | Low: 1'
            }
        }
    ]
};
