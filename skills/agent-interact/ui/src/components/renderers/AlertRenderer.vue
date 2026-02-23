<script setup lang="ts">
import { computed } from 'vue'
import type { AlertNode } from '@/lib/types'

const props = defineProps<{ node: AlertNode }>()

const alertClass = computed(() => {
  const level = props.node.level || 'info'
  if (level === 'warning') return 'border-yellow-500/40 bg-yellow-500/10 text-yellow-900 dark:text-yellow-100'
  if (level === 'error') return 'border-destructive/40 bg-destructive/10 text-destructive'
  if (level === 'success') return 'border-green-500/40 bg-green-500/10 text-green-900 dark:text-green-100'
  return 'border-blue-500/40 bg-blue-500/10 text-blue-900 dark:text-blue-100'
})
</script>

<template>
  <div class="rounded-md border px-3 py-2 text-sm" :class="alertClass">
    {{ props.node.value }}
  </div>
</template>
