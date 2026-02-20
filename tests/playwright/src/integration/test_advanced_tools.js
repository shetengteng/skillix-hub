#!/usr/bin/env node
'use strict';

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
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

function test_runCode() {
  run('navigate', { url: 'https://example.com' });
  const r = run('runCode', { code: 'async (page) => { return await page.title(); }' });
  assert(r.result && r.result.includes('Example Domain'), 'runCode returns page title');
  assert(r.code && r.code.includes('page'), 'runCode generates code');
}

function test_verifyText() {
  run('navigate', { url: 'https://example.com' });
  const r = run('verifyText', { text: 'Example Domain' });
  assert(r.result && r.result.includes('Done'), 'verifyText finds text');
}

function test_verifyElement() {
  const r = run('verifyElement', { role: 'heading', accessibleName: 'Example Domain' });
  assert(r.result && r.result.includes('Done'), 'verifyElement finds heading');
  assert(r.code && r.code.includes('expect'), 'verifyElement generates test code');
}

function test_generateLocator() {
  const snap = run('snapshot', {});
  const match = snap.snapshot.match(/heading "Example Domain".*?\[ref=(e\d+)\]/);
  if (!match) { assert(false, 'no heading ref'); return; }
  const r = run('generateLocator', { ref: match[1], element: 'Example Domain heading' });
  assert(r.result && r.result.length > 0, 'generateLocator returns locator string');
}

function test_tracingStart() {
  const start = run('tracingStart', {});
  assert(start.result && start.result.includes('started'), 'tracingStart returns started');
}

function test_close() {
  const r = run('close', {});
  assert(r.result && r.result.includes('closed'), 'close returns closed');
}

function main() {
  console.log('test_advanced_tools:');
  try { runMeta('stop'); } catch {}
  try {
    test_runCode();
    test_verifyText();
    test_verifyElement();
    test_generateLocator();
    test_tracingStart();
    test_close();
  } finally {
    try { runMeta('stop'); } catch {}
  }
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
