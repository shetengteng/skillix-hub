'use strict';

const os = require('os');
const path = require('path');
const fs = require('fs');

const defaultConfig = {
  browser: {
    browserName: 'chromium',
    launchOptions: {
      channel: 'chrome',
      headless: os.platform() === 'linux' && !process.env.DISPLAY,
    },
    contextOptions: {
      viewport: null,
    },
  },
  timeouts: {
    action: 5000,
    navigation: 60000,
  },
  outputDir: path.join(os.tmpdir(), 'playwright-skill-output'),
  stateDir: path.join(os.tmpdir(), 'playwright-skill'),
};

function resolveConfig(overrides = {}) {
  const config = { ...defaultConfig };

  if (overrides.browser)
    Object.assign(config.browser, overrides.browser);
  if (overrides.timeouts)
    Object.assign(config.timeouts, overrides.timeouts);
  if (overrides.outputDir)
    config.outputDir = overrides.outputDir;

  if (process.env.PLAYWRIGHT_SKILL_BROWSER)
    config.browser.browserName = process.env.PLAYWRIGHT_SKILL_BROWSER;
  if (process.env.PLAYWRIGHT_SKILL_HEADLESS === 'true')
    config.browser.launchOptions.headless = true;
  if (process.env.PLAYWRIGHT_SKILL_HEADLESS === 'false')
    config.browser.launchOptions.headless = false;
  if (process.env.PLAYWRIGHT_SKILL_CHANNEL)
    config.browser.launchOptions.channel = process.env.PLAYWRIGHT_SKILL_CHANNEL;

  return config;
}

async function ensureDir(dir) {
  await fs.promises.mkdir(dir, { recursive: true });
  return dir;
}

async function outputFile(config, prefix, ext, suggestedFilename) {
  if (suggestedFilename && path.isAbsolute(suggestedFilename)) {
    await ensureDir(path.dirname(suggestedFilename));
    return suggestedFilename;
  }
  if (suggestedFilename) {
    const fullPath = path.resolve(process.cwd(), suggestedFilename);
    await ensureDir(path.dirname(fullPath));
    return fullPath;
  }
  const dir = await ensureDir(config.outputDir);
  return path.resolve(dir, `${prefix}-${new Date().toISOString().replace(/[:.]/g, '-')}.${ext}`);
}

module.exports = { defaultConfig, resolveConfig, ensureDir, outputFile };
