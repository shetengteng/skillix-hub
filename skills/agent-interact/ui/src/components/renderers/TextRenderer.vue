<script setup lang="ts">
import type { TextNode } from '@/lib/types'

defineProps<{ node: TextNode }>()
</script>

<template>
  <p class="text-sm leading-6 whitespace-pre-wrap break-words">
    {{ node.value }}
  </p>
</template>
