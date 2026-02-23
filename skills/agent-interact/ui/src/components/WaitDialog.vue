<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import type { WaitDialog } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'

const props = defineProps<{ dialog: WaitDialog }>()
const emit = defineEmits<{ respond: [action: string, data?: unknown] }>()

const elapsed = ref(0)
const timeout = computed(() => (props.dialog.timeout || 60) * 1000)
const progress = computed(() => Math.min((elapsed.value / timeout.value) * 100, 100))

let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  timer = setInterval(() => { elapsed.value += 100 }, 100)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="flex h-screen flex-col p-6 pt-10">
    <div class="mb-1">
      <h2 class="text-lg font-semibold">{{ dialog.title || '等待操作' }}</h2>
      <p v-if="dialog.message" class="mt-1 text-sm text-muted-foreground">{{ dialog.message }}</p>
    </div>

    <div class="flex flex-1 flex-col items-center justify-center gap-6">
      <div class="relative flex h-20 w-20 items-center justify-center">
        <div class="absolute inset-0 animate-ping rounded-full bg-primary/20" />
        <div class="relative flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          <svg class="h-8 w-8 animate-pulse text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      </div>

      <div class="w-full space-y-1">
        <Progress :model-value="progress" class="h-1.5" />
        <p class="text-center text-xs text-muted-foreground">
          {{ Math.ceil((timeout - elapsed) / 1000) }}s 剩余
        </p>
      </div>
    </div>

    <div class="flex items-center justify-end gap-2 pt-4 border-t">
      <Button variant="outline" @click="emit('respond', '__cancelled')">
        {{ dialog.cancelText || '取消' }}
      </Button>
      <Button @click="emit('respond', 'confirmed')">
        {{ dialog.confirmText || '已完成' }}
      </Button>
    </div>
  </div>
</template>
