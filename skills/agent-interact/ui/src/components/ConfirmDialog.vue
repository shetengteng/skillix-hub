<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ConfirmDialog } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const props = defineProps<{ dialog: ConfirmDialog }>()
const emit = defineEmits<{ respond: [action: string, data?: unknown] }>()

const selected = ref<Set<string>>(new Set())

function toggle(id: string) {
  if (props.dialog.allowMultiple) {
    if (selected.value.has(id)) selected.value.delete(id)
    else selected.value.add(id)
  } else {
    selected.value = new Set([id])
  }
}

const canSubmit = computed(() => selected.value.size > 0)

function submit() {
  const ids = [...selected.value]
  emit('respond', ids.length === 1 ? ids[0]! : 'selected', ids.length === 1 ? undefined : ids)
}
</script>

<template>
  <div class="flex h-screen flex-col p-6 pt-10">
    <div class="mb-1">
      <h2 class="text-lg font-semibold">{{ dialog.title || '请选择' }}</h2>
      <p v-if="dialog.message" class="mt-1 text-sm text-muted-foreground">{{ dialog.message }}</p>
    </div>

    <div class="flex-1 grid gap-2 py-4 content-start overflow-y-auto">
      <button
        v-for="opt in dialog.options"
        :key="opt.id"
        class="flex items-center gap-3 rounded-lg border p-4 text-left transition-colors hover:bg-accent"
        :class="{ 'border-primary bg-primary/5': selected.has(opt.id) }"
        @click="toggle(opt.id)"
      >
        <div class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border"
             :class="selected.has(opt.id) ? 'border-primary bg-primary' : 'border-muted-foreground/30'">
          <svg v-if="selected.has(opt.id)" class="h-3 w-3 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div class="flex-1">
          <div class="font-medium">{{ opt.label }}</div>
          <div v-if="opt.description" class="text-sm text-muted-foreground">{{ opt.description }}</div>
        </div>
      </button>
    </div>

    <div class="flex items-center justify-end gap-2 pt-4 border-t">
      <Badge v-if="dialog.allowMultiple" variant="secondary" class="mr-auto">
        已选 {{ selected.size }} 项
      </Badge>
      <Button variant="outline" @click="emit('respond', '__cancelled')">取消</Button>
      <Button :disabled="!canSubmit" @click="submit">确认</Button>
    </div>
  </div>
</template>
