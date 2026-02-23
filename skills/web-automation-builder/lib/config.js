'use strict';

const path = require('path');
const os = require('os');
const fs = require('fs');

const SKILL_DIR = path.join(__dirname, '..');
const SKILLS_PARENT = path.dirname(SKILL_DIR);
const DATA_DIR = path.join(SKILLS_PARENT, 'web-automation-builder-data');

if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

const WORKFLOWS_DIR = path.join(DATA_DIR, 'workflows');
const RECORDINGS_DIR = path.join(DATA_DIR, 'recordings');
const RECORDING_FILE = path.join(DATA_DIR, '.recording.json');
const STOP_SIGNAL_FILE = path.join(DATA_DIR, '.stop-signal');
const RECORDING_RESULT_FILE = path.join(DATA_DIR, '.recording-result.json');

const PLAYWRIGHT_STATE_DIR = path.join(os.tmpdir(), 'playwright-skill');
const BROWSER_STATE_FILE = path.join(PLAYWRIGHT_STATE_DIR, 'browser-state.json');

const PLAYWRIGHT_TOOL = path.resolve(SKILL_DIR, '..', 'playwright', 'tool.js');
const GLOBAL_PLAYWRIGHT_TOOL = path.join(os.homedir(), '.cursor', 'skills', 'playwright', 'tool.js');

function getPlaywrightTool() {
  if (fs.existsSync(PLAYWRIGHT_TOOL)) return PLAYWRIGHT_TOOL;
  if (fs.existsSync(GLOBAL_PLAYWRIGHT_TOOL)) return GLOBAL_PLAYWRIGHT_TOOL;
  return null;
}

async function getBrowserWsEndpoint() {
  try {
    const data = await fs.promises.readFile(BROWSER_STATE_FILE, 'utf-8');
    const state = JSON.parse(data);
    return state?.wsEndpoint || null;
  } catch {
    return null;
  }
}

const MAX_BODY_SIZE = 512 * 1024;

const NETWORK_SKIP_EXTENSIONS = new Set([
  '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2',
  '.ttf', '.eot', '.ico', '.mp4', '.webm', '.mp3', '.map',
]);

const NETWORK_SKIP_HOSTS = new Set([
  'www.google-analytics.com', 'analytics.google.com', 'www.googletagmanager.com',
  'sentry.io', 'browser.sentry-cdn.com', 'cdn.segment.com',
  'fonts.googleapis.com', 'fonts.gstatic.com',
]);

const EVENT_POLL_INTERVAL_MS = 500;

module.exports = {
  SKILL_DIR,
  DATA_DIR,
  WORKFLOWS_DIR,
  RECORDINGS_DIR,
  RECORDING_FILE,
  STOP_SIGNAL_FILE,
  RECORDING_RESULT_FILE,
  PLAYWRIGHT_TOOL,
  BROWSER_STATE_FILE,
  MAX_BODY_SIZE,
  NETWORK_SKIP_EXTENSIONS,
  NETWORK_SKIP_HOSTS,
  EVENT_POLL_INTERVAL_MS,
  getPlaywrightTool,
  getBrowserWsEndpoint,
};
