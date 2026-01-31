/**
 * 获取{{MODULE_NAME_CN}}列表
 * @module pages/{{MODULE_NAME_LOWER}}/api/get{{MODULE_NAME}}List
 * @since {{DATE}}
 * 
 * 模板变量：
 * - {{MODULE_NAME}} - 模块名（PascalCase），如 Student
 * - {{MODULE_NAME_LOWER}} - 模块名（小写），如 student
 * - {{MODULE_NAME_CN}} - 模块中文名，如 学生
 * - {{COLLECTION_NAME}} - 集合常量名，如 STUDENTS
 * - {{FIELDS}} - 字段列表
 * - {{HAS_STATUS}} - 是否有状态字段
 */

import { db, COLLECTIONS } from '@/cloud-emas/database/database'
import { checkEmasError } from '@/cloud-emas/database/error'
import { requireAccountId } from '@/utils/auth'

/**
 * {{MODULE_NAME_CN}}列表项数据结构
 * @typedef {Object} {{MODULE_NAME}}Item
 * @property {string} _id - {{MODULE_NAME_CN}}ID
 * @property {string} accountId - 所属用户ID
 * {{#each FIELDS}}
 * @property {{jsDocType}} {{name}} - {{description}}
 * {{/each}}
 * @property {string} createTime - 创建时间
 * @property {string} updateTime - 更新时间
 */

/**
 * 获取{{MODULE_NAME_CN}}列表
 * @param {Object} params - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.pageSize=20] - 每页数量
 * {{#if HAS_STATUS}}
 * @param {string} [params.status] - 状态筛选
 * {{/if}}
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

    // {{#if HAS_STATUS}}
    if (status) {
      query = query.where({ status })
    }
    // {{/if}}

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
