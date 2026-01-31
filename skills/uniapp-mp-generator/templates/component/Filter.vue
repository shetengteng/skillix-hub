<!--
  筛选组件模板
  
  模板变量：
  - {{MODULE_NAME}} - 模块名（PascalCase），如 Student
  - {{MODULE_NAME_CN}} - 模块中文名，如 学生
  - {{FILTER_OPTIONS}} - 筛选选项列表
-->
<template>
  <view class="bg-card px-md py-sm">
    <sar-space wrap>
      <sar-tag
        v-for="option in options"
        :key="option.value"
        :theme="modelValue === option.value ? 'primary' : 'default'"
        @click="handleSelect(option.value)"
      >
        {{ option.label }}
      </sar-tag>
    </sar-space>
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
// ============ Props ============
const props = defineProps({
  /**
   * 当前选中值
   */
  modelValue: {
    type: String,
    default: 'all'
  },
  /**
   * 筛选选项
   */
  options: {
    type: Array,
    default: () => [
      { label: '全部', value: 'all' },
      { label: '启用', value: 'active' },
      { label: '停用', value: 'inactive' }
    ]
  }
})

// ============ Emits ============
const emit = defineEmits(['update:modelValue', 'change'])

// ============ 方法 ============

/**
 * 选择筛选项
 * @param {string} value - 选中的值
 */
const handleSelect = (value) => {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<style lang="scss">
@import '@/styles/global.scss';
</style>
