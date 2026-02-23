'use strict';

const { app, BrowserWindow, Notification } = require('electron');
const path = require('path');
const WebSocket = require('ws');

const port = parseInt(process.argv[2] || '7890', 10);
const serverUrl = `http://127.0.0.1:${port}`;
const wsUrl = `ws://127.0.0.1:${port}/ws`;

const windows = new Map();
let ws = null;
let reconnectTimer = null;

const WINDOW_SIZES = {
  confirm:  { width: 560, height: 520 },
  wait:     { width: 500, height: 380 },
  chart:    { width: 780, height: 620 },
  form:     { width: 580, height: 700 },
  approval: { width: 580, height: 560 },
  progress: { width: 560, height: 520 },
};

function createDialogWindow(dialog) {
  const size = WINDOW_SIZES[dialog.type] || { width: 520, height: 440 };

  const win = new BrowserWindow({
    width: size.width,
    height: size.height,
    alwaysOnTop: true,
    center: true,
    frame: false,
    resizable: true,
    minimizable: false,
    maximizable: false,
    fullscreenable: false,
    skipTaskbar: false,
    titleBarStyle: 'hidden',
    trafficLightPosition: { x: 12, y: 12 },
    backgroundColor: '#09090b',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.loadURL(`${serverUrl}?dialogId=${dialog.id}`);

  win.on('closed', () => {
    windows.delete(dialog.id);
  });

  windows.set(dialog.id, win);
  return win;
}

function showNotification(dialog) {
  if (!Notification.isSupported()) return;
  const levelEmoji = { success: '\u2705', warning: '\u26a0\ufe0f', error: '\u274c', info: '\u2139\ufe0f' };
  const emoji = levelEmoji[dialog.level] || '';
  new Notification({
    title: `${emoji} ${dialog.title || 'Agent Interact'}`,
    body: dialog.message || '',
    silent: false,
  }).show();
}

function connectWs() {
  if (ws && ws.readyState <= WebSocket.OPEN) return;

  ws = new WebSocket(wsUrl);

  ws.on('open', () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  });

  ws.on('message', (raw) => {
    try {
      const msg = JSON.parse(raw.toString());

      if (msg.event === 'dialog:open') {
        const dialog = msg.data;
        if (dialog.type === 'notification') {
          showNotification(dialog);
          return;
        }
        if (!windows.has(dialog.id)) {
          createDialogWindow(dialog);
        }
      }

      if (msg.event === 'dialog:close') {
        const id = msg.data?.id;
        const win = windows.get(id);
        if (win && !win.isDestroyed()) {
          win.close();
        }
        windows.delete(id);
      }
    } catch { /* ignore */ }
  });

  ws.on('close', () => {
    ws = null;
    scheduleReconnect();
  });

  ws.on('error', () => {
    try { ws?.close(); } catch { /* ok */ }
  });
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connectWs();
  }, 2000);
}

app.on('ready', () => {
  connectWs();
});

app.on('window-all-closed', (e) => {
  e.preventDefault();
});

app.dock?.hide();
