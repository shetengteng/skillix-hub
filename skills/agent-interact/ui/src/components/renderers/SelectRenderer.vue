<script setup lang="ts">
import { computed } from 'vue'
import type { SelectNode } from '@/lib/types'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const props = defineProps<{
  node: SelectNode
  model: Record<string, unknown>
  error?: string
}>()

const value = computed(() => String(props.model[props.node.id] ?? ''))

function onUpdate(value: unknown) {
  props.model[props.node.id] = typeof value === 'string' ? value : ''
}
</script>

<template>
  <div class="grid gap-2">
    <Label :for="props.node.id">
      {{ props.node.label }}
      <span v-if="props.node.required" class="text-destructive">*</span>
    </Label>
    <Select :model-value="value" @update:model-value="onUpdate">
      <SelectTrigger :id="props.node.id">
        <SelectValue :placeholder="props.node.placeholder || '请选择'" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem
          v-for="option in props.node.options"
          :key="option"
          :value="option"
        >
          {{ option }}
        </SelectItem>
      </SelectContent>
    </Select>
    <p v-if="props.error" class="text-xs text-destructive">
      {{ props.error }}
    </p>
  </div>
</template>
