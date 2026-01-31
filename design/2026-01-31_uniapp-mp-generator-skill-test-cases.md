# uni-app 小程序代码生成器 Skill 测试用例文档

> **版本**: v1.0.0
> **创建日期**: 2026-01-31
> **关联设计文档**: 2026-01-31_uniapp-mp-generator-skill-design.md
> **关联实施文档**: 2026-01-31_uniapp-mp-generator-skill-implementation.md

## 一、测试概述

### 1.1 测试目标

验证 uni-app 小程序代码生成器 Skill 能够：
1. 正确理解用户需求文档
2. 生成符合项目规范的代码
3. 生成的代码可直接运行
4. 覆盖各种常见场景

### 1.2 测试范围

| 测试类型 | 说明 |
|---------|------|
| 功能测试 | 验证各类代码生成功能 |
| 规范测试 | 验证生成代码符合规范 |
| 边界测试 | 验证特殊情况处理 |
| 集成测试 | 验证多模块协同 |

---

## 二、测试用例

### 2.1 TC-001：基础模块生成

**测试目标**：验证基础 CRUD 模块的完整生成

**输入需求**：
```markdown
# 课程管理模块

## 功能描述
管理教师的课程信息，包括课程名称、时长、价格等。

## 数据字段
- name: 课程名称（必填，字符串）
- duration: 课时时长（必填，数字，单位分钟）
- price: 单价（必填，数字，单位元）
- description: 课程描述（可选，字符串）
- status: 状态（必填，枚举：active/inactive）

## 页面列表
- 课程列表页：显示所有课程，支持搜索和状态筛选
- 课程详情页：显示课程详细信息
- 新增课程页：表单页面，创建新课程
- 编辑课程页：表单页面，编辑现有课程

## 功能点
1. 课程列表展示
2. 按名称搜索
3. 按状态筛选
4. 新增课程
5. 编辑课程
6. 删除课程
```

**预期输出**：

| 文件 | 说明 |
|-----|------|
| `pages/course/api/getCourseList.js` | 获取课程列表 API |
| `pages/course/api/getCourseDetail.js` | 获取课程详情 API |
| `pages/course/api/createCourse.js` | 创建课程 API |
| `pages/course/api/updateCourse.js` | 更新课程 API |
| `pages/course/api/deleteCourse.js` | 删除课程 API |
| `pages/course/index.vue` | 课程列表页 |
| `pages/course/components/CourseCard.vue` | 课程卡片组件 |
| `pages/course/sub/detail/index.vue` | 课程详情页 |
| `pages/course/sub/add/index.vue` | 新增课程页 |
| `route/index.js` | 路由配置更新 |

**验证点**：
- [ ] API 文件包含完整的 JSDoc 类型定义
- [ ] API 返回格式为 `{ success, list/data, error? }`
- [ ] 页面使用 `<script setup>` 语法
- [ ] 页面包含 `<TtBottomPlaceholder>` 组件
- [ ] 样式引入 `@import '@/styles/global.scss'`
- [ ] 使用全局工具类而非自定义样式
- [ ] 路由使用 `route/index.js` 中的方法

---

### 2.2 TC-002：带关联关系的模块

**测试目标**：验证带外键关联的模块生成

**输入需求**：
```markdown
# 购课记录模块

## 功能描述
记录学生的购课信息，关联学生和课程。

## 数据字段
- studentId: 学生ID（必填，关联 students 集合）
- courseId: 课程ID（必填，关联 courses 集合）
- hours: 购买课时数（必填，数字）
- amount: 支付金额（必填，数字）
- paymentMethod: 支付方式（必填，枚举：cash/wechat/alipay/transfer）
- note: 备注（可选，字符串）
- purchaseDate: 购课日期（必填，日期）

## 页面列表
- 购课记录列表：按学生筛选，显示购课历史
- 购课详情页：显示购课详细信息
- 新增购课页：选择学生和课程，填写购课信息

## 功能点
1. 按学生查看购课记录
2. 新增购课记录
3. 查看购课详情
4. 计算单价（金额/课时）
```

**预期输出**：

| 文件 | 说明 |
|-----|------|
| `pages/purchase/api/getPurchaseList.js` | 获取购课列表（支持 studentId 筛选） |
| `pages/purchase/api/getPurchaseDetail.js` | 获取购课详情 |
| `pages/purchase/api/createPurchase.js` | 创建购课记录 |
| `pages/purchase/index.vue` | 购课列表页 |
| `pages/purchase/components/PurchaseCard.vue` | 购课卡片组件 |
| `pages/purchase/sub/detail/index.vue` | 购课详情页 |
| `pages/purchase/sub/add/index.vue` | 新增购课页 |

