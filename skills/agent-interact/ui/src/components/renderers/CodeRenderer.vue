<script setup lang="ts">
import type { CodeNode } from '@/lib/types'

defineProps<{ node: CodeNode }>()
</script>

<template>
  <div class="overflow-x-auto rounded-md border bg-muted/50">
    <div v-if="node.language" class="border-b px-3 py-1.5 text-xs text-muted-foreground">
      {{ node.language }}
    </div>
    <pre class="p-3 text-sm"><code>{{ node.value }}</code></pre>
  </div>
</template>
