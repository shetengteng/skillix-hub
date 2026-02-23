'use strict';

const http = require('http');
const path = require('path');
const fs = require('fs');
const express = require('express');
const { WebSocketServer } = require('ws');
const DialogManager = require('./dialog-manager');
const { DEFAULT_PORT, UI_DIST, PID_FILE } = require('./config');
const { validateAndNormalizeCustomDialog } = require('./custom-dialog');

function createServer(port = DEFAULT_PORT) {
  const app = express();
  const dm = new DialogManager();

  app.use(express.json());

  if (fs.existsSync(path.join(UI_DIST, 'index.html'))) {
    app.use(express.static(UI_DIST));
  }

  app.get('/api/status', (_req, res) => {
    res.json({ status: 'running', port, activeDialogs: dm.list().length, connectedClients: dm.clientCount() });
  });

  app.get('/api/dialogs', (_req, res) => {
    res.json(dm.list());
  });

  app.post('/api/dialog', async (req, res) => {
    const request = req.body;
    if (!request || !request.type) {
      return res.status(400).json({ error: 'type is required' });
    }
    const validTypes = ['confirm', 'wait', 'chart', 'notification', 'form', 'approval', 'progress', 'custom'];
    if (!validTypes.includes(request.type)) {
      return res.status(400).json({ error: `Invalid type. Must be one of: ${validTypes.join(', ')}` });
    }

    let normalizedRequest = request;
    if (request.type === 'custom') {
      const validated = validateAndNormalizeCustomDialog(request);
      if (!validated.ok) {
        return res.status(400).json({
          error: 'Invalid custom schema',
          details: validated.errors,
        });
      }
      normalizedRequest = validated.value;
    }

    try {
      if (normalizedRequest.type === 'notification') {
        const id = dm.notify(normalizedRequest);
        return res.json({ result: { dialogId: id, action: 'delivered' }, error: null });
      }
      const result = await dm.create(normalizedRequest);
      res.json({ result, error: null });
    } catch (e) {
      res.status(500).json({ result: null, error: e.message });
    }
  });

  app.delete('/api/dialog/:id', (req, res) => {
    const ok = dm.cancel(req.params.id);
    res.json({ cancelled: ok });
  });

  if (fs.existsSync(path.join(UI_DIST, 'index.html'))) {
    app.get('*', (_req, res) => {
      res.sendFile(path.join(UI_DIST, 'index.html'));
    });
  }

  const server = http.createServer(app);
  const wss = new WebSocketServer({ server, path: '/ws' });

  wss.on('connection', (ws) => {
    dm.addClient(ws);

    ws.on('message', (raw) => {
      try {
        const msg = JSON.parse(raw.toString());
        if (msg.event === 'dialog:response' && msg.data) {
          const response = {
            action: msg.data.action,
            data: msg.data.data || null,
          };
          if (typeof msg.data.valid === 'boolean') response.valid = msg.data.valid;
          if (Array.isArray(msg.data.errors)) response.errors = msg.data.errors;
          dm.respond(msg.data.id, response);
        }
      } catch { /* ignore malformed messages */ }
    });

    ws.on('close', () => dm.removeClient(ws));
  });

  return {
    start(callback) {
      server.listen(port, '127.0.0.1', () => {
        fs.writeFileSync(PID_FILE, String(process.pid));
        if (callback) callback(port);
      });
    },
    stop() {
      dm.shutdown();
      wss.close();
      server.close();
      try { fs.unlinkSync(PID_FILE); } catch { /* ok */ }
    },
    server,
    dm,
  };
}

module.exports = { createServer };