**验证点**：
- [ ] API 支持 studentId 参数筛选
- [ ] 新增页面包含学生选择器
- [ ] 新增页面包含课程选择器
- [ ] 自动计算单价字段
- [ ] 支付方式使用 `<sar-radio-group>` 组件
- [ ] 日期选择使用 `<sar-datetime-picker>` 组件

---

### 2.3 TC-003：复杂列表页

**测试目标**：验证带多种筛选和排序的列表页

**输入需求**：
```markdown
# 考勤记录模块

## 功能描述
记录学生的上课考勤情况。

## 数据字段
- studentId: 学生ID（必填）
- courseId: 课程ID（必填）
- date: 上课日期（必填）
- startTime: 开始时间（必填）
- endTime: 结束时间（必填）
- hours: 消耗课时（必填）
- status: 考勤状态（必填，枚举：normal/late/absent/leave）
- note: 备注（可选）

## 页面列表
- 考勤列表页：支持日期范围筛选、学生筛选、状态筛选

## 功能点
1. 按日期范围筛选
2. 按学生筛选
3. 按状态筛选
4. 统计出勤率
```

**预期输出**：

| 文件 | 说明 |
|-----|------|
| `pages/attendance/api/getAttendanceList.js` | 获取考勤列表（多条件筛选） |
| `pages/attendance/api/getAttendanceStats.js` | 获取考勤统计 |
| `pages/attendance/index.vue` | 考勤列表页 |
| `pages/attendance/components/AttendanceCard.vue` | 考勤卡片组件 |
| `pages/attendance/components/AttendanceFilter.vue` | 筛选组件 |
| `pages/attendance/components/AttendanceStats.vue` | 统计组件 |

**验证点**：
- [ ] API 支持日期范围参数（startDate, endDate）
- [ ] API 支持多条件组合筛选
- [ ] 筛选组件使用 `<sar-popup>` 弹出
- [ ] 日期范围使用 `<sar-calendar>` 组件
- [ ] 状态筛选使用 `<sar-tag>` 组件
- [ ] 统计数据展示使用卡片布局

---

### 2.4 TC-004：表单页面

**测试目标**：验证复杂表单页面的生成

**输入需求**：
```markdown
# 学生信息表单

## 功能描述
新增和编辑学生信息。

## 表单字段
- name: 姓名（必填，文本输入）
- phone: 手机号（可选，手机号格式验证）
- avatar: 头像（可选，图片上传）
- gender: 性别（可选，单选：male/female）
- birthday: 生日（可选，日期选择）
- tags: 标签（可选，多选标签）
- note: 备注（可选，多行文本）

## 功能点
1. 表单验证
2. 图片上传
3. 编辑模式回显数据
```

**预期输出**：

| 文件 | 说明 |
|-----|------|
| `pages/student/sub/add/index.vue` | 新增/编辑学生页 |
| `pages/student/api/uploadAvatar.js` | 头像上传 API |

**验证点**：
- [ ] 使用 `<sar-form>` 和 `<sar-form-item>` 组件
- [ ] 必填字段有验证规则
- [ ] 手机号有格式验证
- [ ] 头像使用 `<TtAvatar>` 组件预览
- [ ] 图片上传使用 `uni.chooseImage`
- [ ] 性别使用 `<sar-radio-group>` 组件
- [ ] 生日使用 `<sar-datetime-picker-popout>` 组件
- [ ] 标签使用 `<sar-tag>` 多选
- [ ] 备注使用 `<sar-textarea>` 组件
- [ ] 编辑模式通过 URL 参数传递 id
- [ ] 编辑模式自动加载并回显数据

---

### 2.5 TC-005：Store 状态管理

**测试目标**：验证 Store 文件的生成

**输入需求**：
```markdown
# 教室管理模块

## 功能描述
管理教室信息，需要全局缓存。

## 数据字段
- name: 教室名称（必填）
- capacity: 容量（必填）
- location: 位置（可选）
- status: 状态（必填，枚举：available/occupied/maintenance）

## 需求
- 需要全局 Store 缓存教室列表
- 多个页面共享教室数据
- 支持按 ID 快速查找
```

**预期输出**：

| 文件 | 说明 |
|-----|------|
| `stores/classroom/index.js` | 教室 Store |
| `stores/classroom/api/fetchClassroomList.js` | Store 专用 API |

**验证点**：
- [ ] Store 使用 `defineStore` 定义
- [ ] 包含 `classrooms` 响应式数组
- [ ] 包含 `loading` 和 `loaded` 状态
- [ ] 包含 `loadClassrooms` 方法（支持 force 参数）
- [ ] 包含 `getClassroomById` 方法
- [ ] 包含 `addClassroom`、`updateClassroom`、`removeClassroom` 方法
- [ ] 包含 `reset` 方法
- [ ] 配置持久化（persist）

---

