'use strict';

const crypto = require('crypto');
const { DEFAULT_TIMEOUT, MAX_TIMEOUT } = require('./config');

class DialogManager {
  constructor() {
    this._dialogs = new Map();
    this._wsClients = new Set();
    this.onEmpty = null;
  }

  addClient(ws) {
    this._wsClients.add(ws);
    for (const [id, dialog] of this._dialogs) {
      if (!dialog.resolved) {
        ws.send(JSON.stringify({ event: 'dialog:open', data: { id, ...dialog.request } }));
      }
    }
  }

  removeClient(ws) {
    this._wsClients.delete(ws);
  }

  clientCount() {
    let count = 0;
    for (const ws of this._wsClients) {
      if (ws.readyState === 1) count++;
    }
    return count;
  }

  create(request) {
    const id = `d-${crypto.randomBytes(6).toString('hex')}`;
    const timeout = Math.min(request.timeout || DEFAULT_TIMEOUT, MAX_TIMEOUT);

    return new Promise((resolve) => {
      const timer = setTimeout(() => {
        this._resolve(id, { action: '__timeout', data: null });
      }, timeout * 1000);

      this._dialogs.set(id, {
        request: { ...request, timeout },
        resolve,
        timer,
        resolved: false,
        createdAt: Date.now(),
      });

      this._broadcast({ event: 'dialog:open', data: { id, ...request, timeout } });

      resolve.__dialogId = id;
    });
  }

  notify(request) {
    const id = `n-${crypto.randomBytes(6).toString('hex')}`;
    const autoClose = request.autoClose || 8;

    this._dialogs.set(id, {
      request: { ...request },
      resolve: () => {},
      timer: null,
      resolved: false,
      createdAt: Date.now(),
    });

    this._broadcast({ event: 'dialog:open', data: { id, ...request } });

    setTimeout(() => {
      this._broadcast({ event: 'dialog:close', data: { id } });
      this._dialogs.delete(id);
      if (this._dialogs.size === 0 && typeof this.onEmpty === 'function') {
        this.onEmpty();
      }
    }, autoClose * 1000);

    return id;
  }

  respond(id, result) {
    if (!this._dialogs.has(id)) return false;
    this._resolve(id, result);
    return true;
  }

  cancel(id) {
    return this.respond(id, { action: '__cancelled', data: null });
  }

  list() {
    const out = [];
    for (const [id, d] of this._dialogs) {
      if (!d.resolved) {
        out.push({ id, type: d.request.type, title: d.request.title, createdAt: d.createdAt });
      }
    }
    return out;
  }

  _resolve(id, result) {
    const dialog = this._dialogs.get(id);
    if (!dialog || dialog.resolved) return;
    dialog.resolved = true;
    clearTimeout(dialog.timer);
    this._broadcast({ event: 'dialog:close', data: { id } });
    dialog.resolve({ dialogId: id, ...result });
    this._dialogs.delete(id);
    if (this._dialogs.size === 0 && typeof this.onEmpty === 'function') {
      this.onEmpty();
    }
  }

  _broadcast(message) {
    const payload = JSON.stringify(message);
    for (const ws of this._wsClients) {
      if (ws.readyState === 1) ws.send(payload);
    }
  }

  shutdown() {
    for (const [id] of this._dialogs) {
      this._resolve(id, { action: '__shutdown', data: null });
    }
  }
}

module.exports = DialogManager;
