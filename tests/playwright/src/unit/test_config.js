#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/playwright');
const { resolveConfig, ensureDir, outputFile } = require(path.join(SKILL_DIR, 'lib/config'));
const fs = require('fs');
const os = require('os');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function test_defaultConfig() {
  const config = resolveConfig();
  assert(config.browser.browserName === 'chromium', 'default browser is chromium');
  assert(config.browser.launchOptions.channel === 'chrome', 'default channel is chrome');
  assert(typeof config.timeouts.action === 'number', 'action timeout is number');
  assert(typeof config.timeouts.navigation === 'number', 'navigation timeout is number');
  assert(config.stateDir.includes('playwright-skill'), 'stateDir contains playwright-skill');
}

function test_overrides() {
  const config = resolveConfig({ browser: { browserName: 'firefox' }, timeouts: { action: 10000 } });
  assert(config.browser.browserName === 'firefox', 'browser override works');
  assert(config.timeouts.action === 10000, 'timeout override works');
}

function test_envOverrides() {
  process.env.PLAYWRIGHT_SKILL_BROWSER = 'webkit';
  process.env.PLAYWRIGHT_SKILL_HEADLESS = 'true';
  const config = resolveConfig();
  assert(config.browser.browserName === 'webkit', 'env browser override works');
  assert(config.browser.launchOptions.headless === true, 'env headless override works');
  delete process.env.PLAYWRIGHT_SKILL_BROWSER;
  delete process.env.PLAYWRIGHT_SKILL_HEADLESS;
}

async function test_ensureDir() {
  const tmpDir = path.join(os.tmpdir(), 'pw-skill-test-' + Date.now());
  const result = await ensureDir(tmpDir);
  assert(fs.existsSync(result), 'ensureDir creates directory');
  fs.rmdirSync(tmpDir);
}

async function test_outputFile() {
  const config = resolveConfig();
  const filePath = await outputFile(config, 'test', 'txt');
  assert(filePath.endsWith('.txt'), 'outputFile returns correct extension');
  assert(filePath.includes('test-'), 'outputFile includes prefix');
}

async function main() {
  console.log('test_config:');
  test_defaultConfig();
  test_overrides();
  test_envOverrides();
  await test_ensureDir();
  await test_outputFile();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
