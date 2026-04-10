/**
 * Skillix Hub - knowledge-compiler Skill Data
 */
window.SKILL_DATA_KNOWLEDGE_COMPILER = {
    id: 'knowledge-compiler',
    name: 'knowledge-compiler',
    icon: 'document',
    description: {
        zh: '将团队知识材料编译为结构化、有覆盖度标记的 Wiki。Markdown-first，支持增量编译、覆盖度追踪、Hard/Soft Gate 质量检查、会话注入',
        en: 'Compile team knowledge into structured Wiki with coverage tags. Markdown-first with incremental compilation, coverage tracking, Hard/Soft Gate quality checks, and session injection'
    },
    tags: [
        { zh: '知识编译', en: 'Knowledge Compilation' },
        { zh: 'Markdown-first', en: 'Markdown-first' },
        { zh: '覆盖度追踪', en: 'Coverage Tracking' },
        { zh: '质量门禁', en: 'Quality Gates' },
        { zh: '增量编译', en: 'Incremental Build' }
    ],
    features: [
        { zh: 'Markdown-first：输入输出均为 Markdown，用户可直接编辑', en: 'Markdown-first: input and output are both Markdown, directly editable' },
        { zh: '5 阶段编译管道：Scan → Classify → Compile → Schema+Index+Verify → State', en: '5-phase pipeline: Scan → Classify → Compile → Schema+Index+Verify → State' },
        { zh: '覆盖度追踪：每个章节标记 high/medium/low，AI 据此决定是否回查', en: 'Coverage tracking: each section tagged high/medium/low, AI decides when to consult raw files' },
        { zh: 'Hard/Soft Gate 质量检查：frontmatter 完整性、来源有效性、schema 一致性', en: 'Hard/Soft Gate quality checks: frontmatter completeness, source validity, schema consistency' },
        { zh: '人机共维：编译器保留用户手动编辑，Schema 由人和编译器共同维护', en: 'Human-AI co-maintenance: compiler preserves manual edits, schema co-maintained by both' },
        { zh: '概念状态治理：needs_recompile / aging / weak / orphan 四类状态', en: 'Concept state governance: needs_recompile / aging / weak / orphan status tracking' },
        { zh: '会话注入：staging / recommended / primary 三种模式自动注入上下文', en: 'Session injection: staging / recommended / primary modes for automatic context injection' }
    ],
    scripts: ['main.py'],
    version: '0.2.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/knowledge-compiler',
    useCases: [
        {
            title: { zh: '初始化知识库', en: 'Initialize knowledge base' },
            userInput: { zh: '初始化知识库', en: 'Initialize the knowledge base' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-compiler/main.py init\n\n✅ 知识库初始化完成\n   创建目录: raw/, wiki/concepts/\n   创建文件: .kc-config.json, wiki/INDEX.md, wiki/schema.md, wiki/log.md\n\n💡 下一步：\n  - `kc add <path>` — 添加原始材料\n  - `kc compile --dry-run` — 预览待编译清单',
                en: 'Running: python3 skills/knowledge-compiler/main.py init\n\n✅ Knowledge base initialized\n   Directories: raw/, wiki/concepts/\n   Files: .kc-config.json, wiki/INDEX.md, wiki/schema.md, wiki/log.md\n\n💡 Next:\n  - `kc add <path>` — add source materials\n  - `kc compile --dry-run` — preview compilation list'
            }
        },
        {
            title: { zh: '编译 Wiki（完整 5 阶段流程）', en: 'Compile Wiki (full 5-phase pipeline)' },
            userInput: { zh: '编译知识库', en: 'Compile the knowledge base' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-compiler/main.py compile\n\nPhase 1: 扫描变更...\n  3 new\n\nPhase 2: 分类 3 个文件...\n  api-gateway-design: [\'api-gateway.md\']\n  db-migration: [\'db-migration.md\']\n  redis-caching: [\'redis-caching.md\']\n\nPhase 3: 编译 3 个概念...\n  [new] wiki/concepts/api-gateway-design.md\n  [new] wiki/concepts/db-migration.md\n  [new] wiki/concepts/redis-caching.md\n\nPhase 3.5: 更新 Schema...\n  wiki/schema.md updated\n\nPhase 4: 更新索引 + 质量检查...\n  wiki/INDEX.md updated\n  Verify: Hard: 9 pass / 6 fail | Soft: 9 pass / 3 warn\n\nPhase 5: 更新状态...\n\n✅ 编译完成: 3 new, 0 updated',
                en: 'Running: python3 skills/knowledge-compiler/main.py compile\n\nPhase 1: Scan...\n  3 new\n\nPhase 2: Classify 3 files...\nPhase 3: Compile 3 concepts...\nPhase 3.5: Update Schema...\nPhase 4: Index + Verify...\n  Verify: Hard: 9 pass / 6 fail | Soft: 9 pass / 3 warn\n\nPhase 5: State...\n\n✅ Done: 3 new, 0 updated'
            }
        },
        {
            title: { zh: '健康检查（Hard/Soft Gate）', en: 'Health check (Hard/Soft Gate)' },
            userInput: { zh: '检查一下知识库质量', en: 'Check the knowledge base quality' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-compiler/main.py lint\n\n🔍 执行质量检查...\n\n═══ Hard Gates ═══\n  ❌ [api-design] coverage_tags: 5/7 sections tagged\n  ✅ frontmatter_complete: 3 passed\n  ✅ source_refs_valid: 3 passed\n  ✅ schema_consistent: 3 passed\n\n═══ Soft Gates ═══\n  ⚠️ [api-design] low_coverage: 5/5 low\n  ✅ orphan_concept: 3 passed\n  ✅ broken_links: 3 passed\n  ✅ aging: 3 passed\n\n═══ 概念状态 ═══\n  📉 weak: 3\n\n总结: ❌ FAIL | Hard: 9 pass / 6 fail',
                en: 'Running: python3 skills/knowledge-compiler/main.py lint\n\n🔍 Running quality checks...\n\n═══ Hard Gates ═══\n  ❌ coverage_tags failures\n  ✅ frontmatter, source_refs, schema: all pass\n\n═══ Soft Gates ═══\n  ⚠️ low_coverage warnings\n  ✅ orphan, broken_links, aging: all pass\n\n═══ Concept States ═══\n  📉 weak: 3\n\nResult: ❌ FAIL'
            }
        },
        {
            title: { zh: '查看知识库状态', en: 'View KB status' },
            userInput: { zh: '知识库状态怎么样', en: 'How is the knowledge base doing?' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-compiler/main.py status\n\n═══ Knowledge Compiler Status ═══\n\n  📁 Root: /path/to/project\n  🔧 Session mode: recommended\n  📅 Last compiled: 2026-04-10\n\n  📄 Source files: 15\n  📚 Concepts: 8\n  🏷️ Categories: 3\n\n  Coverage distribution:\n    🟢 high:   12 (30%)\n    🟡 medium: 18 (45%)\n    🔴 low:    10 (25%)\n\n  Concept health:\n    ✅ ok: 5\n    🔄 needs_recompile: 2\n    ⏳ aging: 1',
                en: 'Running: python3 skills/knowledge-compiler/main.py status\n\n═══ Knowledge Compiler Status ═══\n\n  📁 Root: /path/to/project\n  📅 Last compiled: 2026-04-10\n  📄 Sources: 15 | 📚 Concepts: 8 | 🏷️ Categories: 3\n\n  Coverage: 🟢30% high | 🟡45% medium | 🔴25% low\n  Health: ✅5 ok | 🔄2 needs_recompile | ⏳1 aging'
            }
        },
        {
            title: { zh: '浏览知识地图', en: 'Browse knowledge map' },
            userInput: { zh: '浏览一下知识库', en: 'Browse the knowledge base' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-compiler/main.py browse\n\n═══ Knowledge Map ═══\n\n📂 Architecture (3 concepts)\n  - [api-gateway-design] API Gateway Design [gateway, kong] (2H/3M/1L)\n  - [microservice-patterns] Microservice Patterns [patterns] (1H/2M/2L)\n  - [event-sourcing] Event Sourcing [cqrs, events] (0H/1M/3L)\n\n📂 Database (2 concepts)\n  - [db-migration] Database Migration [flyway] (3H/1M/0L)\n  - [redis-caching] Redis Caching [cache, redis] (1H/2M/1L)\n\nTotal: 5 concepts\n💡 Use `kc browse Architecture` for details',
                en: 'Running: python3 skills/knowledge-compiler/main.py browse\n\n═══ Knowledge Map ═══\n\n📂 Architecture (3 concepts)\n  - api-gateway-design (2H/3M/1L)\n  - microservice-patterns (1H/2M/2L)\n  - event-sourcing (0H/1M/3L)\n\n📂 Database (2 concepts)\n  - db-migration (3H/1M/0L)\n  - redis-caching (1H/2M/1L)\n\nTotal: 5 concepts'
            }
        },
        {
            title: { zh: '查询知识库', en: 'Query the knowledge base' },
            userInput: { zh: 'API gateway 的限流策略是什么？', en: 'What is the rate limiting strategy for API gateway?' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-compiler/main.py query "API gateway 限流策略"\n\n找到 2 个相关概念:\n  - API Gateway Design (api-gateway-design)\n  - Microservice Patterns (microservice-patterns)\n\n查询 prompt 已保存到 .kc-query-prompt.md\n\n--- 概念摘要 ---\n\n## API Gateway Design\nWe use Kong as our API gateway... Rate limiting is implemented at the gateway level using token bucket algorithm.\n  ⚠️ low 覆盖: Key Decisions, Open Questions\n\n💡 使用 AI Agent 执行 .kc-query-prompt.md 获取完整回答',
                en: 'Running: python3 skills/knowledge-compiler/main.py query "API gateway rate limiting"\n\nFound 2 relevant concepts:\n  - API Gateway Design\n  - Microservice Patterns\n\nQuery prompt saved to .kc-query-prompt.md\n\n--- Summaries ---\n\n## API Gateway Design\nKong-based gateway with token bucket rate limiting...\n  ⚠️ low coverage: Key Decisions, Open Questions'
            }
        },
        {
            title: { zh: '自动修复质量问题', en: 'Auto-fix quality issues' },
            userInput: { zh: '修复知识库质量问题', en: 'Fix knowledge base quality issues' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-compiler/main.py lint --fix\n\n🔍 执行质量检查...\n\n（...检查结果...）\n\n═══ 自动修复 ═══\n\n  ✅ 已将 2 个概念同步到 schema.md\n\n  修复了 2 个问题。\n\n总结: ❌ FAIL | Hard: 12 pass / 3 fail | Soft: 11 pass / 1 warn',
                en: 'Running: python3 skills/knowledge-compiler/main.py lint --fix\n\n(...check results...)\n\n═══ Auto-fix ═══\n\n  ✅ Synced 2 concepts to schema.md\n\n  Fixed 2 issues.'
            }
        }
    ]
};
