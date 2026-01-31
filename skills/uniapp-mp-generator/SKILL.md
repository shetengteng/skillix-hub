# uni-app 小程序代码生成器

> **版本**: v1.0.0
> **作者**: AI Assistant
> **参考项目**: tt-paikebao-mp（排课宝）

## 功能概述

这是一个基于 **tt-paikebao-mp** 项目代码规范的 uni-app 小程序代码生成器。根据用户提供的需求文档，自动生成符合项目规范的：

- Vue3 页面组件
- API 接口文件
- Pinia Store 状态管理
- 路由配置
- 数据库 Schema 定义

## 触发条件

当用户请求以下内容时，应使用此 Skill：

1. 创建新的页面模块
2. 生成 API 接口文件
3. 创建数据库集合定义
4. 生成 Store 状态管理
5. 提供需求文档要求生成代码
6. 询问 uni-app 小程序开发规范

## 快速开始

### 1. 用户提供需求文档

用户应提供以下格式的需求文档：

```markdown
# 模块名称

## 功能描述
简要描述该模块的功能

## 数据字段
- fieldName: 字段描述（必填/可选，类型）

## 页面列表
- 页面名称：页面描述

## 功能点
1. 功能点描述
```

### 2. AI 分析需求

从需求中提取：
- 模块名称（中文/英文）
- 数据字段及类型
- 页面列表
- 功能点

### 3. AI 生成代码

按以下顺序生成：
1. 数据库 Schema（类型定义）
2. API 文件（CRUD + 业务操作）
3. 页面组件
4. 路由配置
5. pages.json 配置

---

## 技术栈

| 技术 | 版本/说明 |
|-----|---------|
| uni-app | Vue3 模式 |
| Vue | 3.x (Composition API + script setup) |
| Pinia | 状态管理 |
| sard-uniapp | UI 组件库 |
| dayjs | 日期处理 |
| EMAS Serverless | 阿里云云开发 |

---

## 项目配置

### 项目前缀

所有数据库集合、云函数、存储路径使用统一前缀，在 `config/index.js` 中配置：

```javascript
export const PROJECT_CONFIG = {
  prefix: 'pkb',  // 项目前缀
  name: '排课宝',
  // ...
}
```

生成代码时，自动使用此前缀：
- 集合名：`{prefix}-students`
- 云函数：`{prefix}-sendSmsCode`
- 存储路径：`{prefix}/avatars/{userId}/`

---

## 代码规范

### Vue 组件结构

```vue
<template>
  <view class="page bg-page">
    <!-- 页面内容 -->
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
// 1. Vue 核心
import { ref, computed } from 'vue'

// 2. uni-app 生命周期
import { onShow } from '@dcloudio/uni-app'

// 3. 工具函数
import { dayjs } from '@/utils/date'

// 4. 组件
import TtBottomPlaceholder from '@/components/TtBottomPlaceholder.vue'

// 5. 路由/Store
import { goToXxx } from '@/route/index'

// 6. API
import { getXxxList } from './api/getXxxList'

// ============ 响应式数据 ============
const loading = ref(false)
const list = ref([])

// ============ 计算属性 ============
const isEmpty = computed(() => list.value.length === 0)

// ============ 生命周期 ============
onShow(() => {
  loadData()
})

// ============ 方法 ============
const loadData = async () => {
  // ...
}
</script>

<style lang="scss">
@import '@/styles/global.scss';
</style>
```

### API 文件结构

```javascript
/**
 * 获取列表
 * @module pages/xxx/api/getXxxList
 */

import { db, COLLECTIONS } from '@/cloud-emas/database/database'
import { checkEmasError } from '@/cloud-emas/database/error'
import { requireAccountId } from '@/utils/auth'

/**
 * 数据结构定义
 * @typedef {Object} XxxItem
 * @property {string} _id - ID
 * @property {string} name - 名称
 */

/**
 * 获取列表
 * @returns {Promise<{success: boolean, list: XxxItem[], error?: string}>}
 */
export async function getXxxList(params = {}) {
  try {
    const accountId = requireAccountId()
    if (!accountId) {
      return { success: false, list: [], error: '未登录' }
    }

    const res = await db.collection(COLLECTIONS.XXX)
      .where({ accountId })
      .orderBy('createTime', 'desc')
      .get()

    checkEmasError(res, '获取列表')

    return { success: true, list: res.data || [] }
  } catch (error) {
    console.error('[getXxxList] 失败:', error)
    return { success: false, list: [], error: error.message }
  }
}

export default getXxxList
```

