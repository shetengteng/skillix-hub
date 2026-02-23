<script setup lang="ts">
import { computed } from 'vue'
import type { ImageNode } from '@/lib/types'

const props = defineProps<{ node: ImageNode }>()

const isValidSrc = computed(() => props.node.src.startsWith('https://'))
</script>

<template>
  <div v-if="isValidSrc" class="overflow-hidden rounded-md">
    <img
      :src="props.node.src"
      :alt="props.node.alt || ''"
      :width="props.node.width"
      :height="props.node.height"
      class="max-w-full object-contain"
      loading="lazy"
    />
  </div>
  <div v-else class="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
    Image blocked: only https URLs are allowed
  </div>
</template>
