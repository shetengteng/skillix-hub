# uni-app 小程序代码生成器 Skill 设计文档

> **版本**: v1.0.0
> **创建日期**: 2026-01-31
> **作者**: AI Assistant
> **参考项目**: tt-paikebao-mp（排课宝）

## 一、Skill 概述

### 1.1 功能定位

这是一个基于 **tt-paikebao-mp** 项目代码风格的 uni-app 小程序代码生成器 Skill。用户提供需求文档后，AI 可以自动生成符合项目规范的：

- Vue3 页面组件
- API 接口文件
- Service 业务逻辑
- Pinia Store 状态管理
- 路由配置
- 云数据库 Schema

### 1.2 适用场景

- 基于 uni-app + Vue3 的微信小程序开发
- 使用阿里云 EMAS Serverless 作为后端
- 使用 sard-uniapp 作为 UI 组件库
- 采用 Shadcn 风格的设计系统

### 1.3 核心价值

1. **一致性保障**：生成的代码严格遵循项目规范
2. **效率提升**：从需求文档直接生成可用代码
3. **最佳实践**：内置分层架构、错误处理、类型定义等最佳实践
4. **减少沟通**：AI 已学习项目规范，无需反复说明

---

## 二、项目配置

### 2.1 核心配置项

新建项目时，需要在 `config/index.js` 中配置以下变量：

```javascript
// config/index.js
export const PROJECT_CONFIG = {
  // ============ 必填配置 ============
  
  // 项目前缀（用于数据库集合、云函数、存储路径等命名）
  // 建议使用项目名拼音首字母，如 "排课宝" -> "pkb"
  prefix: 'pkb',
  
  // 项目名称
  name: '排课宝',
  
  // 项目英文名（用于包名等）
  nameEn: 'paikebao',
  
  // ============ EMAS 配置 ============
  
  // EMAS 服务空间 ID
  emasSpaceId: 'mp-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
  
  // EMAS 客户端 ID
  emasClientId: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
  
  // EMAS 端点
  emasEndpoint: 'https://api.bspapp.com',
  
  // ============ 可选配置 ============
  
  // 版本号
  version: '1.0.0',
  
  // 是否开启调试模式
  debug: false,
}
```

### 2.2 配置使用示例

```javascript
// 在代码中使用配置
import { PROJECT_CONFIG } from '@/config/index'

// 数据库集合命名
const collectionName = `${PROJECT_CONFIG.prefix}-students`

// 云函数命名
const functionName = `${PROJECT_CONFIG.prefix}-sendSmsCode`

// 存储路径
const storagePath = `${PROJECT_CONFIG.prefix}/avatars/${userId}/${filename}`

// 本地存储 key
const storageKey = `${PROJECT_CONFIG.prefix}-account`
```

### 2.3 新项目初始化清单

创建新项目时，按以下步骤配置：

1. **修改 `config/index.js`**
   - 设置 `prefix`（项目前缀）
   - 设置 `name`（项目名称）
   - 配置 EMAS 相关参数

2. **修改 `manifest.json`**
   - 设置小程序 AppId
   - 设置应用名称

3. **修改 `pages.json`**
   - 设置导航栏标题

4. **创建 EMAS 服务空间**
   - 在阿里云控制台创建
   - 获取 spaceId 和 clientId

5. **创建数据库集合**
   - 使用配置的前缀创建集合

---

## 三、技术栈规范

### 2.1 核心技术栈

| 技术 | 版本/说明 | 用途 |
|-----|---------|------|
| uni-app | Vue3 模式 | 跨端小程序框架 |
| Vue | 3.x (Composition API) | 前端框架 |
| Pinia | 最新版 | 状态管理 |
| sard-uniapp | 1.25.x | UI 组件库 |
| dayjs | 1.11.x | 日期处理 |
| EMAS Serverless | 阿里云 | 云开发后端 |

### 2.2 目录结构规范

