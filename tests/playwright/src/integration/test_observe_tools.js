#!/usr/bin/env node
'use strict';

const { execSync } = require('child_process');
const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/playwright');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function run(cmd, params = {}) {
  const paramsStr = JSON.stringify(params).replace(/'/g, "'\\''");
  return JSON.parse(execSync(`node tool.js ${cmd} '${paramsStr}'`, {
    cwd: SKILL_DIR, encoding: 'utf-8', timeout: 45000,
    env: { ...process.env, PLAYWRIGHT_SKILL_HEADLESS: 'true' },
  }));
}

function runMeta(cmd) {
  return JSON.parse(execSync(`node tool.js ${cmd}`, {
    cwd: SKILL_DIR, encoding: 'utf-8', timeout: 45000,
    env: { ...process.env, PLAYWRIGHT_SKILL_HEADLESS: 'true' },
  }));
}

function test_consoleMessages() {
  run('navigate', { url: 'https://example.com' });
  const r = run('consoleMessages', { level: 'info' });
  assert(r.result !== undefined, 'consoleMessages returns result');
  assert(r.result.includes('Total messages'), 'consoleMessages includes header');
}

function test_consoleClear() {
  const r = run('consoleClear', {});
  assert(r.result && r.result.includes('cleared'), 'consoleClear returns cleared');
}

function test_networkRequests() {
  run('navigate', { url: 'https://example.com' });
  const r = run('networkRequests', { includeStatic: false });
  assert(r.result !== undefined, 'networkRequests returns result');
}

function test_networkClear() {
  const r = run('networkClear', {});
  assert(r.result && r.result.includes('cleared'), 'networkClear returns cleared');
}

function test_screenshot() {
  run('navigate', { url: 'https://example.com' });
  const r = run('screenshot', { type: 'png' });
  assert(r.result && r.result.includes('Screenshot'), 'screenshot returns file link');
}

function test_tabs_list() {
  const r = run('tabs', { action: 'list' });
  assert(r.result && r.result.includes('(current)'), 'tabs list shows current');
}

function test_tabs_new_close() {
  run('tabs', { action: 'new' });
  const list = run('tabs', { action: 'list' });
  assert(list.result.includes('1:'), 'new tab created');
  run('tabs', { action: 'close', index: 1 });
  const list2 = run('tabs', { action: 'list' });
  assert(!list2.result.includes('1:'), 'tab closed');
}

function test_tabs_select() {
  run('tabs', { action: 'new' });
  const r = run('tabs', { action: 'select', index: 0 });
  assert(r.result && r.result.includes('(current)'), 'tab selected');
  run('tabs', { action: 'close', index: 1 });
}

function main() {
  console.log('test_observe_tools:');
  try { runMeta('stop'); } catch {}
  try {
    test_consoleMessages();
    test_consoleClear();
    test_networkRequests();
    test_networkClear();
    test_screenshot();
    test_tabs_list();
    test_tabs_new_close();
    test_tabs_select();
  } finally {
    try { runMeta('stop'); } catch {}
  }
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
