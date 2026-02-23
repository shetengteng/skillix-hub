<script setup lang="ts">
import { computed } from 'vue'
import type { TextareaNode } from '@/lib/types'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'

const props = defineProps<{
  node: TextareaNode
  model: Record<string, unknown>
  error?: string
}>()

const textValue = computed({
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
    <Textarea
      :id="props.node.id"
      v-model="textValue"
      :placeholder="props.node.placeholder"
      rows="3"
    />
    <p v-if="props.error" class="text-xs text-destructive">
      {{ props.error }}
    </p>
  </div>
</template>
