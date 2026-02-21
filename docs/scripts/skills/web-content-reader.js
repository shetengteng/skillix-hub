/**
 * Skillix Hub - web-content-reader Skill Data
 */
window.SKILL_DATA_WEB_CONTENT_READER = {
    id: 'web-content-reader',
    name: 'web-content-reader',
    icon: 'code',
    description: {
        zh: '读取网页内容，支持 SPA 页面自动检测与浏览器渲染降级。当普通 fetch 无法获取 Vue/React 等页面数据时，自动通过浏览器获取完整内容',
        en: 'Read web page content with automatic SPA detection and browser rendering fallback. When fetch fails for Vue/React pages, automatically renders via browser'
    },
    tags: [
        { zh: '网页', en: 'Web' },
        { zh: '内容提取', en: 'Content Extraction' },
        { zh: 'SPA', en: 'SPA' },
        { zh: '浏览器', en: 'Browser' }
    ],
    features: [
        { zh: 'HTTP Fetch + 浏览器双模式', en: 'HTTP Fetch + Browser Dual Mode' },
        { zh: 'SPA 自动检测', en: 'Auto SPA Detection' },
        { zh: '结构化数据提取', en: 'Structured Data Extraction' },
        { zh: 'CSS 选择器定位', en: 'CSS Selector Targeting' },
        { zh: '表格/链接/元信息提取', en: 'Table/Link/Meta Extraction' },
        { zh: '完全独立无依赖', en: 'Fully Independent' },
        { zh: '可选复用 Playwright 浏览器', en: 'Optional Playwright Browser Reuse' }
    ],
    scripts: ['tool.js'],
    version: '1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/web-content-reader',
    useCases: [
        {
            title: { zh: '安装 Web Content Reader', en: 'Install Web Content Reader' },
            userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 安装 web-content-reader skill', en: 'Please install web-content-reader skill from https://github.com/shetengteng/skillix-hub' },
            aiResponse: {
                zh: '正在安装 Web Content Reader Skill...\n\n1. 克隆仓库\n2. 复制 skills/web-content-reader 到项目\n3. 运行 npm install\n\n✅ Web Content Reader 安装成功！\n\n完全独立，不依赖其他 Skill。\n浏览器渲染模式需要系统已安装 Chrome/Chromium。\n\n使用方式：\nnode skills/web-content-reader/tool.js read \'{"url":"https://example.com"}\'',
                en: 'Installing Web Content Reader Skill...\n\n1. Clone repository\n2. Copy skills/web-content-reader to project\n3. Run npm install\n\n✅ Web Content Reader installed!\n\nFully independent, no other Skill dependencies.\nBrowser mode requires Chrome/Chromium installed.\n\nUsage:\nnode skills/web-content-reader/tool.js read \'{"url":"https://example.com"}\''
            }
        },
        {
            title: { zh: '读取普通网页', en: 'Read Static Web Page' },
            userInput: { zh: '帮我读取 https://example.com 的内容', en: 'Help me read the content of https://example.com' },
            aiResponse: {
                zh: '正在读取页面...\n\n✅ 通过 HTTP Fetch 获取成功\n\n标题: Example Domain\n内容: This domain is for use in documentation examples...\n\n链接:\n- Learn more → https://iana.org/domains/example\n\n方式: fetch | 耗时: 0.8s',
                en: 'Reading page...\n\n✅ Fetched via HTTP\n\nTitle: Example Domain\nContent: This domain is for use in documentation examples...\n\nLinks:\n- Learn more → https://iana.org/domains/example\n\nMethod: fetch | Elapsed: 0.8s'
            }
        },
        {
            title: { zh: '读取 SPA 页面', en: 'Read SPA Page' },
            userInput: { zh: '这个页面是 Vue 写的，fetch 读不到数据，帮我用浏览器打开读取', en: 'This page is built with Vue, fetch can\'t get data, please read it via browser' },
            aiResponse: {
                zh: '检测到 SPA 页面，切换到浏览器渲染模式...\n\n✅ 通过浏览器渲染获取成功\n\n标题: Vue 应用\n内容: [完整的渲染后页面内容...]\n\n方式: browser | 耗时: 3.2s',
                en: 'SPA page detected, switching to browser rendering...\n\n✅ Fetched via browser rendering\n\nTitle: Vue App\nContent: [Full rendered page content...]\n\nMethod: browser | Elapsed: 3.2s'
            }
        },
        {
            title: { zh: '提取页面表格数据', en: 'Extract Table Data' },
            userInput: { zh: '提取这个页面的表格数据', en: 'Extract table data from this page' },
            aiResponse: {
                zh: '正在提取页面数据...\n\n✅ 找到 1 个表格\n\n| 姓名 | 年龄 | 城市 |\n|------|------|------|\n| Alice | 30 | 北京 |\n| Bob | 25 | 上海 |\n\n共 2 行数据。',
                en: 'Extracting page data...\n\n✅ Found 1 table\n\n| Name | Age | City |\n|------|-----|------|\n| Alice | 30 | Beijing |\n| Bob | 25 | Shanghai |\n\n2 rows of data.'
            }
        },
        {
            title: { zh: '提取特定区域', en: 'Extract Specific Area' },
            userInput: { zh: '只读取 .main-content 区域的内容', en: 'Only read the .main-content area' },
            aiResponse: {
                zh: '正在提取 .main-content 区域...\n\n✅ 提取成功\n\n[仅包含 .main-content 选择器匹配区域的内容]\n\n方式: fetch | 耗时: 0.6s',
                en: 'Extracting .main-content area...\n\n✅ Extraction successful\n\n[Content from .main-content selector only]\n\nMethod: fetch | Elapsed: 0.6s'
            }
        }
    ]
};
