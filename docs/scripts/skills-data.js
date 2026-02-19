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
            { zh: '一键初始化', en: 'One-click Init' }
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
                    zh: '正在安装 Memory Skill...\n\n1. 克隆仓库\n2. 复制 skills/memory 到 ~/.cursor/skills/\n3. 运行初始化脚本\n\n✅ Memory Skill 安装成功！\n\n已配置：\n• sessionStart Hook → 自动加载记忆\n• preCompact Hook → 上下文压缩前保存事实\n• stop Hook → 会话结束保存摘要\n• memory-rules.mdc → 引导 Agent 执行记忆操作', 
                    en: 'Installing Memory Skill...\n\n1. Clone repository\n2. Copy skills/memory to ~/.cursor/skills/\n3. Run init script\n\n✅ Memory Skill installed!\n\nConfigured:\n• sessionStart Hook → auto-load memory\n• preCompact Hook → save facts before context compression\n• stop Hook → save summary on session end\n• memory-rules.mdc → guide Agent memory operations' 
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
                    zh: '（Agent 在后台静默执行，用户不可见）\n\n[Memory Flush] 触发 → Agent 回顾当前对话：\n\n• save_fact --content \"用户偏好 TypeScript\" --type O --confidence 0.85\n• save_fact --content \"API 采用 GraphQL\" --type W --entities \"GraphQL,API\"\n• save_fact --content \"完成了用户模块重构\" --type B\n\n事实已保存到 daily/2026-02-19.jsonl\n（用户继续正常对话，不感知此操作）', 
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
                    zh: '搜索包含 \"MySQL\" 的记忆...\n\n找到 2 条：\n1. [W] 旧项目使用 MySQL 5.7 (2026-02-15)\n2. [W] MySQL 连接字符串配置 (2026-02-15)\n\n已删除 2 条记忆。索引已更新。', 
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
                    zh: '好的，再见！\n\n（stop Hook 触发，Agent 静默保存会话摘要）\n\nsave_summary:\n  topic: \"认证中间件实现\"\n  summary: \"实现了基于 JWT 的认证中间件，配置了 CORS...\"\n  decisions: \"JWT认证,CORS允许前端域名\"\n  todos: \"添加刷新token逻辑,编写认证测试\"', 
                    en: 'OK, goodbye!\n\n(stop Hook triggered, Agent silently saves session summary)\n\nsave_summary:\n  topic: "Auth middleware implementation"\n  summary: "Implemented JWT-based auth middleware, configured CORS..."\n  decisions: "JWT auth, CORS allow frontend domain"\n  todos: "Add refresh token logic, write auth tests"' 
                }
            }
        ]
    },
    {
        id: 'behavior-prediction',
        name: 'behavior-prediction',
        icon: 'chart',
        description: {
            zh: '学习用户行为模式，记录会话内容，预测下一步操作并提供智能建议，支持多种 AI 助手',
            en: 'Learn user behavior patterns, record sessions, predict next actions and provide smart suggestions, supports multiple AI assistants'
        },
        tags: [
            { zh: '预测', en: 'Prediction' },
            { zh: '行为', en: 'Behavior' },
            { zh: '智能', en: 'Smart' },
            { zh: '通用', en: 'Universal' }
        ],
        features: [
            { zh: '会话记录', en: 'Session Recording' },
            { zh: '模式学习', en: 'Pattern Learning' },
            { zh: '智能预测', en: 'Smart Prediction' },
            { zh: '用户画像', en: 'User Profile' },
            { zh: '自动执行', en: 'Auto Execute' },
            { zh: '工作流程分析', en: 'Workflow Analysis' }
        ],
        scripts: ['hook.py', 'record_session.py', 'extract_patterns.py', 'user_profile.py', 'get_predictions.py', 'setup_rule.py', 'utils.py'],
        version: '2.0',
        author: 'shetengteng',
        repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/behavior-prediction',
        useCases: [
            {
                title: { zh: '安装 Behavior Prediction Skill', en: 'Install Behavior Prediction Skill' },
                userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 安装 behavior-prediction skill', en: 'Please install behavior-prediction skill from https://github.com/shetengteng/skillix-hub' },
                aiResponse: { 
                    zh: '✅ Behavior Prediction Skill V2 安装成功！\n\n👉 下一步：说「启用行为预测规则」\n\n这样 AI 会自动记录你的工作流程，学习你的习惯，并在适当时机提供智能建议。', 
                    en: '✅ Behavior Prediction Skill V2 installed!\n\n👉 Next step: Say "enable behavior prediction rule"\n\nThis will let AI record your workflow, learn your habits, and provide smart suggestions at appropriate times.' 
                }
            },
            {
                title: { zh: '更新 Behavior Prediction Skill', en: 'Update Behavior Prediction Skill' },
                userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 更新 behavior-prediction skill', en: 'Please update behavior-prediction skill from https://github.com/shetengteng/skillix-hub' },
                aiResponse: {
                    zh: '正在更新 Behavior Prediction Skill...\n\n1. 拉取最新代码\n2. 更新 skill 代码\n3. 保留已有行为数据和用户画像\n\n✅ Behavior Prediction Skill 已更新到最新版本！\n\n已有的行为模式、用户画像数据完整保留。',
                    en: 'Updating Behavior Prediction Skill...\n\n1. Pull latest code\n2. Update skill code\n3. Preserve existing behavior data and user profile\n\n✅ Behavior Prediction Skill updated to latest version!\n\nExisting behavior patterns and user profile data fully preserved.'
                }
            },
            {
                title: { zh: '启用行为预测规则', en: 'Enable Behavior Prediction Rule' },
                userInput: { zh: '启用行为预测规则', en: 'Enable behavior prediction rule' },
                aiResponse: { 
                    zh: '✅ 行为预测规则已启用！\n\n📄 规则文件: ~/.cursor/rules/behavior-prediction.mdc\n\n规则已生效，AI 会自动：\n• 会话开始时加载你的行为模式\n• 会话结束时记录并学习你的工作流程\n• 在适当时机提供智能预测建议\n\n你可以说"禁用行为预测规则"来关闭此功能。', 
                    en: '✅ Behavior prediction rule enabled!\n\n📄 Rule file: ~/.cursor/rules/behavior-prediction.mdc\n\nRule is now active, AI will automatically:\n• Load your behavior patterns at session start\n• Record and learn your workflow at session end\n• Provide smart predictions at appropriate times\n\nYou can say "disable behavior prediction rule" to turn this off.' 
                }
            },
            {
                title: { zh: '会话结束时的自动记录', en: 'Auto Recording at Session End' },
                userInput: { zh: '谢谢，今天就到这里', en: 'Thanks, that\'s all for today' },
                aiResponse: { 
                    zh: '好的！已记录本次会话。\n\n📝 会话摘要：\n- 主题: API 用户模块开发\n- 工作流程: design → implement → test → commit\n- 技术: Python, FastAPI, pytest\n\n基于你的习惯，下次你可能想要：\n→ 继续完善文档 (60%)\n\n再见！', 
                    en: 'OK! Session recorded.\n\n📝 Session Summary:\n- Topic: API User Module Development\n- Workflow: design → implement → test → commit\n- Tech: Python, FastAPI, pytest\n\nBased on your habits, next time you might want to:\n→ Continue improving docs (60%)\n\nGoodbye!' 
                }
            },
            {
                title: { zh: '智能预测下一步', en: 'Smart Next Step Prediction' },
                userInput: { zh: '（用户刚完成了代码实现）', en: '(User just completed code implementation)' },
                aiResponse: { 
                    zh: '✨ 基于你的习惯，你可能想要：\n→ 运行测试 (置信度: 85%)\n\n要执行 pytest 吗？', 
                    en: '✨ Based on your habits, you might want to:\n→ Run tests (Confidence: 85%)\n\nWould you like to run pytest?' 
                }
            },
            {
                title: { zh: '查看行为模式', en: 'View Behavior Patterns' },
                userInput: { zh: '查看我的行为模式', en: 'View my behavior patterns' },
                aiResponse: { 
                    zh: '📊 你的行为模式分析\n\n**基本统计：**\n- 活跃天数: 15 天\n- 总会话数: 42 次\n- 平均会话时长: 25 分钟\n\n**常见工作流程：**\n1. design → implement (78%)\n2. implement → test (85%)\n3. test → commit (65%)\n\n**技术偏好：**\n- 语言: Python, TypeScript\n- 框架: FastAPI, Vue\n- 工具: pytest, ruff\n\n**工作风格：**\n- 测试驱动 (35%)\n- 注重规划 (25%)', 
                    en: '📊 Your Behavior Pattern Analysis\n\n**Basic Stats:**\n- Active days: 15\n- Total sessions: 42\n- Avg session duration: 25 min\n\n**Common Workflows:**\n1. design → implement (78%)\n2. implement → test (85%)\n3. test → commit (65%)\n\n**Tech Preferences:**\n- Languages: Python, TypeScript\n- Frameworks: FastAPI, Vue\n- Tools: pytest, ruff\n\n**Work Style:**\n- Test-driven (35%)\n- Planning-focused (25%)' 
                }
            },
            {
                title: { zh: '查看用户画像', en: 'View User Profile' },
                userInput: { zh: '查看用户画像', en: 'View user profile' },
                aiResponse: { 
                    zh: '👤 用户画像\n\n**统计数据：**\n- 总会话数: 50\n- 活跃天数: 30\n\n**偏好设置：**\n- 常见阶段: implement, test, commit\n- 常用技术: python, fastapi, pytest\n\n**工作风格：**\n- 规划倾向: 0.3\n- 测试驱动: 0.6\n- 文档关注: 0.2', 
                    en: '👤 User Profile\n\n**Statistics:**\n- Total sessions: 50\n- Active days: 30\n\n**Preferences:**\n- Common stages: implement, test, commit\n- Common tech: python, fastapi, pytest\n\n**Work Style:**\n- Planning tendency: 0.3\n- Test-driven: 0.6\n- Documentation focus: 0.2' 
                }
            },
            {
                title: { zh: '预测下一步', en: 'Predict Next Step' },
                userInput: { zh: '预测下一步', en: 'Predict next step' },
                aiResponse: { 
                    zh: '基于当前上下文预测：\n\n你刚刚完成了 **实现** 阶段。\n\n**最可能的下一步：**\n✅ 运行测试 (置信度: 85%)\n\n**其他可能：**\n- 继续编辑 (10%)\n- 提交代码 (3%)\n- 查看文档 (2%)\n\n需要我帮你运行测试吗？', 
                    en: 'Prediction Based on Current Context:\n\nYou just completed **implement** stage.\n\n**Most Likely Next Step:**\n✅ Run tests (Confidence: 85%)\n\n**Other Possibilities:**\n- Continue editing (10%)\n- Commit code (3%)\n- View docs (2%)\n\nWould you like me to run the tests?' 
                }
            },
            {
                title: { zh: '禁用行为预测规则', en: 'Disable Behavior Prediction Rule' },
                userInput: { zh: '禁用行为预测规则', en: 'Disable behavior prediction rule' },
                aiResponse: { 
                    zh: '✅ 行为预测规则已禁用！\n\n规则文件已移除，AI 将不再自动记录会话和预测行为。\n\n你可以随时说"启用行为预测规则"重新开启此功能。', 
                    en: '✅ Behavior prediction rule disabled!\n\nRule file removed, AI will no longer auto-record sessions or predict behavior.\n\nYou can say "enable behavior prediction rule" anytime to turn this back on.' 
                }
            }
        ]
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
            { zh: '演化', en: 'Evolution' },
            { zh: '通用', en: 'Universal' }
        ],
        features: [
            { zh: '观察记录', en: 'Observation Recording' },
            { zh: '模式检测', en: 'Pattern Detection' },
            { zh: '本能生成', en: 'Instinct Generation' },
            { zh: '技能演化', en: 'Skill Evolution' },
            { zh: '用户纠正学习', en: 'User Correction Learning' },
            { zh: '错误解决学习', en: 'Error Resolution Learning' }
        ],
        scripts: ['observe.py', 'analyze.py', 'instinct.py', 'setup_rule.py', 'utils.py'],
        version: '1.0',
        author: 'shetengteng',
        repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/continuous-learning',
        useCases: [
            {
                title: { zh: '安装 Continuous Learning Skill', en: 'Install Continuous Learning Skill' },
                userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 安装 continuous-learning skill', en: 'Please install continuous-learning skill from https://github.com/shetengteng/skillix-hub' },
                aiResponse: { 
                    zh: '✅ Continuous Learning Skill 安装成功！\n\n👉 下一步：说「启用持续学习规则」\n\n这样 AI 会自动学习你的工作习惯和偏好，并生成新的技能。', 
                    en: '✅ Continuous Learning Skill installed!\n\n👉 Next step: Say "enable continuous learning rules"\n\nThis will let AI learn your work habits and preferences, and generate new skills.' 
                }
            },
            {
                title: { zh: '更新 Continuous Learning Skill', en: 'Update Continuous Learning Skill' },
                userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 更新 continuous-learning skill', en: 'Please update continuous-learning skill from https://github.com/shetengteng/skillix-hub' },
                aiResponse: {
                    zh: '正在更新 Continuous Learning Skill...\n\n1. 拉取最新代码\n2. 更新 skill 代码\n3. 保留已有本能和演化技能数据\n\n✅ Continuous Learning Skill 已更新到最新版本！\n\n已有的本能、观察记录和演化技能完整保留。',
                    en: 'Updating Continuous Learning Skill...\n\n1. Pull latest code\n2. Update skill code\n3. Preserve existing instincts and evolved skills\n\n✅ Continuous Learning Skill updated to latest version!\n\nExisting instincts, observations and evolved skills fully preserved.'
                }
            },
            {
                title: { zh: '启用持续学习规则', en: 'Enable Continuous Learning Rules' },
                userInput: { zh: '启用持续学习规则', en: 'Enable continuous learning rules' },
                aiResponse: { 
                    zh: '✅ 持续学习规则已启用！\n\n📄 规则文件: ~/.cursor/rules/continuous-learning.mdc\n\n规则已生效，AI 会自动：\n• 记录会话中的关键动作\n• 检测用户纠正和错误解决模式\n• 生成可复用的本能\n• 将相关本能演化为技能\n\n你可以说"禁用持续学习规则"来关闭此功能。', 
                    en: '✅ Continuous learning rules enabled!\n\n📄 Rule file: ~/.cursor/rules/continuous-learning.mdc\n\nRule is now active, AI will automatically:\n• Record key actions during sessions\n• Detect user corrections and error resolution patterns\n• Generate reusable instincts\n• Evolve related instincts into skills\n\nYou can say "disable continuous learning rules" to turn this off.' 
                }
            },
            {
                title: { zh: '查看学习到的知识', en: 'View Learned Knowledge' },
                userInput: { zh: '查看学习到的知识', en: 'View learned knowledge' },
                aiResponse: { 
                    zh: '📚 学习到的知识\n\n**本能统计：**\n- 总数: 12 个\n- 高置信度: 5 个\n\n**高置信度本能：**\n1. prefer-functional (85%)\n   触发: 编写新函数时\n   行为: 使用函数式风格\n\n2. pytest-first (78%)\n   触发: 完成代码实现后\n   行为: 优先运行 pytest\n\n3. api-prefix (72%)\n   触发: 创建 API 端点时\n   行为: 使用 /api/v2 前缀\n\n**演化的技能：**\n- testing-workflow (来自 3 个本能)', 
                    en: '📚 Learned Knowledge\n\n**Instinct Stats:**\n- Total: 12\n- High confidence: 5\n\n**High Confidence Instincts:**\n1. prefer-functional (85%)\n   Trigger: When writing new functions\n   Behavior: Use functional style\n\n2. pytest-first (78%)\n   Trigger: After completing implementation\n   Behavior: Run pytest first\n\n3. api-prefix (72%)\n   Trigger: When creating API endpoints\n   Behavior: Use /api/v2 prefix\n\n**Evolved Skills:**\n- testing-workflow (from 3 instincts)' 
                }
            },
            {
                title: { zh: '用户纠正学习', en: 'User Correction Learning' },
                userInput: { zh: '不要用 class，改成函数', en: 'Don\'t use class, change to functions' },
                aiResponse: { 
                    zh: '好的，我来修改为函数式风格。\n\n（已记录这个偏好，下次我会优先使用函数式风格）\n\n```python\ndef create_user(name: str, email: str) -> dict:\n    return {"name": name, "email": email}\n```', 
                    en: 'OK, I\'ll change to functional style.\n\n(Recorded this preference, I\'ll use functional style next time)\n\n```python\ndef create_user(name: str, email: str) -> dict:\n    return {"name": name, "email": email}\n```' 
                }
            },
            {
                title: { zh: '演化本能为技能', en: 'Evolve Instincts into Skills' },
                userInput: { zh: '演化本能', en: 'Evolve instincts' },
                aiResponse: { 
                    zh: '正在分析本能...\n\n找到可演化的组合：\n- 领域: testing\n- 本能数: 3\n- 平均置信度: 75%\n\n✅ 已创建技能: testing-workflow\n\n📄 技能文件: ~/.cursor/skills/evolved-testing-workflow/SKILL.md\n\n这个技能整合了你的测试相关偏好，包括：\n- 优先使用 pytest\n- 测试文件命名规范\n- 测试覆盖率要求', 
                    en: 'Analyzing instincts...\n\nFound evolvable combination:\n- Domain: testing\n- Instincts: 3\n- Avg confidence: 75%\n\n✅ Created skill: testing-workflow\n\n📄 Skill file: ~/.cursor/skills/evolved-testing-workflow/SKILL.md\n\nThis skill integrates your testing preferences:\n- Prefer pytest\n- Test file naming conventions\n- Test coverage requirements' 
                }
            },
            {
                title: { zh: '删除演化技能', en: 'Delete Evolved Skill' },
                userInput: { zh: '删除技能: testing-workflow', en: 'Delete skill: testing-workflow' },
                aiResponse: { 
                    zh: '正在检查技能类型...\n\n✅ testing-workflow 是演化生成的技能\n\n已删除：\n- 源文件: ~/.cursor/skills/continuous-learning-data/evolved/skills/testing-workflow/\n- 符号链接: ~/.cursor/skills/evolved-testing-workflow/\n- 技能索引已更新\n\n技能已完全删除。', 
                    en: 'Checking skill type...\n\n✅ testing-workflow is an evolved skill\n\nDeleted:\n- Source: ~/.cursor/skills/continuous-learning-data/evolved/skills/testing-workflow/\n- Symlink: ~/.cursor/skills/evolved-testing-workflow/\n- Skill index updated\n\nSkill completely deleted.' 
                }
            }
        ]
    },
    {
        id: 'uniapp-mp-generator',
        name: 'uniapp-mp-generator',
        icon: 'folder',
        description: {
            zh: '基于 uni-app 项目规范的小程序代码生成器，根据需求文档自动生成 Vue3 页面、API、Store 等代码',
            en: 'uni-app mini-program code generator based on project standards, auto-generate Vue3 pages, API, Store code from requirements'
        },
        tags: [
            { zh: '代码生成', en: 'Code Gen' },
            { zh: 'uni-app', en: 'uni-app' },
            { zh: '小程序', en: 'Mini Program' },
            { zh: 'Vue3', en: 'Vue3' }
        ],
        features: [
            { zh: 'Vue3 页面生成', en: 'Vue3 Page Generation' },
            { zh: 'API 文件生成', en: 'API File Generation' },
            { zh: 'Store 生成', en: 'Store Generation' },
            { zh: 'Schema 定义', en: 'Schema Definition' },
            { zh: '组件生成', en: 'Component Generation' },
            { zh: '路由配置', en: 'Route Configuration' }
        ],
        scripts: [],
        version: '1.0',
        author: 'shetengteng',
        repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/uniapp-mp-generator',
        useCases: [
            {
                title: { zh: '安装 uni-app 代码生成器', en: 'Install uni-app Code Generator' },
                userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 安装 uniapp-mp-generator skill', en: 'Please install uniapp-mp-generator skill from https://github.com/shetengteng/skillix-hub' },
                aiResponse: { 
                    zh: '✅ uni-app 小程序代码生成器安装成功！\n\n这个 Skill 可以：\n• 根据需求文档生成 Vue3 页面\n• 自动创建 API 接口文件\n• 生成 Pinia Store\n• 创建数据库 Schema\n\n使用方式：提供需求文档，我会自动生成符合规范的代码。', 
                    en: '✅ uni-app Mini Program Code Generator installed!\n\nThis Skill can:\n• Generate Vue3 pages from requirements\n• Auto-create API interface files\n• Generate Pinia Store\n• Create database Schema\n\nUsage: Provide requirements doc, I\'ll auto-generate standard-compliant code.' 
                }
            },
            {
                title: { zh: '更新 uni-app 代码生成器', en: 'Update uni-app Code Generator' },
                userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 更新 uniapp-mp-generator skill', en: 'Please update uniapp-mp-generator skill from https://github.com/shetengteng/skillix-hub' },
                aiResponse: {
                    zh: '正在更新 uni-app 代码生成器...\n\n1. 拉取最新代码\n2. 更新 SKILL.md 和模板文件\n\n✅ uni-app 代码生成器已更新到最新版本！\n\n新版本可能包含更多页面模板和组件支持。',
                    en: 'Updating uni-app Code Generator...\n\n1. Pull latest code\n2. Update SKILL.md and template files\n\n✅ uni-app Code Generator updated to latest version!\n\nNew version may include more page templates and component support.'
                }
            },
            {
                title: { zh: '生成课程管理模块', en: 'Generate Course Management Module' },
                userInput: { zh: '帮我生成课程管理模块，包含课程列表、详情、新增页面', en: 'Help me generate course management module with list, detail, and add pages' },
                aiResponse: { 
                    zh: '好的，我来为你生成课程管理模块。\n\n📁 将创建以下文件：\n\npages/course/\n├── api/\n│   ├── getCourseList.js\n│   ├── getCourseDetail.js\n│   ├── createCourse.js\n│   ├── updateCourse.js\n│   └── deleteCourse.js\n├── components/\n│   └── CourseCard.vue\n├── index.vue\n└── sub/\n    ├── detail/index.vue\n    └── add/index.vue\n\n正在生成代码...', 
                    en: 'OK, I\'ll generate the course management module for you.\n\n📁 Files to be created:\n\npages/course/\n├── api/\n│   ├── getCourseList.js\n│   ├── getCourseDetail.js\n│   ├── createCourse.js\n│   ├── updateCourse.js\n│   └── deleteCourse.js\n├── components/\n│   └── CourseCard.vue\n├── index.vue\n└── sub/\n    ├── detail/index.vue\n    └── add/index.vue\n\nGenerating code...' 
                }
            },
            {
                title: { zh: '根据需求文档生成代码', en: 'Generate Code from Requirements' },
                userInput: { zh: '根据这个需求文档生成代码：\n# 学生管理\n## 数据字段\n- name: 姓名\n- phone: 电话\n- status: 状态', en: 'Generate code from this requirements doc:\n# Student Management\n## Data Fields\n- name: Name\n- phone: Phone\n- status: Status' },
                aiResponse: { 
                    zh: '分析需求文档完成！\n\n📋 模块信息：\n- 模块名: Student (学生)\n- 字段: name, phone, status\n\n正在生成：\n1. ✅ Schema 定义 (COLLECTIONS.STUDENTS)\n2. ✅ API 文件 (5 个 CRUD 接口)\n3. ✅ 列表页 (pages/student/index.vue)\n4. ✅ 详情页 (pages/student/sub/detail/index.vue)\n5. ✅ 表单页 (pages/student/sub/add/index.vue)\n6. ✅ 卡片组件 (StudentCard.vue)\n\n代码已生成完成！', 
                    en: 'Requirements analysis complete!\n\n📋 Module Info:\n- Module: Student\n- Fields: name, phone, status\n\nGenerating:\n1. ✅ Schema definition (COLLECTIONS.STUDENTS)\n2. ✅ API files (5 CRUD endpoints)\n3. ✅ List page (pages/student/index.vue)\n4. ✅ Detail page (pages/student/sub/detail/index.vue)\n5. ✅ Form page (pages/student/sub/add/index.vue)\n6. ✅ Card component (StudentCard.vue)\n\nCode generation complete!' 
                }
            }
        ]
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
        repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/swagger-api-reader',
        useCases: [
            {
                title: { zh: '安装 Swagger API Reader', en: 'Install Swagger API Reader' },
                userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 安装 swagger-api-reader skill', en: 'Please install swagger-api-reader skill from https://github.com/shetengteng/skillix-hub' },
                aiResponse: { 
                    zh: '正在安装 Swagger API Reader...\n\n1. 克隆仓库\n2. 复制 skills/swagger-api-reader 到 ~/.cursor/skills/\n3. 安装依赖: pip install -r requirements.txt\n\n✅ 安装完成！\n\n你可以说"读取 API 文档"来开始使用。', 
                    en: 'Installing Swagger API Reader...\n\n1. Clone repository\n2. Copy skills/swagger-api-reader to ~/.cursor/skills/\n3. Install deps: pip install -r requirements.txt\n\n✅ Installation complete!\n\nYou can say "read API docs" to start using.' 
                }
            },
            {
                title: { zh: '更新 Swagger API Reader', en: 'Update Swagger API Reader' },
                userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 更新 swagger-api-reader skill', en: 'Please update swagger-api-reader skill from https://github.com/shetengteng/skillix-hub' },
                aiResponse: {
                    zh: '正在更新 Swagger API Reader...\n\n1. 拉取最新代码\n2. 更新 skill 代码和脚本\n3. 更新依赖\n\n✅ Swagger API Reader 已更新到最新版本！\n\n已有的 API 缓存数据完整保留。',
                    en: 'Updating Swagger API Reader...\n\n1. Pull latest code\n2. Update skill code and scripts\n3. Update dependencies\n\n✅ Swagger API Reader updated to latest version!\n\nExisting API cache data fully preserved.'
                }
            },
            {
                title: { zh: '读取 API 文档', en: 'Read API Documentation' },
                userInput: { zh: '帮我读取 https://api.example.com/swagger.json 的 API 文档', en: 'Help me read the API docs from https://api.example.com/swagger.json' },
                aiResponse: { 
                    zh: '正在读取 Swagger 文档...\n\n✅ 读取成功！\n\n**API 概览：**\n- 基础路径: /api/v1\n- 端点数量: 24\n- 认证方式: Bearer Token\n\n**主要模块：**\n- /users (5 个端点)\n- /products (8 个端点)\n- /orders (6 个端点)\n- /auth (5 个端点)\n\n需要查看哪个模块的详细信息？', 
                    en: 'Reading Swagger documentation...\n\n✅ Read successful!\n\n**API Overview:**\n- Base path: /api/v1\n- Endpoints: 24\n- Auth: Bearer Token\n\n**Main Modules:**\n- /users (5 endpoints)\n- /products (8 endpoints)\n- /orders (6 endpoints)\n- /auth (5 endpoints)\n\nWhich module details would you like to see?' 
                }
            },
            {
                title: { zh: '生成 API 文档', en: 'Generate API Documentation' },
                userInput: { zh: '生成 users 模块的 API 文档', en: 'Generate API docs for users module' },
                aiResponse: { 
                    zh: 'Users 模块 API 文档\n\n**GET /users**\n获取用户列表\n- 参数: page, limit, search\n- 响应: UserList\n\n**POST /users**\n创建新用户\n- 请求体: CreateUserRequest\n- 响应: User\n\n**GET /users/{id}**\n获取用户详情\n- 参数: id (path)\n- 响应: User\n\n...\n\n文档已生成到 docs/api/users.md', 
                    en: 'Users Module API Documentation\n\n**GET /users**\nGet user list\n- Params: page, limit, search\n- Response: UserList\n\n**POST /users**\nCreate new user\n- Body: CreateUserRequest\n- Response: User\n\n**GET /users/{id}**\nGet user details\n- Params: id (path)\n- Response: User\n\n...\n\nDocs generated to docs/api/users.md' 
                }
            },
            {
                title: { zh: '需要认证的 API', en: 'API Requiring Authentication' },
                userInput: { zh: '读取需要登录的内部 API 文档', en: 'Read internal API docs that require login' },
                aiResponse: { 
                    zh: '检测到该 API 需要认证。\n\n正在启动浏览器认证...\n\n请在打开的浏览器窗口中完成登录，然后我会自动获取认证信息并读取 API 文档。\n\n（浏览器窗口已打开，等待登录...）\n\n✅ 认证成功！正在读取 API 文档...', 
                    en: 'Detected that this API requires authentication.\n\nStarting browser authentication...\n\nPlease complete login in the opened browser window, then I\'ll automatically get auth info and read the API docs.\n\n(Browser window opened, waiting for login...)\n\n✅ Authentication successful! Reading API docs...' 
                }
            }
        ]
    }
];

// 图标 SVG 路径映射
const ICON_PATHS = {
    lightbulb: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    document: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    chart: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    brain: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    plus: 'M12 6v6m0 0v6m0-6h6m-6 0H6',
    globe: 'M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    folder: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z',
    info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    code: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4'
};

// 导出供 Vue 使用
if (typeof window !== 'undefined') {
    window.SKILLS_DATA = SKILLS_DATA;
    window.ICON_PATHS = ICON_PATHS;
}
