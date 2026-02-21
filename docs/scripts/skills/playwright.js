/**
 * Skillix Hub - playwright Skill Data
 */
window.SKILL_DATA_PLAYWRIGHT = {
    id: 'playwright',
    name: 'playwright',
    icon: 'globe',
    description: {
        zh: '浏览器自动化工具，通过 48 个 CLI 命令控制真实浏览器，支持导航、快照、点击、表单填写、截图、Cookie/存储管理、网络拦截等，复刻自 Playwright MCP',
        en: 'Browser automation via 48 CLI commands controlling a real browser. Navigate, snapshot, click, fill forms, screenshot, manage cookies/storage, intercept network, and more. Replicated from Playwright MCP'
    },
    tags: [
        { zh: '浏览器', en: 'Browser' },
        { zh: '自动化', en: 'Automation' },
        { zh: 'Playwright', en: 'Playwright' },
        { zh: '测试', en: 'Testing' }
    ],
    features: [
        { zh: '22 个 MCP Tools 直接调用', en: '22 MCP Tools Direct Call' },
        { zh: '48 个 CLI 浏览器工具', en: '48 CLI Browser Tools' },
        { zh: '无障碍快照 + ref 系统', en: 'Accessibility Snapshot + Ref System' },
        { zh: '浏览器跨调用持久化', en: 'Browser Persistence Across Calls' },
        { zh: '网络请求拦截', en: 'Network Request Interception' },
        { zh: 'Cookie/Storage 管理', en: 'Cookie/Storage Management' },
        { zh: '截图与 PDF 导出', en: 'Screenshot & PDF Export' },
        { zh: '元素验证', en: 'Element Verification' }
    ],
    scripts: ['tool.js'],
    version: '1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/playwright',
    useCases: [
        {
            title: { zh: '安装 Playwright Skill', en: 'Install Playwright Skill' },
            userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 安装 playwright skill', en: 'Please install playwright skill from https://github.com/shetengteng/skillix-hub' },
            aiResponse: {
                zh: '正在安装 Playwright Skill...\n\n1. 克隆仓库\n2. 复制 skills/playwright 到项目\n3. 运行 npm install && npx playwright install chromium\n\n✅ Playwright Skill 安装成功！\n\n包含 48 个浏览器自动化工具，通过 CLI 调用：\nnode skills/playwright/tool.js <命令> \'<JSON参数>\'',
                en: 'Installing Playwright Skill...\n\n1. Clone repository\n2. Copy skills/playwright to project\n3. Run npm install && npx playwright install chromium\n\n✅ Playwright Skill installed!\n\nIncludes 48 browser automation tools via CLI:\nnode skills/playwright/tool.js <command> \'<json_params>\''
            }
        },
        {
            title: { zh: '更新 Playwright Skill', en: 'Update Playwright Skill' },
            userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 更新 playwright skill', en: 'Please update playwright skill from https://github.com/shetengteng/skillix-hub' },
            aiResponse: {
                zh: '正在更新 Playwright Skill...\n\n1. 拉取最新代码\n2. 更新 skill 文件（SKILL.md、tool.js 等）\n3. 运行 npm install 更新依赖\n\n✅ Playwright Skill 已更新到最新版本！\n\n支持 22 个 MCP Tools 直接调用 + 48 个 CLI 工具。',
                en: 'Updating Playwright Skill...\n\n1. Pull latest code\n2. Update skill files (SKILL.md, tool.js, etc.)\n3. Run npm install to update dependencies\n\n✅ Playwright Skill updated to latest version!\n\nSupports 22 MCP Tools direct call + 48 CLI tools.'
            }
        },
        {
            title: { zh: '导航到网页', en: 'Navigate to Web Page' },
            userInput: { zh: '打开 https://example.com', en: 'Open https://example.com' },
            aiResponse: {
                zh: '正在导航...\n\n✅ 页面已加载\n\n快照：\n- heading "Example Domain"\n- paragraph: This domain is for use in documentation...\n- link "Learn more" [ref=e6]\n\n页面包含一个标题和一个链接。需要我点击链接或执行其他操作吗？',
                en: 'Navigating...\n\n✅ Page loaded\n\nSnapshot:\n- heading "Example Domain"\n- paragraph: This domain is for use in documentation...\n- link "Learn more" [ref=e6]\n\nPage contains a heading and a link. Want me to click the link or perform other actions?'
            }
        },
        {
            title: { zh: '点击元素', en: 'Click Element' },
            userInput: { zh: '点击 Learn more 链接', en: 'Click the Learn more link' },
            aiResponse: {
                zh: '已点击 "Learn more" 链接\n\n页面已导航到 IANA 的示例域名说明页面。\n\n新页面快照：\n- heading "Example Domains"\n- link "RFC 2606" [ref=e22]\n- link "RFC 6761" [ref=e23]\n...\n\n生成的代码：\nawait page.getByRole(\'link\', { name: \'Learn more\' }).click();',
                en: 'Clicked "Learn more" link\n\nPage navigated to IANA example domains page.\n\nNew page snapshot:\n- heading "Example Domains"\n- link "RFC 2606" [ref=e22]\n- link "RFC 6761" [ref=e23]\n...\n\nGenerated code:\nawait page.getByRole(\'link\', { name: \'Learn more\' }).click();'
            }
        },
        {
            title: { zh: '截图', en: 'Take Screenshot' },
            userInput: { zh: '截个图', en: 'Take a screenshot' },
            aiResponse: {
                zh: '✅ 截图已保存\n\n[Screenshot](/tmp/playwright-skill-output/page-2026-02-20T12-00-00.png)\n\n截图包含当前页面的完整视图。',
                en: '✅ Screenshot saved\n\n[Screenshot](/tmp/playwright-skill-output/page-2026-02-20T12-00-00.png)\n\nScreenshot contains the full view of the current page.'
            }
        },
        {
            title: { zh: '管理 Cookie', en: 'Manage Cookies' },
            userInput: { zh: '查看当前页面的 Cookie', en: 'Show cookies for current page' },
            aiResponse: {
                zh: '当前页面 Cookie 列表：\n\nsession_id=abc123 (domain: example.com, path: /, httpOnly: true)\ntheme=dark (domain: example.com, path: /)\n\n共 2 个 Cookie。需要设置、删除或清除 Cookie 吗？',
                en: 'Current page cookies:\n\nsession_id=abc123 (domain: example.com, path: /, httpOnly: true)\ntheme=dark (domain: example.com, path: /)\n\n2 cookies total. Want to set, delete, or clear cookies?'
            }
        },
        {
            title: { zh: '执行 JavaScript', en: 'Execute JavaScript' },
            userInput: { zh: '获取页面标题', en: 'Get the page title' },
            aiResponse: {
                zh: '执行 JavaScript: () => document.title\n\n结果: "Example Domain"\n\n生成的代码：\nawait page.evaluate(() => document.title);',
                en: 'Executing JavaScript: () => document.title\n\nResult: "Example Domain"\n\nGenerated code:\nawait page.evaluate(() => document.title);'
            }
        }
    ]
};