```
project-root/
├── cloud-emas/                 # EMAS 云开发层
│   ├── database/
│   │   ├── index.js           # SDK 初始化
│   │   ├── database.js        # CloudBase 风格封装
│   │   ├── schema.js          # 集合/函数常量 + 类型定义
│   │   └── error.js           # 错误处理
│   └── functions/             # 云函数
│
├── components/                 # 公共组件（Tt 前缀）
│   ├── TtAvatar.vue
│   ├── TtDialog.vue
│   └── ...
│
├── composables/               # Vue3 组合式函数
│   └── use{Name}.js
│
├── config/                    # 全局配置
│   ├── index.js
│   └── pages.js
│
├── pages/                     # 页面目录（分包结构）
│   └── {module}/
│       ├── api/               # 页面级 API（原子操作）
│       ├── service/           # 业务逻辑层（可选）
│       ├── components/        # 页面专属组件
│       ├── index.vue          # 主页面
│       └── sub/               # 子页面
│
├── plugins/                   # 插件配置
├── route/                     # 路由管理
├── stores/                    # Pinia 状态管理
├── static/                    # 静态资源
│   └── svg/                   # SVG 图标
├── styles/                    # 全局样式
│   └── global.scss
├── utils/                     # 工具函数
│
├── App.vue                    # 应用入口
├── main.js                    # 入口文件
├── manifest.json              # 应用配置
├── pages.json                 # 页面路由配置
└── uni.scss                   # SCSS 变量
```

---

## 四、代码风格规范

### 3.1 Vue 组件规范

#### 3.1.1 组件结构

```vue
<template>
  <view class="page bg-page">
    <!-- 页面内容 -->
    
    <!-- 底部留白（必须） -->
    <TtBottomPlaceholder />
  </view>
</template>

<script>
// 微信小程序组件选项（如需使用全局样式类）
export default {
  options: {
    virtualHost: true,
    styleIsolation: 'shared'
  }
}
</script>

<script setup>
// 1. Vue 核心
import { ref, computed, onMounted } from 'vue'

// 2. uni-app 生命周期
import { onShow, onLoad } from '@dcloudio/uni-app'

// 3. 工具函数
import { dayjs, formatDate } from '@/utils/date'
import { notify } from '@/utils/notify'

// 4. 组件
import TtBottomPlaceholder from '@/components/TtBottomPlaceholder.vue'

// 5. 路由/Store
import { goToXxx } from '@/route/index'
import { useXxxStore } from '@/stores/xxx'

// 6. API
import { getXxxList } from './api/getXxxList'

// ============ 响应式数据 ============
const loading = ref(false)
const list = ref([])

// ============ 计算属性 ============
const isEmpty = computed(() => list.value.length === 0)

// ============ 生命周期 ============
onLoad((options) => {
  // 页面加载
})

onShow(() => {
  // 页面显示
  loadData()
})

// ============ 方法 ============
/**
 * 加载数据
 */
const loadData = async () => {
  loading.value = true
  try {
    const res = await getXxxList()
    if (res.success) {
      list.value = res.list
    }
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss">
@import '@/styles/global.scss';
</style>
```

#### 3.1.2 Props 定义

```javascript
const props = defineProps({
  // 必填属性
  id: {
    type: String,
    required: true
  },
  // 可选属性（带默认值）
  size: {
    type: String,
    default: '56rpx'
  },
  // 布尔属性
  disabled: {
    type: Boolean,
    default: false
  },
  // 对象属性
  data: {
    type: Object,
    default: () => ({})
  }
})
```

#### 3.1.3 Emits 定义

```javascript
const emit = defineEmits(['update:visible', 'confirm', 'cancel'])

// 双向绑定实现
const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})
```

### 3.2 API 文件规范

#### 3.2.1 文件结构

```javascript
/**
 * 获取学生列表
 * @module pages/student/api/getStudentList
 * @since 2026-01-31
 */

import { db, COLLECTIONS } from '@/cloud-emas/database/database'
import { checkEmasError } from '@/cloud-emas/database/error'
import { requireAccountId } from '@/utils/auth'

/**
 * 学生列表项数据结构
 * @typedef {Object} StudentItem
 * @property {string} _id - 学生ID
 * @property {string} name - 学生姓名
 * @property {string} phone - 联系电话
 * @property {StudentStatus} status - 状态
 * @property {number} remainingHours - 剩余课时
 * @property {string} createTime - 创建时间
 */

/**
 * 学生状态枚举
 * @typedef {'active'|'inactive'|'graduated'} StudentStatus
 */

/**
 * 获取学生列表
 * @param {Object} params - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.pageSize=20] - 每页数量
 * @param {StudentStatus} [params.status] - 状态筛选
 * @returns {Promise<{success: boolean, list: StudentItem[], error?: string}>}
 */
export async function getStudentList(params = {}) {
  try {
    const accountId = requireAccountId()
    if (!accountId) {
      return { success: false, list: [], error: '未登录' }
    }
    
    const { page = 1, pageSize = 20, status } = params
    
    let query = db.collection(COLLECTIONS.STUDENTS)
      .where({ accountId })
    
    if (status) {
      query = query.where({ status })
    }
    
    const res = await query
      .orderBy('createTime', 'desc')
      .skip((page - 1) * pageSize)
      .limit(pageSize)
      .get()
    
    checkEmasError(res, '获取学生列表')
    
    return {
      success: true,
      list: res.data || []
    }
  } catch (error) {
    console.error('[getStudentList] 失败:', error)
    return { success: false, list: [], error: error.message }
  }
}

export default getStudentList
```

