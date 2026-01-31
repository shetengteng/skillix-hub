/**
 * {{MODULE_NAME_CN}}集合定义
 * @module cloud-emas/database/collections/{{MODULE_NAME_LOWER}}
 * @since {{DATE}}
 * 
 * 模板变量：
 * - {{MODULE_NAME}} - 模块名（PascalCase），如 Student
 * - {{MODULE_NAME_LOWER}} - 模块名（小写），如 student
 * - {{MODULE_NAME_CN}} - 模块中文名，如 学生
 * - {{PREFIX}} - 项目前缀，如 pkb
 * - {{FIELDS}} - 字段列表
 * - {{HAS_STATUS}} - 是否有状态字段
 * - {{STATUS_OPTIONS}} - 状态选项列表
 */

import { PROJECT_CONFIG } from '@/config/index'

const PREFIX = PROJECT_CONFIG.prefix

// ============ 集合名称 ============

/**
 * {{MODULE_NAME_CN}}集合名称
 */
export const COLLECTION_{{COLLECTION_NAME}} = `${PREFIX}-{{MODULE_NAME_LOWER}}s`

// ============ 数据结构定义 ============

/**
 * {{MODULE_NAME_CN}}数据结构
 * @typedef {Object} {{MODULE_NAME}}
 * @property {string} _id - {{MODULE_NAME_CN}}ID（系统生成）
 * @property {string} accountId - 所属用户ID
 * {{#each FIELDS}}
 * @property {{jsDocType}} {{#if optional}}[{{name}}]{{else}}{{name}}{{/if}} - {{description}}{{#if unit}}（单位：{{unit}}）{{/if}}
 * {{/each}}
 * @property {string} createTime - 创建时间（ISO 8601）
 * @property {string} updateTime - 更新时间（ISO 8601）
 */

// {{#if HAS_STATUS}}
/**
 * {{MODULE_NAME_CN}}状态枚举
 * @typedef {{{STATUS_ENUM}}} {{MODULE_NAME}}Status
 * {{#each STATUS_OPTIONS}}
 * - {{value}}: {{label}}
 * {{/each}}
 */
// {{/if}}

// ============ 索引建议 ============

/**
 * 索引建议（在数据库控制台创建）
 * 
 * 1. accountId - 按用户查询（必须）
 * 2. createTime - 按时间排序
 * {{#if HAS_STATUS}}
 * 3. status - 按状态筛选
 * {{/if}}
 * 
 * 复合索引：
 * - { accountId: 1, createTime: -1 } - 按用户查询并按时间倒序
 * {{#if HAS_STATUS}}
 * - { accountId: 1, status: 1, createTime: -1 } - 按用户和状态查询
 * {{/if}}
 */

// ============ 默认值 ============

/**
 * {{MODULE_NAME_CN}}默认值
 */
export const DEFAULT_{{COLLECTION_NAME}} = {
  // {{#each FIELDS}}
  // {{name}}: {{#if defaultValue}}{{defaultValue}}{{else}}{{#if (eq type 'string')}}''{{else if (eq type 'number')}}0{{else if (eq type 'boolean')}}false{{else if (eq type 'array')}}[]{{else}}null{{/if}}{{/if}},
  // {{/each}}
}

// ============ 验证规则 ============

/**
 * {{MODULE_NAME_CN}}验证规则（用于表单）
 */
export const {{COLLECTION_NAME}}_RULES = {
  // {{#each REQUIRED_FIELDS}}
  {{name}}: [
    { required: true, message: '{{description}}不能为空' }
  ],
  // {{/each}}
}
