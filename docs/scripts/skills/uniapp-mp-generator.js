/**
 * Skillix Hub - uniapp-mp-generator Skill Data
 */
window.SKILL_DATA_UNIAPP_MP_GENERATOR = {
    id: 'uniapp-mp-generator',
    name: 'uniapp-mp-generator',
    icon: 'folder',
    description: {
        zh: '基于 uni-app 项目规范的小程序代码生成器，根据需求文档自动生成 Vue3 页面、API、Store 等代码',
        en: 'uni-app mini-program code generator based on project standards, auto-generate Vue3 pages, API, Store code from requirements'
    },
    tags: [
        { zh: '代码生成', en: 'Code Gen' },
        { zh: 'uni-app', en: 'uni-app' },
        { zh: '小程序', en: 'Mini Program' },
        { zh: 'Vue3', en: 'Vue3' }
    ],
    features: [
        { zh: 'Vue3 页面生成', en: 'Vue3 Page Generation' },
        { zh: 'API 文件生成', en: 'API File Generation' },
        { zh: 'Store 生成', en: 'Store Generation' },
        { zh: 'Schema 定义', en: 'Schema Definition' },
        { zh: '组件生成', en: 'Component Generation' },
        { zh: '路由配置', en: 'Route Configuration' }
    ],
    scripts: [],
    version: '1.0',
    author: 'shetengteng',
    repo: 'https://github.com/shetengteng/skillix-hub/tree/main/skills/uniapp-mp-generator',
    useCases: [
        {
            title: { zh: '安装 uni-app 代码生成器', en: 'Install uni-app Code Generator' },
            userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 安装 uniapp-mp-generator skill', en: 'Please install uniapp-mp-generator skill from https://github.com/shetengteng/skillix-hub' },
            aiResponse: {
                zh: '✅ uni-app 小程序代码生成器安装成功！\n\n这个 Skill 可以：\n• 根据需求文档生成 Vue3 页面\n• 自动创建 API 接口文件\n• 生成 Pinia Store\n• 创建数据库 Schema\n\n使用方式：提供需求文档，我会自动生成符合规范的代码。',
                en: '✅ uni-app Mini Program Code Generator installed!\n\nThis Skill can:\n• Generate Vue3 pages from requirements\n• Auto-create API interface files\n• Generate Pinia Store\n• Create database Schema\n\nUsage: Provide requirements doc, I\'ll auto-generate standard-compliant code.'
            }
        },
        {
            title: { zh: '更新 uni-app 代码生成器', en: 'Update uni-app Code Generator' },
            userInput: { zh: '帮我从 https://github.com/shetengteng/skillix-hub 更新 uniapp-mp-generator skill', en: 'Please update uniapp-mp-generator skill from https://github.com/shetengteng/skillix-hub' },
            aiResponse: {
                zh: '正在更新 uni-app 代码生成器...\n\n1. 拉取最新代码\n2. 更新 SKILL.md 和模板文件\n\n✅ uni-app 代码生成器已更新到最新版本！\n\n新版本可能包含更多页面模板和组件支持。',
                en: 'Updating uni-app Code Generator...\n\n1. Pull latest code\n2. Update SKILL.md and template files\n\n✅ uni-app Code Generator updated to latest version!\n\nNew version may include more page templates and component support.'
            }
        },
        {
            title: { zh: '生成课程管理模块', en: 'Generate Course Management Module' },
            userInput: { zh: '帮我生成课程管理模块，包含课程列表、详情、新增页面', en: 'Help me generate course management module with list, detail, and add pages' },
            aiResponse: {
                zh: '好的，我来为你生成课程管理模块。\n\n📁 将创建以下文件：\n\npages/course/\n├── api/\n│   ├── getCourseList.js\n│   ├── getCourseDetail.js\n│   ├── createCourse.js\n│   ├── updateCourse.js\n│   └── deleteCourse.js\n├── components/\n│   └── CourseCard.vue\n├── index.vue\n└── sub/\n    ├── detail/index.vue\n    └── add/index.vue\n\n正在生成代码...',
                en: 'OK, I\'ll generate the course management module for you.\n\n📁 Files to be created:\n\npages/course/\n├── api/\n│   ├── getCourseList.js\n│   ├── getCourseDetail.js\n│   ├── createCourse.js\n│   ├── updateCourse.js\n│   └── deleteCourse.js\n├── components/\n│   └── CourseCard.vue\n├── index.vue\n└── sub/\n    ├── detail/index.vue\n    └── add/index.vue\n\nGenerating code...'
            }
        },
        {
            title: { zh: '根据需求文档生成代码', en: 'Generate Code from Requirements' },
            userInput: { zh: '根据这个需求文档生成代码：\n# 学生管理\n## 数据字段\n- name: 姓名\n- phone: 电话\n- status: 状态', en: 'Generate code from this requirements doc:\n# Student Management\n## Data Fields\n- name: Name\n- phone: Phone\n- status: Status' },
            aiResponse: {
                zh: '分析需求文档完成！\n\n📋 模块信息：\n- 模块名: Student (学生)\n- 字段: name, phone, status\n\n正在生成：\n1. ✅ Schema 定义 (COLLECTIONS.STUDENTS)\n2. ✅ API 文件 (5 个 CRUD 接口)\n3. ✅ 列表页 (pages/student/index.vue)\n4. ✅ 详情页 (pages/student/sub/detail/index.vue)\n5. ✅ 表单页 (pages/student/sub/add/index.vue)\n6. ✅ 卡片组件 (StudentCard.vue)\n\n代码已生成完成！',
                en: 'Requirements analysis complete!\n\n📋 Module Info:\n- Module: Student\n- Fields: name, phone, status\n\nGenerating:\n1. ✅ Schema definition (COLLECTIONS.STUDENTS)\n2. ✅ API files (5 CRUD endpoints)\n3. ✅ List page (pages/student/index.vue)\n4. ✅ Detail page (pages/student/sub/detail/index.vue)\n5. ✅ Form page (pages/student/sub/add/index.vue)\n6. ✅ Card component (StudentCard.vue)\n\nCode generation complete!'
            }
        }
    ]
};
