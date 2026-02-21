/**
 * Skillix Hub - skill-builder Skill Data
 */
window.SKILL_DATA_SKILL_BUILDER = {
    id: 'skill-builder',
    name: 'skill-builder',
    icon: 'folder',
    description: {
        zh: 'skillix-hub 项目标准化 Skill 开发流程指南和脚手架工具，提供 8 阶段完整生命周期和模板自动生成',
        en: 'Standardized Skill development workflow guide and scaffold tool for skillix-hub, with 8-phase lifecycle and template auto-generation'
    },
    tags: [
        { zh: '脚手架', en: 'Scaffold' },
        { zh: '开发流程', en: 'Workflow' },
        { zh: '模板', en: 'Templates' },
        { zh: '规范', en: 'Standards' }
    ],
    features: [
        { zh: '8 阶段开发生命周期', en: '8-Phase Development Lifecycle' },
        { zh: '脚手架自动创建目录', en: 'Scaffold Auto Directory Creation' },
        { zh: '模板文件生成', en: 'Template File Generation' },
        { zh: '设计文档规范', en: 'Design Document Standards' },
        { zh: '测试规范与报告', en: 'Test Standards & Reports' },
        { zh: 'README/docs 同步指南', en: 'README/docs Sync Guide' },
        { zh: '支持 Node.js/Python', en: 'Node.js/Python Support' }
    ],
    scripts: ['scaffold.js'],
    version: '1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/skill-builder',
    useCases: [
        {
            title: { zh: '创建新 Skill', en: 'Create New Skill' },
            userInput: { zh: '帮我创建一个新 skill，叫 data-analyzer', en: 'Help me create a new skill called data-analyzer' },
            aiResponse: {
                zh: '好的，开始创建 data-analyzer Skill。\n\n运行脚手架初始化：\nnode skills/skill-builder/scaffold.js init \'{"name":"data-analyzer","tech":"node"}\'\n\n已创建：\n• skills/data-analyzer/ (SKILL.md, tool.js, package.json, lib/)\n• design/data-analyzer/ (设计文档模板)\n• tests/data-analyzer/ (测试运行器和示例测试)\n\n接下来进入 Phase 2：编写设计文档...',
                en: 'OK, creating data-analyzer Skill.\n\nRunning scaffold init:\nnode skills/skill-builder/scaffold.js init \'{"name":"data-analyzer","tech":"node"}\'\n\nCreated:\n• skills/data-analyzer/ (SKILL.md, tool.js, package.json, lib/)\n• design/data-analyzer/ (design doc template)\n• tests/data-analyzer/ (test runner and example test)\n\nMoving to Phase 2: writing design document...'
            }
        },
        {
            title: { zh: '查看开发流程', en: 'View Development Workflow' },
            userInput: { zh: 'skill 开发流程是什么', en: 'What is the skill development workflow' },
            aiResponse: {
                zh: 'skillix-hub 的 Skill 开发遵循 8 阶段流程：\n\n1. 需求命名 - 确认名称、技术栈、使用场景\n2. 设计文档 - 编写 design/<name>/YYYY-MM-DD-NN-描述.md\n3. 讨论迭代 - Plan 模式确认方案\n4. 代码开发 - 实现 skills/<name>/ 下的源码\n5. 单元测试 - 编写 tests/<name>/src/unit/test_*.js\n6. 测试报告 - 运行测试生成 Markdown 报告\n7. README 同步 - 更新 README.md 和 README_EN.md\n8. docs 同步 - 更新 docs/scripts/skills-data.js',
                en: 'skillix-hub Skill development follows an 8-phase workflow:\n\n1. Requirements Naming - confirm name, tech stack, use cases\n2. Design Document - write design/<name>/YYYY-MM-DD-NN-description.md\n3. Discussion Iteration - confirm plan in Plan mode\n4. Code Development - implement source in skills/<name>/\n5. Unit Testing - write tests/<name>/src/unit/test_*.js\n6. Test Report - run tests and generate Markdown report\n7. README Sync - update README.md and README_EN.md\n8. docs Sync - update docs/scripts/skills-data.js'
            }
        },
        {
            title: { zh: '初始化 Skill 目录', en: 'Initialize Skill Directory' },
            userInput: { zh: '初始化一个 Python 技术栈的 skill 目录', en: 'Initialize a Python skill directory' },
            aiResponse: {
                zh: '好的，请提供 Skill 名称和描述。\n\n示例：\nnode skills/skill-builder/scaffold.js init \'{"name":"my-analyzer","tech":"python","description":"数据分析工具"}\'\n\n将创建：\n• skills/my-analyzer/ (SKILL.md, requirements.txt, lib/)\n• design/my-analyzer/ (设计文档模板)\n• tests/my-analyzer/ (测试运行器和示例测试)',
                en: 'OK, please provide the Skill name and description.\n\nExample:\nnode skills/skill-builder/scaffold.js init \'{"name":"my-analyzer","tech":"python","description":"Data analysis tool"}\'\n\nWill create:\n• skills/my-analyzer/ (SKILL.md, requirements.txt, lib/)\n• design/my-analyzer/ (design doc template)\n• tests/my-analyzer/ (test runner and example test)'
            }
        }
    ]
};
