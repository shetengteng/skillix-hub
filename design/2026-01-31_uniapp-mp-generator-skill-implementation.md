# uni-app 小程序代码生成器 Skill 实施文档

> **版本**: v1.0.0
> **创建日期**: 2026-01-31
> **关联设计文档**: 2026-01-31_uniapp-mp-generator-skill-design.md

## 一、实施概述

### 1.1 目标

实现一个 Cursor Skill，使 AI 能够：
1. 理解 tt-paikebao-mp 项目的代码规范
2. 根据用户提供的需求文档生成符合规范的代码
3. 生成完整的页面、API、Store、路由等文件

### 1.2 实施范围

| 模块 | 说明 | 优先级 |
|-----|------|--------|
| SKILL.md | Skill 入口文件 | P0 |
| 代码模板 | 各类代码模板文件 | P0 |
| 规则文件 | 代码生成规则 | P1 |
| 示例文件 | 参考示例 | P2 |

---

## 二、目录结构

```
skills/
└── uniapp-mp-generator/
    ├── SKILL.md                    # Skill 入口（AI 阅读）
    ├── default_config.json         # 默认配置
    ├── templates/                  # 代码模板
    │   ├── page/
    │   │   ├── list.vue.template       # 列表页模板
    │   │   ├── detail.vue.template     # 详情页模板
    │   │   ├── form.vue.template       # 表单页模板
    │   │   └── index.vue.template      # 通用页面模板
    │   ├── component/
    │   │   ├── card.vue.template       # 卡片组件模板
    │   │   ├── filter.vue.template     # 筛选组件模板
    │   │   └── list-item.vue.template  # 列表项组件模板
    │   ├── api/
    │   │   ├── get-list.js.template    # 获取列表 API
    │   │   ├── get-detail.js.template  # 获取详情 API
    │   │   ├── create.js.template      # 创建 API
    │   │   ├── update.js.template      # 更新 API
    │   │   └── delete.js.template      # 删除 API
    │   ├── store/
    │   │   └── index.js.template       # Store 模板
    │   └── schema/
    │       └── collection.js.template  # 集合定义模板
    ├── rules/
    │   ├── code-style.mdc          # 代码风格规则
    │   ├── naming.mdc              # 命名规范规则
    │   └── structure.mdc           # 目录结构规则
    └── examples/
        ├── student-module/         # 学生模块示例
        └── course-module/          # 课程模块示例
```

---

## 三、核心文件实现

### 3.1 SKILL.md 入口文件

```markdown
# uni-app 小程序代码生成器

## 功能
根据需求文档生成符合 tt-paikebao-mp 项目规范的代码。

## 触发条件
- 用户请求创建新的页面模块
- 用户请求生成 API 文件
- 用户请求创建数据库集合
- 用户提供需求文档要求生成代码

## 使用方式

### 1. 读取配置
首先读取项目配置获取前缀等信息：
\`\`\`
config/index.js -> PROJECT_CONFIG.prefix
\`\`\`

### 2. 分析需求
从用户需求中提取：
- 模块名称（中文/英文）
- 数据字段
- 页面列表
- 功能点

### 3. 生成代码
按以下顺序生成：
1. 数据库 Schema（类型定义）
2. API 文件（CRUD + 业务操作）
3. 页面组件
4. 路由配置
5. pages.json 配置

## 代码规范
[引用设计文档中的规范...]

## 模板位置
templates/ 目录下的模板文件

## 示例
examples/ 目录下的示例代码
```

### 3.2 default_config.json

```json
{
  "version": "1.0.0",
  "projectType": "uniapp-mp",
  "framework": "vue3",
  "uiLibrary": "sard-uniapp",
  "backend": "emas",
  "defaults": {
    "pageSize": 20,
    "dateFormat": "YYYY-MM-DD HH:mm:ss",
    "componentPrefix": "Tt",
    "apiReturnFormat": {
      "success": "boolean",
      "data": "any",
      "error": "string?"
    }
  },
  "templates": {
    "page": {
      "list": "templates/page/list.vue.template",
      "detail": "templates/page/detail.vue.template",
      "form": "templates/page/form.vue.template"
    },
    "api": {
      "getList": "templates/api/get-list.js.template",
      "getDetail": "templates/api/get-detail.js.template",
      "create": "templates/api/create.js.template",
      "update": "templates/api/update.js.template",
      "delete": "templates/api/delete.js.template"
    },
    "store": "templates/store/index.js.template",
    "schema": "templates/schema/collection.js.template"
  }
}
```

