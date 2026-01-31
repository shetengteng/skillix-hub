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
        repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/memory',
        useCases: [
            {
                title: { zh: '继续昨天的工作', en: 'Continue Yesterday\'s Work' },
                userInput: { zh: '继续昨天的 API 重构工作', en: 'Continue yesterday\'s API refactoring work' },
                aiResponse: { 
                    zh: '让我检索一下相关记忆...\n\n找到了！昨天我们讨论了：\n- 使用 FastAPI 替换 Flask\n- RESTful 风格设计\n- 需要添加认证中间件\n\n我们继续从认证中间件开始吧。', 
                    en: 'Let me retrieve relevant memories...\n\nFound it! Yesterday we discussed:\n- Replace Flask with FastAPI\n- RESTful style design\n- Need to add auth middleware\n\nLet\'s continue from the auth middleware.' 
                }
            },
            {
                title: { zh: '保存重要决策', en: 'Save Important Decisions' },
                userInput: { zh: '记住这个：我们决定使用 PostgreSQL 而不是 MySQL', en: 'Remember this: we decided to use PostgreSQL instead of MySQL' },
                aiResponse: { 
                    zh: '已保存记忆！\n\n记忆 ID: 2026-01-31-001\n主题: 数据库选型决策\n关键信息: 使用 PostgreSQL 替代 MySQL\n标签: #database #decision', 
                    en: 'Memory saved!\n\nMemory ID: 2026-01-31-001\nTopic: Database Selection Decision\nKey Info: Use PostgreSQL instead of MySQL\nTags: #database #decision' 
                }
            },
            {
                title: { zh: '查看今日记忆', en: 'View Today\'s Memories' },
                userInput: { zh: '查看今日记忆', en: 'View today\'s memories' },
                aiResponse: { 
                    zh: '今日记忆（共 3 条）：\n\n1. [10:30] API 设计讨论\n   - 使用 FastAPI 框架\n   - RESTful 风格\n\n2. [14:15] 数据库选型\n   - 选择 PostgreSQL\n\n3. [16:45] 部署方案\n   - Docker + K8s', 
                    en: 'Today\'s memories (3 total):\n\n1. [10:30] API Design Discussion\n   - Use FastAPI framework\n   - RESTful style\n\n2. [14:15] Database Selection\n   - Choose PostgreSQL\n\n3. [16:45] Deployment Plan\n   - Docker + K8s' 
                }
            },
            {
                title: { zh: '启用自动记忆', en: 'Enable Auto Memory' },
                userInput: { zh: '启用自动记忆检索', en: 'Enable memory auto retrieve' },
                aiResponse: { 
                    zh: '已启用自动记忆规则！\n\n现在每次对话开始时，我会自动检索相关历史记忆；对话结束时，会自动保存重要内容。\n\n你可以随时说"禁用自动记忆检索"来关闭此功能。', 
                    en: 'Auto memory rules enabled!\n\nNow I will automatically retrieve relevant memories at the start of each conversation and save important content at the end.\n\nYou can say "disable memory auto retrieve" anytime to turn this off.' 
                }
            }
        ]
    },
    {
        id: 'behavior-prediction',
        name: 'behavior-prediction',
        icon: 'chart',
        description: {
            zh: '学习用户行为模式，当用户执行动作 A 后，自动预测并建议下一个可能的动作 B，支持多种 AI 助手',
            en: 'Learn user behavior patterns, predict next actions after action A and provide smart suggestions, supports multiple AI assistants'
        },
        tags: [
            { zh: '预测', en: 'Prediction' },
            { zh: '行为', en: 'Behavior' },
            { zh: '智能', en: 'Smart' },
            { zh: '通用', en: 'Universal' }
        ],
        features: [
            { zh: '行为记录', en: 'Behavior Recording' },
            { zh: '模式学习', en: 'Pattern Learning' },
            { zh: '智能预测', en: 'Smart Prediction' },
            { zh: '统计分析', en: 'Statistics Analysis' },
            { zh: '开放式类型', en: 'Open Types' },
            { zh: '会话管理', en: 'Session Management' }
        ],
        scripts: ['record_action.py', 'get_statistics.py', 'finalize_session.py', 'check_last_session.py', 'utils.py'],
        version: '1.0',
        author: 'shetengteng',
        repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/behavior-prediction',
        useCases: [
            {
                title: { zh: '智能预测下一步', en: 'Smart Next Step Prediction' },
                userInput: { zh: '（用户刚创建了一个新文件 user.py）', en: '(User just created a new file user.py)' },
                aiResponse: { 
                    zh: '💡 预测建议：\n\n根据你的历史行为模式，创建文件后你通常会：\n\n1. **编辑文件** (85% 概率) - 添加初始代码\n2. **运行测试** (10% 概率) - 验证文件创建\n3. **创建相关文件** (5% 概率) - 如 test_user.py\n\n需要我帮你开始编辑 user.py 吗？', 
                    en: '💡 Prediction Suggestion:\n\nBased on your behavior patterns, after creating a file you usually:\n\n1. **Edit file** (85% probability) - Add initial code\n2. **Run tests** (10% probability) - Verify file creation\n3. **Create related files** (5% probability) - Like test_user.py\n\nWould you like me to help you start editing user.py?' 
                }
            },
            {
                title: { zh: '查看行为模式', en: 'View Behavior Patterns' },
                userInput: { zh: '查看我的行为模式', en: 'View my behavior patterns' },
                aiResponse: { 
                    zh: '📊 你的行为模式分析：\n\n**Top 5 常见序列：**\n1. 创建文件 → 编辑文件 (92%)\n2. 编辑文件 → 运行测试 (78%)\n3. 运行测试 → 修复代码 (65%)\n4. 修复代码 → 运行测试 (88%)\n5. 提交代码 → 推送远程 (95%)\n\n**今日统计：**\n- 总动作数: 47\n- 最频繁: 编辑文件 (23次)', 
                    en: '📊 Your Behavior Pattern Analysis:\n\n**Top 5 Common Sequences:**\n1. Create file → Edit file (92%)\n2. Edit file → Run tests (78%)\n3. Run tests → Fix code (65%)\n4. Fix code → Run tests (88%)\n5. Commit code → Push remote (95%)\n\n**Today\'s Stats:**\n- Total actions: 47\n- Most frequent: Edit file (23 times)' 
                }
            },
            {
                title: { zh: '预测下一步', en: 'Predict Next Step' },
                userInput: { zh: '预测下一步', en: 'Predict next step' },
                aiResponse: { 
                    zh: '🔮 基于当前上下文预测：\n\n你刚刚完成了 **编辑文件** 操作。\n\n**最可能的下一步：**\n✅ 运行测试 (置信度: 78%)\n\n**其他可能：**\n- 继续编辑 (15%)\n- 提交代码 (5%)\n- 查看文档 (2%)\n\n需要我帮你运行测试吗？', 
                    en: '🔮 Prediction Based on Current Context:\n\nYou just completed **Edit file** operation.\n\n**Most Likely Next Step:**\n✅ Run tests (Confidence: 78%)\n\n**Other Possibilities:**\n- Continue editing (15%)\n- Commit code (5%)\n- View docs (2%)\n\nWould you like me to run the tests?' 
                }
            },
            {
                title: { zh: '自动学习新模式', en: 'Auto Learn New Patterns' },
                userInput: { zh: '（用户连续执行：创建模型 → 生成迁移 → 运行迁移）', en: '(User executes: Create model → Generate migration → Run migration)' },
                aiResponse: { 
                    zh: '🧠 新模式学习完成！\n\n检测到新的行为序列：\n**创建模型 → 生成迁移 → 运行迁移**\n\n这个模式已被记录。下次你创建模型时，我会建议你生成和运行迁移。\n\n当前置信度: 33% (需要更多样本)\n达到 50% 后将自动建议。', 
                    en: '🧠 New Pattern Learned!\n\nDetected new behavior sequence:\n**Create model → Generate migration → Run migration**\n\nThis pattern has been recorded. Next time you create a model, I\'ll suggest generating and running migrations.\n\nCurrent confidence: 33% (needs more samples)\nWill auto-suggest after reaching 50%.' 
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
                    zh: '📄 Users 模块 API 文档\n\n**GET /users**\n获取用户列表\n- 参数: page, limit, search\n- 响应: UserList\n\n**POST /users**\n创建新用户\n- 请求体: CreateUserRequest\n- 响应: User\n\n**GET /users/{id}**\n获取用户详情\n- 参数: id (path)\n- 响应: User\n\n...\n\n文档已生成到 docs/api/users.md', 
                    en: '📄 Users Module API Documentation\n\n**GET /users**\nGet user list\n- Params: page, limit, search\n- Response: UserList\n\n**POST /users**\nCreate new user\n- Body: CreateUserRequest\n- Response: User\n\n**GET /users/{id}**\nGet user details\n- Params: id (path)\n- Response: User\n\n...\n\nDocs generated to docs/api/users.md' 
                }
            },
            {
                title: { zh: '需要认证的 API', en: 'API Requiring Authentication' },
                userInput: { zh: '读取需要登录的内部 API 文档', en: 'Read internal API docs that require login' },
                aiResponse: { 
                    zh: '检测到该 API 需要认证。\n\n🔐 正在启动浏览器认证...\n\n请在打开的浏览器窗口中完成登录，然后我会自动获取认证信息并读取 API 文档。\n\n（浏览器窗口已打开，等待登录...）\n\n✅ 认证成功！正在读取 API 文档...', 
                    en: 'Detected that this API requires authentication.\n\n🔐 Starting browser authentication...\n\nPlease complete login in the opened browser window, then I\'ll automatically get auth info and read the API docs.\n\n(Browser window opened, waiting for login...)\n\n✅ Authentication successful! Reading API docs...' 
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
