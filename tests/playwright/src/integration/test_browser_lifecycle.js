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

function run(cmd) {
  return JSON.parse(execSync(`node tool.js ${cmd}`, {
    cwd: SKILL_DIR, encoding: 'utf-8', timeout: 45000,
    env: { ...process.env, PLAYWRIGHT_SKILL_HEADLESS: 'true' },
  }));
}

function test_startAndStatus() {
  const startResult = run('start');
  assert(startResult.result && startResult.result.includes('Browser'), 'start returns result');

  const status = run('status');
  assert(status.running === true, 'status shows running');
}

function test_stopAndStatus() {
  const stopResult = run('stop');
  assert(stopResult.result.includes('stopped'), 'stop returns stopped');

  const status = run('status');
  assert(status.running === false, 'status shows not running');
}

function test_doubleStart() {
  run('start');
  const second = run('start');
  assert(second.result.includes('already running'), 'double start detected');
  run('stop');
}

function main() {
  console.log('test_browser_lifecycle:');
  try {
    run('stop');
  } catch {}

  test_startAndStatus();
  test_stopAndStatus();
  test_doubleStart();

  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
