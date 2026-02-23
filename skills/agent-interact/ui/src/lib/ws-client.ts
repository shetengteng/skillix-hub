import { ref, computed } from 'vue'
import type { DialogData, DialogRespondMeta, WsMessage } from './types'

const allDialogs = ref<DialogData[]>([])
const connected = ref(false)

let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null

function getTargetDialogId(): string | null {
  const params = new URLSearchParams(window.location.search)
  return params.get('dialogId')
}

const targetDialogId = getTargetDialogId()
const isElectron = !!(window as any).electronAPI?.isElectron

const dialogs = computed(() => {
  if (targetDialogId) {
    return allDialogs.value.filter((d) => d.id === targetDialogId)
  }
  return allDialogs.value
})

function getWsUrl(): string {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${location.host}/ws`
}

function connect() {
  if (ws && ws.readyState <= 1) return

  ws = new WebSocket(getWsUrl())

  ws.onopen = () => {
    connected.value = true
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  ws.onmessage = (event) => {
    try {
      const msg: WsMessage = JSON.parse(event.data)
      if (msg.event === 'dialog:open') {
        const d = msg.data as DialogData
        if (!allDialogs.value.find((x) => x.id === d.id)) {
          allDialogs.value.push(d)
        }
      } else if (msg.event === 'dialog:close') {
        const { id } = msg.data as { id: string }
        allDialogs.value = allDialogs.value.filter((x) => x.id !== id)
      }
    } catch { /* ignore */ }
  }

  ws.onclose = () => {
    connected.value = false
    scheduleReconnect()
  }

  ws.onerror = () => {
    ws?.close()
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    connect()
  }, 2000)
}

function respond(id: string, action: string, data?: unknown, meta?: DialogRespondMeta) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return
  ws.send(JSON.stringify({
    event: 'dialog:response',
    data: {
      id,
      action,
      data,
      valid: meta?.valid,
      errors: meta?.errors,
    },
  }))
  if (meta?.close !== false) {
    allDialogs.value = allDialogs.value.filter((x) => x.id !== id)
  }
}

export function useWsClient() {
  return { dialogs, connected, connect, respond, isElectron }
}
