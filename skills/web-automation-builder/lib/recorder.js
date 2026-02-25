'use strict';

const fs = require('fs');
const path = require('path');
const net = require('net');
const { spawn } = require('child_process');
const playwright = require('playwright-core');
const {
  SKILL_DIR, DATA_DIR, RECORDING_FILE, RECORDINGS_DIR, STOP_SIGNAL_FILE, RECORDING_RESULT_FILE,
  EVENT_POLL_INTERVAL_MS, BROWSER_STATE_FILE, filterNavigations,
} = require('./config');
const { buildInjectionScript, COLLECT_SCRIPT } = require('./injector');
const { NetworkMonitor } = require('./network-monitor');

const WELCOME_PAGE = path.join(SKILL_DIR, 'templates', 'welcome.html');

class Recorder {
  constructor() {
    this._browser = null;
    this._pages = [];
    this._networkMonitor = new NetworkMonitor();
    this._pollTimer = null;
    this._rawEvents = [];
    this._id = null;
    this._name = null;
    this._startedAt = null;
    this._chromePid = null;
  }

  async start(name) {
    const existingState = readState();
    if (existingState && existingState.active) {
      if (existingState.pid && isProcessAlive(existingState.pid)) {
        return { started: false, reason: `Already recording: ${existingState.name} (${existingState.id})` };
      }
      cleanupFiles();
    }

    const launchResult = await this._launchBrowser();
    if (launchResult.error) {
      return { started: false, reason: launchResult.error };
    }

    this._id = `wf-${Date.now()}`;
    this._name = name || 'Untitled';
    this._startedAt = new Date().toISOString();
    this._rawEvents = [];

    const contexts = this._browser.contexts();
    let initialPage = null;
    for (const ctx of contexts) {
      const pages = ctx.pages();
      for (const p of pages) {
        this._pages.push(p);
        await this._setupPage(p);
        if (!initialPage) initialPage = p;
      }
    }

    if (!initialPage && contexts.length > 0) {
      initialPage = await contexts[0].newPage();
      this._pages.push(initialPage);
      await this._setupPage(initialPage);
    }

    if (initialPage) {
      const welcomeUrl = `file://${WELCOME_PAGE}`;
      try { await initialPage.goto(welcomeUrl); } catch { /* ok */ }
    }

    for (const context of contexts) {
      context.on('page', async (page) => {
        this._pages.push(page);
        await this._setupPage(page);
      });
    }

    this._networkMonitor.start();
    cleanupFiles();
    this._writeState();

    return { started: true, id: this._id, name: this._name };
  }

  async _launchBrowser() {
    let execPath;
    try {
      const registry = require('playwright-core/lib/server').registry;
      const descriptor = registry.findExecutable('chrome') || registry.findExecutable('chromium');
      execPath = descriptor?.executablePath();
    } catch { /* ok */ }

    if (!execPath) {
      try {
        const bt = playwright.chromium;
        execPath = bt.executablePath('chrome');
      } catch { /* ok */ }
    }

    if (!execPath) {
      return { error: 'Cannot find Chrome/Chromium executable. Install Chrome or run: npx playwright install chromium' };
    }

    try {
      const oldState = JSON.parse(fs.readFileSync(BROWSER_STATE_FILE, 'utf-8'));
      if (oldState?.pid) {
        try { process.kill(oldState.pid, 'SIGTERM'); } catch { /* ok */ }
        await new Promise((r) => setTimeout(r, 1000));
      }
    } catch { /* no old state */ }

    const cdpPort = await findFreePort();
    const userDataDir = path.join(DATA_DIR, 'chrome-profile');
    fs.mkdirSync(userDataDir, { recursive: true });

    try { fs.unlinkSync(path.join(userDataDir, 'SingletonLock')); } catch { /* ok */ }

    const args = [
      `--remote-debugging-port=${cdpPort}`,
      `--user-data-dir=${userDataDir}`,
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-background-networking',
      '--disable-default-apps',
      '--disable-sync',
    ];

    const child = spawn(execPath, args, { detached: true, stdio: 'ignore' });
    child.unref();
    this._chromePid = child.pid;

    const ready = await waitForCDP(cdpPort, 15000);
    if (!ready) {
      try { process.kill(child.pid, 'SIGTERM'); } catch { /* ok */ }
      return { error: `Chrome started but CDP port ${cdpPort} not ready` };
    }

    const cdpEndpoint = `http://127.0.0.1:${cdpPort}`;

    fs.writeFileSync(BROWSER_STATE_FILE, JSON.stringify({
      wsEndpoint: cdpEndpoint,
      pid: child.pid,
      startedAt: new Date().toISOString(),
      source: 'web-automation-builder',
    }, null, 2));

    try {
      this._browser = await playwright.chromium.connectOverCDP(cdpEndpoint, { timeout: 10000 });
    } catch (e) {
      try { process.kill(child.pid, 'SIGTERM'); } catch { /* ok */ }
      return { error: `CDP connection failed: ${e.message}` };
    }

    return { error: null };
  }

