/**
 * 创建{{MODULE_NAME_CN}}
 * @module pages/{{MODULE_NAME_LOWER}}/api/create{{MODULE_NAME}}
 * @since {{DATE}}
 * 
 * 模板变量：
 * - {{MODULE_NAME}} - 模块名（PascalCase），如 Student
 * - {{MODULE_NAME_LOWER}} - 模块名（小写），如 student
 * - {{MODULE_NAME_CN}} - 模块中文名，如 学生
 * - {{COLLECTION_NAME}} - 集合常量名，如 STUDENTS
 * - {{FIELDS}} - 字段列表
 * - {{REQUIRED_FIELDS}} - 必填字段
 * - {{OPTIONAL_FIELDS}} - 可选字段
 */

import { db, COLLECTIONS } from '@/cloud-emas/database/database'
import { checkEmasError } from '@/cloud-emas/database/error'
import { requireAccountId } from '@/utils/auth'

/**
 * 创建{{MODULE_NAME_CN}}请求参数
 * @typedef {Object} Create{{MODULE_NAME}}Params
 * {{#each REQUIRED_FIELDS}}
 * @property {{jsDocType}} {{name}} - {{description}}（必填）
 * {{/each}}
 * {{#each OPTIONAL_FIELDS}}
 * @property {{jsDocType}} [{{name}}] - {{description}}（可选）
 * {{/each}}
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
    // {{#each REQUIRED_FIELDS}}
    if (!params.{{name}}) {
      return { success: false, error: '{{description}}不能为空' }
    }
    // {{/each}}

    const now = new Date().toISOString()
    const data = {
      accountId,
      // {{#each FIELDS}}
      {{name}}: params.{{name}}{{#if defaultValue}} ?? {{defaultValue}}{{/if}},
      // {{/each}}
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
