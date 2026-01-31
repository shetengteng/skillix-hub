<!--
  详情页模板
  
  模板变量：
  - {{MODULE_NAME}} - 模块名（PascalCase），如 Student
  - {{MODULE_NAME_LOWER}} - 模块名（小写），如 student
  - {{MODULE_NAME_CN}} - 模块中文名，如 学生
  - {{FIELDS}} - 字段列表
-->
<template>
  <view class="page bg-page">
    <!-- 基本信息卡片 -->
    <view class="bg-card m-md p-lg rounded-lg">
      <view class="flex-row flex-center-v">
        <!-- 头像/图标 -->
        <TtAvatar :name="detail.name" size="80rpx" />
        
        <!-- 基本信息 -->
        <view class="ml-md flex-1">
          <text class="text-lg font-semibold text-foreground">
            {{ detail.name }}
          </text>
          <view class="flex-row flex-center-v mt-xs">
            <sar-tag size="small" :theme="detail.status === 'active' ? 'success' : 'default'">
              {{ detail.status === 'active' ? '启用' : '停用' }}
            </sar-tag>
          </view>
        </view>
      </view>
    </view>

    <!-- 详细信息 -->
    <view class="bg-card m-md rounded-lg">
      <sar-list>
        <!-- {{#each FIELDS}} -->
        <sar-list-item title="{{description}}">
          <template #value>
            <text class="text-foreground">{{ detail.{{name}} }}</text>
          </template>
        </sar-list-item>
        <!-- {{/each}} -->
        
        <sar-list-item title="创建时间">
          <template #value>
            <text class="text-muted">{{ formatDateTime(detail.createTime) }}</text>
          </template>
        </sar-list-item>
      </sar-list>
    </view>

    <!-- 操作按钮 -->
    <view class="fixed-bottom-bar bg-card p-md">
      <view class="flex-row">
        <sar-button 
          class="flex-1 mr-sm" 
          theme="pale"
          @click="handleEdit"
        >
          编辑
        </sar-button>
        <sar-button 
          class="flex-1" 
          theme="danger"
          @click="handleDelete"
        >
          删除
        </sar-button>
      </view>
      <TtSafeBottom />
    </view>

    <!-- 底部留白 -->
    <TtBottomPlaceholder :height="160" />
    
    <!-- 弹窗代理 -->
    <sar-dialog-agent />
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
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { dialog, toast } from '@/uni_modules/sard-uniapp'

// 组件
import TtAvatar from '@/components/TtAvatar.vue'
import TtSafeBottom from '@/components/TtSafeBottom.vue'
import TtBottomPlaceholder from '@/components/TtBottomPlaceholder.vue'

// 工具
import { formatDateTime } from '@/utils/date'

// 路由
import { goTo{{MODULE_NAME}}Edit, goBack } from '@/route/index'

// API
import { get{{MODULE_NAME}}Detail } from '../api/get{{MODULE_NAME}}Detail'
import { delete{{MODULE_NAME}} } from '../api/delete{{MODULE_NAME}}'

// ============ 响应式数据 ============
const id = ref('')
const detail = ref({})
const loading = ref(false)

// ============ 生命周期 ============
onLoad((options) => {
  if (options.id) {
    id.value = options.id
    loadDetail()
  }
})

// ============ 方法 ============

/**
 * 加载详情
 */
const loadDetail = async () => {
  loading.value = true
  try {
    const res = await get{{MODULE_NAME}}Detail(id.value)
    if (res.success) {
      detail.value = res.data
    }
  } finally {
    loading.value = false
  }
}

/**
 * 编辑
 */
const handleEdit = () => {
  goTo{{MODULE_NAME}}Edit(id.value)
}

/**
 * 删除
 */
const handleDelete = async () => {
  try {
    await dialog({
      title: '确认删除',
      message: '删除后数据将无法恢复，确定要删除吗？'
    })
    
    const res = await delete{{MODULE_NAME}}(id.value)
    if (res.success) {
      toast.success('删除成功')
      setTimeout(() => {
        goBack()
      }, 1000)
    }
  } catch {
    // 用户取消
  }
}
</script>

<style lang="scss">
@import '@/styles/global.scss';
</style>
