'use strict';

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const playwright = require('playwright-core');
const { ensureDir } = require('./config');

const STATE_FILE = 'browser-state.json';
const SERVER_SCRIPT = path.join(__dirname, 'server.js');

class BrowserManager {
  constructor(config) {
    this._config = config;
    this._stateDir = config.stateDir;
    this._browser = null;
    this._browserContext = null;
  }

  _stateFilePath() {
    return path.join(this._stateDir, STATE_FILE);
  }

  async _readState() {
    try {
      const data = await fs.promises.readFile(this._stateFilePath(), 'utf-8');
      return JSON.parse(data);
    } catch {
      return null;
    }
  }

  async _clearState() {
    try {
      await fs.promises.unlink(this._stateFilePath());
    } catch {}
  }

  async connect() {
    const state = await this._readState();
    if (state?.wsEndpoint) {
      try {
        this._browser = await playwright.chromium.connectOverCDP(state.wsEndpoint, { timeout: 3000 });
        const contexts = this._browser.contexts();
        this._browserContext = contexts[0] || await this._browser.newContext(this._config.browser.contextOptions);
        return { browser: this._browser, browserContext: this._browserContext, reused: true };
      } catch {
        await this._clearState();
      }
    }
    return this._launch();
  }

  async _launch() {
    await ensureDir(this._stateDir);

    const env = { ...process.env };
    if (this._config.browser.launchOptions.headless)
      env.PLAYWRIGHT_SKILL_HEADLESS = 'true';
    if (this._config.browser.launchOptions.channel)
      env.PLAYWRIGHT_SKILL_CHANNEL = this._config.browser.launchOptions.channel;
    if (this._config.browser.browserName)
      env.PLAYWRIGHT_SKILL_BROWSER = this._config.browser.browserName;

    const child = spawn(process.execPath, [SERVER_SCRIPT], {
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe'],
      env,
    });

    const serverInfo = await new Promise((resolve, reject) => {
      let data = '';
      let errData = '';
      const timeout = setTimeout(() => reject(new Error('Browser server startup timeout')), 20000);
      child.stdout.on('data', chunk => {
        data += chunk.toString();
        const nl = data.indexOf('\n');
        if (nl !== -1) {
          clearTimeout(timeout);
          try {
            resolve(JSON.parse(data.substring(0, nl)));
          } catch (e) {
            reject(new Error('Invalid server response: ' + data));
          }
        }
      });
      child.stderr.on('data', chunk => { errData += chunk.toString(); });
      child.on('error', e => { clearTimeout(timeout); reject(e); });
      child.on('exit', code => { clearTimeout(timeout); reject(new Error(`Server exited with code ${code}: ${errData}`)); });
    });

    child.stdout.destroy();
    child.stderr.destroy();
    child.unref();

    await new Promise(r => setTimeout(r, 1500));

    this._browser = await playwright.chromium.connectOverCDP(serverInfo.wsEndpoint, { timeout: 10000 });
    const contexts = this._browser.contexts();
    this._browserContext = contexts[0] || await this._browser.newContext(this._config.browser.contextOptions);

    return { browser: this._browser, browserContext: this._browserContext, reused: false };
  }

  async close() {
    const state = await this._readState();
    if (state?.pid) {
      try { process.kill(state.pid, 'SIGTERM'); } catch {}
    }
    if (this._browser) {
      await this._browser.close().catch(() => {});
      this._browser = null;
      this._browserContext = null;
    }
    await this._clearState();
    await new Promise(r => setTimeout(r, 300));
  }

  async status() {
    const state = await this._readState();
    if (!state)
      return { running: false };
    try {
      const browser = await playwright.chromium.connectOverCDP(state.wsEndpoint, { timeout: 2000 });
      const contexts = browser.contexts();
      const pages = contexts.reduce((acc, ctx) => acc + ctx.pages().length, 0);
      await browser.close();
      return { running: true, ...state, pages };
    } catch {
      await this._clearState();
      return { running: false };
    }
  }
}

module.exports = { BrowserManager };
