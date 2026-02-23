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