#### 3.2.2 命名规范

| 操作类型 | 命名格式 | 示例 |
|---------|---------|------|
| 查询列表 | `get{Entity}List.js` | `getStudentList.js` |
| 查询详情 | `get{Entity}Detail.js` | `getStudentDetail.js` |
| 按条件查找 | `find{Entity}By{Field}.js` | `findUserByPhone.js` |
| 创建 | `create{Entity}.js` | `createStudent.js` |
| 更新 | `update{Entity}.js` | `updateStudent.js` |
| 删除 | `delete{Entity}.js` | `deleteStudent.js` |
| 特定操作 | `{action}{Entity}.js` | `adjustStudentHours.js` |

### 3.3 Store 规范

```javascript
/**
 * 学生状态管理
 * @module stores/student
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchStudentList } from './api/fetchStudentList'

export const useStudentStore = defineStore('student', () => {
  // ============ 状态 ============
  const students = ref([])
  const loading = ref(false)
  const loaded = ref(false)
  
  // ============ 计算属性 ============
  const studentCount = computed(() => students.value.length)
  
  // ============ 方法 ============
  
  /**
   * 加载学生列表
   * @param {boolean} [force=false] - 是否强制刷新
   */
  const loadStudents = async (force = false) => {
    if (loaded.value && !force) return
    
    loading.value = true
    try {
      const res = await fetchStudentList()
      if (res.success) {
        students.value = res.list
        loaded.value = true
      }
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 根据 ID 获取学生
   * @param {string} id - 学生ID
   * @returns {Object|null}
   */
  const getStudentById = (id) => {
    return students.value.find(s => s._id === id) || null
  }
  
  /**
   * 添加学生到缓存
   * @param {Object} student - 学生数据
   */
  const addStudent = (student) => {
    students.value.unshift(student)
  }
  
  /**
   * 更新缓存中的学生
   * @param {string} id - 学生ID
   * @param {Object} data - 更新数据
   */
  const updateStudent = (id, data) => {
    const index = students.value.findIndex(s => s._id === id)
    if (index !== -1) {
      students.value[index] = { ...students.value[index], ...data }
    }
  }
  
  /**
   * 从缓存中删除学生
   * @param {string} id - 学生ID
   */
  const removeStudent = (id) => {
    const index = students.value.findIndex(s => s._id === id)
    if (index !== -1) {
      students.value.splice(index, 1)
    }
  }
  
  /**
   * 重置状态
   */
  const reset = () => {
    students.value = []
    loaded.value = false
  }
  
  return {
    // 状态
    students,
    loading,
    loaded,
    // 计算属性
    studentCount,
    // 方法
    loadStudents,
    getStudentById,
    addStudent,
    updateStudent,
    removeStudent,
    reset
  }
}, {
  persist: {
    key: 'pkb-student',
    paths: ['students']
  }
})
```

### 3.4 路由配置规范