---

## 四、模板文件实现

### 4.1 列表页模板 (list.vue.template)

```vue
<template>
  <view class="page bg-page">
    <!-- 搜索栏 -->
    <sar-sticky>
      <view class="bg-card p-md">
        <sar-input
          v-model="searchKeyword"
          placeholder="搜索{{MODULE_NAME_CN}}..."
          clearable
        >
          <template #prepend>
            <TtSvg name="search" :size="36" color="#999" />
          </template>
        </sar-input>
      </view>
    </sar-sticky>

    <!-- 筛选器 -->
    {{#if HAS_FILTER}}
    <view class="bg-card px-md py-sm">
      <sar-space>
        {{#each FILTER_OPTIONS}}
        <sar-tag
          :theme="filter === '{{value}}' ? 'primary' : 'default'"
          @click="filter = '{{value}}'"
        >
          {{label}}
        </sar-tag>
        {{/each}}
      </sar-space>
    </view>
    {{/if}}

    <!-- 列表 -->
    <view class="p-md">
      <sar-space direction="vertical" size="24rpx">
        <{{MODULE_NAME}}Card
          v-for="item in filteredList"
          :key="item._id"
          :data="item"
          @click="goToDetail(item._id)"
        />
      </sar-space>
    </view>

    <!-- 空状态 -->
    <sar-empty
      v-if="!loading && filteredList.length === 0"
      description="暂无{{MODULE_NAME_CN}}"
    />

    <!-- 加载状态 -->
    <view v-if="loading" class="flex-center p-xl">
      <sar-loading />
    </view>

    <!-- FAB 添加按钮 -->
    <TtFab @click="goToAdd">
      <TtSvg name="add" :size="48" color="#fff" />
    </TtFab>

    <!-- 底部留白 -->
    <TtBottomPlaceholder />
  </view>
</template>

<script>
export default {
  options: {
    virtualHost: true,
    styleIsolation: 'shared'
  }
}
</script>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'

// 组件
import TtSvg from '@/components/TtSvg.vue'
import TtFab from '@/components/TtFab.vue'
import TtBottomPlaceholder from '@/components/TtBottomPlaceholder.vue'
import {{MODULE_NAME}}Card from './components/{{MODULE_NAME}}Card.vue'

// 路由
import { goTo{{MODULE_NAME}}Detail, goTo{{MODULE_NAME}}Add } from '@/route/index'

// API
import { get{{MODULE_NAME}}List } from './api/get{{MODULE_NAME}}List'

// ============ 响应式数据 ============
const loading = ref(false)
const list = ref([])
const searchKeyword = ref('')
const filter = ref('all')

// ============ 计算属性 ============
const filteredList = computed(() => {
  let result = list.value

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(item =>
      item.name?.toLowerCase().includes(keyword)
    )
  }

  // 状态过滤
  if (filter.value !== 'all') {
    result = result.filter(item => item.status === filter.value)
  }

  return result
})

// ============ 生命周期 ============
onShow(() => {
  loadData()
})

// ============ 方法 ============

/**
 * 加载数据
 */
const loadData = async () => {
  loading.value = true
  try {
    const res = await get{{MODULE_NAME}}List()
    if (res.success) {
      list.value = res.list
    }
  } finally {
    loading.value = false
  }
}

/**
 * 跳转到详情
 */
const goToDetail = (id) => {
  goTo{{MODULE_NAME}}Detail(id)
}

/**
 * 跳转到新增
 */
const goToAdd = () => {
  goTo{{MODULE_NAME}}Add()
}
</script>

<style lang="scss">
@import '@/styles/global.scss';
</style>
```

### 4.2 获取列表 API 模板 (get-list.js.template)

