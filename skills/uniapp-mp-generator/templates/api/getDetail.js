/**
 * 获取{{MODULE_NAME_CN}}详情
 * @module pages/{{MODULE_NAME_LOWER}}/api/get{{MODULE_NAME}}Detail
 * @since {{DATE}}
 * 
 * 模板变量：
 * - {{MODULE_NAME}} - 模块名（PascalCase），如 Student
 * - {{MODULE_NAME_LOWER}} - 模块名（小写），如 student
 * - {{MODULE_NAME_CN}} - 模块中文名，如 学生
 * - {{COLLECTION_NAME}} - 集合常量名，如 STUDENTS
 */

import { db, COLLECTIONS } from '@/cloud-emas/database/database'
import { checkEmasError } from '@/cloud-emas/database/error'
import { requireAccountId } from '@/utils/auth'

/**
 * 获取{{MODULE_NAME_CN}}详情
 * @param {string} id - {{MODULE_NAME_CN}}ID
 * @returns {Promise<{success: boolean, data?: Object, error?: string}>}
 */
export async function get{{MODULE_NAME}}Detail(id) {
  try {
    const accountId = requireAccountId()
    if (!accountId) {
      return { success: false, error: '未登录' }
    }

    if (!id) {
      return { success: false, error: 'ID不能为空' }
    }

    const res = await db.collection(COLLECTIONS.{{COLLECTION_NAME}})
      .doc(id)
      .get()

    checkEmasError(res, '获取{{MODULE_NAME_CN}}详情')

    // 检查数据是否存在
    if (!res.data || res.data.length === 0) {
      return { success: false, error: '{{MODULE_NAME_CN}}不存在' }
    }

    // 检查权限（是否属于当前用户）
    const data = res.data[0]
    if (data.accountId !== accountId) {
      return { success: false, error: '无权访问' }
    }

    return {
      success: true,
      data
    }
  } catch (error) {
    console.error('[get{{MODULE_NAME}}Detail] 失败:', error)
    return { success: false, error: error.message }
  }
}

export default get{{MODULE_NAME}}Detail
