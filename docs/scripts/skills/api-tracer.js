/**
 * Skillix Hub - api-tracer Skill Data
 */
window.SKILL_DATA_API_TRACER = {
    id: 'api-tracer',
    name: 'api-tracer',
    icon: 'globe',
    description: {
        zh: '录制和分析浏览器网络请求，通过 CDP 捕获完整 API 信息（URL、headers、cookie、请求/响应体），生成分析报告用于自动化',
        en: 'Record and analyze browser network requests via CDP, capture full API info (URL, headers, cookies, request/response body), generate reports for automation'
    },
    tags: [
        { zh: '网络', en: 'Network' },
        { zh: 'API', en: 'API' },
        { zh: '录制', en: 'Recording' },
        { zh: '分析', en: 'Analysis' }
    ],
    features: [
        { zh: 'CDP 网络请求捕获', en: 'CDP Network Capture' },
        { zh: '完整请求/响应数据', en: 'Full Request/Response Data' },
        { zh: 'API 端点分析', en: 'API Endpoint Analysis' },
        { zh: 'Schema 自动推断', en: 'Auto Schema Inference' },
        { zh: '认证方式识别', en: 'Auth Detection' },
        { zh: 'Markdown/curl 报告', en: 'Markdown/curl Reports' },
        { zh: '后台 daemon 录制', en: 'Background Daemon Recording' },
        { zh: '与 Playwright Skill 协同', en: 'Playwright Skill Integration' }
    ],
    scripts: ['tool.js'],
    version: '1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/api-tracer',
    useCases: [
        {
            title: { zh: '安装 API Tracer', en: 'Install API Tracer' },
            userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 安装 api-tracer skill', en: 'Please install api-tracer skill from https://github.com/shetengteng/skillix-hub' },
            aiResponse: {
                zh: '正在安装 API Tracer Skill...\n\n1. 克隆仓库\n2. 复制 skills/api-tracer 到项目\n3. 运行 npm install\n\n✅ API Tracer Skill 安装成功！\n\n前置条件：需要 Playwright Skill 已启动浏览器。\n\n使用方式：\nnode skills/api-tracer/tool.js <命令> \'<JSON参数>\'',
                en: 'Installing API Tracer Skill...\n\n1. Clone repository\n2. Copy skills/api-tracer to project\n3. Run npm install\n\n✅ API Tracer Skill installed!\n\nPrerequisite: Playwright Skill browser must be running.\n\nUsage:\nnode skills/api-tracer/tool.js <command> \'<json_params>\''
            }
        },
        {
            title: { zh: '启动录制', en: 'Start Recording' },
            userInput: { zh: '开始录制网络请求，只录制 API 请求', en: 'Start recording network requests, only API requests' },
            aiResponse: {
                zh: '正在启动 API 录制...\n\n✅ 录制已启动\n\n会话名称: api-session-20260221\n过滤规则: api/\n\n现在你可以操作页面，所有匹配的网络请求会被自动捕获。\n\n说「停止录制」来结束。',
                en: 'Starting API recording...\n\n✅ Recording started\n\nSession: api-session-20260221\nFilter: api/\n\nNow operate the page, all matching network requests will be captured.\n\nSay "stop recording" to end.'
            }
        },
        {
            title: { zh: '生成分析报告', en: 'Generate Analysis Report' },
            userInput: { zh: '生成 API 报告', en: 'Generate API report' },
            aiResponse: {
                zh: '# API Trace Report: api-session-20260221\n\n## 认证\n- 类型: Bearer Token\n- Header: Authorization\n\n## API 端点\n\n### POST /api/login\n- 请求体: {"username": "string", "password": "string"}\n- 响应: {"token": "string", "user": {...}}\n\n### GET /api/users\n- Headers: Authorization: Bearer xxx\n- 响应: {"data": [{...}], "total": "number"}\n\n共发现 5 个 API 端点，8 次请求。',
                en: '# API Trace Report: api-session-20260221\n\n## Authentication\n- Type: Bearer Token\n- Header: Authorization\n\n## API Endpoints\n\n### POST /api/login\n- Body: {"username": "string", "password": "string"}\n- Response: {"token": "string", "user": {...}}\n\n### GET /api/users\n- Headers: Authorization: Bearer xxx\n- Response: {"data": [{...}], "total": "number"}\n\n5 API endpoints found, 8 requests total.'
            }
        },
        {
            title: { zh: '导出为 curl', en: 'Export as curl' },
            userInput: { zh: '导出为 curl 命令', en: 'Export as curl commands' },
            aiResponse: {
                zh: 'curl 命令导出：\n\ncurl -X POST \\\n  -H \'content-type: application/json\' \\\n  -d \'{"username":"test","password":"pass"}\' \\\n  \'https://api.example.com/login\'\n\ncurl -X GET \\\n  -H \'authorization: Bearer token123\' \\\n  \'https://api.example.com/users\'\n\n共导出 5 个端点的 curl 命令。',
                en: 'curl commands exported:\n\ncurl -X POST \\\n  -H \'content-type: application/json\' \\\n  -d \'{"username":"test","password":"pass"}\' \\\n  \'https://api.example.com/login\'\n\ncurl -X GET \\\n  -H \'authorization: Bearer token123\' \\\n  \'https://api.example.com/users\'\n\n5 endpoint curl commands exported.'
            }
        }
    ]
};