```javascript
/**
 * 获取{{MODULE_NAME_CN}}列表
 * @module pages/{{MODULE_NAME_LOWER}}/api/get{{MODULE_NAME}}List
 * @since {{DATE}}
 */

import { db, COLLECTIONS } from '@/cloud-emas/database/database'
import { checkEmasError } from '@/cloud-emas/database/error'
import { requireAccountId } from '@/utils/auth'

/**
 * {{MODULE_NAME_CN}}列表项数据结构
 * @typedef {Object} {{MODULE_NAME}}Item
{{#each FIELDS}}
 * @property {{jsDocType}} {{name}} - {{description}}
{{/each}}
 * @property {string} createTime - 创建时间
 * @property {string} updateTime - 更新时间
 */

/**
 * 获取{{MODULE_NAME_CN}}列表
 * @param {Object} params - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.pageSize=20] - 每页数量
{{#if HAS_STATUS}}
 * @param {string} [params.status] - 状态筛选
{{/if}}
 * @returns {Promise<{success: boolean, list: {{MODULE_NAME}}Item[], error?: string}>}
 */
export async function get{{MODULE_NAME}}List(params = {}) {
  try {
    const accountId = requireAccountId()
    if (!accountId) {
      return { success: false, list: [], error: '未登录' }
    }

    const { page = 1, pageSize = 20{{#if HAS_STATUS}}, status{{/if}} } = params

    let query = db.collection(COLLECTIONS.{{COLLECTION_NAME}})
      .where({ accountId })

{{#if HAS_STATUS}}
    if (status) {
      query = query.where({ status })
    }
{{/if}}

    const res = await query
      .orderBy('createTime', 'desc')
      .skip((page - 1) * pageSize)
      .limit(pageSize)
      .get()

    checkEmasError(res, '获取{{MODULE_NAME_CN}}列表')

    return {
      success: true,
      list: res.data || []
    }
  } catch (error) {
    console.error('[get{{MODULE_NAME}}List] 失败:', error)
    return { success: false, list: [], error: error.message }
  }
}

export default get{{MODULE_NAME}}List
```

### 4.3 创建 API 模板 (create.js.template)

```javascript
/**
 * 创建{{MODULE_NAME_CN}}
 * @module pages/{{MODULE_NAME_LOWER}}/api/create{{MODULE_NAME}}
 * @since {{DATE}}
 */

import { db, COLLECTIONS } from '@/cloud-emas/database/database'
import { checkEmasError } from '@/cloud-emas/database/error'
import { requireAccountId } from '@/utils/auth'

/**
 * 创建{{MODULE_NAME_CN}}请求参数
 * @typedef {Object} Create{{MODULE_NAME}}Params
{{#each REQUIRED_FIELDS}}
 * @property {{jsDocType}} {{name}} - {{description}}（必填）
{{/each}}
{{#each OPTIONAL_FIELDS}}
 * @property {{jsDocType}} [{{name}}] - {{description}}（可选）
{{/each}}
 */

/**
 * 创建{{MODULE_NAME_CN}}
 * @param {Create{{MODULE_NAME}}Params} params - 创建参数
 * @returns {Promise<{success: boolean, id?: string, error?: string}>}
 */
export async function create{{MODULE_NAME}}(params) {
  try {
    const accountId = requireAccountId()
    if (!accountId) {
      return { success: false, error: '未登录' }
    }

    // 参数校验
{{#each REQUIRED_FIELDS}}
    if (!params.{{name}}) {
      return { success: false, error: '{{description}}不能为空' }
    }
{{/each}}

    const now = new Date().toISOString()
    const data = {
      accountId,
{{#each FIELDS}}
      {{name}}: params.{{name}}{{#if defaultValue}} || {{defaultValue}}{{/if}},
{{/each}}
      createTime: now,
      updateTime: now
    }

    const res = await db.collection(COLLECTIONS.{{COLLECTION_NAME}}).add(data)
    checkEmasError(res, '创建{{MODULE_NAME_CN}}')

    return {
      success: true,
      id: res._id
    }
  } catch (error) {
    console.error('[create{{MODULE_NAME}}] 失败:', error)
    return { success: false, error: error.message }
  }
}

export default create{{MODULE_NAME}}
```

