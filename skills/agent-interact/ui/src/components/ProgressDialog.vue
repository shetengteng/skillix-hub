<script setup lang="ts">
import { computed } from 'vue'
import type { ProgressDialog } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'

const props = defineProps<{ dialog: ProgressDialog }>()
const emit = defineEmits<{ respond: [action: string, data?: unknown] }>()

const percent = computed(() => props.dialog.percent ?? 0)
const actions = computed(() =>
  props.dialog.actions?.length ? props.dialog.actions : [{ id: 'ok', label: '了解' }]
)

const statusIcon = {
  pending: { path: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z', class: 'text-muted-foreground' },
  running: { path: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15', class: 'text-primary animate-spin' },
  completed: { path: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', class: 'text-green-500' },
  failed: { path: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z', class: 'text-red-500' },
}
</script>

<template>
  <div class="flex h-screen flex-col p-6 pt-10">
    <div class="mb-1">
      <h2 class="text-lg font-semibold">{{ dialog.title || '进度' }}</h2>
      <p v-if="dialog.message" class="mt-1 text-sm text-muted-foreground">{{ dialog.message }}</p>
    </div>

    <div class="flex-1 overflow-y-auto py-4 space-y-4">
      <div class="space-y-1">
        <div class="flex items-center justify-between text-sm">
          <span class="text-muted-foreground">总进度</span>
          <span class="font-medium">{{ percent }}%</span>
        </div>
        <Progress :model-value="percent" class="h-2" />
      </div>

      <div class="space-y-2">
        <div
          v-for="(step, idx) in dialog.steps"
          :key="step.id"
          class="flex items-center gap-3 rounded-lg p-2 text-sm"
          :class="{ 'bg-muted/50': step.status === 'running' }"
        >
          <div class="flex h-6 w-6 shrink-0 items-center justify-center">
            <svg class="h-5 w-5" :class="statusIcon[step.status].class" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" :d="statusIcon[step.status].path" />
            </svg>
          </div>
          <span class="flex-1" :class="{ 'font-medium': step.status === 'running', 'text-muted-foreground': step.status === 'pending' }">
            {{ step.label }}
          </span>
          <span class="text-xs text-muted-foreground">{{ idx + 1 }}/{{ dialog.steps.length }}</span>
        </div>
      </div>
    </div>

    <div class="flex items-center justify-end gap-2 pt-4 border-t">
      <Button
        v-for="act in actions"
        :key="act.id"
        :variant="(act as any).variant || 'default'"
        @click="emit('respond', act.id)"
      >
        {{ act.label }}
      </Button>
    </div>
  </div>
</template>