### 命名规范

| 类型 | 规范 | 示例 |
|-----|------|------|
| 组件文件 | PascalCase | `StudentCard.vue` |
| API 文件 | camelCase | `getStudentList.js` |
| 变量 | camelCase | `studentList` |
| 常量 | UPPER_SNAKE_CASE | `COLLECTIONS` |
| 集合名 | {prefix}-{name}s | `pkb-students` |

### 样式规范

**优先级**：
1. sard-uniapp 组件
2. 全局工具类（`flex-row`、`p-lg` 等）
3. 组件 root-style
4. 自定义样式（几乎禁止）

**全局工具类**：
- 布局：`flex-row` `flex-col` `flex-center` `flex-between`
- 文字：`text-sm` `text-base` `text-lg` `text-muted`
- 间距：`p-sm` `p-md` `p-lg` `m-sm` `m-md` `m-lg`
- 背景：`bg-page` `bg-card` `bg-muted`
- 边框：`border` `border-t` `border-b`
- 圆角：`rounded-sm` `rounded-md` `rounded-lg`

---

## 目录结构

```
pages/
└── {module}/
    ├── api/                    # API 文件
    │   ├── get{Module}List.js
    │   ├── get{Module}Detail.js
    │   ├── create{Module}.js
    │   ├── update{Module}.js
    │   └── delete{Module}.js
    ├── components/             # 页面专属组件
    │   ├── {Module}Card.vue
    │   └── {Module}Filter.vue
    ├── index.vue               # 列表页
    └── sub/                    # 子页面
        ├── detail/
        │   └── index.vue       # 详情页
        └── add/
            └── index.vue       # 新增/编辑页
```

---

## 组件使用

### 项目封装组件（优先使用）

| 组件 | 说明 |
|-----|------|
| `<TtAvatar>` | 头像，自动生成背景色和首字 |
| `<TtDialog>` | 对话框，黑色确认按钮风格 |
| `<TtTabbar>` | 底部导航栏 |
| `<TtSvg>` | SVG 图标，支持渐变 |
| `<TtInput>` | 输入框，支持插槽 |
| `<TtBottomPlaceholder>` | 底部留白（必须） |
| `<TtSafeBottom>` | 安全区域占位 |

### sard-uniapp 常用组件

| 组件 | 用途 |
|-----|------|
| `<sar-button>` | 按钮 |
| `<sar-input>` | 输入框 |
| `<sar-list>` / `<sar-list-item>` | 列表 |
| `<sar-popup>` | 弹出层 |
| `<sar-dialog>` | 对话框 |
| `<sar-toast-agent>` | Toast 代理 |
| `<sar-notify-agent>` | 通知代理 |
| `<sar-tabs>` | 标签页 |
| `<sar-empty>` | 空状态 |
| `<sar-tag>` | 标签 |
| `<sar-space>` | 间距 |
| `<sar-sticky>` | 粘性定位 |
| `<sar-form>` / `<sar-form-item>` | 表单 |
| `<sar-datetime-picker-popout>` | 日期选择器 |

---

## 禁止事项

1. **禁止使用 Emoji 图标**
   ```vue
   <!-- ❌ --> <text>🔵 张三</text>
   <!-- ✅ --> <TtSvg name="user" /> <text>张三</text>
   ```

2. **禁止直接导入 dayjs**
   ```javascript
   // ❌ import dayjs from 'dayjs'
   // ✅ import { dayjs } from '@/utils/date'
   ```

