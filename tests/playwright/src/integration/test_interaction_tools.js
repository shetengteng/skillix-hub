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

function getRef(snapshot, pattern) {
  const match = snapshot.match(pattern);
  return match ? match[1] : null;
}

function test_click() {
  run('navigate', { url: 'https://example.com' });
  const snap = run('snapshot', {});
  const ref = getRef(snap.snapshot, /link "Learn more" \[ref=(e\d+)\]/);
  assert(ref, 'found Learn more ref');
  if (!ref) return;
  const r = run('click', { ref, element: 'Learn more' });
  assert(r.code && r.code.includes('click'), 'click generates code');
  assert(r.snapshot, 'click returns snapshot');
}

function test_hover() {
  run('navigate', { url: 'https://example.com' });
  const snap = run('snapshot', {});
  const ref = getRef(snap.snapshot, /link "Learn more" \[ref=(e\d+)\]/);
  if (!ref) { assert(false, 'no ref for hover'); return; }
  const r = run('hover', { ref, element: 'Learn more' });
  assert(r.code && r.code.includes('hover'), 'hover generates code');
}

function test_pressKey() {
  run('navigate', { url: 'https://example.com' });
  const r = run('pressKey', { key: 'Tab' });
  assert(r.code && r.code.includes('keyboard.press'), 'pressKey generates code');
}

function test_mouseMove() {
  const r = run('mouseMove', { x: 100, y: 200 });
  assert(r.code && r.code.includes('mouse.move'), 'mouseMove generates code');
}

function test_mouseClick() {
  const r = run('mouseClick', { x: 100, y: 200 });
  assert(r.code && r.code.includes('mouse'), 'mouseClick generates code');
}

function test_mouseWheel() {
  const r = run('mouseWheel', { deltaX: 0, deltaY: 100 });
  assert(r.code && r.code.includes('mouse.wheel'), 'mouseWheel generates code');
}

function test_waitFor() {
  run('navigate', { url: 'https://example.com' });
  const r = run('waitFor', { text: 'Example Domain' });
  assert(r.result && r.result.includes('Waited'), 'waitFor returns result');
}

function test_resize() {
  const r = run('resize', { width: 800, height: 600 });
  assert(r.code && r.code.includes('setViewportSize'), 'resize generates code');
}

function main() {
  console.log('test_interaction_tools:');
  try { runMeta('stop'); } catch {}
  try {
    test_click();
    test_hover();
    test_pressKey();
    test_mouseMove();
    test_mouseClick();
    test_mouseWheel();
    test_waitFor();
    test_resize();
  } finally {
    try { runMeta('stop'); } catch {}
  }
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
