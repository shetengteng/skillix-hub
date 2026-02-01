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
            zh: '为 AI 助手提供长期记忆能力，支持关键词触发保存、临时记忆、智能汇总，自动记录对话并检索相关历史上下文',
            en: 'Long-term memory for AI assistants with keyword-triggered saving, temp memory, smart summarization, auto-record and retrieve history'
        },
        tags: [
            { zh: '记忆', en: 'Memory' },
            { zh: '上下文', en: 'Context' },
            { zh: '检索', en: 'Retrieval' },
            { zh: '智能保存', en: 'Smart Save' }
        ],
        features: [
            { zh: '关键词触发保存', en: 'Keyword-triggered Save' },
            { zh: '临时记忆机制', en: 'Temp Memory' },
            { zh: '智能汇总', en: 'Smart Summarization' },
            { zh: '搜索记忆', en: 'Search Memory' },
            { zh: '查看记忆', en: 'View Memory' },
            { zh: '导出导入', en: 'Export/Import' },
            { zh: '自动记忆规则', en: 'Auto Memory Rules' }
        ],
        scripts: ['save_memory.py', 'search_memory.py', 'view_memory.py', 'delete_memory.py', 'hook.py', 'summarize.py', 'utils.py'],
        version: '2.0',
        author: 'shetengteng',
        repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/memory',
        useCases: [
            {
                title: { zh: '安装 Memory Skill', en: 'Install Memory Skill' },
                userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 安装 memory skill', en: 'Please install memory skill from https://github.com/shetengteng/skillix-hub' },
                aiResponse: { 
                    zh: '✅ Memory Skill v2.0 安装成功！\n\n👉 下一步：说「启用自动记忆检索」\n\nv2.0 新特性：\n• 关键词触发保存\n• 临时记忆机制\n• 智能汇总', 
                    en: '✅ Memory Skill v2.0 installed!\n\n👉 Next step: Say "enable memory auto retrieve"\n\nv2.0 Features:\n• Keyword-triggered save\n• Temp memory\n• Smart summarization' 
                }
            },
            {
                title: { zh: '关键词自动保存', en: 'Keyword Auto Save' },
                userInput: { zh: '我们决定使用 FastAPI 替换 Flask', en: 'We decided to use FastAPI instead of Flask' },
                aiResponse: { 
                    zh: '好的，我来帮你实现这个迁移。\n\n（已自动保存：检测到关键词"决定"、"使用"）\n\n首先，让我们创建 FastAPI 的基础结构...', 
                    en: 'OK, I\'ll help you with this migration.\n\n(Auto-saved: detected keywords "decided", "use")\n\nFirst, let\'s create the FastAPI base structure...' 
                }
            },
            {
                title: { zh: '查看会话状态', en: 'View Session Status' },
                userInput: { zh: '查看会话状态', en: 'View session status' },
                aiResponse: { 
                    zh: '📊 当前会话状态\n\n状态: 活跃\n开始时间: 10:30:00\n临时记忆数: 3\n\n最近记忆:\n1. 技术选型 - 使用 FastAPI\n2. API 配置 - 前缀 /api/v2\n3. 计划 - 实现认证功能', 
                    en: '📊 Current Session Status\n\nStatus: Active\nStart: 10:30:00\nTemp memories: 3\n\nRecent:\n1. Tech choice - Use FastAPI\n2. API config - prefix /api/v2\n3. Plan - Implement auth' 
                }
            },
            {
                title: { zh: '手动汇总记忆', en: 'Manual Summarize' },
                userInput: { zh: '汇总记忆', en: 'Summarize memories' },
                aiResponse: { 
                    zh: '正在汇总临时记忆...\n\n✅ 汇总完成！\n\n原始记忆数: 5\n合并后: 3\n保存位置: memory-data/daily/2026-02-01.md\n\n已合并相似主题的记忆。', 
                    en: 'Summarizing temp memories...\n\n✅ Summarization complete!\n\nOriginal: 5\nMerged: 3\nSaved to: memory-data/daily/2026-02-01.md\n\nSimilar topics merged.' 
                }
            },
            {
                title: { zh: '继续昨天的工作', en: 'Continue Yesterday\'s Work' },
                userInput: { zh: '继续昨天的 API 重构工作', en: 'Continue yesterday\'s API refactoring work' },
                aiResponse: { 
                    zh: '让我检索一下相关记忆...\n\n找到了！昨天我们讨论了：\n- 使用 FastAPI 替换 Flask\n- RESTful 风格设计\n- 需要添加认证中间件\n\n我们继续从认证中间件开始吧。', 
                    en: 'Let me retrieve relevant memories...\n\nFound it! Yesterday we discussed:\n- Replace Flask with FastAPI\n- RESTful style design\n- Need to add auth middleware\n\nLet\'s continue from the auth middleware.' 
                }
            },
            {
                title: { zh: '清空临时记忆', en: 'Clear Temp Memories' },
                userInput: { zh: '清空临时记忆', en: 'Clear temp memories' },
                aiResponse: { 
                    zh: '✅ 已清空 3 条临时记忆\n\n当前会话的临时记忆已清除，不会被汇总保存。', 
                    en: '✅ Cleared 3 temp memories\n\nCurrent session temp memories cleared, won\'t be summarized.' 
                }
            },
            {
                title: { zh: '清空所有记忆', en: 'Clear All Memories' },
                userInput: { zh: '清空所有记忆', en: 'Clear all memories' },
                aiResponse: { 
                    zh: '⚠️ 确认清空所有记忆？\n\n这将删除：\n- 所有每日记忆文件\n- 所有索引数据\n\n请说"确认清空"来执行此操作。', 
                    en: '⚠️ Confirm clear all memories?\n\nThis will delete:\n- All daily memory files\n- All index data\n\nSay "confirm clear" to proceed.' 
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
