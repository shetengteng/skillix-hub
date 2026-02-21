'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const PW_STATE_FILE = path.join(os.tmpdir(), 'playwright-skill', 'browser-state.json');

function readPlaywrightState() {
  try {
    const data = fs.readFileSync(PW_STATE_FILE, 'utf-8');
    return JSON.parse(data);
  } catch {
    return null;
  }
}

async function getPlaywright() {
  try {
    return require('playwright-core');
  } catch {
    return null;
  }
}

async function connectOrLaunch(pw) {
  const state = readPlaywrightState();
  if (state?.wsEndpoint) {
    try {
      const browser = await pw.chromium.connectOverCDP(state.wsEndpoint, { timeout: 3000 });
      return { browser, reused: true };
    } catch {}
  }

  const headless = os.platform() === 'linux' && !process.env.DISPLAY;
  const browser = await pw.chromium.launch({
    channel: 'chrome',
    headless,
  });
  return { browser, reused: false };
}

async function renderPage(url, config, options = {}) {
  const { waitSelector, timeout = config.browserTimeout } = options;

  const pw = await getPlaywright();
  if (!pw) {
    return {
      html: null,
      error: 'playwright-core not available. Run: cd skills/web-content-reader && npm install',
    };
  }

  let browser = null;
  let page = null;
  let reused = false;

  try {
    const conn = await connectOrLaunch(pw);
    browser = conn.browser;
    reused = conn.reused;

    const contexts = browser.contexts();
    const context = contexts[0] || await browser.newContext();
    page = await context.newPage();

    await page.goto(url, { waitUntil: 'domcontentloaded', timeout });

    if (waitSelector) {
      await page.waitForSelector(waitSelector, { timeout });
    } else {
      await page.waitForLoadState('networkidle', { timeout }).catch(() => {});
    }

    const html = await page.evaluate(() => document.documentElement.outerHTML);

    if (!html || typeof html !== 'string') {
      return { html: null, error: 'Empty page content from browser' };
    }

    if (html.length > config.maxContentLength) {
      return { html: html.substring(0, config.maxContentLength), error: null, truncated: true };
    }

    return { html, error: null };
  } catch (e) {
    return { html: null, error: e.message };
  } finally {
    if (page) await page.close().catch(() => {});
    if (browser && !reused) await browser.close().catch(() => {});
  }
}

module.exports = { renderPage };
