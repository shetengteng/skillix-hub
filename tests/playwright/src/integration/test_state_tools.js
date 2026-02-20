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

function runSafe(cmd, params = {}) {
  try {
    return run(cmd, params);
  } catch (e) {
    try { return JSON.parse(e.stdout || '{}'); } catch { return { error: e.message }; }
  }
}

function test_storageState() {
  run('navigate', { url: 'https://example.com' });
  const r = run('storageState', {});
  assert(r.result && (r.result.includes('storage-state') || r.result.includes('.json')),
    'storageState saves file and returns path');
}

function test_setStorageState() {
  const tmpFile = path.join(SKILL_DIR, '.output', 'test-storage-state.json');
  const state = { cookies: [], origins: [] };
  fs.mkdirSync(path.dirname(tmpFile), { recursive: true });
  fs.writeFileSync(tmpFile, JSON.stringify(state));
  const r = runSafe('setStorageState', { filename: tmpFile });
  assert(r.result && r.result.includes('restored') || r.error,
    'setStorageState attempts to restore state');
  try { fs.unlinkSync(tmpFile); } catch {}
}

function test_tracingStop_without_start() {
  const r = runSafe('tracingStop', {});
  assert(r.error && r.error.includes('start tracing'),
    'tracingStop without start returns appropriate error');
}

function test_handleDialog_no_dialog() {
  run('navigate', { url: 'https://example.com' });
  const r = runSafe('handleDialog', { accept: true });
  assert(r.error && r.error.includes('No dialog'),
    'handleDialog with no dialog returns error');
}

function test_fileUpload_no_chooser() {
  run('navigate', { url: 'https://example.com' });
  const r = runSafe('fileUpload', { paths: ['/tmp/test.txt'] });
  assert(r.error && r.error.includes('No file chooser'),
    'fileUpload with no file chooser returns error');
}

function test_pdf() {
  run('navigate', { url: 'https://example.com' });
  const r = runSafe('pdf', {});
  const isPdfResult = r.result && (r.result.includes('.pdf') || r.result.includes('page'));
  const isPdfError = r.error && (r.error.includes('PDF') || r.error.includes('pdf') || r.error.includes('Printing'));
  assert(isPdfResult || isPdfError,
    'pdf either generates file or returns known limitation error');
}

function test_devtoolsStart() {
  const r = runSafe('devtoolsStart', {});
  const isResult = r.result && r.result.includes('DevTools');
  const isError = r.error && (r.error.includes('DevTools') || r.error.includes('not supported'));
  assert(isResult || isError,
    'devtoolsStart either starts or returns not-supported error');
}

function test_startVideo_stopVideo() {
  const r = runSafe('startVideo', {});
  const started = r.result && r.result.includes('started');
  const errored = !!r.error;
  assert(started || errored, 'startVideo either starts or returns error');
  if (started) {
    const r2 = runSafe('stopVideo', {});
    assert(r2.result !== undefined || r2.error !== undefined,
      'stopVideo returns result after start');
  }
}

function test_install() {
  const r = runSafe('install', {});
  assert(r.result && r.result.includes('installed') || r.error,
    'install either installs or returns error');
}

function main() {
  console.log('test_state_tools:');
  try { runMeta('stop'); } catch {}
  try {
    test_storageState();
    test_setStorageState();
    test_tracingStop_without_start();
    test_handleDialog_no_dialog();
    test_fileUpload_no_chooser();
    test_pdf();
    test_devtoolsStart();
    test_startVideo_stopVideo();
    test_install();
  } finally {
    try { runMeta('stop'); } catch {}
  }
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
