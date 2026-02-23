'use strict';

const fs = require('fs');
const path = require('path');
const playwright = require('playwright-core');
const {
  RECORDING_FILE, RECORDINGS_DIR, STOP_SIGNAL_FILE, RECORDING_RESULT_FILE,
  EVENT_POLL_INTERVAL_MS, getBrowserWsEndpoint, getPlaywrightTool,
} = require('./config');
const { buildInjectionScript, COLLECT_SCRIPT } = require('./injector');
const { NetworkMonitor } = require('./network-monitor');
const { execSync } = require('child_process');

class Recorder {
  constructor() {
    this._browser = null;
    this._page = null;
    this._networkMonitor = new NetworkMonitor();
    this._pollTimer = null;
    this._rawEvents = [];
    this._id = null;
    this._name = null;
    this._startedAt = null;
  }

  async start(name) {
    const existingState = readState();
    if (existingState && existingState.active) {
      if (existingState.pid && isProcessAlive(existingState.pid)) {
        return { started: false, reason: `Already recording: ${existingState.name} (${existingState.id})` };
      }
      cleanupFiles();
    }

    let wsEndpoint = await getBrowserWsEndpoint();
    if (!wsEndpoint) {
      const pw = getPlaywrightTool();
      if (!pw) {
        return { started: false, reason: 'Playwright Skill not found. Install it first.' };
      }
      try {
        execSync(`node "${pw}" navigate '{"url":"about:blank"}'`, {
          encoding: 'utf-8',
          timeout: 30000,
        });
      } catch (e) {
        return { started: false, reason: `Failed to launch browser: ${e.message}` };
      }
      await new Promise((r) => setTimeout(r, 2000));
      wsEndpoint = await getBrowserWsEndpoint();
      if (!wsEndpoint) {
        return { started: false, reason: 'Browser launched but wsEndpoint not found' };
      }
    }

    try {
      this._browser = await playwright.chromium.connectOverCDP(wsEndpoint, { timeout: 5000 });
    } catch (e) {
      return { started: false, reason: `CDP connection failed: ${e.message}` };
    }

    this._id = `wf-${Date.now()}`;
    this._name = name || 'Untitled';
    this._startedAt = new Date().toISOString();
    this._rawEvents = [];

    const contexts = this._browser.contexts();
    if (contexts.length > 0) {
      const pages = contexts[0].pages();
      if (pages.length > 0) {
        this._page = pages[0];
      }
    }

    if (this._page) {
      await this._setupPage(this._page);
    }

    for (const context of contexts) {
      context.on('page', async (page) => {
        await this._setupPage(page);
      });
    }

    this._networkMonitor.start();
    cleanupFiles();
    this._writeState();

    return { started: true, id: this._id, name: this._name };
  }

  async _setupPage(page) {
    await this._networkMonitor.attachToPage(page);
    try {
      await page.evaluate(buildInjectionScript());
    } catch { /* page might not be ready */ }

    page.on('framenavigated', async (frame) => {
      if (frame === page.mainFrame()) {
        this._rawEvents.push({
          type: 'navigation',
          timestamp: new Date().toISOString(),
          url: frame.url(),
        });
        try {
          await frame.evaluate(buildInjectionScript());
        } catch { /* ok */ }
      }
    });
  }

  async runDaemon() {
    while (true) {
      if (fs.existsSync(STOP_SIGNAL_FILE)) {
        break;
      }

      if (this._page) {
        try {
          const raw = await this._page.evaluate(COLLECT_SCRIPT);
          const events = JSON.parse(raw);
          if (events.length > 0) {
            this._rawEvents.push(...events);
            this._writeState();
          }
        } catch { /* page closed or navigated */ }
      }

      const netEvents = this._networkMonitor.collectRequests();
      if (netEvents.length > 0) {
        this._rawEvents.push(...netEvents);
        this._writeState();
      }

      await new Promise((r) => setTimeout(r, EVENT_POLL_INTERVAL_MS));
    }

    return this._finalize();
  }

