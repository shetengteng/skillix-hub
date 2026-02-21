'use strict';

const playwright = require('playwright-core');
const { getBrowserWsEndpoint, readJson, writeJson, TRACER_STATE_FILE } = require('./config');

const MAX_BODY_SIZE = 512 * 1024;

class Recorder {
  constructor() {
    this._browser = null;
    this._cdpSessions = [];
    this._requests = new Map();
    this._completedRequests = [];
    this._recording = false;
    this._sessionName = null;
    this._startTime = null;
    this._urlFilter = null;
  }

  async start(options = {}) {
    const wsEndpoint = options.wsEndpoint || await getBrowserWsEndpoint();
    if (!wsEndpoint) {
      throw new Error(
        'No browser found. Start Playwright browser first:\n' +
        '  node skills/playwright/tool.js navigate \'{"url":"https://example.com"}\''
      );
    }

    this._browser = await playwright.chromium.connectOverCDP(wsEndpoint, { timeout: 5000 });
    this._sessionName = options.name || `trace-${Date.now()}`;
    this._startTime = new Date().toISOString();
    this._urlFilter = options.filter || null;
    this._requests.clear();
    this._completedRequests = [];
    this._recording = true;

    for (const context of this._browser.contexts()) {
      for (const page of context.pages()) {
        await this._attachToPage(page);
      }
      context.on('page', page => this._attachToPage(page));
    }

    await writeJson(TRACER_STATE_FILE, {
      recording: true,
      sessionName: this._sessionName,
      startTime: this._startTime,
      wsEndpoint,
      pid: process.pid,
    });

    return {
      sessionName: this._sessionName,
      startTime: this._startTime,
      pages: this._browser.contexts().reduce((n, c) => n + c.pages().length, 0),
    };
  }

  async _attachToPage(page) {
    let cdp;
    try {
      cdp = await page.context().newCDPSession(page);
    } catch {
      return;
    }
    this._cdpSessions.push(cdp);

    await cdp.send('Network.enable');

    cdp.on('Network.requestWillBeSent', event => {
      if (!this._recording) return;
      if (this._shouldSkip(event.request.url)) return;

      this._requests.set(event.requestId, {
        requestId: event.requestId,
        url: event.request.url,
        method: event.request.method,
        requestHeaders: event.request.headers,
        postData: event.request.postData || null,
        resourceType: event.type || 'Other',
        timestamp: event.timestamp,
        wallTime: event.wallTime,
        initiator: event.initiator?.type || 'other',
      });
    });

    cdp.on('Network.responseReceived', event => {
      if (!this._recording) return;
      const req = this._requests.get(event.requestId);
      if (!req) return;

      req.status = event.response.status;
      req.statusText = event.response.statusText;
      req.responseHeaders = event.response.headers;
      req.mimeType = event.response.mimeType;
      req.protocol = event.response.protocol;
      req.responseTimestamp = event.timestamp;
    });

    cdp.on('Network.loadingFinished', async event => {
      if (!this._recording) return;
      const req = this._requests.get(event.requestId);
      if (!req) return;

      req.encodedDataLength = event.encodedDataLength;

      if (this._isTextMime(req.mimeType) && event.encodedDataLength < MAX_BODY_SIZE) {
        try {
          const { body, base64Encoded } = await cdp.send('Network.getResponseBody', {
            requestId: event.requestId,
          });
          req.responseBody = base64Encoded ? Buffer.from(body, 'base64').toString('utf-8') : body;
        } catch {
          req.responseBody = null;
        }
      }

      this._requests.delete(event.requestId);
      this._completedRequests.push(req);
    });

    cdp.on('Network.loadingFailed', event => {
      const req = this._requests.get(event.requestId);
      if (!req) return;
      req.error = event.errorText;
      req.canceled = event.canceled || false;
      this._requests.delete(event.requestId);
      this._completedRequests.push(req);
    });
  }

  _shouldSkip(url) {
    if (this._urlFilter) {
      return !url.includes(this._urlFilter);
    }
    return false;
  }

  _isTextMime(mime) {
    if (!mime) return false;
    return (
      mime.includes('json') ||
      mime.includes('text') ||
      mime.includes('xml') ||
      mime.includes('javascript') ||
      mime.includes('html') ||
      mime.includes('css') ||
      mime.includes('form-urlencoded')
    );
  }

  getRequests() {
    return [...this._completedRequests];
  }

  getStatus() {
    return {
      recording: this._recording,
      sessionName: this._sessionName,
      startTime: this._startTime,
      capturedRequests: this._completedRequests.length,
      pendingRequests: this._requests.size,
    };
  }

  async stop() {
    this._recording = false;
    const endTime = new Date().toISOString();

    for (const cdp of this._cdpSessions) {
      try { await cdp.detach(); } catch {}
    }
    this._cdpSessions = [];

    if (this._browser) {
      try { await this._browser.close(); } catch {}
      this._browser = null;
    }

    await writeJson(TRACER_STATE_FILE, { recording: false });

    return {
      sessionName: this._sessionName,
      startTime: this._startTime,
      endTime,
      totalRequests: this._completedRequests.length,
    };
  }

  buildSessionData() {
    return {
      session: {
        name: this._sessionName,
        startTime: this._startTime,
        endTime: new Date().toISOString(),
        totalRequests: this._completedRequests.length,
      },
      requests: this._completedRequests.map(r => ({
        url: r.url,
        method: r.method,
        resourceType: r.resourceType,
        requestHeaders: r.requestHeaders,
        postData: r.postData,
        status: r.status,
        statusText: r.statusText,
        responseHeaders: r.responseHeaders,
        mimeType: r.mimeType,
        responseBody: r.responseBody || null,
        encodedDataLength: r.encodedDataLength,
        error: r.error || null,
        initiator: r.initiator,
        wallTime: r.wallTime,
      })),
    };
  }
}

async function getTracerState() {
  return await readJson(TRACER_STATE_FILE);
}

module.exports = { Recorder, getTracerState };
