/**
 * Skillix Hub - Web Automation Builder Skill Data
 */
window.SKILL_DATA_WEB_AUTOMATION_BUILDER = {
    id: 'web-automation-builder',
    name: 'web-automation-builder',
    icon: 'code',
    description: {
        zh: '被动录制用户浏览器操作（CDP + DOM 事件注入 + 网络监听），生成可重放的参数化工作流，支持生成独立 Skill 和导出 Playwright 脚本',
        en: 'Passively record user browser actions (CDP + DOM event injection + network monitoring), generate replayable parameterized workflows, standalone Skills or Playwright scripts'
    },
    tags: [
        { zh: '被动录制', en: 'Passive Recording' },
        { zh: '自动化', en: 'Automation' },
        { zh: '工作流', en: 'Workflow' },
        { zh: 'CDP', en: 'CDP' },
        { zh: 'Playwright', en: 'Playwright' }
    ],
    dependencies: [
        { zh: 'Playwright Skill — 浏览器启动和操作命令（必需）', en: 'Playwright Skill — browser launch and operation commands (required)' },
        { zh: 'playwright-core — CDP 连接库（npm install）', en: 'playwright-core — CDP connection library (npm install)' }
    ],
    features: [
        { zh: '被动录制 — 用户自由操作浏览器，系统通过 CDP + DOM 事件注入自动记录', en: 'Passive recording — user operates browser freely, system auto-records via CDP + DOM event injection' },
        { zh: 'API 监听 — 通过 CDP Network 域捕获请求入参和响应出参', en: 'API monitoring — capture request/response via CDP Network domain' },
        { zh: '参数化重放 — 支持 {{param}} 模板变量，相同流程不同输入', en: 'Parameterized replay — {{param}} template variables, same flow with different inputs' },
        { zh: '生成独立 Skill — 将工作流转为完整 Skill 目录（SKILL.md + tool.js）', en: 'Generate standalone Skill — convert workflow to full Skill directory (SKILL.md + tool.js)' },
        { zh: '导出 Playwright 脚本 — 生成标准 JS 自动化脚本，参数通过环境变量注入', en: 'Export Playwright script — generate standard JS automation script with env var params' },
        { zh: 'agent-interact 集成 — 录制期间通过 Electron 置顶窗口与用户交互', en: 'agent-interact integration — interact with user via Electron topmost window during recording' }
    ],
    scripts: ['tool.js'],
    version: '2.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/web-automation-builder',
    useCases: [
        {
            title: { zh: '被动录制浏览器操作', en: 'Passively record browser actions' },
            userInput: { zh: '帮我录制一下部署后端代码的操作', en: 'Record the deployment process for backend code' },
            aiResponse: { zh: 'Agent 启动浏览器并注入监听，弹出 wait 弹框。用户自由操作后点击确认，Agent 分析录制数据并保存工作流', en: 'Agent launches browser with listeners, shows wait dialog. User operates freely, clicks confirm when done. Agent analyzes and saves workflow' }
        },
        {
            title: { zh: '重放工作流', en: 'Replay workflow' },
            userInput: { zh: '用新账号重新执行一次登录流程', en: 'Re-run the login flow with a new account' },
            aiResponse: { zh: 'Agent 调用 replay 命令，注入新的用户名和密码参数，自动执行录制的操作序列', en: 'Agent calls replay with new username/password params, auto-executes the recorded action sequence' }
        },
        {
            title: { zh: '生成独立 Skill', en: 'Generate standalone Skill' },
            userInput: { zh: '把这个部署流程生成一个 Skill，以后直接用', en: 'Generate a Skill from this deployment flow for future use' },
            aiResponse: { zh: 'Agent 调用 generate 命令，生成包含 SKILL.md、tool.js、workflow.json 的独立 Skill 目录，安装到全局', en: 'Agent calls generate, creates standalone Skill directory with SKILL.md, tool.js, workflow.json, installs globally' }
        },
        {
            title: { zh: '导出 Playwright 脚本', en: 'Export Playwright script' },
            userInput: { zh: '把这个工作流导出为 JS 脚本，参数用环境变量', en: 'Export this workflow as a JS script with env var params' },
            aiResponse: { zh: 'Agent 导出标准 Playwright 脚本，参数通过环境变量注入：USERNAME=admin PASSWORD=xxx node deploy.js', en: 'Agent exports standard Playwright script with env var params: USERNAME=admin PASSWORD=xxx node deploy.js' }
        }
    ]
};
