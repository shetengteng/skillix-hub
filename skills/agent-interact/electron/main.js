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

const BASE_SIZES = {
  confirm:      { width: 500, height: 440 },
  wait:         { width: 440, height: 400 },
  chart:        { width: 720, height: 560 },
  form:         { width: 520, height: 560 },
  approval:     { width: 520, height: 500 },
  progress:     { width: 500, height: 520 },
  custom:       { width: 620, height: 560 },
  notification: { width: 420, height: 200 },
};

function estimateWindowSize(dialog) {
  const base = BASE_SIZES[dialog.type] || { width: 480, height: 400 };
  let { width, height } = base;

  if (dialog.type === 'notification' && dialog.message) {
    const lines = Math.ceil(dialog.message.length / 40);
    height = Math.max(height, 120 + lines * 22);
  }

  if (dialog.type === 'confirm' && dialog.options) {
    height = Math.max(height, 240 + dialog.options.length * 76);
  }

  if (dialog.type === 'form' && dialog.fields) {
    height = Math.max(height, 240 + dialog.fields.length * 84);
  }

  if (dialog.type === 'progress' && dialog.steps) {
    height = Math.max(height, 280 + dialog.steps.length * 52);
  }

  if (dialog.type === 'custom' && dialog.content) {
    let contentHeight = 0;
    for (const node of dialog.content) {
      switch (node.kind) {
        case 'heading': contentHeight += 40; break;
        case 'text': contentHeight += 30; break;
        case 'divider': contentHeight += 20; break;
        case 'alert': contentHeight += 50; break;
        case 'badge': contentHeight += 32; break;
        case 'kv': contentHeight += (node.items ? node.items.length * 28 : 60) + 16; break;
        case 'progress': contentHeight += 50; break;
        case 'table': contentHeight += 40 + (node.rows ? node.rows.length * 36 : 0); break;
        case 'chart': contentHeight += 280; width = Math.max(width, 640); break;
        case 'code': contentHeight += 80; break;
        case 'image': contentHeight += 200; break;
        case 'input': case 'select': contentHeight += 70; break;
        case 'textarea': contentHeight += 100; break;
        case 'checkbox': contentHeight += 40; break;
        case 'row': case 'column': case 'grid': case 'section': case 'group':
          contentHeight += 60 + (node.children ? node.children.length * 50 : 0);
          break;
        default: contentHeight += 40;
      }
    }
    height = Math.max(height, 200 + contentHeight);

    if (dialog.meta?.maxWidth === '2xl') width = Math.max(width, 800);
    else if (dialog.meta?.maxWidth === 'xl') width = Math.max(width, 700);
  }

  return {
    width: Math.min(width, 1200),
    height: Math.min(height, 900),
  };
}

function createDialogWindow(dialog) {
  const size = estimateWindowSize(dialog);

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
    backgroundColor: '#ffffff',
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
          if (!windows.has(dialog.id)) {
            const win = createDialogWindow(dialog);
            const autoClose = dialog.autoClose || 8;
            setTimeout(() => {
              if (win && !win.isDestroyed()) win.close();
              windows.delete(dialog.id);
            }, autoClose * 1000);
          }
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
