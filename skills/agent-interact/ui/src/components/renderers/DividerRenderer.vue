<script setup lang="ts">
import type { DividerNode } from '@/lib/types'
import { Separator } from '@/components/ui/separator'

defineProps<{ node: DividerNode }>()
</script>

<template>
  <Separator />
</template>
