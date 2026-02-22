<script setup lang="ts">
import { onMounted } from 'vue'
import { useWsClient } from '@/lib/ws-client'
import type {
  ConfirmDialog as ConfirmType, WaitDialog as WaitType, ChartDialog as ChartType,
  NotificationDialog as NotificationType, FormDialog as FormType,
  ApprovalDialog as ApprovalType, ProgressDialog as ProgressType,
} from '@/lib/types'
import ConfirmDialog from './ConfirmDialog.vue'
import WaitDialog from './WaitDialog.vue'
import ChartDialog from './ChartDialog.vue'
import NotificationDialog from './NotificationDialog.vue'
import FormDialog from './FormDialog.vue'
import ApprovalDialog from './ApprovalDialog.vue'
import ProgressDialog from './ProgressDialog.vue'

const { dialogs, connected, connect, respond } = useWsClient()

onMounted(() => connect())

function onRespond(id: string, action: string, data?: unknown) {
  respond(id, action, data)
}
</script>

<template>
  <div class="min-h-screen bg-background">
    <div v-if="dialogs.length === 0" class="flex min-h-screen flex-col items-center justify-center gap-4 text-muted-foreground">
      <div class="relative">
        <div class="flex h-24 w-24 items-center justify-center rounded-2xl border-2 border-dashed border-muted-foreground/20">
          <svg class="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
          </svg>
        </div>
        <div class="absolute -bottom-1 -right-1 h-3 w-3 rounded-full"
             :class="connected ? 'bg-green-500' : 'bg-red-500'" />
      </div>
      <div class="text-center">
        <p class="text-lg font-medium text-foreground">Agent Interact</p>
        <p class="text-sm">{{ connected ? '等待 Agent 发起交互...' : '正在连接服务...' }}</p>
      </div>
    </div>

    <template v-for="d in dialogs" :key="d.id">
      <ConfirmDialog
        v-if="d.type === 'confirm'"
        :dialog="(d as ConfirmType)"
        @respond="(action, data) => onRespond(d.id, action, data)"
      />
      <WaitDialog
        v-else-if="d.type === 'wait'"
        :dialog="(d as WaitType)"
        @respond="(action, data) => onRespond(d.id, action, data)"
      />
      <ChartDialog
        v-else-if="d.type === 'chart'"
        :dialog="(d as ChartType)"
        @respond="(action, data) => onRespond(d.id, action, data)"
      />
      <NotificationDialog
        v-else-if="d.type === 'notification'"
        :dialog="(d as NotificationType)"
        @respond="(action, data) => onRespond(d.id, action, data)"
      />
      <FormDialog
        v-else-if="d.type === 'form'"
        :dialog="(d as FormType)"
        @respond="(action, data) => onRespond(d.id, action, data)"
      />
      <ApprovalDialog
        v-else-if="d.type === 'approval'"
        :dialog="(d as ApprovalType)"
        @respond="(action, data) => onRespond(d.id, action, data)"
      />
      <ProgressDialog
        v-else-if="d.type === 'progress'"
        :dialog="(d as ProgressType)"
        @respond="(action, data) => onRespond(d.id, action, data)"
      />
    </template>
  </div>
</template>
