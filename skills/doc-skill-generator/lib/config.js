'use strict';

const path = require('path');
const fs = require('fs');
const os = require('os');

const SKILL_DIR = path.join(__dirname, '..');
const SKILLS_PARENT = path.dirname(SKILL_DIR);
const DATA_DIR = path.join(SKILLS_PARENT, 'doc-skill-generator-data');

const EXTRACTS_DIR = path.join(DATA_DIR, 'extracts');
const CACHE_DIR = path.join(DATA_DIR, 'cache');
const SPECS_DIR = path.join(DATA_DIR, 'specs');
const GENERATED_DIR = path.join(DATA_DIR, 'generated');

for (const dir of [EXTRACTS_DIR, CACHE_DIR, SPECS_DIR, GENERATED_DIR]) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

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
  EXTRACTS_DIR,
  CACHE_DIR,
  SPECS_DIR,
  GENERATED_DIR,
  getPlaywrightTool,
};
