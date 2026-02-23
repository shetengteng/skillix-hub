#!/usr/bin/env node
'use strict';

const path = require('path');
const fs = require('fs');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/web-automation-builder');
const TESTDATA_DIR = path.resolve(__dirname, '../../testdata/runtime');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function makeSandbox(label) {
  const id = `${label}-${Date.now()}`;
  const dir = path.join(TESTDATA_DIR, id);
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function cleanSandbox(dir) {
  try { fs.rmSync(dir, { recursive: true, force: true }); } catch { /* ok */ }
}

function test_store() {
  const sandbox = makeSandbox('store');
  try {
    const configMod = require(path.join(SKILL_DIR, 'lib/config'));
    const savedDir = configMod.WORKFLOWS_DIR;
    configMod.WORKFLOWS_DIR = path.join(sandbox, 'workflows');

    delete require.cache[require.resolve(path.join(SKILL_DIR, 'lib/store'))];
    const store = require(path.join(SKILL_DIR, 'lib/store'));

    const wf = {
      id: 'wf-test-001',
      name: 'Test Workflow',
      steps: [{ seq: 1, command: 'navigate', args: { url: 'https://example.com' } }],
      params: [],
      createdAt: new Date().toISOString(),
    };

    store.save(wf);
    assert(fs.existsSync(path.join(sandbox, 'workflows', 'wf-test-001.json')), 'store.save creates file');

    const loaded = store.load('wf-test-001');
    assert(loaded !== null, 'store.load returns workflow');
    assert(loaded.name === 'Test Workflow', 'store.load preserves name');
    assert(loaded.steps.length === 1, 'store.load preserves steps');

    const items = store.list();
    assert(items.length === 1, 'store.list returns 1 item');
    assert(items[0].id === 'wf-test-001', 'store.list returns correct id');
    assert(items[0].stepCount === 1, 'store.list returns stepCount');

    const removed = store.remove('wf-test-001');
    assert(removed === true, 'store.remove returns true');
    assert(!fs.existsSync(path.join(sandbox, 'workflows', 'wf-test-001.json')), 'store.remove deletes file');

    const removeMissing = store.remove('wf-nonexistent');
    assert(removeMissing === false, 'store.remove returns false for missing');

    const loadMissing = store.load('wf-nonexistent');
    assert(loadMissing === null, 'store.load returns null for missing');

    configMod.WORKFLOWS_DIR = savedDir;
  } finally {
    cleanSandbox(sandbox);
  }
}

test_store();
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