```javascript
/**
 * 路由配置
 * @module route/index
 */

// ============ 路由路径定义 ============
export const routes = {
  // 主包
  home: '/pages/home/index',
  
  // 登录分包
  login: '/pages/login/index',
  
  // 学生分包
  student: '/pages/student/index',
  studentDetail: '/pages/student/sub/detail/index',
  studentAdd: '/pages/student/sub/add/index',
  
  // 设置分包
  settings: '/pages/settings/index',
}

// ============ 白名单（无需登录） ============
export const WHITE_LIST = [
  routes.home,
  routes.login,
  '/pages/agreement'  // 前缀匹配
]

// ============ 跳转方法 ============

/**
 * 跳转到学生详情
 * @param {string} id - 学生ID
 */
export function goToStudentDetail(id) {
  uni.navigateTo({
    url: `${routes.studentDetail}?id=${id}`
  })
}

/**
 * 跳转到新增学生
 */
export function goToStudentAdd() {
  uni.navigateTo({
    url: routes.studentAdd
  })
}

/**
 * 切换 Tab
 * @param {'home'|'student'|'settings'} tab - Tab 名称
 */
export function switchTab(tab) {
  const tabRoutes = {
    home: routes.home,
    student: routes.student,
    settings: routes.settings
  }
  uni.reLaunch({
    url: tabRoutes[tab] || routes.home
  })
}

/**
 * 返回上一页
 * @param {number} [delta=1] - 返回层数
 */
export function goBack(delta = 1) {
  uni.navigateBack({ delta })
}

/**
 * 检查是否在白名单
 * @param {string} path - 页面路径
 * @returns {boolean}
 */
export function isInWhiteList(path) {
  return WHITE_LIST.some(p => path.startsWith(p))
}
```

---

## 五、样式规范

### 4.1 设计系统（Shadcn 风格）

#### 4.1.1 颜色变量

```scss
// 背景与前景
$tt-background: #ffffff;        // 主背景
$tt-foreground: #0a0a0a;       // 主前景/文字
$tt-card: #ffffff;             // 卡片背景
$tt-muted: #f5f5f5;           // 柔和背景
$tt-accent: #f5f5f5;          // 强调背景

// 主色与次级色
$tt-primary: #171717;          // 主色（接近黑色）
$tt-primary-foreground: #fafafa;
$tt-secondary: #f5f5f5;
$tt-secondary-foreground: #171717;
$tt-muted-foreground: #737373; // 次要文字

// 边框
$tt-border: #e5e5e5;
$tt-input: #e5e5e5;
$tt-ring: #0a0a0a;

// 功能色
$tt-success: #10b981;
$tt-warning: #f59e0b;
$tt-error: #ef4444;
```

#### 4.1.2 间距变量

```scss
$tt-spacing-xs: 8rpx;
$tt-spacing-sm: 16rpx;
$tt-spacing-md: 24rpx;
$tt-spacing-lg: 32rpx;
$tt-spacing-xl: 48rpx;
```

#### 4.1.3 圆角变量

```scss
$tt-radius-sm: 6rpx;
$tt-radius-md: 12rpx;
$tt-radius-lg: 16rpx;
$tt-radius-xl: 24rpx;
```

### 4.2 全局工具类

| 类型 | 工具类 | 说明 |
|-----|--------|------|
| Flex 布局 | `flex-row` `flex-col` `flex-center` `flex-between` | 弹性布局 |
| 文字大小 | `text-xs` `text-sm` `text-base` `text-lg` `text-xl` | 22-44rpx |
| 文字粗细 | `font-normal` `font-medium` `font-semibold` `font-bold` | 400-700 |
| 文字颜色 | `text-foreground` `text-muted` `text-success` `text-error` | 语义色 |
| 背景色 | `bg-background` `bg-card` `bg-muted` `bg-accent` | 分层背景 |
| 边框 | `border` `border-t` `border-b` | 边框（替代阴影） |
| 圆角 | `rounded-sm` `rounded-md` `rounded-lg` `rounded-xl` | 6-24rpx |
| 间距 | `m-sm` `p-lg` `mt-md` `px-lg` | 外边距/内边距 |

### 4.3 样式使用优先级

1. **sard-uniapp 组件** - 首选
2. **sard 布局组件** - `sar-row`/`sar-col`/`sar-space`
3. **全局工具类** - `flex-row`、`p-lg` 等
4. **组件的 root-style** - 微调
5. **自定义样式** - 几乎禁止

### 4.4 微信小程序兼容性

**禁止使用**：
- `position: sticky` → 使用 `<sar-sticky>`
- `gap` 属性 → 使用 `<sar-space>` 或 margin
- CSS 变量 `var()` → 使用 SCSS 变量
- `display: grid` → 使用 `<sar-row>/<sar-col>`
- `backdrop-filter` → 不使用毛玻璃

---

## 六、数据库规范

### 5.1 集合命名

所有集合使用**项目前缀**，前缀通过配置文件定义：

```javascript
// config/index.js - 项目配置
export const PROJECT_CONFIG = {
  // 项目前缀（用于数据库集合、云函数等命名）
  prefix: 'pkb',
  
  // 其他配置...
}
```