### 4.4 Store 模板 (index.js.template)

```javascript
/**
 * {{MODULE_NAME_CN}}状态管理
 * @module stores/{{MODULE_NAME_LOWER}}
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { get{{MODULE_NAME}}List } from '@/pages/{{MODULE_NAME_LOWER}}/api/get{{MODULE_NAME}}List'

export const use{{MODULE_NAME}}Store = defineStore('{{MODULE_NAME_LOWER}}', () => {
  // ============ 状态 ============
  const {{MODULE_NAME_LOWER}}s = ref([])
  const loading = ref(false)
  const loaded = ref(false)

  // ============ 计算属性 ============
  const {{MODULE_NAME_LOWER}}Count = computed(() => {{MODULE_NAME_LOWER}}s.value.length)

  // ============ 方法 ============

  /**
   * 加载{{MODULE_NAME_CN}}列表
   * @param {boolean} [force=false] - 是否强制刷新
   */
  const load{{MODULE_NAME}}s = async (force = false) => {
    if (loaded.value && !force) return

    loading.value = true
    try {
      const res = await get{{MODULE_NAME}}List()
      if (res.success) {
        {{MODULE_NAME_LOWER}}s.value = res.list
        loaded.value = true
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 根据 ID 获取{{MODULE_NAME_CN}}
   * @param {string} id - {{MODULE_NAME_CN}}ID
   * @returns {Object|null}
   */
  const get{{MODULE_NAME}}ById = (id) => {
    return {{MODULE_NAME_LOWER}}s.value.find(item => item._id === id) || null
  }

  /**
   * 添加{{MODULE_NAME_CN}}到缓存
   * @param {Object} item - {{MODULE_NAME_CN}}数据
   */
  const add{{MODULE_NAME}} = (item) => {
    {{MODULE_NAME_LOWER}}s.value.unshift(item)
  }

  /**
   * 更新缓存中的{{MODULE_NAME_CN}}
   * @param {string} id - {{MODULE_NAME_CN}}ID
   * @param {Object} data - 更新数据
   */
  const update{{MODULE_NAME}} = (id, data) => {
    const index = {{MODULE_NAME_LOWER}}s.value.findIndex(item => item._id === id)
    if (index !== -1) {
      {{MODULE_NAME_LOWER}}s.value[index] = { ...{{MODULE_NAME_LOWER}}s.value[index], ...data }
    }
  }

  /**
   * 从缓存中删除{{MODULE_NAME_CN}}
   * @param {string} id - {{MODULE_NAME_CN}}ID
   */
  const remove{{MODULE_NAME}} = (id) => {
    const index = {{MODULE_NAME_LOWER}}s.value.findIndex(item => item._id === id)
    if (index !== -1) {
      {{MODULE_NAME_LOWER}}s.value.splice(index, 1)
    }
  }

  /**
   * 重置状态
   */
  const reset = () => {
    {{MODULE_NAME_LOWER}}s.value = []
    loaded.value = false
  }

  return {
    // 状态
    {{MODULE_NAME_LOWER}}s,
    loading,
    loaded,
    // 计算属性
    {{MODULE_NAME_LOWER}}Count,
    // 方法
    load{{MODULE_NAME}}s,
    get{{MODULE_NAME}}ById,
    add{{MODULE_NAME}},
    update{{MODULE_NAME}},
    remove{{MODULE_NAME}},
    reset
  }
})
```

### 4.5 集合定义模板 (collection.js.template)

