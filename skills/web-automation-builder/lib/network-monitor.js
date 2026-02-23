'use strict';

const { MAX_BODY_SIZE, NETWORK_SKIP_EXTENSIONS, NETWORK_SKIP_HOSTS } = require('./config');

class NetworkMonitor {
  constructor() {
    this._cdpSessions = [];
    this._requests = new Map();
    this._completedRequests = [];
    this._recording = false;
  }

  async attachToPage(page) {
    let cdp;
    try {
      cdp = await page.context().newCDPSession(page);
    } catch {
      return;
    }
    this._cdpSessions.push(cdp);
    await cdp.send('Network.enable');

    cdp.on('Network.requestWillBeSent', (event) => {
      if (!this._recording) return;
      if (this._shouldSkip(event.request.url, event.type)) return;

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

    cdp.on('Network.responseReceived', (event) => {
      if (!this._recording) return;
      const req = this._requests.get(event.requestId);
      if (!req) return;

      req.status = event.response.status;
      req.statusText = event.response.statusText;
      req.responseHeaders = event.response.headers;
      req.mimeType = event.response.mimeType;
      req.responseTimestamp = event.timestamp;
    });

    cdp.on('Network.loadingFinished', async (event) => {
      if (!this._recording) return;
      const req = this._requests.get(event.requestId);
      if (!req) return;

      req.encodedDataLength = event.encodedDataLength;

      if (this._isTextMime(req.mimeType) && event.encodedDataLength < MAX_BODY_SIZE) {
        try {
          const { body, base64Encoded } = await cdp.send('Network.getResponseBody', {
            requestId: event.requestId,
          });
          req.responseBody = base64Encoded
            ? Buffer.from(body, 'base64').toString('utf-8')
            : body;
        } catch {
          req.responseBody = null;
        }
      }

      this._requests.delete(event.requestId);
      this._completedRequests.push(req);
    });

    cdp.on('Network.loadingFailed', (event) => {
      const req = this._requests.get(event.requestId);
      if (!req) return;
      req.error = event.errorText;
      req.canceled = event.canceled || false;
      this._requests.delete(event.requestId);
      this._completedRequests.push(req);
    });
  }

  start() {
    this._recording = true;
    this._requests.clear();
    this._completedRequests = [];
  }

  stop() {
    this._recording = false;
  }

  async detachAll() {
    for (const cdp of this._cdpSessions) {
      try { await cdp.detach(); } catch { /* ok */ }
    }
    this._cdpSessions = [];
  }

  collectRequests() {
    const requests = [...this._completedRequests];
    this._completedRequests = [];
    return requests.map((r) => ({
      type: 'network',
      timestamp: r.wallTime ? new Date(r.wallTime * 1000).toISOString() : new Date().toISOString(),
      request: {
        url: r.url,
        method: r.method,
        headers: r.requestHeaders,
        body: this._parseBody(r.postData),
        resourceType: r.resourceType,
      },
      response: {
        status: r.status,
        statusText: r.statusText,
        headers: r.responseHeaders,
        body: this._parseBody(r.responseBody),
        mimeType: r.mimeType,
      },
      error: r.error || null,
      encodedDataLength: r.encodedDataLength,
    }));
  }

  getStats() {
    return {
      captured: this._completedRequests.length,
      pending: this._requests.size,
    };
  }

  _shouldSkip(url, resourceType) {
    const skipTypes = new Set(['Image', 'Font', 'Stylesheet', 'Media']);
    if (skipTypes.has(resourceType)) return true;

    try {
      const parsed = new URL(url);
      if (NETWORK_SKIP_HOSTS.has(parsed.hostname)) return true;
      const ext = parsed.pathname.match(/\.\w+$/)?.[0]?.toLowerCase();
      if (ext && NETWORK_SKIP_EXTENSIONS.has(ext)) return true;
    } catch { /* invalid URL, don't skip */ }

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

  _parseBody(raw) {
    if (!raw) return null;
    try { return JSON.parse(raw); } catch { return raw; }
  }
}

module.exports = { NetworkMonitor };
