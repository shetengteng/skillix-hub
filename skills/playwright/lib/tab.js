'use strict';

const { asLocator } = require('playwright-core/lib/utils');
const { waitForCompletion } = require('./utils');

class Tab {
  constructor(context, page, onClose) {
    this.context = context;
    this.page = page;
    this._onPageClose = onClose;
    this._modalStates = [];
    this._requests = [];
    this._consoleMessages = [];
    this._initialized = false;

    page.on('console', msg => {
      this._consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
        timestamp: Date.now(),
        toString: () => `[${msg.type().toUpperCase()}] ${msg.text()}`,
      });
    });

    page.on('pageerror', error => {
      this._consoleMessages.push({
        type: 'error',
        text: error.message,
        timestamp: Date.now(),
        toString: () => error.stack || error.message,
      });
    });

    page.on('request', request => this._requests.push(request));

    page.on('close', () => {
      this._onPageClose(this);
    });

    page.on('filechooser', chooser => {
      this.setModalState({
        type: 'fileChooser',
        description: 'File chooser',
        fileChooser: chooser,
      });
    });

    page.on('dialog', dialog => {
      this.setModalState({
        type: 'dialog',
        description: `"${dialog.type()}" dialog with message "${dialog.message()}"`,
        dialog,
      });
    });

    page.setDefaultNavigationTimeout(context.config.timeouts.navigation);
    page.setDefaultTimeout(context.config.timeouts.action);
    this._initialized = true;
  }

  modalStates() {
    return this._modalStates;
  }

  setModalState(state) {
    this._modalStates.push(state);
  }

  clearModalState(state) {
    this._modalStates = this._modalStates.filter(s => s !== state);
  }

  async safeTitle() {
    try {
      return await this.page.title();
    } catch {
      return '';
    }
  }

  async navigate(url) {
    this._requests = [];
    try {
      await this.page.goto(url, { waitUntil: 'domcontentloaded' });
    } catch (e) {
      const mightBeDownload = e.message.includes('net::ERR_ABORTED') || e.message.includes('Download is starting');
      if (!mightBeDownload)
        throw e;
      await new Promise(r => setTimeout(r, 500));
      return;
    }
    await this.page.waitForLoadState('load', { timeout: 5000 }).catch(() => {});
  }

  async captureSnapshot() {
    const snapshot = await this.page._snapshotForAI();
    this._lastSnapshotTime = Date.now();
    return snapshot.full;
  }

  async refLocator(params) {
    if (!this._lastSnapshotTime || (Date.now() - this._lastSnapshotTime > 500))
      await this.captureSnapshot();
    try {
      let locator = this.page.locator(`aria-ref=${params.ref}`);
      if (params.element)
        locator = locator.describe(params.element);
      const { resolvedSelector } = await locator._resolveSelector();
      return { locator, resolved: asLocator('javascript', resolvedSelector) };
    } catch {
      throw new Error(`Ref ${params.ref} not found in the current page snapshot. Try capturing a new snapshot.`);
    }
  }

  async resolveLocator(params) {
    if (params.ref) return this.refLocator(params);

    let locator;
    let resolved;

    if (params.selector) {
      locator = this.page.locator(params.selector);
      resolved = `locator('${params.selector.replace(/'/g, "\\'")}')`;
    } else if (params.text) {
      locator = this.page.getByText(params.text, { exact: false });
      resolved = `getByText('${params.text.replace(/'/g, "\\'")}')`;
    } else if (params.role) {
      const opts = params.name ? { name: params.name } : {};
      locator = this.page.getByRole(params.role, opts);
      resolved = params.name
        ? `getByRole('${params.role}', { name: '${params.name.replace(/'/g, "\\'")}' })`
        : `getByRole('${params.role}')`;
    } else if (params.placeholder) {
      locator = this.page.getByPlaceholder(params.placeholder);
      resolved = `getByPlaceholder('${params.placeholder.replace(/'/g, "\\'")}')`;
    } else if (params.label) {
      locator = this.page.getByLabel(params.label);
      resolved = `getByLabel('${params.label.replace(/'/g, "\\'")}')`;
    } else if (params.testId) {
      locator = this.page.getByTestId(params.testId);
      resolved = `getByTestId('${params.testId.replace(/'/g, "\\'")}')`;
    } else {
      throw new Error('No locator provided: need ref, selector, text, role, placeholder, label, or testId');
    }

    await locator.waitFor({ state: 'visible', timeout: params.timeout || 10000 });
    return { locator, resolved };
  }

  async refLocators(paramsList) {
    return Promise.all(paramsList.map(p => this.refLocator(p)));
  }

  async consoleMessageCount() {
    let errors = 0, warnings = 0;
    for (const msg of this._consoleMessages) {
      if (msg.type === 'error') errors++;
      else if (msg.type === 'warning') warnings++;
    }
    return { total: this._consoleMessages.length, errors, warnings };
  }

  async consoleMessages(level) {
    const levels = ['error', 'warning', 'info', 'debug'];
    const threshold = levels.indexOf(level || 'info');
    return this._consoleMessages.filter(msg => {
      const msgLevel = msg.type === 'error' || msg.type === 'assert' ? 0
        : msg.type === 'warning' ? 1
        : msg.type === 'debug' ? 3
        : 2;
      return msgLevel <= threshold;
    });
  }

  async clearConsoleMessages() {
    this._consoleMessages = [];
  }

  async requests() {
    return this._requests;
  }

  async clearRequests() {
    this._requests = [];
  }

  async waitForCompletion(callback) {
    return waitForCompletion(this, callback);
  }

  async waitForTimeout(time) {
    const blocked = this._modalStates.some(s => s.type === 'dialog');
    if (blocked) {
      await new Promise(f => setTimeout(f, time));
      return;
    }
    await this.page.evaluate(() => new Promise(f => setTimeout(f, 1000))).catch(() => {});
  }

  isCurrentTab() {
    return this === this.context.currentTab();
  }
}

module.exports = { Tab };
