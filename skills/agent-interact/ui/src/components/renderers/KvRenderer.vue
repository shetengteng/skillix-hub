<script setup lang="ts">
import type { KvNode } from '@/lib/types'

defineProps<{ node: KvNode }>()
</script>

<template>
  <div class="rounded-lg border bg-muted/50 p-4">
    <div class="grid gap-2 text-sm">
      <div v-for="(item, index) in node.items" :key="`kv-${index}`" class="grid grid-cols-3 gap-2">
        <span class="font-medium text-muted-foreground">{{ item.key }}</span>
        <span class="col-span-2 break-all">{{ item.value }}</span>
      </div>
    </div>
  </div>
</template>
