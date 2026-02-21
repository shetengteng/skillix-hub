'use strict';

const os = require('os');
const path = require('path');
const fs = require('fs');

const PLAYWRIGHT_STATE_DIR = path.join(os.tmpdir(), 'playwright-skill');
const TRACER_STATE_DIR = path.join(os.tmpdir(), 'api-tracer');
const BROWSER_STATE_FILE = path.join(PLAYWRIGHT_STATE_DIR, 'browser-state.json');
const TRACER_STATE_FILE = path.join(TRACER_STATE_DIR, 'tracer-state.json');

async function ensureDir(dir) {
  await fs.promises.mkdir(dir, { recursive: true });
  return dir;
}

async function readJson(filePath) {
  try {
    const data = await fs.promises.readFile(filePath, 'utf-8');
    return JSON.parse(data);
  } catch {
    return null;
  }
}

async function writeJson(filePath, data) {
  await ensureDir(path.dirname(filePath));
  await fs.promises.writeFile(filePath, JSON.stringify(data, null, 2) + '\n', 'utf-8');
}

async function getBrowserWsEndpoint() {
  const state = await readJson(BROWSER_STATE_FILE);
  return state?.wsEndpoint || null;
}

module.exports = {
  PLAYWRIGHT_STATE_DIR,
  TRACER_STATE_DIR,
  BROWSER_STATE_FILE,
  TRACER_STATE_FILE,
  ensureDir,
  readJson,
  writeJson,
  getBrowserWsEndpoint,
};
