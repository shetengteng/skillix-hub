<script setup lang="ts">
import type { ProgressNode } from '@/lib/types'
import { Progress } from '@/components/ui/progress'

defineProps<{ node: ProgressNode }>()
</script>

<template>
  <div class="space-y-1">
    <div class="flex items-center justify-between text-sm">
      <span v-if="node.label" class="text-muted-foreground">{{ node.label }}</span>
      <span class="font-medium">{{ node.value }}%</span>
    </div>
    <Progress :model-value="node.value" class="h-2" />
  </div>
</template>
