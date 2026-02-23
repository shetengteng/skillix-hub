'use strict';

const { execSync } = require('child_process');
const { getPlaywrightTool } = require('./config');

const DEFAULT_CONFIG = {
  maxDepth: 3,
  maxPages: 50,
  pageTimeout: 15000,
  waitAfterNav: 2000,
  scrollRetries: 3,
  scrollWaitMs: 500,
};

function execPlaywright(command, args) {
  const tool = getPlaywrightTool();
  if (!tool) throw new Error('Playwright Skill not found');
  const argsJson = JSON.stringify(args);
  const result = execSync(`node "${tool}" ${command} '${argsJson}'`, {
    encoding: 'utf-8',
    timeout: 30000,
    stdio: ['pipe', 'pipe', 'pipe'],
  });
  return JSON.parse(result);
}

function isSameDomain(url, baseUrl) {
  try {
    return new URL(url).origin === new URL(baseUrl).origin;
  } catch {
    return false;
  }
}

function normalizeUrl(href, baseUrl) {
  try {
    const url = new URL(href, baseUrl);
    url.hash = '';
    return url.href;
  } catch {
    return null;
  }
}

function scrollToBottom() {
  try {
    execPlaywright('evaluate', {
      expression: 'window.scrollTo(0, document.body.scrollHeight)',
    });
  } catch { /* ok */ }
}

function extractPageContent() {
  try {
    const result = execPlaywright('evaluate', {
      expression: `
        (function() {
          const sections = [];
          const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
          
          if (headings.length === 0) {
            const body = document.body.innerText.trim();
            return { title: document.title, sections: [{ heading: '', level: 1, content: body, codeBlocks: [], tables: [], links: [] }] };
          }
          
          for (let i = 0; i < headings.length; i++) {
            const h = headings[i];
            const level = parseInt(h.tagName[1]);
            const heading = h.innerText.trim();
            
            let content = '';
            let sibling = h.nextElementSibling;
            const codeBlocks = [];
            const tables = [];
            
            while (sibling && !sibling.matches('h1, h2, h3, h4, h5, h6')) {
              if (sibling.matches('pre, code')) {
                const lang = sibling.className.match(/language-(\\w+)/);
                codeBlocks.push({ language: lang ? lang[1] : '', code: sibling.innerText.trim() });
              } else if (sibling.matches('table')) {
                const rows = [];
                sibling.querySelectorAll('tr').forEach(tr => {
                  const cells = [];
                  tr.querySelectorAll('th, td').forEach(cell => cells.push(cell.innerText.trim()));
                  rows.push(cells);
                });
                tables.push(rows);
              } else {
                content += sibling.innerText.trim() + '\\n';
              }
              sibling = sibling.nextElementSibling;
            }
            
            sections.push({ heading, level, content: content.trim(), codeBlocks, tables, links: [] });
          }
          
          return { title: document.title, sections };
        })()
      `,
    });
    return result.result || result;
  } catch (e) {
    return { title: '', sections: [{ heading: '', level: 1, content: `Extract error: ${e.message}`, codeBlocks: [], tables: [], links: [] }] };
  }
}

function getSnapshot() {
  try {
    const result = execPlaywright('snapshot', {});
    return result.result || result;
  } catch {
    return null;
  }
}

function getAllLinks(baseUrl) {
  try {
    const result = execPlaywright('evaluate', {
      expression: `
        (function() {
          const links = [];
          document.querySelectorAll('a[href]').forEach(a => {
            const href = a.getAttribute('href');
            const text = a.innerText.trim();
            if (href && text && !href.startsWith('#') && !href.startsWith('javascript:')) {
              links.push({ href, text });
            }
          });
          return links;
        })()
      `,
    });
    const rawLinks = result.result || result;
    if (!Array.isArray(rawLinks)) return [];

    const seen = new Set();
    return rawLinks
      .map(l => ({ url: normalizeUrl(l.href, baseUrl), text: l.text }))
      .filter(l => l.url && isSameDomain(l.url, baseUrl) && !seen.has(l.url) && seen.add(l.url));
  } catch {
    return [];
  }
}

function crawlSinglePage(url) {
  try {
    execPlaywright('navigate', { url });
  } catch (e) {
    return { url, error: `Navigate failed: ${e.message}`, sections: [], tabs: [] };
  }

  for (let i = 0; i < DEFAULT_CONFIG.scrollRetries; i++) {
    scrollToBottom();
    try {
      execSync(`sleep ${DEFAULT_CONFIG.scrollWaitMs / 1000}`, { stdio: 'pipe' });
    } catch { /* ok */ }
  }

  const content = extractPageContent();
  return {
    url,
    title: content.title || '',
    sections: content.sections || [],
    tabs: [],
  };
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

    if (depth < cfg.maxDepth) {
      const links = getAllLinks(normalized);
      for (const link of links) {
        if (!visited.has(link.url)) {
          queue.push({ url: link.url, depth: depth + 1 });
        }
      }
    }
  }

  return {
    rootUrl: entryUrl,
    pages,
    totalPages: pages.length,
    crawlConfig: cfg,
  };
}

module.exports = { crawlBFS, crawlSinglePage, execPlaywright, getSnapshot, getAllLinks };