  async _injectDOMListeners(pageOrFrame) {
    const script = buildInjectionScript();
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        await pageOrFrame.evaluate(script);
        return true;
      } catch {
        await new Promise((r) => setTimeout(r, 300 * (attempt + 1)));
      }
    }
    return false;
  }

  async _setupPage(page) {
    await this._networkMonitor.attachToPage(page);

    try {
      await page.context().addInitScript(buildInjectionScript());
    } catch { /* addInitScript may not work in CDP mode */ }

    await this._injectDOMListeners(page);

    let lastNavRequestUrl = null;
    page.on('request', (request) => {
      if (request.isNavigationRequest() && request.frame() === page.mainFrame()) {
        lastNavRequestUrl = request.url();
      }
    });

    page.on('framenavigated', async (frame) => {
      if (frame === page.mainFrame()) {
        const finalUrl = frame.url();
        if (lastNavRequestUrl && lastNavRequestUrl !== finalUrl) {
          this._rawEvents.push({
            type: 'navigation',
            timestamp: new Date().toISOString(),
            url: lastNavRequestUrl,
            redirectedTo: finalUrl,
          });
        }
        this._rawEvents.push({
          type: 'navigation',
          timestamp: new Date().toISOString(),
          url: finalUrl,
        });
        lastNavRequestUrl = null;
      }
    });

    page.on('load', async () => {
      await this._injectDOMListeners(page);
    });

    page.on('domcontentloaded', async () => {
      await this._injectDOMListeners(page);
    });
  }

  async _collectDOMFromAllPages() {
    let collected = false;
    for (const page of this._pages) {
      try {
        const raw = await page.evaluate(COLLECT_SCRIPT);
        const events = JSON.parse(raw);
        if (events.length > 0) {
          this._rawEvents.push(...events);
          collected = true;
        }
      } catch {
        try { await this._injectDOMListeners(page); } catch { /* ok */ }
      }
    }
    return collected;
  }

  async runDaemon() {
    while (true) {
      if (fs.existsSync(STOP_SIGNAL_FILE)) {
        break;
      }

      const domCollected = await this._collectDOMFromAllPages();

      const netEvents = this._networkMonitor.collectRequests();
      if (netEvents.length > 0) {
        this._rawEvents.push(...netEvents);
      }

      if (domCollected || netEvents.length > 0) {
        this._writeState();
      }

      await new Promise((r) => setTimeout(r, EVENT_POLL_INTERVAL_MS));
    }

    return this._finalize();
  }

  async _finalize() {
    await this._collectDOMFromAllPages();

    const netEvents = this._networkMonitor.collectRequests();
    this._rawEvents.push(...netEvents);

    this._networkMonitor.stop();
    await this._networkMonitor.detachAll();

    if (this._browser) {
      try { await this._browser.close(); } catch { /* ok */ }
      this._browser = null;
    }

    if (this._chromePid) {
      try { process.kill(this._chromePid, 'SIGTERM'); } catch { /* ok */ }
      this._chromePid = null;
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

    const domEvents = this._rawEvents.filter((e) => e.type !== 'network' && e.type !== 'navigation');
    const rawNavigations = this._rawEvents.filter((e) => e.type === 'navigation');
    const navigations = filterNavigations(rawNavigations);
    const apiRequests = this._rawEvents
      .filter((e) => e.type === 'network' && e.resourceType === 'Fetch')
      .map(({ type: _t, resourceType: _r, ...rest }) => rest);

    const summaryResult = {
      id: this._id,
      name: this._name,
      startedAt: this._startedAt,
      stoppedAt,
      eventCount: this._rawEvents.length,
      domCount: domEvents.length,
      networkCount: result.networkCount,
      summary: { domEvents, navigations, apiRequests },
    };

    this._saveRecording(summaryResult);

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

function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
    server.on('error', reject);
  });
}

async function waitForCDP(port, timeoutMs) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (res.ok) return true;
    } catch { /* not ready yet */ }
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
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
