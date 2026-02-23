<script setup lang="ts">
import type { CheckboxNode } from '@/lib/types'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'

const props = defineProps<{
  node: CheckboxNode
  model: Record<string, unknown>
  error?: string
}>()

function onUpdate(checked: boolean | 'indeterminate') {
  props.model[props.node.id] = checked === true
}
</script>

<template>
  <div class="grid gap-1">
    <div class="flex items-center gap-2">
      <Checkbox
        :id="props.node.id"
        :checked="Boolean(props.model[props.node.id])"
        @update:checked="onUpdate"
      />
      <Label :for="props.node.id">
        {{ props.node.label }}
        <span v-if="props.node.required" class="text-destructive">*</span>
      </Label>
    </div>
    <p v-if="props.error" class="text-xs text-destructive">
      {{ props.error }}
    </p>
  </div>
</template>
