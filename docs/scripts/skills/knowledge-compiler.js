/**
 * Skillix Hub - knowledge-compiler Skill Data
 */
window.SKILL_DATA_KNOWLEDGE_COMPILER = {
    id: 'knowledge-compiler',
    name: 'knowledge-compiler',
    icon: 'document',
    description: {
        zh: '将团队知识材料编译为结构化、有覆盖度标记的 Wiki。Markdown-first，支持增量编译、覆盖度追踪、过期检测',
        en: 'Compile team knowledge into structured Wiki with coverage tags. Markdown-first, incremental compilation, coverage tracking, and staleness detection'
    },
    tags: [
        { zh: '知识编译', en: 'Knowledge Compilation' },
        { zh: 'Markdown-first', en: 'Markdown-first' },
        { zh: '覆盖度追踪', en: 'Coverage Tracking' },
        { zh: '增量编译', en: 'Incremental Build' }
    ],
    features: [
        { zh: 'Markdown-first：输入输出均为 Markdown，用户可直接编辑', en: 'Markdown-first: input and output are both Markdown, directly editable' },
        { zh: '覆盖度追踪：每个章节标记 high/medium/low，AI 据此决定是否回查', en: 'Coverage tracking: each section tagged high/medium/low, AI decides when to consult raw files' },
        { zh: '增量编译：基于 mtime 检测变更，只重编译有变化的概念', en: 'Incremental compilation: detects changes via mtime, recompiles only affected concepts' },
        { zh: '人机共维：编译器保留用户手动编辑，Schema 由人和编译器共同维护', en: 'Human-AI co-maintenance: compiler preserves manual edits, schema co-maintained by both' },
        { zh: '会话模式：staging / recommended / primary 三种模式适配不同场景', en: 'Session modes: staging / recommended / primary for different usage scenarios' }
    ],
    scripts: ['main.py'],
    version: '0.1.0',
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
            title: { zh: '添加设计文档到知识库', en: 'Add design docs to KB' },
            userInput: { zh: '把 design/ 目录下的设计文档都添加到知识库', en: 'Add all design docs from design/ to the knowledge base' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-compiler/main.py add design/ --tags "architecture,design"\n\n✅ 已添加 12 个文件到 raw/\n   目标目录: raw/designs/\n   文件类型: *.md\n\n💡 下一步：\n  - `kc compile` — 编译 Wiki\n  - `kc compile --dry-run` — 预览待编译清单',
                en: 'Running: python3 skills/knowledge-compiler/main.py add design/ --tags "architecture,design"\n\n✅ Added 12 files to raw/\n   Target: raw/designs/\n   Type: *.md\n\n💡 Next:\n  - `kc compile` — compile Wiki\n  - `kc compile --dry-run` — preview compilation list'
            }
        },
        {
            title: { zh: '编译 Wiki', en: 'Compile Wiki' },
            userInput: { zh: '编译知识库', en: 'Compile the knowledge base' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-compiler/main.py compile\n\n📦 Phase 1 — 扫描: 发现 5 个新文件, 2 个变更\n📂 Phase 2 — 分类: 归入 4 个主题\n📝 Phase 3 — 编译: 生成 4 个概念文章\n📋 Phase 4 — 索引: 更新 INDEX.md + schema.md\n💾 Phase 5 — 状态: 保存编译状态\n\n✅ 编译完成，产出 4 个概念文章\n\n💡 执行 `kc status` 查看知识库状态',
                en: 'Running: python3 skills/knowledge-compiler/main.py compile\n\n📦 Phase 1 — Scan: 5 new files, 2 changed\n📂 Phase 2 — Classify: assigned to 4 topics\n📝 Phase 3 — Compile: generated 4 concept articles\n📋 Phase 4 — Index: updated INDEX.md + schema.md\n💾 Phase 5 — State: saved compilation state\n\n✅ Compilation complete, 4 concept articles generated\n\n💡 Run `kc status` to check KB status'
            }
        },
        {
            title: { zh: '增量编译', en: 'Incremental compilation' },
            userInput: { zh: '修改了一个文件后重新编译', en: 'Recompile after modifying a file' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-compiler/main.py compile\n\n📦 Phase 1 — 扫描: 0 个新文件, 1 个变更, 0 个删除\n📂 Phase 2 — 分类: 1 个变更文件归入已有主题\n📝 Phase 3 — 编译: 重编译 1 个概念文章\n📋 Phase 4 — 索引: INDEX.md 无变化\n💾 Phase 5 — 状态: 更新\n\n✅ 增量编译完成，仅重编译 1 个概念\n   跳过未变化的 3 个概念',
                en: 'Running: python3 skills/knowledge-compiler/main.py compile\n\n📦 Phase 1 — Scan: 0 new, 1 changed, 0 deleted\n📂 Phase 2 — Classify: 1 changed file mapped to existing topic\n📝 Phase 3 — Compile: recompiled 1 concept article\n📋 Phase 4 — Index: INDEX.md unchanged\n💾 Phase 5 — State: updated\n\n✅ Incremental compilation done, recompiled 1 concept\n   Skipped 3 unchanged concepts'
            }
        },
        {
            title: { zh: '预览编译计划（dry-run）', en: 'Preview compilation plan (dry-run)' },
            userInput: { zh: '预览一下编译计划', en: 'Preview the compilation plan' },
            aiResponse: {
                zh: '执行：python3 skills/knowledge-compiler/main.py compile --dry-run\n\n=== Dry Run — 编译计划 ===\n\n📦 待处理文件:\n  新增: raw/designs/api-design.md\n  变更: raw/notes/meeting-0410.md\n\n📂 主题分配:\n  api-gateway-design → 1 个新来源\n  sprint-meeting-notes → 1 个变更来源\n\n📝 将编译 2 个概念文章\n\n⚠️ Dry-run 模式，未实际写入',
                en: 'Running: python3 skills/knowledge-compiler/main.py compile --dry-run\n\n=== Dry Run — Compilation Plan ===\n\n📦 Files to process:\n  New: raw/designs/api-design.md\n  Changed: raw/notes/meeting-0410.md\n\n📂 Topic assignment:\n  api-gateway-design → 1 new source\n  sprint-meeting-notes → 1 changed source\n\n📝 Will compile 2 concept articles\n\n⚠️ Dry-run mode, no files written'
            }
        }
    ]
};
