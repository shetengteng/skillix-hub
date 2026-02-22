<script setup lang="ts">
import { reactive, computed } from 'vue'
import type { FormDialog } from '@/lib/types'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '@/components/ui/dialog'
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
  <Dialog :open="true">
    <DialogContent class="sm:max-w-lg" @interact-outside.prevent>
      <DialogHeader>
        <DialogTitle>{{ dialog.title || '请填写' }}</DialogTitle>
        <DialogDescription v-if="dialog.message">{{ dialog.message }}</DialogDescription>
      </DialogHeader>

      <div class="grid gap-4 py-4">
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

      <DialogFooter class="gap-2">
        <Button variant="outline" @click="emit('respond', '__cancelled')">
          {{ dialog.cancelText || '取消' }}
        </Button>
        <Button :disabled="!allRequiredFilled" @click="submit">
          {{ dialog.submitText || '提交' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