### 2.6 TC-006：路由配置

**测试目标**：验证路由配置的生成和更新

**输入需求**：
```markdown
# 新增模块路由

模块名：notification（通知）
页面：
- 通知列表页：/pages/notification/index
- 通知详情页：/pages/notification/sub/detail/index
```

**预期输出**：

更新 `route/index.js`：

```javascript
// 路由路径
export const routes = {
  // ... 现有路由
  notification: '/pages/notification/index',
  notificationDetail: '/pages/notification/sub/detail/index',
}

// 跳转方法
export function goToNotification() {
  uni.navigateTo({ url: routes.notification })
}

export function goToNotificationDetail(id) {
  uni.navigateTo({ url: `${routes.notificationDetail}?id=${id}` })
}
```

**验证点**：
- [ ] 路由路径添加到 `routes` 对象
- [ ] 生成对应的跳转方法
- [ ] 方法命名符合 `goTo{PageName}` 规范
- [ ] 详情页方法接收 id 参数

---

### 2.7 TC-007：pages.json 配置

**测试目标**：验证 pages.json 配置的生成

**输入需求**：
```markdown
# 新增分包配置

分包名：notification
页面：
- index：通知列表（自定义导航栏）
- sub/detail/index：通知详情
```

**预期输出**：

更新 `pages.json`：

```json
{
  "subPackages": [
    // ... 现有分包
    {
      "root": "pages/notification",
      "pages": [
        {
          "path": "index",
          "style": {
            "navigationStyle": "custom"
          }
        },
        {
          "path": "sub/detail/index",
          "style": {
            "navigationBarTitleText": "通知详情"
          }
        }
      ]
    }
  ]
}
```

**验证点**：
- [ ] 分包配置正确
- [ ] 页面路径正确
- [ ] 自定义导航栏配置正确
- [ ] 页面标题配置正确

---

### 2.8 TC-008：数据库 Schema

**测试目标**：验证数据库 Schema 定义的生成

**输入需求**：
```markdown
# 订单集合定义

集合名：orders
字段：
- studentId: 学生ID（必填，string）
- items: 订单项（必填，array）
- totalAmount: 总金额（必填，number）
- status: 状态（必填，枚举：pending/paid/cancelled/refunded）
- payTime: 支付时间（可选，string）
- refundTime: 退款时间（可选，string）
```

**预期输出**：

```javascript
// cloud-emas/database/schema.js 更新

/**
 * 订单数据结构
 * @typedef {Object} Order
 * @property {string} _id - 订单ID（系统生成）
 * @property {string} accountId - 所属用户ID
 * @property {string} studentId - 学生ID
 * @property {OrderItem[]} items - 订单项
 * @property {number} totalAmount - 总金额（单位：元）
 * @property {OrderStatus} status - 订单状态
 * @property {string} [payTime] - 支付时间
 * @property {string} [refundTime] - 退款时间
 * @property {string} createTime - 创建时间
 * @property {string} updateTime - 更新时间
 */

/**
 * 订单状态枚举
 * @typedef {'pending'|'paid'|'cancelled'|'refunded'} OrderStatus
 * - pending: 待支付
 * - paid: 已支付
 * - cancelled: 已取消
 * - refunded: 已退款
 */

// COLLECTIONS 更新
export const COLLECTIONS = {
  // ... 现有集合
  ORDERS: `${PREFIX}-orders`,
}
```

**验证点**：
- [ ] 使用 JSDoc @typedef 定义类型
- [ ] 包含所有字段及说明
- [ ] 可选字段使用 `[fieldName]` 标记
- [ ] 枚举类型单独定义
- [ ] 枚举值有中文说明
- [ ] 集合名使用项目前缀

---

## 三、规范验证测试

### 3.1 TC-101：代码风格验证

**验证项**：

| 项目 | 预期 | 验证方法 |
|-----|------|---------|
| 注释语言 | 中文 | 检查所有注释 |
| 组件结构 | template > script > script setup > style | 检查文件结构 |
| 响应式数据 | 使用 ref | 检查变量定义 |
| Props 定义 | 对象式，有类型和默认值 | 检查 defineProps |
| 方法注释 | JSDoc 格式 | 检查方法注释 |

### 3.2 TC-102：命名规范验证

**验证项**：

| 项目 | 预期 | 验证方法 |
|-----|------|---------|
| 组件文件 | PascalCase | 检查文件名 |
| API 文件 | camelCase | 检查文件名 |
| 变量命名 | camelCase | 检查变量名 |
| 常量命名 | UPPER_SNAKE_CASE | 检查常量名 |
| 集合命名 | {prefix}-{name}s | 检查集合名 |

### 3.3 TC-103：样式规范验证

**验证项**：

