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

function test_navigateAndSnapshot() {
  const result = run('navigate', { url: 'https://example.com' });
  assert(result.snapshot && result.snapshot.includes('Example Domain'), 'navigate returns snapshot with Example Domain');
  assert(result.code && result.code.includes('goto'), 'navigate returns code');
  assert(result.tabs && result.tabs.length > 0, 'navigate returns tabs');

  const snap = run('snapshot', {});
  assert(snap.snapshot && snap.snapshot.includes('[ref='), 'snapshot contains refs');
  assert(snap.snapshot.includes('Example Domain'), 'snapshot preserves page across calls');
}

function test_clickLink() {
  run('navigate', { url: 'https://example.com' });
  const snap = run('snapshot', {});
  const refMatch = snap.snapshot.match(/link "Learn more" \[ref=(e\d+)\]/);
  if (!refMatch) {
    assert(false, 'could not find Learn more link ref');
    return;
  }
  const ref = refMatch[1];
  const clickResult = run('click', { ref, element: 'Learn more' });
  assert(clickResult.code && clickResult.code.includes('click'), 'click returns code');
  assert(clickResult.snapshot, 'click returns snapshot');
}

function test_tabs() {
  const tabList = run('tabs', { action: 'list' });
  assert(tabList.result && tabList.result.includes('(current)'), 'tabs list shows current tab');
}

function test_consoleAndNetwork() {
  run('navigate', { url: 'https://example.com' });
  const console = run('consoleMessages', { level: 'info' });
  assert(console.result !== undefined, 'consoleMessages returns result');

  const network = run('networkRequests', { includeStatic: false });
  assert(network.result !== undefined, 'networkRequests returns result');
}

function test_cookies() {
  run('navigate', { url: 'https://example.com' });
  const cookies = run('cookieList', {});
  assert(cookies.result !== undefined, 'cookieList returns result');
}

function main() {
  console.log('test_navigation_flow:');
  try { runMeta('stop'); } catch {}

  try {
    test_navigateAndSnapshot();
    test_clickLink();
    test_tabs();
    test_consoleAndNetwork();
    test_cookies();
  } finally {
    try { runMeta('stop'); } catch {}
  }

  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
