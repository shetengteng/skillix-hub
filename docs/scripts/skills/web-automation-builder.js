/**
 * Skillix Hub - Web Automation Builder Skill Data
 */
window.SKILL_DATA_WEB_AUTOMATION_BUILDER = {
    id: 'web-automation-builder',
    name: 'web-automation-builder',
    icon: 'code',
    description: {
        zh: '录制浏览器操作序列，保存为可重放的参数化工作流，支持生成独立 Skill 和导出 Playwright 脚本',
        en: 'Record browser action sequences as replayable parameterized workflows, generate standalone Skills or export Playwright scripts'
    },
    tags: [
        { zh: '录制', en: 'Recording' },
        { zh: '自动化', en: 'Automation' },
        { zh: '工作流', en: 'Workflow' },
        { zh: '参数化', en: 'Parameterized' },
        { zh: 'Playwright', en: 'Playwright' }
    ],
    dependencies: [
        { zh: 'Playwright Skill — 浏览器自动化引擎（必需）', en: 'Playwright Skill — browser automation engine (required)' }
    ],
    features: [
        { zh: '操作录制 — 通过 exec 代理 Playwright 命令，自动记录操作序列', en: 'Action recording — proxy Playwright commands via exec, auto-record action sequences' },
        { zh: '参数化重放 — 支持 {{param}} 模板变量，相同流程不同输入', en: 'Parameterized replay — {{param}} template variables, same flow with different inputs' },
        { zh: '生成独立 Skill — 将工作流转为完整 Skill 目录（SKILL.md + tool.js）', en: 'Generate standalone Skill — convert workflow to full Skill directory (SKILL.md + tool.js)' },
        { zh: '导出 Playwright 脚本 — 生成标准 JS 自动化脚本', en: 'Export Playwright script — generate standard JS automation script' },
        { zh: '参数化分析 — 自动识别可变输入，输出参数化建议', en: 'Parameter analysis — auto-detect variable inputs, output parameterization suggestions' },
        { zh: '一键安装/更新 — install/update 命令支持自然语言安装', en: 'One-click install/update — install/update commands support natural language installation' }
    ],
    scripts: ['tool.js'],
    version: '1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/web-automation-builder',
    useCases: [
        {
            title: { zh: '录制浏览器操作', en: 'Record browser actions' },
            userInput: { zh: '帮我录制一下登录后台的操作', en: 'Record the login process for the admin panel' },
            aiResponse: { zh: 'Agent 开始录制，通过 exec 代理所有 Playwright 操作，录制完成后保存为工作流', en: 'Agent starts recording, proxies all Playwright operations via exec, saves as workflow when done' }
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
            userInput: { zh: '把这个工作流导出为 JS 脚本', en: 'Export this workflow as a JS script' },
            aiResponse: { zh: 'Agent 调用 export 命令，生成标准 Playwright 自动化脚本，可脱离 Cursor 独立运行', en: 'Agent calls export, generates standard Playwright automation script that runs independently' }
        }
    ]
};
