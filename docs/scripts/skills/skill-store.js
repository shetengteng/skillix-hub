/**
 * Skillix Hub - skill-store Skill Data
 */
window.SKILL_DATA_SKILL_STORE = {
    id: 'skill-store',
    name: 'skill-store',
    icon: 'folder',
    description: {
        zh: 'Cursor Skill 包管理器，配置 Git 仓库源、同步索引、自然语言搜索推荐，支持项目级和全局安装与版本更新',
        en: 'Cursor Skill package manager. Configure Git repos, sync indexes, natural language search, project/global install with version updates'
    },
    tags: [
        { zh: '包管理', en: 'Package Manager' },
        { zh: 'Git 仓库', en: 'Git Registry' },
        { zh: '依赖解析', en: 'Dependency Resolution' },
        { zh: '自动更新', en: 'Auto Update' }
    ],
    features: [
        { zh: '配置 Git 仓库作为 Skill 源', en: 'Configure Git Repos as Skill Sources' },
        { zh: '自动同步仓库并构建索引', en: 'Auto Sync Repos and Build Index' },
        { zh: '自然语言搜索可用 Skill', en: 'Natural Language Skill Search' },
        { zh: '项目级和全局安装', en: 'Project and Global Installation' },
        { zh: '依赖解析与循环检测', en: 'Dependency Resolution with Cycle Detection' },
        { zh: '版本检测与更新提示', en: 'Version Detection and Update Prompts' },
        { zh: '会话 Hook 自动检查更新', en: 'Session Hook Auto Update Check' }
    ],
    scripts: ['main.py', 'scripts/registry.py', 'scripts/sync.py', 'scripts/index.py', 'scripts/install.py', 'scripts/status.py', 'scripts/hook.py'],
    version: '1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/skill-store',
    useCases: [
        {
            title: { zh: '搜索并安装 Skill', en: 'Search and Install Skill' },
            userInput: { zh: '我需要一个处理 PDF 的 Skill', en: 'I need a Skill for PDF processing' },
            aiResponse: {
                zh: '搜索可用 Skill...\n\n1. index search → 找到 3 个匹配：pdf-processor、doc-converter、pdf-reader\n2. 推荐 pdf-processor（最匹配）\n3. install → 安装到全局，自动解析依赖\n4. 安装完成，新会话即可使用',
                en: 'Searching available Skills...\n\n1. index search → Found 3 matches: pdf-processor, doc-converter, pdf-reader\n2. Recommend pdf-processor (best match)\n3. install → Global install with auto dependency resolution\n4. Done, available in new sessions'
            }
        },
        {
            title: { zh: '添加仓库源', en: 'Add Registry Source' },
            userInput: { zh: '添加这个仓库 https://github.com/team/skills-repo', en: 'Add this repo https://github.com/team/skills-repo' },
            aiResponse: {
                zh: '添加仓库源...\n\n1. registry add → 注册仓库\n2. sync all → Clone 仓库到本地\n3. index rebuild → 构建索引，发现 8 个新 Skill\n4. 完成！可以搜索和安装了',
                en: 'Adding registry source...\n\n1. registry add → Register repo\n2. sync all → Clone repo locally\n3. index rebuild → Build index, found 8 new Skills\n4. Done! Ready to search and install'
            }
        }
    ]
};
