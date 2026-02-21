/**
 * Skillix Hub - behavior-prediction Skill Data
 */
window.SKILL_DATA_BEHAVIOR_PREDICTION = {
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
};
