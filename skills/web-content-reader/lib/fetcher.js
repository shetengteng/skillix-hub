'use strict';

async function fetchPage(url, config) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), config.fetchTimeout);

  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: {
        'User-Agent': config.userAgent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
      },
      redirect: 'follow',
    });

    if (!res.ok) {
      return { html: null, status: res.status, error: `HTTP ${res.status} ${res.statusText}` };
    }

    const contentType = res.headers.get('content-type') || '';
    if (!contentType.includes('text/html') && !contentType.includes('application/xhtml')) {
      return { html: null, status: res.status, error: `Unsupported content-type: ${contentType}` };
    }

    const html = await res.text();

    if (html.length > config.maxContentLength) {
      return { html: html.substring(0, config.maxContentLength), status: res.status, error: null, truncated: true };
    }

    return { html, status: res.status, error: null };
  } catch (e) {
    if (e.name === 'AbortError') {
      return { html: null, status: null, error: `Fetch timeout after ${config.fetchTimeout}ms` };
    }
    return { html: null, status: null, error: e.message };
  } finally {
    clearTimeout(timer);
  }
}

module.exports = { fetchPage };
