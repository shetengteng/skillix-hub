'use strict';

const path = require('path');
const os = require('os');
const fs = require('fs');

const SKILL_DIR = path.join(__dirname, '..');

function getDataDir() {
  const projectLocal = path.join(process.cwd(), '.cursor', 'skills', 'web-automation-builder-data');
  const skillLocal = path.join(SKILL_DIR, 'workflows');

  if (fs.existsSync(projectLocal)) return projectLocal;
  if (fs.existsSync(skillLocal)) return path.dirname(skillLocal);

  fs.mkdirSync(projectLocal, { recursive: true });
  return projectLocal;
}

const DATA_DIR = getDataDir();
const WORKFLOWS_DIR = path.join(DATA_DIR, 'workflows');
const RECORDING_FILE = path.join(DATA_DIR, '.recording.json');

const PLAYWRIGHT_TOOL = path.resolve(SKILL_DIR, '..', 'playwright', 'tool.js');
const GLOBAL_PLAYWRIGHT_TOOL = path.join(os.homedir(), '.cursor', 'skills', 'playwright', 'tool.js');

function getPlaywrightTool() {
  if (fs.existsSync(PLAYWRIGHT_TOOL)) return PLAYWRIGHT_TOOL;
  if (fs.existsSync(GLOBAL_PLAYWRIGHT_TOOL)) return GLOBAL_PLAYWRIGHT_TOOL;
  return null;
}

module.exports = {
  SKILL_DIR,
  DATA_DIR,
  WORKFLOWS_DIR,
  RECORDING_FILE,
  PLAYWRIGHT_TOOL,
  getPlaywrightTool,
};
