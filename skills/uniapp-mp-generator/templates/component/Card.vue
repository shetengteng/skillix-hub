<!--
  卡片组件模板
  
  模板变量：
  - {{MODULE_NAME}} - 模块名（PascalCase），如 Student
  - {{MODULE_NAME_LOWER}} - 模块名（小写），如 student
  - {{MODULE_NAME_CN}} - 模块中文名，如 学生
  - {{DISPLAY_FIELDS}} - 需要显示的字段列表
-->
<template>
  <view 
    class="bg-card rounded-lg border p-md"
    hover-class="bg-muted"
    @click="handleClick"
  >
    <view class="flex-row flex-center-v">
      <!-- 左侧头像/图标 -->
      <TtAvatar :name="data.name" size="64rpx" />
      
      <!-- 中间内容 -->
      <view class="flex-1 ml-md">
        <!-- 标题行 -->
        <view class="flex-row flex-center-v flex-between">
          <text class="text-base font-medium text-foreground">
            {{ data.name }}
          </text>
          <sar-tag 
            size="small" 
            :theme="data.status === 'active' ? 'success' : 'default'"
          >
            {{ data.status === 'active' ? '启用' : '停用' }}
          </sar-tag>
        </view>
        
        <!-- 描述行 -->
        <view class="flex-row flex-center-v mt-xs">
          <!-- {{#each DISPLAY_FIELDS}} -->
          <text class="text-sm text-muted">
            {{ data.{{name}} }}
          </text>
          <!-- {{/each}} -->
        </view>
      </view>
      
      <!-- 右侧箭头 -->
      <TtSvg name="arrow-right" :size="32" color="#999" class="ml-sm" />
    </view>
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
// 组件
import TtAvatar from '@/components/TtAvatar.vue'
import TtSvg from '@/components/TtSvg.vue'

// ============ Props ============
const props = defineProps({
  /**
   * {{MODULE_NAME_CN}}数据
   */
  data: {
    type: Object,
    required: true
  }
})

// ============ Emits ============
const emit = defineEmits(['click'])

// ============ 方法 ============

/**
 * 点击卡片
 */
const handleClick = () => {
  emit('click', props.data)
}
</script>

<style lang="scss">
@import '@/styles/global.scss';
</style>
