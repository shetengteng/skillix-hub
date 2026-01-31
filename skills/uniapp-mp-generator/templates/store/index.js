/**
 * {{MODULE_NAME_CN}}状态管理
 * @module stores/{{MODULE_NAME_LOWER}}
 * 
 * 模板变量：
 * - {{MODULE_NAME}} - 模块名（PascalCase），如 Student
 * - {{MODULE_NAME_LOWER}} - 模块名（小写），如 student
 * - {{MODULE_NAME_CN}} - 模块中文名，如 学生
 * - {{PREFIX}} - 项目前缀，如 pkb
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { get{{MODULE_NAME}}List } from '@/pages/{{MODULE_NAME_LOWER}}/api/get{{MODULE_NAME}}List'

export const use{{MODULE_NAME}}Store = defineStore('{{MODULE_NAME_LOWER}}', () => {
  // ============ 状态 ============
  
  /**
   * {{MODULE_NAME_CN}}列表
   */
  const {{MODULE_NAME_LOWER}}s = ref([])
  
  /**
   * 加载状态
   */
  const loading = ref(false)
  
  /**
   * 是否已加载
   */
  const loaded = ref(false)

  // ============ 计算属性 ============
  
  /**
   * {{MODULE_NAME_CN}}数量
   */
  const {{MODULE_NAME_LOWER}}Count = computed(() => {{MODULE_NAME_LOWER}}s.value.length)

  // ============ 方法 ============

  /**
   * 加载{{MODULE_NAME_CN}}列表
   * @param {boolean} [force=false] - 是否强制刷新
   */
  const load{{MODULE_NAME}}s = async (force = false) => {
    // 已加载且非强制刷新，直接返回
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
   * 根据 ID 列表获取{{MODULE_NAME_CN}}
   * @param {string[]} ids - {{MODULE_NAME_CN}}ID列表
   * @returns {Object[]}
   */
  const get{{MODULE_NAME}}sByIds = (ids) => {
    return {{MODULE_NAME_LOWER}}s.value.filter(item => ids.includes(item._id))
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
    get{{MODULE_NAME}}sByIds,
    add{{MODULE_NAME}},
    update{{MODULE_NAME}},
    remove{{MODULE_NAME}},
    reset
  }
}, {
  // 持久化配置
  persist: {
    key: '{{PREFIX}}-{{MODULE_NAME_LOWER}}',
    paths: ['{{MODULE_NAME_LOWER}}s']
  }
})