3. **禁止使用 uni.showToast**
   ```javascript
   // ❌ uni.showToast({ title: '成功' })
   // ✅ toast.success('成功')
   ```

4. **禁止直接使用 uni.navigateTo**
   ```javascript
   // ❌ uni.navigateTo({ url: '/pages/xxx' })
   // ✅ goToXxx()  // 使用 route/index.js
   ```

5. **禁止使用不兼容的 CSS**
   - `position: sticky` → 使用 `<sar-sticky>`
   - `gap` → 使用 `<sar-space>` 或 margin
   - CSS 变量 `var()` → 使用 SCSS 变量

---

## 必须事项

1. **所有注释使用中文**

2. **所有页面添加底部留白**
   ```vue
   <TtBottomPlaceholder />
   ```

3. **页面引入全局样式**
   ```vue
   <style lang="scss">
   @import '@/styles/global.scss';
   </style>
   ```

4. **组件配置样式隔离**
   ```javascript
   export default {
     options: {
       virtualHost: true,
       styleIsolation: 'shared'
     }
   }
   ```

5. **API 文件包含完整类型定义**

6. **API 返回统一格式**
   ```javascript
   { success: boolean, data/list: any, error?: string }
   ```

7. **使用 checkEmasError 检查数据库操作**

8. **使用 requireAccountId 检查登录状态**

---

## 示例：生成课程模块

### 输入需求

```markdown
# 课程管理模块

## 功能描述
管理教师的课程信息

## 数据字段
- name: 课程名称（必填，字符串）
- duration: 课时时长（必填，数字，分钟）
- price: 单价（必填，数字，元）
- status: 状态（必填，枚举：active/inactive）

## 页面列表
- 课程列表页
- 课程详情页
- 新增课程页

## 功能点
1. 课程列表展示
2. 按状态筛选
3. 新增课程
4. 编辑课程
5. 删除课程
```

### 输出文件

```
pages/course/
├── api/
│   ├── getCourseList.js
│   ├── getCourseDetail.js
│   ├── createCourse.js
│   ├── updateCourse.js
│   └── deleteCourse.js
├── components/
│   └── CourseCard.vue
├── index.vue
└── sub/
    ├── detail/
    │   └── index.vue
    └── add/
        └── index.vue

route/index.js  (更新)
pages.json      (更新)
```

---

## 模板文件

本 Skill 目录下提供了完整的代码模板，位于 `templates/` 目录：

```
skills/uniapp-mp-generator/
├── SKILL.md                    # 本文件
├── default_config.json         # 默认配置
└── templates/                  # 代码模板
    ├── page/
    │   ├── list.vue            # 列表页模板
    │   ├── detail.vue          # 详情页模板
    │   └── form.vue            # 表单页模板
    ├── api/
    │   ├── getList.js          # 获取列表 API
    │   ├── getDetail.js        # 获取详情 API
    │   ├── create.js           # 创建 API
    │   ├── update.js           # 更新 API
    │   └── delete.js           # 删除 API
    ├── component/
    │   ├── Card.vue            # 卡片组件模板
    │   └── Filter.vue          # 筛选组件模板
    ├── store/
    │   └── index.js            # Store 模板
    └── schema/
        └── collection.js       # 集合定义模板
```

**使用方式**：生成代码时，读取对应模板文件，替换模板变量后输出。

### 模板变量说明

| 变量 | 说明 | 示例 |
|-----|------|------|
| `{{MODULE_NAME}}` | 模块名（PascalCase） | `Student` |
| `{{MODULE_NAME_LOWER}}` | 模块名（小写） | `student` |
| `{{MODULE_NAME_CN}}` | 模块中文名 | `学生` |
| `{{DATE}}` | 当前日期 | `2026-01-31` |
| `{{PREFIX}}` | 项目前缀 | `pkb` |
| `{{COLLECTION_NAME}}` | 集合常量名 | `STUDENTS` |
| `{{FIELDS}}` | 字段列表 | `[{name, type, description}]` |
