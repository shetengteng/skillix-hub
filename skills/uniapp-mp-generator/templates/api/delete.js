/**
 * 删除{{MODULE_NAME_CN}}
 * @module pages/{{MODULE_NAME_LOWER}}/api/delete{{MODULE_NAME}}
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
 * 删除{{MODULE_NAME_CN}}
 * @param {string} id - {{MODULE_NAME_CN}}ID
 * @returns {Promise<{success: boolean, error?: string}>}
 */
export async function delete{{MODULE_NAME}}(id) {
  try {
    const accountId = requireAccountId()
    if (!accountId) {
      return { success: false, error: '未登录' }
    }

    if (!id) {
      return { success: false, error: 'ID不能为空' }
    }

    // 先检查记录是否存在且属于当前用户
    const checkRes = await db.collection(COLLECTIONS.{{COLLECTION_NAME}})
      .doc(id)
      .get()

    if (!checkRes.data || checkRes.data.length === 0) {
      return { success: false, error: '{{MODULE_NAME_CN}}不存在' }
    }

    if (checkRes.data[0].accountId !== accountId) {
      return { success: false, error: '无权删除' }
    }

    // 执行删除
    const res = await db.collection(COLLECTIONS.{{COLLECTION_NAME}})
      .doc(id)
      .remove()

    checkEmasError(res, '删除{{MODULE_NAME_CN}}')

    return { success: true }
  } catch (error) {
    console.error('[delete{{MODULE_NAME}}] 失败:', error)
    return { success: false, error: error.message }
  }
}

export default delete{{MODULE_NAME}}
