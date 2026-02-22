<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import type { NotificationDialog } from '@/lib/types'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const props = defineProps<{ dialog: NotificationDialog }>()
const emit = defineEmits<{ respond: [action: string, data?: unknown] }>()

const visible = ref(true)

const iconMap = {
  info: { path: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z', color: 'text-blue-500' },
  success: { path: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', color: 'text-green-500' },
  warning: { path: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z', color: 'text-yellow-500' },
  error: { path: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z', color: 'text-red-500' },
}

const icon = computed(() => iconMap[props.dialog.level] || iconMap.info)

let timer: ReturnType<typeof setTimeout> | null = null

onMounted(() => {
  const autoClose = props.dialog.autoClose
  if (autoClose && autoClose > 0) {
    timer = setTimeout(() => { visible.value = false }, autoClose * 1000)
  }
})

onUnmounted(() => { if (timer) clearTimeout(timer) })

function dismiss() {
  visible.value = false
  emit('respond', 'dismissed')
}
</script>

<template>
  <Transition name="slide">
    <div v-if="visible" class="fixed right-4 top-4 z-50 w-96">
      <Card class="shadow-lg border-l-4" :class="{
        'border-l-blue-500': dialog.level === 'info',
        'border-l-green-500': dialog.level === 'success',
        'border-l-yellow-500': dialog.level === 'warning',
        'border-l-red-500': dialog.level === 'error',
      }">
        <CardHeader class="flex flex-row items-start gap-3 p-4">
          <svg class="mt-0.5 h-5 w-5 shrink-0" :class="icon.color" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" :d="icon.path" />
          </svg>
          <div class="flex-1 space-y-1">
            <CardTitle class="text-sm font-medium">{{ dialog.title || dialog.level }}</CardTitle>
            <CardDescription v-if="dialog.message" class="text-sm">{{ dialog.message }}</CardDescription>
          </div>
          <Button variant="ghost" size="icon" class="-mr-2 -mt-2 h-6 w-6 shrink-0" @click="dismiss">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </Button>
        </CardHeader>
      </Card>
    </div>
  </Transition>
</template>

<style scoped>
.slide-enter-active { transition: all 0.3s ease-out; }
.slide-leave-active { transition: all 0.2s ease-in; }
.slide-enter-from { transform: translateX(100%); opacity: 0; }
.slide-leave-to { transform: translateX(100%); opacity: 0; }
</style>
