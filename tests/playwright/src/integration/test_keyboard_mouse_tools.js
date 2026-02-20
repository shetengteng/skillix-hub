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

function test_keydown() {
  run('navigate', { url: 'https://example.com' });
  const r = run('keydown', { key: 'Shift' });
  assert(r.code && r.code.includes("keyboard.down('Shift')"), 'keydown generates code');
}

function test_keyup() {
  const r = run('keyup', { key: 'Shift' });
  assert(r.code && r.code.includes("keyboard.up('Shift')"), 'keyup generates code');
}

function test_mouseDown() {
  const r = run('mouseDown', {});
  assert(r.code && r.code.includes('mouse.down'), 'mouseDown generates code');
}

function test_mouseUp() {
  const r = run('mouseUp', {});
  assert(r.code && r.code.includes('mouse.up'), 'mouseUp generates code');
}

function test_mouseDrag() {
  const r = run('mouseDrag', { startX: 10, startY: 10, endX: 200, endY: 200 });
  assert(r.code && r.code.includes('mouse.move') && r.code.includes('mouse.down') && r.code.includes('mouse.up'),
    'mouseDrag generates full drag sequence code');
}

function main() {
  console.log('test_keyboard_mouse_tools:');
  try { runMeta('stop'); } catch {}
  try {
    test_keydown();
    test_keyup();
    test_mouseDown();
    test_mouseUp();
    test_mouseDrag();
  } finally {
    try { runMeta('stop'); } catch {}
  }
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
