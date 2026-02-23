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

function test_exporter() {
  const sandbox = makeSandbox('exporter');
  try {
    const { exportScript, toPlaywrightScript } = require(path.join(SKILL_DIR, 'lib/exporter'));

    const wf = {
      id: 'wf-export-test',
      name: 'Export Test',
      params: [{ id: 'query', label: 'Search Query', type: 'text', required: true }],
      steps: [
        { seq: 1, command: 'navigate', args: { url: 'https://example.com' }, locators: null },
        { seq: 2, command: 'type', args: { ref: 'e3', text: '{{query}}' }, locators: { css: '#search', placeholder: 'Search...' } },
        { seq: 3, command: 'click', args: { ref: 'e5', element: 'Go' }, locators: { text: 'Go', role: 'button' } },
        { seq: 4, command: 'screenshot', args: {}, locators: null },
      ],
      createdAt: '2026-02-23T10:00:00Z',
    };

    const script = toPlaywrightScript(wf);
    assert(script.includes("require('playwright')"), 'script imports playwright');
    assert(script.includes('page.goto'), 'script has navigate');
    assert(script.includes('params.query'), 'script references param');
    assert(script.includes('getByPlaceholder'), 'script uses placeholder locator for type');
    assert(script.includes("getByText"), 'script uses text locator for click');
    assert(script.includes('screenshot'), 'script has screenshot');
    assert(script.includes('QUERY'), 'script has env var for param');

    const outPath = path.join(sandbox, 'test-export.js');
    const result = exportScript(wf, outPath);
    assert(result === outPath, 'exportScript returns output path');
    assert(fs.existsSync(outPath), 'exportScript creates file');
  } finally {
    cleanSandbox(sandbox);
  }
}

test_exporter();
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
