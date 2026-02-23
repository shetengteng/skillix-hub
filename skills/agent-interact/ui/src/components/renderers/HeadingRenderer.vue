<script setup lang="ts">
import { computed } from 'vue'
import type { HeadingNode } from '@/lib/types'

const props = defineProps<{ node: HeadingNode }>()

const headingClass = computed(() => {
  const level = props.node.level || 2
  if (level === 1) return 'text-2xl font-semibold tracking-tight'
  if (level === 2) return 'text-xl font-semibold tracking-tight'
  if (level === 3) return 'text-lg font-semibold'
  return 'text-base font-semibold'
})
</script>

<template>
  <p :class="headingClass">
    {{ props.node.value }}
  </p>
</template>