  async _finalize() {
    if (this._page) {
      try {
        const raw = await this._page.evaluate(COLLECT_SCRIPT);
        const events = JSON.parse(raw);
        this._rawEvents.push(...events);
      } catch { /* ok */ }
    }

    const netEvents = this._networkMonitor.collectRequests();
    this._rawEvents.push(...netEvents);

    this._networkMonitor.stop();
    await this._networkMonitor.detachAll();

    if (this._browser) {
      try { this._browser.close(); } catch { /* ok */ }
      this._browser = null;
    }

    const stoppedAt = new Date().toISOString();
    const result = {
      id: this._id,
      name: this._name,
      startedAt: this._startedAt,
      stoppedAt,
      rawEvents: this._rawEvents,
      eventCount: this._rawEvents.length,
      networkCount: this._rawEvents.filter((e) => e.type === 'network').length,
      domCount: this._rawEvents.filter((e) => e.type !== 'network' && e.type !== 'navigation').length,
    };

    this._saveRecording(result);

    try {
      fs.writeFileSync(RECORDING_RESULT_FILE, JSON.stringify(result, null, 2));
    } catch { /* ok */ }

    try { fs.unlinkSync(RECORDING_FILE); } catch { /* ok */ }
    try { fs.unlinkSync(STOP_SIGNAL_FILE); } catch { /* ok */ }
    return result;
  }

  _writeState() {
    try {
      fs.writeFileSync(RECORDING_FILE, JSON.stringify({
        active: true,
        pid: process.pid,
        id: this._id,
        name: this._name,
        startedAt: this._startedAt,
        eventCount: this._rawEvents.length,
      }, null, 2));
    } catch { /* ok */ }
  }

  _saveRecording(result) {
    try {
      if (!fs.existsSync(RECORDINGS_DIR)) {
        fs.mkdirSync(RECORDINGS_DIR, { recursive: true });
      }
      const date = new Date().toISOString().slice(0, 10);
      const filename = `${date}-${result.id}.json`;
      fs.writeFileSync(
        path.join(RECORDINGS_DIR, filename),
        JSON.stringify(result, null, 2),
      );
    } catch { /* non-critical */ }
  }

  isRecording() {
    return this._id !== null;
  }

  getStatus() {
    if (this.isRecording()) {
      return {
        recording: true,
        id: this._id,
        name: this._name,
        startedAt: this._startedAt,
        eventCount: this._rawEvents.length,
        domCount: this._rawEvents.filter((e) => e.type !== 'network' && e.type !== 'navigation').length,
        networkCount: this._rawEvents.filter((e) => e.type === 'network').length,
      };
    }
    return { recording: false };
  }
}

function readState() {
  if (!fs.existsSync(RECORDING_FILE)) return null;
  try {
    return JSON.parse(fs.readFileSync(RECORDING_FILE, 'utf-8'));
  } catch {
    return null;
  }
}

function isProcessAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

function requestStop() {
  fs.writeFileSync(STOP_SIGNAL_FILE, new Date().toISOString());
}

function waitForResult(timeoutMs = 30000) {
  const start = Date.now();
  const pollMs = 200;

  while (Date.now() - start < timeoutMs) {
    if (fs.existsSync(RECORDING_RESULT_FILE)) {
      try {
        const data = fs.readFileSync(RECORDING_RESULT_FILE, 'utf-8');
        const result = JSON.parse(data);
        try { fs.unlinkSync(RECORDING_RESULT_FILE); } catch { /* ok */ }
        return result;
      } catch { /* retry */ }
    }

    const waitUntil = Date.now() + pollMs;
    while (Date.now() < waitUntil) { /* busy wait for sync context */ }
  }

  return null;
}

function cleanupFiles() {
  try { fs.unlinkSync(RECORDING_FILE); } catch { /* ok */ }
  try { fs.unlinkSync(STOP_SIGNAL_FILE); } catch { /* ok */ }
  try { fs.unlinkSync(RECORDING_RESULT_FILE); } catch { /* ok */ }
}

function getState() {
  return readState();
}

module.exports = {
  Recorder,
  readState,
  getState,
  requestStop,
  waitForResult,
  cleanupFiles,
  isProcessAlive,
};
