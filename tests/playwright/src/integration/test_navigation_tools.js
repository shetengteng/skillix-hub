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

function test_navigate() {
  const r = run('navigate', { url: 'https://example.com' });
  assert(r.snapshot && r.snapshot.includes('Example Domain'), 'navigate returns correct snapshot');
  assert(r.code && r.code.includes('goto'), 'navigate generates code');
}

function test_snapshot() {
  const r = run('snapshot', {});
  assert(r.snapshot && r.snapshot.includes('[ref='), 'snapshot returns refs');
}

function test_reload() {
  const r = run('reload', {});
  assert(r.snapshot && r.snapshot.includes('Example Domain'), 'reload preserves page');
  assert(r.code && r.code.includes('reload'), 'reload generates code');
}

function test_goBack() {
  run('navigate', { url: 'https://example.com' });
  const r = run('goBack', {});
  assert(r.code && r.code.includes('goBack'), 'goBack generates code');
}

function test_goForward() {
  run('navigate', { url: 'https://example.com' });
  const r = run('goForward', {});
  assert(r.code && r.code.includes('goForward'), 'goForward generates code');
}

function main() {
  console.log('test_navigation_tools:');
  try { runMeta('stop'); } catch {}
  try {
    test_navigate();
    test_snapshot();
    test_reload();
    test_goBack();
    test_goForward();
  } finally {
    try { runMeta('stop'); } catch {}
  }
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
