<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import type {
  CheckboxNode,
  CustomAction,
  CustomDialog as CustomDialogType,
  CustomNode,
  DialogRespondMeta,
  DialogValidationError,
  InputNode,
  SelectNode,
  TextareaNode,
} from '@/lib/types'
import { Button } from '@/components/ui/button'
import ContentRenderer from '@/components/ContentRenderer.vue'

interface FieldDefinition {
  id: string
  label: string
  required: boolean
  kind: 'input' | 'select' | 'checkbox' | 'textarea'
  defaultValue: unknown
}

const props = defineProps<{ dialog: CustomDialogType }>()
const emit = defineEmits<{ respond: [action: string, data?: unknown, meta?: DialogRespondMeta] }>()

const formData = reactive<Record<string, unknown>>({})
const validationErrors = ref<DialogValidationError[]>([])

type FieldNodeType = InputNode | SelectNode | CheckboxNode | TextareaNode

function isFieldNode(node: CustomNode): node is FieldNodeType {
  return node.kind === 'input' || node.kind === 'select' || node.kind === 'checkbox' || node.kind === 'textarea'
}

function hasChildren(node: CustomNode): node is CustomNode & { children: CustomNode[] } {
  return 'children' in node && Array.isArray((node as any).children)
}

function collectFieldDefinitions(nodes: CustomNode[]): FieldDefinition[] {
  const fields: FieldDefinition[] = []
  for (const node of nodes) {
    if (isFieldNode(node)) {
      fields.push({
        id: node.id,
        label: node.label,
        required: node.required === true,
        kind: node.kind,
        defaultValue: node.kind === 'checkbox' ? Boolean(node.default) : (node.default ?? ''),
      })
      continue
    }
    if (hasChildren(node)) {
      fields.push(...collectFieldDefinitions(node.children))
    }
  }
  return fields
}

const fieldDefinitions = collectFieldDefinitions(props.dialog.content)
for (const field of fieldDefinitions) {
  formData[field.id] = field.defaultValue
}

const errorMap = computed<Record<string, string>>(() => {
  const out: Record<string, string> = {}
  for (const err of validationErrors.value) {
    if (err.fieldId && !out[err.fieldId]) out[err.fieldId] = err.message
  }
  return out
})

const actions = computed<CustomAction[]>(() => {
  if (props.dialog.actions && props.dialog.actions.length > 0) return props.dialog.actions
  return [{ id: 'ok', label: '确定', submit: false, requireValid: false, closeOnSubmit: true }]
})

function validateFields(): DialogValidationError[] {
  const errors: DialogValidationError[] = []
  for (const field of fieldDefinitions) {
    if (!field.required) continue
    const value = formData[field.id]
    if (field.kind === 'checkbox') {
      if (value !== true) {
        errors.push({ fieldId: field.id, message: `${field.label}必须勾选` })
      }
      continue
    }
    if (value === '' || value === null || value === undefined) {
      errors.push({ fieldId: field.id, message: `${field.label}为必填项` })
    }
  }
  return errors
}

function onAction(action: CustomAction) {
  const shouldSubmit = action.submit !== false
  const requireValid = action.requireValid === true
  const closeOnSubmit = action.closeOnSubmit !== false

  let errors: DialogValidationError[] = []
  if (shouldSubmit) {
    errors = validateFields()
    validationErrors.value = errors
  } else {
    validationErrors.value = []
  }

  const valid = errors.length === 0
  if (shouldSubmit && requireValid && !valid) return

  const meta: DialogRespondMeta = {
    valid: shouldSubmit ? valid : true,
    errors,
    close: closeOnSubmit,
  }

  emit('respond', action.id, shouldSubmit ? { ...formData } : null, meta)
}
</script>

<template>
  <div class="flex h-screen flex-col p-6 pt-10">
    <div class="mb-1">
      <h2 class="text-lg font-semibold">{{ props.dialog.title || '交互确认' }}</h2>
      <p v-if="props.dialog.message" class="mt-1 text-sm text-muted-foreground">
        {{ props.dialog.message }}
      </p>
    </div>

    <div class="flex-1 overflow-y-auto space-y-4 py-4 pr-1">
      <ContentRenderer
        v-for="(node, index) in props.dialog.content"
        :key="`custom-node-${index}`"
        :node="node"
        :model="formData"
        :errors="errorMap"
      />
    </div>

    <div class="flex flex-wrap items-center justify-end gap-2 pt-4 border-t">
      <Button
        v-for="action in actions"
        :key="action.id"
        :variant="action.variant || 'default'"
        @click="onAction(action)"
      >
        {{ action.label }}
      </Button>
    </div>
  </div>
</template>
