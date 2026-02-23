<script setup lang="ts">
import { computed } from 'vue'
import type { ApprovalDialog } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'

const props = defineProps<{ dialog: ApprovalDialog }>()
const emit = defineEmits<{ respond: [action: string, data?: unknown] }>()

const severityConfig = computed(() => {
  const map = {
    low: { label: 'LOW', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' },
    medium: { label: 'MEDIUM', class: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' },
    high: { label: 'HIGH', class: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200' },
    critical: { label: 'CRITICAL', class: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' },
  }
  return map[props.dialog.severity] || map.medium
})

const details = computed(() => {
  if (!props.dialog.details) return []
  return Object.entries(props.dialog.details)
})
</script>

<template>
  <div class="flex h-screen flex-col p-6 pt-10">
    <div class="mb-1">
      <div class="flex items-center gap-2">
        <h2 class="text-lg font-semibold">{{ dialog.title || '需要审批' }}</h2>
        <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold" :class="severityConfig.class">
          {{ severityConfig.label }}
        </span>
      </div>
      <p v-if="dialog.message" class="mt-1 text-sm text-muted-foreground">{{ dialog.message }}</p>
    </div>

    <div class="flex-1 overflow-y-auto py-4">
      <div v-if="details.length">
        <Separator class="mb-4" />
        <div class="rounded-lg border bg-muted/50 p-4">
          <div class="grid gap-2 text-sm">
            <div v-for="[key, value] in details" :key="key" class="grid grid-cols-3 gap-2">
              <span class="font-medium text-muted-foreground">{{ key }}</span>
              <span class="col-span-2 font-mono text-xs break-all">{{ value }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="dialog.severity === 'critical'" class="mt-4 flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/5 p-3 text-sm text-destructive">
        <svg class="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        此操作不可逆，请谨慎确认
      </div>
    </div>

    <div class="flex items-center justify-end gap-2 pt-4 border-t">
      <Button variant="outline" @click="emit('respond', 'rejected')">
        {{ dialog.rejectText || '拒绝' }}
      </Button>
      <Button
        :variant="dialog.severity === 'critical' ? 'destructive' : 'default'"
        @click="emit('respond', 'approved')"
      >
        {{ dialog.approveText || '批准' }}
      </Button>
    </div>
  </div>
</template>