```javascript
/**
 * {{MODULE_NAME_CN}}集合定义
 * @module cloud-emas/database/collections/{{MODULE_NAME_LOWER}}
 * @since {{DATE}}
 */

import { PROJECT_CONFIG } from '@/config/index'

const PREFIX = PROJECT_CONFIG.prefix

/**
 * 集合名称
 */
export const {{COLLECTION_CONST}} = `${PREFIX}-{{MODULE_NAME_LOWER}}s`

/**
 * {{MODULE_NAME_CN}}数据结构
 * @typedef {Object} {{MODULE_NAME}}
 * @property {string} _id - {{MODULE_NAME_CN}}ID（系统生成）
 * @property {string} accountId - 所属用户ID
{{#each FIELDS}}
 * @property {{jsDocType}} {{#if optional}}[{{name}}]{{else}}{{name}}{{/if}} - {{description}}
{{/each}}
 * @property {string} createTime - 创建时间（ISO 8601）
 * @property {string} updateTime - 更新时间（ISO 8601）
 */

{{#if HAS_STATUS}}
/**
 * {{MODULE_NAME_CN}}状态枚举
 * @typedef {{{STATUS_ENUM}}} {{MODULE_NAME}}Status
{{#each STATUS_OPTIONS}}
 * - {{value}}: {{label}}
{{/each}}
 */
{{/if}}

/**
 * 索引建议
 * - accountId: 按用户查询
 * - createTime: 按时间排序
{{#if HAS_STATUS}}
 * - status: 按状态筛选
{{/if}}
 */
```

---

## 五、规则文件实现

### 5.1 代码风格规则 (code-style.mdc)

```markdown
# 代码风格规则

## Vue 组件规范

### 1. 组件结构顺序
1. `<template>` - 模板
2. `<script>` - Options API（组件选项，如需要）
3. `<script setup>` - Composition API
4. `<style>` - 样式

### 2. script setup 内部顺序
1. Vue 核心导入（ref, computed 等）
2. uni-app 生命周期导入
3. 工具函数导入
4. 组件导入
5. 路由/Store 导入
6. API 导入
7. 响应式数据定义
8. 计算属性定义
9. 生命周期钩子
10. 方法定义

### 3. 响应式数据
- 统一使用 `ref`，不使用 `reactive`
- 命名使用 camelCase

### 4. Props 定义
- 使用对象式定义
- 必须指定类型
- 必须提供默认值（除 required: true）

### 5. 注释规范
- 所有注释使用中文
- 方法必须有 JSDoc 注释
- 复杂逻辑必须有行内注释

## API 文件规范

### 1. 文件命名
- 使用 camelCase
- 格式：{动词}{名词}.js
- 一个文件一个主要方法

### 2. 返回格式
统一返回：
```javascript
{ success: boolean, data/list: any, error?: string }
```

### 3. 错误处理
- 使用 try-catch 包裹
- 使用 checkEmasError 检查响应
- 错误时返回 { success: false, error: message }

### 4. 类型定义
- 使用 JSDoc @typedef 定义数据结构
- 必须包含字段说明
- 枚举类型列出所有值
```

### 5.2 命名规范规则 (naming.mdc)

```markdown
# 命名规范规则

## 文件命名

| 类型 | 规范 | 示例 |
|-----|------|------|
| Vue 组件 | PascalCase | `StudentCard.vue` |
| 页面文件 | kebab-case | `student-detail.vue` |
| API 文件 | camelCase | `getStudentList.js` |
| Store 文件 | camelCase | `studentStore.js` |
| 工具文件 | camelCase | `dateUtils.js` |

## 变量命名

| 类型 | 规范 | 示例 |
|-----|------|------|
| 响应式变量 | camelCase | `studentList` |
| 常量 | UPPER_SNAKE_CASE | `COLLECTIONS` |
| 方法 | camelCase | `loadStudents` |
| 组件 Props | camelCase | `studentId` |
| 事件名 | kebab-case | `@update:visible` |

## 数据库命名

| 类型 | 规范 | 示例 |
|-----|------|------|
| 集合名 | {prefix}-{name}s | `pkb-students` |
| 云函数名 | {prefix}-{action} | `pkb-sendSmsCode` |
| 存储路径 | {prefix}/{type}/{id}/ | `pkb/avatars/xxx/` |

## 路由命名

| 类型 | 规范 | 示例 |
|-----|------|------|
| 路由常量 | camelCase | `studentDetail` |
| 跳转方法 | goTo{Page} | `goToStudentDetail` |
| Tab 切换 | switchTab | `switchTab('home')` |
```

