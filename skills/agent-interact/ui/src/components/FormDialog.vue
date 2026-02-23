<script setup lang="ts">
import { reactive, computed } from 'vue'
import type { FormDialog } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'

const props = defineProps<{ dialog: FormDialog }>()
const emit = defineEmits<{ respond: [action: string, data?: unknown] }>()

const formData = reactive<Record<string, string | number | boolean>>(
  Object.fromEntries(props.dialog.fields.map((f) => [f.id, f.default ?? '']))
)

const allRequiredFilled = computed(() =>
  props.dialog.fields
    .filter((f) => f.required)
    .every((f) => {
      const v = formData[f.id]
      return v !== '' && v !== undefined && v !== null
    })
)

function submit() {
  emit('respond', 'submitted', { ...formData })
}
</script>

<template>
  <div class="flex h-screen flex-col p-6 pt-10">
    <div class="mb-1">
      <h2 class="text-lg font-semibold">{{ dialog.title || '请填写' }}</h2>
      <p v-if="dialog.message" class="mt-1 text-sm text-muted-foreground">{{ dialog.message }}</p>
    </div>

    <div class="flex-1 overflow-y-auto py-4">
      <div class="grid gap-4">
        <div v-for="field in dialog.fields" :key="field.id" class="grid gap-2">
          <Label :for="field.id">
            {{ field.label }}
            <span v-if="field.required" class="text-destructive">*</span>
          </Label>

          <Input
            v-if="field.type === 'text'"
            :id="field.id"
            v-model="formData[field.id] as string"
            :placeholder="field.placeholder"
          />

          <Input
            v-else-if="field.type === 'number'"
            :id="field.id"
            type="number"
            :model-value="String(formData[field.id])"
            @update:model-value="formData[field.id] = Number($event)"
            :placeholder="field.placeholder"
          />

          <Textarea
            v-else-if="field.type === 'textarea'"
            :id="field.id"
            v-model="formData[field.id] as string"
            :placeholder="field.placeholder"
            rows="3"
          />

          <Select
            v-else-if="field.type === 'select'"
            :model-value="String(formData[field.id])"
            @update:model-value="formData[field.id] = $event as string"
          >
            <SelectTrigger>
              <SelectValue :placeholder="field.placeholder || '请选择'" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</SelectItem>
            </SelectContent>
          </Select>

          <div v-else-if="field.type === 'checkbox'" class="flex items-center gap-2">
            <Checkbox
              :id="field.id"
              :checked="!!formData[field.id]"
              @update:checked="formData[field.id] = $event"
            />
            <Label :for="field.id" class="text-sm font-normal">{{ field.placeholder || field.label }}</Label>
          </div>
        </div>
      </div>
    </div>

    <div class="flex items-center justify-end gap-2 pt-4 border-t">
      <Button variant="outline" @click="emit('respond', '__cancelled')">
        {{ dialog.cancelText || '取消' }}
      </Button>
      <Button :disabled="!allRequiredFilled" @click="submit">
        {{ dialog.submitText || '提交' }}
      </Button>
    </div>
  </div>
</template>
