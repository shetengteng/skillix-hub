/**
 * Skillix Hub - continuous-learning Skill Data
 */
window.SKILL_DATA_CONTINUOUS_LEARNING = {
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
};
