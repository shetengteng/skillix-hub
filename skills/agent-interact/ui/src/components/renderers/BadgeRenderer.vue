<script setup lang="ts">
import { computed } from 'vue'
import type { BadgeNode } from '@/lib/types'

const props = defineProps<{ node: BadgeNode }>()

const badgeClass = computed(() => {
  const v = props.node.variant || 'default'
  const map: Record<string, string> = {
    default: 'bg-primary/10 text-primary border-primary/20',
    success: 'bg-green-500/10 text-green-700 dark:text-green-300 border-green-500/20',
    warning: 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-300 border-yellow-500/20',
    error: 'bg-destructive/10 text-destructive border-destructive/20',
  }
  return map[v] || map.default
})
</script>

<template>
  <span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold" :class="badgeClass">
    {{ props.node.value }}
  </span>
</template>
