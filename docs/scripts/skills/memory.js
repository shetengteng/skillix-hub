/**
 * Skillix Hub - memory Skill Data
 */
window.SKILL_DATA_MEMORY = {
    id: 'memory',
    name: 'memory',
    icon: 'lightbulb',
    description: {
        zh: '为 AI 助手提供跨会话长期记忆能力，零外部依赖，通过 Hook 机制自动保存事实和摘要，支持语义搜索和记忆管理',
        en: 'Cross-session long-term memory for AI assistants, zero dependencies, auto-save facts and summaries via Hooks, with semantic search and memory management'
    },
    tags: [
        { zh: '记忆', en: 'Memory' },
        { zh: '上下文', en: 'Context' },
        { zh: '语义搜索', en: 'Semantic Search' },
        { zh: 'Hook', en: 'Hook' }
    ],
    features: [
        { zh: '自动记忆（Hook 触发）', en: 'Auto Memory (Hook-triggered)' },
        { zh: '语义搜索', en: 'Semantic Search' },
        { zh: '事实保存（W/B/O 分类）', en: 'Fact Storage (W/B/O Types)' },
        { zh: '会话摘要', en: 'Session Summary' },
        { zh: '记忆管理', en: 'Memory Management' },
        { zh: '自然语言配置', en: 'Natural Language Config' },
        { zh: '数据库可视化', en: 'Database Viewer' },
        { zh: '一键初始化', en: 'One-click Init' },
        { zh: '项目级禁用开关', en: 'Per-project Disable Switch' },
        { zh: '新项目自动初始化', en: 'Auto Init for New Projects' }
    ],
    scripts: ['service/memory/save_fact.py', 'service/memory/search_memory.py', 'service/manage/index.py', 'service/manage/commands/cmd_db.py', 'service/hooks/load_memory.py', 'service/init/index.py'],
    version: '2.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/memory',
    useCases: [
        {
            title: { zh: '安装 Memory Skill', en: 'Install Memory Skill' },
            userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 安装 memory skill', en: 'Please install memory skill from https://github.com/shetengteng/skillix-hub' },
            aiResponse: {
                zh: '正在安装 Memory Skill...\n\n1. 克隆仓库\n2. 复制 skills/memory 到 ~/.cursor/skills/\n3. 运行初始化脚本\n\n✅ Memory Skill 安装成功！\n\n已配置：\n• sessionStart Hook → 自动加载记忆\n• preCompact Hook → 上下文压缩前保存事实\n• stop Hook → 会话结束保存摘要\n• sessionEnd Hook → 同步索引与清理\n• memory-rules.mdc → 引导 Agent 执行记忆操作\n\n数据目录：\n• 记忆数据存储在各项目本地：<项目>/.cursor/skills/memory-data/\n• 首次会话时自动创建，无需手动初始化',
                en: 'Installing Memory Skill...\n\n1. Clone repository\n2. Copy skills/memory to ~/.cursor/skills/\n3. Run init script\n\n✅ Memory Skill installed!\n\nConfigured:\n• sessionStart Hook → auto-load memory\n• preCompact Hook → save facts before context compression\n• stop Hook → save summary on session end\n• sessionEnd Hook → sync index and cleanup\n• memory-rules.mdc → guide Agent memory operations\n\nData directory:\n• Memory data stored per-project at: <project>/.cursor/skills/memory-data/\n• Auto-created on first session, no manual init needed'
            }
        },
        {
            title: { zh: '更新 Memory Skill', en: 'Update Memory Skill' },
            userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 更新 memory skill', en: 'Please update memory skill from https://github.com/shetengteng/skillix-hub' },
            aiResponse: {
                zh: '正在更新 Memory Skill...\n\n1. 克隆最新代码到临时目录\n2. 运行 update.py 脚本（非直接覆盖文件）\n   python3 /tmp/skillix-hub/skills/memory/scripts/service/init/update.py --source /tmp/skillix-hub/skills/memory --project-path .\n3. update.py 自动完成：\n   • 替换 skill 代码并处理占位符\n   • 合并 hooks.json（不重复添加）\n   • 更新 memory-rules.mdc 和 SKILL.md\n   • 不触碰 memory-data/、config.json、MEMORY.md\n\n✅ Memory Skill 已更新到最新版本！\n已有记忆数据和配置完整保留',
                en: 'Updating Memory Skill...\n\n1. Clone latest code to temp directory\n2. Run update.py script (not direct file copy)\n   python3 /tmp/skillix-hub/skills/memory/scripts/service/init/update.py --source /tmp/skillix-hub/skills/memory --project-path .\n3. update.py automatically:\n   • Replaces skill code with placeholder resolution\n   • Merges hooks.json (no duplicates)\n   • Updates memory-rules.mdc and SKILL.md\n   • Preserves memory-data/, config.json, MEMORY.md\n\n✅ Memory Skill updated to latest version!\nExisting memory data and config fully preserved'
            }
        },
        {
            title: { zh: '自动加载记忆（新会话开始）', en: 'Auto Load Memory (New Session)' },
            userInput: { zh: '继续昨天的 API 重构工作', en: 'Continue yesterday\'s API refactoring work' },
            aiResponse: {
                zh: '（sessionStart Hook 已自动加载记忆上下文）\n\n根据之前的记忆，昨天我们讨论了：\n\n• 决定使用 FastAPI 替换 Flask（W 类型事实）\n• 采用 RESTful 风格，路径前缀 /api/v2（W 类型事实）\n• 待办：实现认证中间件（上次会话摘要）\n\n我们从认证中间件开始吧。需要我先设计接口还是直接实现？',
                en: '(sessionStart Hook auto-loaded memory context)\n\nBased on previous memories, yesterday we discussed:\n\n• Decided to use FastAPI instead of Flask (W-type fact)\n• Adopted RESTful style, path prefix /api/v2 (W-type fact)\n• TODO: implement auth middleware (last session summary)\n\nLet\'s start with the auth middleware. Want me to design the API first or go straight to implementation?'
            }
        },
        {
            title: { zh: '记住这个决策', en: 'Remember This Decision' },
            userInput: { zh: '记住这个：我们项目统一使用 PostgreSQL 数据库，不用 MySQL', en: 'Remember this: our project uses PostgreSQL, not MySQL' },
            aiResponse: {
                zh: '已记录到核心记忆 MEMORY.md 中。\n\n以后的会话中我会记得项目使用 PostgreSQL 数据库。',
                en: 'Recorded to core memory MEMORY.md.\n\nI\'ll remember the project uses PostgreSQL in future sessions.'
            }
        },
        {
            title: { zh: '搜索记忆', en: 'Search Memory' },
            userInput: { zh: '搜索一下我们之前关于数据库的讨论', en: 'Search our previous discussions about database' },
            aiResponse: {
                zh: '搜索记忆中...\n\n找到 3 条相关记忆：\n\n1. [W] 项目统一使用 PostgreSQL 数据库（置信度 0.95）\n   - 日期: 2026-02-18\n   - 实体: PostgreSQL, 数据库\n\n2. [W] 数据库连接池配置为最大 20 个连接\n   - 日期: 2026-02-17\n   - 实体: PostgreSQL, 连接池\n\n3. [S] 会话摘要：讨论了数据库选型方案\n   - 日期: 2026-02-16\n   - 决策: 选择 PostgreSQL',
                en: 'Searching memory...\n\nFound 3 relevant memories:\n\n1. [W] Project uses PostgreSQL database (confidence 0.95)\n   - Date: 2026-02-18\n   - Entities: PostgreSQL, database\n\n2. [W] Database connection pool configured to max 20\n   - Date: 2026-02-17\n   - Entities: PostgreSQL, connection pool\n\n3. [S] Session summary: discussed database selection\n   - Date: 2026-02-16\n   - Decision: chose PostgreSQL'
            }
        },
        {
            title: { zh: '上下文压缩时自动保存', en: 'Auto Save on Context Compression' },
            userInput: { zh: '（长对话中触发 preCompact Hook，Agent 静默执行）', en: '(preCompact Hook triggered during long conversation, Agent executes silently)' },
            aiResponse: {
                zh: '（Agent 在后台静默执行，用户不可见）\n\n[Memory Flush] 触发 → Agent 回顾当前对话：\n\n• save_fact --content "用户偏好 TypeScript" --type O --confidence 0.85\n• save_fact --content "API 采用 GraphQL" --type W --entities "GraphQL,API"\n• save_fact --content "完成了用户模块重构" --type B\n\n事实已保存到 daily/2026-02-19.jsonl\n（用户继续正常对话，不感知此操作）',
                en: '(Agent executes silently in background, invisible to user)\n\n[Memory Flush] triggered → Agent reviews current conversation:\n\n• save_fact --content "User prefers TypeScript" --type O --confidence 0.85\n• save_fact --content "API uses GraphQL" --type W --entities "GraphQL,API"\n• save_fact --content "Completed user module refactoring" --type B\n\nFacts saved to daily/2026-02-19.jsonl\n(User continues conversation normally, unaware of this operation)'
            }
        },
        {
            title: { zh: '管理记忆', en: 'Manage Memory' },
            userInput: { zh: '帮我看一下记忆统计', en: 'Show me memory statistics' },
            aiResponse: {
                zh: '📊 记忆统计\n\n• 核心记忆 (MEMORY.md): 856 字符\n• 事实记录: 47 条\n  - W (客观事实): 28 条\n  - B (项目经历): 11 条\n  - O (用户偏好): 8 条\n• 会话摘要: 12 条\n• 最近 7 天活跃\n• 磁盘占用: 156 KB\n\n需要删除或编辑某条记忆吗？',
                en: '📊 Memory Statistics\n\n• Core memory (MEMORY.md): 856 characters\n• Fact records: 47 entries\n  - W (World facts): 28\n  - B (Biographical): 11\n  - O (Opinions): 8\n• Session summaries: 12\n• Active in last 7 days\n• Disk usage: 156 KB\n\nNeed to delete or edit any memory?'
            }
        },
        {
            title: { zh: '删除记忆', en: 'Delete Memory' },
            userInput: { zh: '删除关于 MySQL 的记忆', en: 'Delete memories about MySQL' },
            aiResponse: {
                zh: '搜索包含 "MySQL" 的记忆...\n\n找到 2 条：\n1. [W] 旧项目使用 MySQL 5.7 (2026-02-15)\n2. [W] MySQL 连接字符串配置 (2026-02-15)\n\n已删除 2 条记忆。索引已更新。',
                en: 'Searching memories containing "MySQL"...\n\nFound 2 entries:\n1. [W] Old project uses MySQL 5.7 (2026-02-15)\n2. [W] MySQL connection string config (2026-02-15)\n\nDeleted 2 memories. Index updated.'
            }
        },
        {
            title: { zh: '自然语言修改配置', en: 'Natural Language Config' },
            userInput: { zh: '多加载几天的记忆，全量加载改成5天，事实上限改为30条', en: 'Load more days of memory, set full load to 5 days and facts limit to 30' },
            aiResponse: {
                zh: '已更新配置：\n\n1. memory.load_days_full: 2 → 5\n   （最近 5 天的事实将全部加载）\n\n2. memory.facts_limit: 15 → 30\n   （单次最多加载 30 条事实）\n\n配置已保存到 .cursor/skills/memory-data/config.json',
                en: 'Configuration updated:\n\n1. memory.load_days_full: 2 → 5\n   (Facts from last 5 days will be fully loaded)\n\n2. memory.facts_limit: 15 → 30\n   (Up to 30 facts per load)\n\nConfig saved to .cursor/skills/memory-data/config.json'
            }
        },
        {
            title: { zh: '查看配置', en: 'View Configuration' },
            userInput: { zh: '帮我看一下现在的记忆配置', en: 'Show me the current memory configuration' },
            aiResponse: {
                zh: '当前记忆配置：\n\n📋 记忆加载\n• 全量加载天数: 5 天\n• 部分加载天数: 5 天（每天 3 条）\n• 最大加载天数: 7 天\n• 事实上限: 30 条\n\n🔍 嵌入模型\n• 模型: BAAI/bge-small-zh-v1.5\n\n📝 日志\n• 级别: INFO\n• 保留天数: 7 天\n\n🧹 自动清理\n• 清理周期: 90 天\n• 备份保留: 30 天',
                en: 'Current memory configuration:\n\n📋 Memory Loading\n• Full load days: 5\n• Partial load days: 5 (3 per day)\n• Max load days: 7\n• Facts limit: 30\n\n🔍 Embedding Model\n• Model: BAAI/bge-small-zh-v1.5\n\n📝 Logging\n• Level: INFO\n• Retain days: 7\n\n🧹 Auto Cleanup\n• Cleanup cycle: 90 days\n• Backup retain: 30 days'
            }
        },
        {
            title: { zh: '查看数据库内容', en: 'View Database Contents' },
            userInput: { zh: '帮我看一下数据库里存了什么', en: 'Show me what\'s in the database' },
            aiResponse: {
                zh: '📊 索引数据库统计\n\n• 数据库大小: 256 KB\n• 总 chunk 数: 42\n• 含向量索引: 42 条\n\n按类型分布:\n• fact: 35 条\n• core: 4 条\n• summary: 3 条\n\n按记忆类型:\n• W (客观事实): 25 条\n• B (项目经历): 6 条\n• O (用户偏好): 4 条\n\n已同步文件: 8 个\n\n需要查看具体内容或在浏览器中打开吗？',
                en: '📊 Index Database Statistics\n\n• Database size: 256 KB\n• Total chunks: 42\n• With vector index: 42\n\nBy type:\n• fact: 35\n• core: 4\n• summary: 3\n\nBy memory type:\n• W (World facts): 25\n• B (Biographical): 6\n• O (Opinions): 4\n\nSynced files: 8\n\nWant to see specific contents or open in browser?'
            }
        },
        {
            title: { zh: '浏览器打开数据库', en: 'Open Database in Browser' },
            userInput: { zh: '在浏览器中打开数据库看看', en: 'Open the database in browser' },
            aiResponse: {
                zh: '正在启动 datasette Web 界面...\n\n✅ 已在浏览器中打开 http://localhost:8685\n\n你可以在网页中：\n• 浏览所有表和数据\n• 执行自定义 SQL 查询\n• 按列排序和过滤\n• 导出数据为 CSV/JSON\n\n按 Ctrl+C 关闭服务。',
                en: 'Starting datasette web interface...\n\n✅ Opened in browser at http://localhost:8685\n\nYou can:\n• Browse all tables and data\n• Execute custom SQL queries\n• Sort and filter by columns\n• Export data as CSV/JSON\n\nPress Ctrl+C to stop the server.'
            }
        },
        {
            title: { zh: '会话结束自动保存摘要', en: 'Auto Save Summary on Session End' },
            userInput: { zh: '好的，今天就到这里，谢谢', en: 'OK, that\'s all for today, thanks' },
            aiResponse: {
                zh: '好的，再见！\n\n（stop Hook 触发，Agent 静默保存会话摘要）\n\nsave_summary:\n  topic: "认证中间件实现"\n  summary: "实现了基于 JWT 的认证中间件，配置了 CORS..."\n  decisions: "JWT认证,CORS允许前端域名"\n  todos: "添加刷新token逻辑,编写认证测试"',
                en: 'OK, goodbye!\n\n(stop Hook triggered, Agent silently saves session summary)\n\nsave_summary:\n  topic: "Auth middleware implementation"\n  summary: "Implemented JWT-based auth middleware, configured CORS..."\n  decisions: "JWT auth, CORS allow frontend domain"\n  todos: "Add refresh token logic, write auth tests"'
            }
        },
        {
            title: { zh: '禁用/启用记忆功能', en: 'Disable/Enable Memory' },
            userInput: { zh: '这个项目不需要记忆功能', en: 'This project doesn\'t need memory' },
            aiResponse: {
                zh: '已禁用当前项目的 Memory 功能。\n\n执行：mkdir -p .cursor/skills && touch .cursor/skills/.memory-disable\n\n✅ Memory 已禁用\n\n禁用后：\n• 不会加载/保存记忆\n• 不会生成 [Memory Flush] 和 [Session Save] 提示\n• 已有数据保留，重新启用后恢复\n\n如需重新启用，说「重新开启记忆」即可。',
                en: 'Memory disabled for current project.\n\nExecuted: mkdir -p .cursor/skills && touch .cursor/skills/.memory-disable\n\n✅ Memory disabled\n\nWhen disabled:\n• No memory loading/saving\n• No [Memory Flush] or [Session Save] prompts\n• Existing data preserved, restored when re-enabled\n\nTo re-enable, say "re-enable memory".'
            }
        }
    ]
};
