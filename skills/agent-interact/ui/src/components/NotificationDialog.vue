<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import type { NotificationDialog } from '@/lib/types'

const props = defineProps<{ dialog: NotificationDialog }>()
defineEmits<{ respond: [action: string, data?: unknown] }>()

const visible = ref(true)

const iconMap: Record<string, { path: string; color: string; bg: string }> = {
  info:    { path: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z', color: 'text-blue-500', bg: 'bg-blue-50' },
  success: { path: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', color: 'text-green-500', bg: 'bg-green-50' },
  warning: { path: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z', color: 'text-yellow-500', bg: 'bg-yellow-50' },
  error:   { path: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z', color: 'text-red-500', bg: 'bg-red-50' },
}

const icon = computed(() => iconMap[props.dialog.level ?? 'info'] ?? iconMap.info!)

let timer: ReturnType<typeof setTimeout> | null = null

onMounted(() => {
  const autoClose = props.dialog.autoClose
  if (autoClose && autoClose > 0) {
    timer = setTimeout(() => { visible.value = false }, autoClose * 1000)
  }
})

onUnmounted(() => { if (timer) clearTimeout(timer) })
</script>

<template>
  <div v-if="visible" class="flex h-screen flex-col p-5 pt-10">
    <div class="flex items-start gap-3">
      <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full" :class="icon.bg">
        <svg class="h-5 w-5" :class="icon.color" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" :d="icon.path" />
        </svg>
      </div>
      <div class="flex-1 min-w-0">
        <h2 class="text-base font-semibold text-foreground">{{ dialog.title || dialog.level }}</h2>
        <p v-if="dialog.message" class="mt-2 text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">{{ dialog.message }}</p>
      </div>
    </div>
  </div>
</template>
