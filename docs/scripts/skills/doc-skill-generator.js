/**
 * Skillix Hub - doc-skill-generator Skill Data
 */
window.SKILL_DATA_DOC_SKILL_GENERATOR = {
    id: 'doc-skill-generator',
    name: 'doc-skill-generator',
    icon: 'document',
    description: {
        zh: '从文档（网页、PDF、本地文件）中提取内容，自动生成 Cursor Skill。支持 Playwright BFS 深度采集 SPA 页面',
        en: 'Extract content from docs (web, PDF, local files) and auto-generate Cursor Skills. Supports Playwright BFS deep crawling for SPA pages'
    },
    tags: [
        { zh: '文档采集', en: 'Doc Crawling' },
        { zh: 'Skill 生成', en: 'Skill Generation' },
        { zh: 'SPA 支持', en: 'SPA Support' },
        { zh: 'Playwright', en: 'Playwright' }
    ],
    features: [
        { zh: 'Playwright BFS 深度采集网页', en: 'Playwright BFS Deep Web Crawling' },
        { zh: '支持 SPA/Vue/React 页面', en: 'SPA/Vue/React Page Support' },
        { zh: 'PDF 文件解析', en: 'PDF File Parsing' },
        { zh: '两阶段生成：暂存 + 安装', en: 'Two-Phase Generation: Staging + Install' },
        { zh: 'LLM 辅助创建 SKILL.md', en: 'LLM-Assisted SKILL.md Creation' },
        { zh: '追加采集遗漏页面', en: 'Append Missing Pages' },
        { zh: '已生成 Skill 更新', en: 'Update Generated Skills' }
    ],
    scripts: ['tool.js'],
    version: '1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/doc-skill-generator',
    useCases: [
        {
            title: { zh: '从网页生成 Skill', en: 'Generate Skill from Web' },
            userInput: { zh: '帮我读一下 https://docs.example.com 生成一个 Skill', en: 'Read https://docs.example.com and generate a Skill' },
            aiResponse: {
                zh: '开始采集文档...\n\n1. fetch → Playwright BFS 采集，共 45 页，128 个代码块\n2. show-extract → 展示摘要\n3. analyze → 识别为 API Reference\n4. generate → 生成到暂存目录\n5. 创建 SKILL.md\n6. install-skill → 安装到 ~/.cursor/skills/example-api/',
                en: 'Starting doc crawl...\n\n1. fetch → Playwright BFS crawl, 45 pages, 128 code blocks\n2. show-extract → Display summary\n3. analyze → Identified as API Reference\n4. generate → Output to staging dir\n5. Create SKILL.md\n6. install-skill → Install to ~/.cursor/skills/example-api/'
            }
        },
        {
            title: { zh: '追加采集', en: 'Append Crawl' },
            userInput: { zh: '好像少了高级配置那部分', en: 'Seems like the advanced config section is missing' },
            aiResponse: {
                zh: '追加采集遗漏的页面...\n\n1. append → 追加采集 https://docs.example.com/advanced\n2. show-extract → 更新后的摘要：共 52 页\n3. 用户确认 → generate + install-skill',
                en: 'Appending missing pages...\n\n1. append → Crawl https://docs.example.com/advanced\n2. show-extract → Updated summary: 52 pages\n3. User confirms → generate + install-skill'
            }
        }
    ]
};