---

## 六、示例模块

### 6.1 学生模块示例结构

```
examples/student-module/
├── api/
│   ├── getStudentList.js
│   ├── getStudentDetail.js
│   ├── createStudent.js
│   ├── updateStudent.js
│   └── deleteStudent.js
├── components/
│   ├── StudentCard.vue
│   └── StudentFilter.vue
├── index.vue
└── sub/
    ├── detail/
    │   └── index.vue
    └── add/
        └── index.vue
```

---

## 七、实施步骤

### 7.1 Phase 1：基础框架（Day 1-2）

1. **创建 Skill 目录结构**
   ```bash
   mkdir -p skills/uniapp-mp-generator/{templates,rules,examples}
   ```

2. **编写 SKILL.md 入口文件**
   - 定义触发条件
   - 说明使用方式
   - 引用代码规范

3. **创建 default_config.json**
   - 配置模板路径
   - 配置默认值

### 7.2 Phase 2：模板文件（Day 3-5）

1. **页面模板**
   - list.vue.template
   - detail.vue.template
   - form.vue.template

2. **API 模板**
   - get-list.js.template
   - get-detail.js.template
   - create.js.template
   - update.js.template
   - delete.js.template

3. **Store 模板**
   - index.js.template

4. **Schema 模板**
   - collection.js.template

### 7.3 Phase 3：规则文件（Day 6）

1. **代码风格规则**
   - code-style.mdc

2. **命名规范规则**
   - naming.mdc

3. **目录结构规则**
   - structure.mdc

### 7.4 Phase 4：示例和测试（Day 7）

1. **创建示例模块**
   - student-module 完整示例

2. **测试验证**
   - 测试代码生成
   - 验证生成代码质量

---

## 八、模板变量说明

### 8.1 通用变量

| 变量 | 说明 | 示例 |
|-----|------|------|
| `{{MODULE_NAME}}` | 模块名（PascalCase） | `Student` |
| `{{MODULE_NAME_LOWER}}` | 模块名（小写） | `student` |
| `{{MODULE_NAME_CN}}` | 模块中文名 | `学生` |
| `{{DATE}}` | 当前日期 | `2026-01-31` |
| `{{PREFIX}}` | 项目前缀 | `pkb` |

### 8.2 字段变量

| 变量 | 说明 | 示例 |
|-----|------|------|
| `{{FIELDS}}` | 字段列表 | `[{name, type, description}]` |
| `{{REQUIRED_FIELDS}}` | 必填字段 | `[...]` |
| `{{OPTIONAL_FIELDS}}` | 可选字段 | `[...]` |

### 8.3 条件变量

| 变量 | 说明 | 示例 |
|-----|------|------|
| `{{#if HAS_STATUS}}` | 是否有状态字段 | `true/false` |
| `{{#if HAS_FILTER}}` | 是否有筛选功能 | `true/false` |

### 8.4 集合变量

| 变量 | 说明 | 示例 |
|-----|------|------|
| `{{COLLECTION_NAME}}` | 集合常量名 | `STUDENTS` |
| `{{COLLECTION_CONST}}` | 集合定义常量 | `COLLECTION_STUDENTS` |

---

## 九、验收标准

### 9.1 功能验收

- [ ] SKILL.md 可被 AI 正确读取和理解
- [ ] 模板文件可正确生成代码
- [ ] 生成的代码符合项目规范
- [ ] 生成的代码可直接运行

### 9.2 质量验收

- [ ] 代码风格一致
- [ ] 类型定义完整
- [ ] 注释规范完整
- [ ] 错误处理完善

### 9.3 文档验收

- [ ] SKILL.md 说明清晰
- [ ] 模板变量说明完整
- [ ] 示例代码可参考

---

## 十、风险与应对

| 风险 | 影响 | 应对措施 |
|-----|------|---------|
| 模板复杂度高 | 维护困难 | 模块化设计，拆分小模板 |
| AI 理解偏差 | 生成代码不符合预期 | 增加示例，明确规范 |
| 项目规范变更 | 模板需要更新 | 版本管理，变更记录 |
