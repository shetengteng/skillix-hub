<script setup lang="ts">
import { computed } from 'vue'
import type { InputNode } from '@/lib/types'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const props = defineProps<{
  node: InputNode
  model: Record<string, unknown>
  error?: string
}>()

const inputValue = computed({
  get: () => String(props.model[props.node.id] ?? ''),
  set: (value: string) => {
    props.model[props.node.id] = value
  },
})
</script>

<template>
  <div class="grid gap-2">
    <Label :for="props.node.id">
      {{ props.node.label }}
      <span v-if="props.node.required" class="text-destructive">*</span>
    </Label>
    <Input
      :id="props.node.id"
      v-model="inputValue"
      :placeholder="props.node.placeholder"
    />
    <p v-if="props.error" class="text-xs text-destructive">
      {{ props.error }}
    </p>
  </div>
</template>
