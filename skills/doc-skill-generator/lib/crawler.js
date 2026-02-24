'use strict';

const { execFileSync } = require('child_process');
const { getPlaywrightTool } = require('./config');
const { loadTemplate } = require('./template');

const DEFAULT_CONFIG = {
  maxDepth: 3,
  maxPages: 50,
  pageTimeout: 30000,
  scrollWaitMs: 300,
};

function execPlaywright(command, args) {
  const tool = getPlaywrightTool();
  if (!tool) throw new Error('Playwright Skill not found');
  const argsJson = JSON.stringify(args);
  const result = execFileSync('node', [tool, command, argsJson], {
    encoding: 'utf-8',
    timeout: DEFAULT_CONFIG.pageTimeout,
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  return JSON.parse(result);
}

function parseEvalResult(result) {
  const raw = result.result || result;
  return typeof raw === 'string' ? JSON.parse(raw) : raw;
}

function isSameDomain(url, baseUrl) {
  try { return new URL(url).origin === new URL(baseUrl).origin; } catch { return false; }
}

function normalizeUrl(href, baseUrl) {
  try { const url = new URL(href, baseUrl); url.hash = ''; return url.href; } catch { return null; }
}

let _extractFn;
function getExtractAndLinksFn() {
  if (!_extractFn) _extractFn = loadTemplate('extract-and-links.js');
  return _extractFn;
}

function crawlSinglePage(url) {
  try { execPlaywright('navigate', { url }); } catch (e) {
    return { url, error: 'Navigate failed: ' + e.message, sections: [], links: [] };
  }
  try {
    const result = execPlaywright('evaluate', { function: getExtractAndLinksFn() });
    const data = parseEvalResult(result);
    return {
      url,
      title: data.title || '',
      sections: data.sections || [],
      links: data.links || [],
    };
  } catch (e) {
    return { url, error: 'Extract failed: ' + e.message, sections: [], links: [] };
  }
}

function crawlBFS(entryUrl, config = {}) {
  const cfg = { ...DEFAULT_CONFIG, ...config };
  const queue = [{ url: entryUrl, depth: 0 }];
  const visited = new Set();
  const pages = [];

  while (queue.length > 0 && pages.length < cfg.maxPages) {
    const { url, depth } = queue.shift();
    const normalized = normalizeUrl(url, entryUrl);
    if (!normalized || visited.has(normalized)) continue;
    visited.add(normalized);

    const page = crawlSinglePage(normalized);
    page.depth = depth;
    pages.push(page);

    if (depth < cfg.maxDepth && !page.error) {
      const rawLinks = page.links || [];
      const seen = new Set();
      for (const link of rawLinks) {
        const linkUrl = normalizeUrl(link.href, normalized);
        if (linkUrl && isSameDomain(linkUrl, entryUrl) && !visited.has(linkUrl) && !seen.has(linkUrl)) {
          seen.add(linkUrl);
          queue.push({ url: linkUrl, depth: depth + 1 });
        }
      }
    }

    delete page.links;
  }

  return { rootUrl: entryUrl, pages, totalPages: pages.length, crawlConfig: cfg };
}

function getSnapshot() {
  try { return execPlaywright('snapshot', {}).result || null; } catch { return null; }
}

module.exports = { crawlBFS, crawlSinglePage, execPlaywright, getSnapshot };