| 项目 | 预期 | 验证方法 |
|-----|------|---------|
| 样式引入 | `@import '@/styles/global.scss'` | 检查 style 块 |
| 工具类使用 | 优先使用全局工具类 | 检查 class 属性 |
| 自定义样式 | 几乎没有 | 检查 style 块内容 |
| 组件使用 | 优先使用 sard/Tt 组件 | 检查 template |
| 图标使用 | 使用 TtSvg/sar-icon | 检查图标组件 |

### 3.4 TC-104：API 规范验证

**验证项**：

| 项目 | 预期 | 验证方法 |
|-----|------|---------|
| 返回格式 | `{ success, data/list, error? }` | 检查返回语句 |
| 错误处理 | try-catch + checkEmasError | 检查错误处理 |
| 类型定义 | JSDoc @typedef | 检查注释 |
| 认证检查 | requireAccountId | 检查认证调用 |

---

## 四、边界测试

### 4.1 TC-201：空需求处理

**输入**：空的需求文档或不完整的需求

**预期**：
- 提示用户补充必要信息
- 不生成不完整的代码

### 4.2 TC-202：特殊字符处理

**输入**：字段名包含特殊字符（如中文、空格）

**预期**：
- 自动转换为合法的变量名
- 保留原始名称作为注释

### 4.3 TC-203：重复模块处理

**输入**：请求生成已存在的模块

**预期**：
- 提示模块已存在
- 询问是否覆盖或合并

### 4.4 TC-204：大量字段处理

**输入**：包含 20+ 字段的数据结构

**预期**：
- 正确生成所有字段
- 表单页面合理分组

---

## 五、集成测试

### 5.1 TC-301：完整模块集成

**测试目标**：验证生成的完整模块可以正常运行

**步骤**：
1. 使用 Skill 生成完整的课程管理模块
2. 将生成的代码复制到项目中
3. 配置 pages.json 和路由
4. 运行项目，测试各功能

**验证点**：
- [ ] 页面可正常加载
- [ ] 列表数据可正常显示
- [ ] 搜索和筛选功能正常
- [ ] 新增功能正常
- [ ] 编辑功能正常
- [ ] 删除功能正常
- [ ] 路由跳转正常

### 5.2 TC-302：多模块协同

**测试目标**：验证多个模块之间的数据关联

**步骤**：
1. 生成学生模块
2. 生成课程模块
3. 生成购课记录模块（关联学生和课程）
4. 测试数据关联是否正确

**验证点**：
- [ ] 购课记录可正确关联学生
- [ ] 购课记录可正确关联课程
- [ ] 选择器组件正常工作
- [ ] 详情页显示关联数据

---

## 六、性能测试

### 6.1 TC-401：生成速度

**测试目标**：验证代码生成的响应速度

**指标**：
- 简单模块（5 字段）：< 30 秒
- 中等模块（10 字段）：< 60 秒
- 复杂模块（20 字段）：< 120 秒

### 6.2 TC-402：生成代码质量

**测试目标**：验证生成代码的质量

**指标**：
- 无语法错误
- 无 ESLint 警告
- 无 TypeScript 类型错误（如使用 TS）

---

## 七、测试执行记录

### 7.1 测试环境

| 项目 | 值 |
|-----|-----|
| 操作系统 | macOS |
| Cursor 版本 | - |
| Node.js 版本 | - |
| 项目版本 | - |

### 7.2 测试结果汇总

| 用例编号 | 用例名称 | 状态 | 备注 |
|---------|---------|------|------|
| TC-001 | 基础模块生成 | - | - |
| TC-002 | 带关联关系的模块 | - | - |
| TC-003 | 复杂列表页 | - | - |
| TC-004 | 表单页面 | - | - |
| TC-005 | Store 状态管理 | - | - |
| TC-006 | 路由配置 | - | - |
| TC-007 | pages.json 配置 | - | - |
| TC-008 | 数据库 Schema | - | - |
| TC-101 | 代码风格验证 | - | - |
| TC-102 | 命名规范验证 | - | - |
| TC-103 | 样式规范验证 | - | - |
| TC-104 | API 规范验证 | - | - |
| TC-201 | 空需求处理 | - | - |
| TC-202 | 特殊字符处理 | - | - |
| TC-203 | 重复模块处理 | - | - |
| TC-204 | 大量字段处理 | - | - |
| TC-301 | 完整模块集成 | - | - |
| TC-302 | 多模块协同 | - | - |
| TC-401 | 生成速度 | - | - |
| TC-402 | 生成代码质量 | - | - |

---

## 八、问题跟踪

### 8.1 已知问题

| 编号 | 描述 | 严重程度 | 状态 |
|-----|------|---------|------|
| - | - | - | - |

### 8.2 改进建议

| 编号 | 描述 | 优先级 |
|-----|------|--------|
| - | - | - |
