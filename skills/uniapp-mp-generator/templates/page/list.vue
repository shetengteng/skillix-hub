<!--
  列表页模板
  
  模板变量：
  - {{MODULE_NAME}} - 模块名（PascalCase），如 Student
  - {{MODULE_NAME_LOWER}} - 模块名（小写），如 student
  - {{MODULE_NAME_CN}} - 模块中文名，如 学生
  - {{HAS_FILTER}} - 是否有筛选功能
  - {{FILTER_OPTIONS}} - 筛选选项列表
-->
<template>
  <view class="page bg-page">
    <!-- 搜索栏 -->
    <sar-sticky>
      <view class="bg-card p-md">
        <sar-input
          v-model="searchKeyword"
          placeholder="搜索{{MODULE_NAME_CN}}..."
          clearable
        >
          <template #prepend>
            <TtSvg name="search" :size="36" color="#999" />
          </template>
        </sar-input>
      </view>
    </sar-sticky>

    <!-- 筛选器（如有） -->
    <!-- {{#if HAS_FILTER}} -->
    <view class="bg-card px-md py-sm">
      <sar-space>
        <sar-tag
          v-for="option in filterOptions"
          :key="option.value"
          :theme="filter === option.value ? 'primary' : 'default'"
          @click="filter = option.value"
        >
          {{ option.label }}
        </sar-tag>
      </sar-space>
    </view>
    <!-- {{/if}} -->

    <!-- 列表 -->
    <view class="p-md">
      <sar-space direction="vertical" size="24rpx">
        <{{MODULE_NAME}}Card
          v-for="item in filteredList"
          :key="item._id"
          :data="item"
          @click="goToDetail(item._id)"
        />
      </sar-space>
    </view>

    <!-- 空状态 -->
    <sar-empty
      v-if="!loading && filteredList.length === 0"
      description="暂无{{MODULE_NAME_CN}}"
    />

    <!-- 加载状态 -->
    <view v-if="loading" class="flex-center p-xl">
      <sar-loading />
    </view>

    <!-- FAB 添加按钮 -->
    <TtFab @click="goToAdd">
      <TtSvg name="add" :size="48" color="#fff" />
    </TtFab>

    <!-- 底部留白 -->
    <TtBottomPlaceholder />
    
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
import { onShow } from '@dcloudio/uni-app'

// 组件
import TtSvg from '@/components/TtSvg.vue'
import TtFab from '@/components/TtFab.vue'
import TtBottomPlaceholder from '@/components/TtBottomPlaceholder.vue'
import {{MODULE_NAME}}Card from './components/{{MODULE_NAME}}Card.vue'

// 路由
import { goTo{{MODULE_NAME}}Detail, goTo{{MODULE_NAME}}Add } from '@/route/index'

// API
import { get{{MODULE_NAME}}List } from './api/get{{MODULE_NAME}}List'

// ============ 响应式数据 ============
const loading = ref(false)
const list = ref([])
const searchKeyword = ref('')
const filter = ref('all')

// 筛选选项
const filterOptions = [
  { label: '全部', value: 'all' },
  { label: '启用', value: 'active' },
  { label: '停用', value: 'inactive' }
]

// ============ 计算属性 ============
const filteredList = computed(() => {
  let result = list.value

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(item =>
      item.name?.toLowerCase().includes(keyword)
    )
  }

  // 状态过滤
  if (filter.value !== 'all') {
    result = result.filter(item => item.status === filter.value)
  }

  return result
})

// ============ 生命周期 ============
onShow(() => {
  loadData()
})

// ============ 方法 ============

/**
 * 加载数据
 */
const loadData = async () => {
  loading.value = true
  try {
    const res = await get{{MODULE_NAME}}List()
    if (res.success) {
      list.value = res.list
    }
  } finally {
    loading.value = false
  }
}

/**
 * 跳转到详情
 * @param {string} id - 记录ID
 */
const goToDetail = (id) => {
  goTo{{MODULE_NAME}}Detail(id)
}

/**
 * 跳转到新增
 */
const goToAdd = () => {
  goTo{{MODULE_NAME}}Add()
}
</script>

<style lang="scss">
@import '@/styles/global.scss';
</style>