```javascript
// cloud-emas/database/schema.js - 集合定义
import { PROJECT_CONFIG } from '@/config/index'

const PREFIX = PROJECT_CONFIG.prefix

export const COLLECTIONS = {
  ACCOUNTS: `${PREFIX}-accounts`,
  STUDENTS: `${PREFIX}-students`,
  COURSES: `${PREFIX}-courses`,
  PURCHASES: `${PREFIX}-purchases`,
  ATTENDANCES: `${PREFIX}-attendances`,
  SETTINGS: `${PREFIX}-settings`
}

// 云函数命名也使用相同前缀
export const FUNCTIONS = {
  SEND_SMS_CODE: `${PREFIX}-sendSmsCode`,
  VERIFY_SMS_CODE: `${PREFIX}-verifySmsCode`,
  // ...
}
```

**使用新项目时**，只需修改 `config/index.js` 中的 `prefix` 值即可：

```javascript
// 示例：新项目 "课程助手" 使用 "kczs" 前缀
export const PROJECT_CONFIG = {
  prefix: 'kczs',  // 修改这里
}

// 集合将自动变为：kczs-accounts, kczs-students, ...
```

### 5.2 数据结构定义

使用 JSDoc `@typedef` 定义：

```javascript
/**
 * 学生数据结构
 * @typedef {Object} Student
 * @property {string} _id - 学生ID（系统生成）
 * @property {string} accountId - 所属教师账户ID
 * @property {string} name - 学生姓名
 * @property {string} [phone] - 联系电话（可选）
 * @property {string} [avatar] - 头像URL（可选）
 * @property {StudentStatus} status - 状态
 * @property {number} remainingHours - 剩余课时
 * @property {number} totalPurchased - 已购课时总数
 * @property {number} totalConsumed - 已消耗课时总数
 * @property {string} createTime - 创建时间（ISO 8601）
 * @property {string} updateTime - 更新时间（ISO 8601）
 */

/**
 * 学生状态
 * @typedef {'active'|'inactive'|'graduated'} StudentStatus
 * - active: 在读
 * - inactive: 暂停
 * - graduated: 结业
 */
```

### 5.3 通用字段

所有业务数据必须包含：

| 字段 | 类型 | 说明 |
|-----|------|------|
| `_id` | string | 系统生成的唯一ID |
| `accountId` | string | 所属用户ID |
| `createTime` | string | 创建时间（ISO 8601） |
| `updateTime` | string | 更新时间（ISO 8601） |

---

## 七、组件使用规范

### 6.1 项目封装组件（优先使用）

| 组件 | 说明 | 替代 |
|-----|------|------|
| `<TtAvatar>` | 头像，自动生成背景色和首字 | `sar-avatar` |
| `<TtDialog>` | 对话框，黑色确认按钮风格 | `sar-dialog` |
| `<TtTabbar>` | 底部导航栏 | `sar-tabbar` |
| `<TtSvg>` | SVG 图标，支持渐变 | `sar-icon` |
| `<TtInput>` | 输入框，支持插槽 | `sar-input` |
| `<TtBottomPlaceholder>` | 底部留白 | - |
| `<TtSafeBottom>` | 安全区域占位 | - |

### 6.2 sard-uniapp 常用组件

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

### 6.3 图标使用

**禁止使用 Emoji**，统一使用 TtSvg 或 sar-icon：

```vue
<!-- ❌ 禁止 -->
<text>🔵 张三</text>

<!-- ✅ 正确 -->
<TtSvg name="user" :size="40" color="#333" />
<text>张三</text>
```

---

## 八、Skill 使用流程

### 7.1 输入格式

用户提供需求文档，格式建议：

```markdown
# 功能模块名称

## 功能描述
简要描述该模块的功能

## 数据结构
列出需要的数据字段

## 页面列表
- 页面1：描述
- 页面2：描述

## 功能点
1. 功能点1
2. 功能点2

## 交互说明
描述用户交互流程
```

### 7.2 输出内容

AI 将生成：

1. **数据库 Schema**
   - 集合定义
   - 字段类型定义（JSDoc）
   - 索引建议

2. **API 文件**
   - CRUD 操作
   - 特殊业务操作
   - 完整的类型注释

3. **页面组件**
   - 列表页
   - 详情页
   - 新增/编辑页
   - 页面专属组件

