/**
 * Skillix Hub - swagger-api-reader Skill Data
 */
window.SKILL_DATA_SWAGGER_API_READER = {
    id: 'swagger-api-reader',
    name: 'swagger-api-reader',
    icon: 'document',
    description: {
        zh: '读取并缓存 Swagger/OpenAPI 文档，支持浏览器认证，自动生成结构化 API 文档',
        en: 'Read and cache Swagger/OpenAPI docs with browser auth support, auto-generate structured API documentation'
    },
    tags: [
        { zh: 'API', en: 'API' },
        { zh: 'Swagger', en: 'Swagger' },
        { zh: '文档', en: 'Docs' }
    ],
    features: [
        { zh: '读取 Swagger 文档', en: 'Read Swagger Docs' },
        { zh: '生成 API 文档', en: 'Generate API Docs' },
        { zh: '浏览器认证', en: 'Browser Auth' }
    ],
    scripts: ['swagger_reader.py', 'doc_generator.py'],
    version: '1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/swagger-api-reader',
    useCases: [
        {
            title: { zh: '安装 Swagger API Reader', en: 'Install Swagger API Reader' },
            userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 安装 swagger-api-reader skill', en: 'Please install swagger-api-reader skill from https://github.com/shetengteng/skillix-hub' },
            aiResponse: {
                zh: '正在安装 Swagger API Reader...\n\n1. 克隆仓库\n2. 复制 skills/swagger-api-reader 到 ~/.cursor/skills/\n3. 安装依赖: pip install -r requirements.txt\n\n✅ 安装完成！\n\n你可以说"读取 API 文档"来开始使用。',
                en: 'Installing Swagger API Reader...\n\n1. Clone repository\n2. Copy skills/swagger-api-reader to ~/.cursor/skills/\n3. Install deps: pip install -r requirements.txt\n\n✅ Installation complete!\n\nYou can say "read API docs" to start using.'
            }
        },
        {
            title: { zh: '更新 Swagger API Reader', en: 'Update Swagger API Reader' },
            userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 更新 swagger-api-reader skill', en: 'Please update swagger-api-reader skill from https://github.com/shetengteng/skillix-hub' },
            aiResponse: {
                zh: '正在更新 Swagger API Reader...\n\n1. 拉取最新代码\n2. 更新 skill 代码和脚本\n3. 更新依赖\n\n✅ Swagger API Reader 已更新到最新版本！\n\n已有的 API 缓存数据完整保留。',
                en: 'Updating Swagger API Reader...\n\n1. Pull latest code\n2. Update skill code and scripts\n3. Update dependencies\n\n✅ Swagger API Reader updated to latest version!\n\nExisting API cache data fully preserved.'
            }
        },
        {
            title: { zh: '读取 API 文档', en: 'Read API Documentation' },
            userInput: { zh: '帮我读取 https://api.example.com/swagger.json 的 API 文档', en: 'Help me read the API docs from https://api.example.com/swagger.json' },
            aiResponse: {
                zh: '正在读取 Swagger 文档...\n\n✅ 读取成功！\n\n**API 概览：**\n- 基础路径: /api/v1\n- 端点数量: 24\n- 认证方式: Bearer Token\n\n**主要模块：**\n- /users (5 个端点)\n- /products (8 个端点)\n- /orders (6 个端点)\n- /auth (5 个端点)\n\n需要查看哪个模块的详细信息？',
                en: 'Reading Swagger documentation...\n\n✅ Read successful!\n\n**API Overview:**\n- Base path: /api/v1\n- Endpoints: 24\n- Auth: Bearer Token\n\n**Main Modules:**\n- /users (5 endpoints)\n- /products (8 endpoints)\n- /orders (6 endpoints)\n- /auth (5 endpoints)\n\nWhich module details would you like to see?'
            }
        },
        {
            title: { zh: '生成 API 文档', en: 'Generate API Documentation' },
            userInput: { zh: '生成 users 模块的 API 文档', en: 'Generate API docs for users module' },
            aiResponse: {
                zh: 'Users 模块 API 文档\n\n**GET /users**\n获取用户列表\n- 参数: page, limit, search\n- 响应: UserList\n\n**POST /users**\n创建新用户\n- 请求体: CreateUserRequest\n- 响应: User\n\n**GET /users/{id}**\n获取用户详情\n- 参数: id (path)\n- 响应: User\n\n...\n\n文档已生成到 docs/api/users.md',
                en: 'Users Module API Documentation\n\n**GET /users**\nGet user list\n- Params: page, limit, search\n- Response: UserList\n\n**POST /users**\nCreate new user\n- Body: CreateUserRequest\n- Response: User\n\n**GET /users/{id}**\nGet user details\n- Params: id (path)\n- Response: User\n\n...\n\nDocs generated to docs/api/users.md'
            }
        },
        {
            title: { zh: '需要认证的 API', en: 'API Requiring Authentication' },
            userInput: { zh: '读取需要登录的内部 API 文档', en: 'Read internal API docs that require login' },
            aiResponse: {
                zh: '检测到该 API 需要认证。\n\n正在启动浏览器认证...\n\n请在打开的浏览器窗口中完成登录，然后我会自动获取认证信息并读取 API 文档。\n\n（浏览器窗口已打开，等待登录...）\n\n✅ 认证成功！正在读取 API 文档...',
                en: 'Detected that this API requires authentication.\n\nStarting browser authentication...\n\nPlease complete login in the opened browser window, then I\'ll automatically get auth info and read the API docs.\n\n(Browser window opened, waiting for login...)\n\n✅ Authentication successful! Reading API docs...'
            }
        }
    ]
};
