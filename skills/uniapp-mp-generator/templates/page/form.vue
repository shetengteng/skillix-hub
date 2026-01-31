<!--
  表单页模板（新增/编辑）
  
  模板变量：
  - {{MODULE_NAME}} - 模块名（PascalCase），如 Student
  - {{MODULE_NAME_LOWER}} - 模块名（小写），如 student
  - {{MODULE_NAME_CN}} - 模块中文名，如 学生
  - {{FIELDS}} - 字段列表
  - {{REQUIRED_FIELDS}} - 必填字段
-->
<template>
  <view class="page bg-page">
    <!-- 表单 -->
    <view class="bg-card m-md rounded-lg">
      <sar-form ref="formRef" :model="formData" :rules="rules">
        <!-- {{#each FIELDS}} -->
        <sar-form-item label="{{description}}" name="{{name}}" {{#if required}}required{{/if}}>
          <!-- 文本输入 -->
          {{#if (eq type 'string')}}
          <sar-input 
            v-model="formData.{{name}}" 
            placeholder="请输入{{description}}"
          />
          {{/if}}
          
          <!-- 数字输入 -->
          {{#if (eq type 'number')}}
          <sar-input 
            v-model="formData.{{name}}" 
            type="number"
            placeholder="请输入{{description}}"
          />
          {{/if}}
          
          <!-- 多行文本 -->
          {{#if (eq type 'textarea')}}
          <sar-textarea 
            v-model="formData.{{name}}" 
            placeholder="请输入{{description}}"
            :maxlength="500"
            show-count
          />
          {{/if}}
          
          <!-- 单选（枚举） -->
          {{#if (eq type 'enum')}}
          <sar-radio-group v-model="formData.{{name}}">
            {{#each options}}
            <sar-radio value="{{value}}">{{label}}</sar-radio>
            {{/each}}
          </sar-radio-group>
          {{/if}}
          
          <!-- 日期选择 -->
          {{#if (eq type 'date')}}
          <sar-datetime-picker-popout
            v-model="formData.{{name}}"
            type="date"
            title="选择{{description}}"
          />
          {{/if}}
        </sar-form-item>
        <!-- {{/each}} -->
      </sar-form>
    </view>

    <!-- 提交按钮 -->
    <view class="fixed-bottom-bar bg-card p-md">
      <sar-button 
        theme="primary" 
        block 
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ isEdit ? '保存' : '创建' }}
      </sar-button>
      <TtSafeBottom />
    </view>

    <!-- 底部留白 -->
    <TtBottomPlaceholder :height="160" />
    
    <!-- Toast 代理 -->
    <sar-toast-agent />
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
import { onLoad } from '@dcloudio/uni-app'
import { toast } from '@/uni_modules/sard-uniapp'

// 组件
import TtSafeBottom from '@/components/TtSafeBottom.vue'
import TtBottomPlaceholder from '@/components/TtBottomPlaceholder.vue'

// 路由
import { goBack } from '@/route/index'

// API
import { get{{MODULE_NAME}}Detail } from '../api/get{{MODULE_NAME}}Detail'
import { create{{MODULE_NAME}} } from '../api/create{{MODULE_NAME}}'
import { update{{MODULE_NAME}} } from '../api/update{{MODULE_NAME}}'

// ============ 响应式数据 ============
const formRef = ref(null)
const id = ref('')
const submitting = ref(false)

// 表单数据
const formData = ref({
  // {{#each FIELDS}}
  // {{name}}: {{#if defaultValue}}{{defaultValue}}{{else}}''{{/if}},
  // {{/each}}
})

// 表单验证规则
const rules = {
  // {{#each REQUIRED_FIELDS}}
  // {{name}}: [{ required: true, message: '请输入{{description}}' }],
  // {{/each}}
}

// ============ 计算属性 ============
const isEdit = computed(() => !!id.value)

// ============ 生命周期 ============
onLoad((options) => {
  if (options.id) {
    id.value = options.id
    loadDetail()
  }
})

// ============ 方法 ============

/**
 * 加载详情（编辑模式）
 */
const loadDetail = async () => {
  const res = await get{{MODULE_NAME}}Detail(id.value)
  if (res.success) {
    // 回显表单数据
    Object.keys(formData.value).forEach(key => {
      if (res.data[key] !== undefined) {
        formData.value[key] = res.data[key]
      }
    })
  }
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  // 表单验证
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  submitting.value = true
  try {
    let res
    if (isEdit.value) {
      res = await update{{MODULE_NAME}}(id.value, formData.value)
    } else {
      res = await create{{MODULE_NAME}}(formData.value)
    }
    
    if (res.success) {
      toast.success(isEdit.value ? '保存成功' : '创建成功')
      setTimeout(() => {
        goBack()
      }, 1000)
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss">
@import '@/styles/global.scss';
</style>