4. **Store 文件**（如需要）
   - 状态定义
   - 缓存管理
   - 业务方法

5. **路由配置**
   - 路由路径
   - 跳转方法

6. **pages.json 配置**
   - 分包配置
   - 页面配置

### 7.3 生成示例

**输入**：
```
创建一个课程管理模块，包含：
- 课程列表（支持筛选）
- 课程详情
- 新增课程
- 编辑课程
```

**输出**：
- `pages/course/api/getCourseList.js`
- `pages/course/api/getCourseDetail.js`
- `pages/course/api/createCourse.js`
- `pages/course/api/updateCourse.js`
- `pages/course/api/deleteCourse.js`
- `pages/course/index.vue`（列表页）
- `pages/course/components/CourseCard.vue`
- `pages/course/components/CourseFilter.vue`
- `pages/course/sub/detail/index.vue`
- `pages/course/sub/add/index.vue`
- `route/index.js`（更新）
- `pages.json`（更新）

---

## 九、注意事项

### 8.1 必须遵守

1. **中文注释**：所有代码注释使用中文
2. **类型定义**：API 文件必须包含完整的 JSDoc 类型定义
3. **错误处理**：使用 `checkEmasError` 检查数据库操作
4. **路由管理**：禁止直接使用 `uni.navigateTo`，使用 `route/index.js`
5. **底部留白**：所有页面必须添加 `<TtBottomPlaceholder>`
6. **样式引入**：页面必须引入 `@import '@/styles/global.scss'`

### 8.2 禁止行为

1. ❌ 使用 Emoji 图标
2. ❌ 直接导入 dayjs（使用 `@/utils/date`）
3. ❌ 使用 `uni.showToast`（使用 sard toast）
4. ❌ 编写自定义样式（优先使用组件和工具类）
5. ❌ 使用不兼容的 CSS 特性（sticky、gap、var()等）

### 8.3 最佳实践

1. ✅ 优先使用项目封装组件
2. ✅ API 文件原子化设计
3. ✅ 使用 Store 缓存减少请求
4. ✅ 正向逻辑卫语句
5. ✅ 组件内聚（导航、交互逻辑内聚）

---

## 十、扩展计划

### 9.1 Phase 1（当前）
- 基础代码生成
- 页面模板生成
- API 文件生成

### 9.2 Phase 2（计划）
- 云函数模板生成
- 测试用例生成
- 文档自动生成

### 9.3 Phase 3（未来）
- 可视化配置界面
- 代码质量检查
- 自动化部署脚本

---

## 十一、模板文件

Skill 目录下提供了完整的代码模板，位于 `skills/uniapp-mp-generator/templates/`：

### 11.1 目录结构

```
skills/uniapp-mp-generator/
├── SKILL.md                    # Skill 入口文件
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

### 11.2 模板变量

| 变量 | 说明 | 示例 |
|-----|------|------|
| `{{MODULE_NAME}}` | 模块名（PascalCase） | `Student` |
| `{{MODULE_NAME_LOWER}}` | 模块名（小写） | `student` |
| `{{MODULE_NAME_CN}}` | 模块中文名 | `学生` |
| `{{DATE}}` | 当前日期 | `2026-01-31` |
| `{{PREFIX}}` | 项目前缀 | `pkb` |
| `{{COLLECTION_NAME}}` | 集合常量名 | `STUDENTS` |
| `{{FIELDS}}` | 字段列表 | `[{name, type, description}]` |
| `{{REQUIRED_FIELDS}}` | 必填字段 | `[...]` |
| `{{OPTIONAL_FIELDS}}` | 可选字段 | `[...]` |
| `{{HAS_STATUS}}` | 是否有状态字段 | `true/false` |
| `{{HAS_FILTER}}` | 是否有筛选功能 | `true/false` |

### 11.3 使用方式

生成代码时：
1. 读取对应模板文件
2. 解析用户需求，提取模板变量值
3. 替换模板中的变量
4. 输出生成的代码

---

## 十二、参考资料

- [uni-app 官方文档](https://uniapp.dcloud.net.cn/)
- [Vue3 官方文档](https://cn.vuejs.org/)
- [sard-uniapp 组件库](https://sard.wzt.zone/sard-uniapp-docs/)
- [阿里云 EMAS 文档](https://help.aliyun.com/product/434942.html)
- [Shadcn/ui 设计系统](https://ui.shadcn.com/)
