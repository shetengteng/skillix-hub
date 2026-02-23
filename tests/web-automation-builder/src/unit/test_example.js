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

// --- response.js ---

function test_response() {
  const { success, error } = require(path.join(SKILL_DIR, 'lib/response'));

  const s = success({ msg: 'ok' });
  assert(s.result && s.result.msg === 'ok', 'success wraps data in result');
  assert(s.error === null, 'success sets error to null');

  const e = error('fail');
  assert(e.result === null, 'error sets result to null');
  assert(e.error === 'fail', 'error wraps message');
}

// --- store.js ---

function test_store() {
  const sandbox = makeSandbox('store');
  try {
    const originalDir = require(path.join(SKILL_DIR, 'lib/config')).WORKFLOWS_DIR;
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

// --- recorder.js ---

function test_recorder() {
  const sandbox = makeSandbox('recorder');
  try {
    const configMod = require(path.join(SKILL_DIR, 'lib/config'));
    const savedFile = configMod.RECORDING_FILE;
    configMod.RECORDING_FILE = path.join(sandbox, '.recording.json');

    delete require.cache[require.resolve(path.join(SKILL_DIR, 'lib/recorder'))];
    const recorder = require(path.join(SKILL_DIR, 'lib/recorder'));

    assert(!recorder.isRecording(), 'initially not recording');
    assert(recorder.getState() === null, 'initial state is null');

    const startResult = recorder.start('Test Recording');
    assert(startResult.started === true, 'start returns started=true');
    assert(startResult.id.startsWith('wf-'), 'start returns id with wf- prefix');
    assert(startResult.name === 'Test Recording', 'start returns name');

    assert(recorder.isRecording(), 'isRecording returns true after start');

    const state = recorder.getState();
    assert(state !== null, 'getState returns state');
    assert(state.active === true, 'state.active is true');
    assert(state.steps.length === 0, 'state.steps is empty initially');

    const dupResult = recorder.start('Duplicate');
    assert(dupResult.started === false, 'duplicate start returns started=false');

    const step = recorder.addStep('navigate', { url: 'https://example.com' }, null);
    assert(step !== null, 'addStep returns step');
    assert(step.seq === 1, 'first step seq is 1');
    assert(step.command === 'navigate', 'step command is navigate');

    const step2 = recorder.addStep('click', { ref: 'e5', element: 'Login' }, null);
    assert(step2.seq === 2, 'second step seq is 2');
    assert(step2.locators !== null, 'click step has locators');
    assert(step2.locators.ref === 'e5', 'locators.ref is e5');
    assert(step2.locators.text === 'Login', 'locators.text is Login');

    const workflow = recorder.stop();
    assert(workflow !== null, 'stop returns workflow');
    assert(workflow.steps.length === 2, 'workflow has 2 steps');
    assert(workflow.name === 'Test Recording', 'workflow name preserved');
    assert(workflow.params.length === 0, 'workflow params is empty');

    assert(!recorder.isRecording(), 'not recording after stop');
    assert(!fs.existsSync(path.join(sandbox, '.recording.json')), 'recording file removed after stop');

    const stopAgain = recorder.stop();
    assert(stopAgain === null, 'stop returns null when not recording');

    configMod.RECORDING_FILE = savedFile;
  } finally {
    cleanSandbox(sandbox);
  }
}

// --- replayer.js ---

function test_replayer_template() {
  const { renderTemplate, renderArgs } = require(path.join(SKILL_DIR, 'lib/replayer'));

  assert(renderTemplate('hello {{name}}', { name: 'world' }) === 'hello world', 'renderTemplate replaces param');
  assert(renderTemplate('{{a}} and {{b}}', { a: '1', b: '2' }) === '1 and 2', 'renderTemplate replaces multiple');
  assert(renderTemplate('no params', {}) === 'no params', 'renderTemplate no-op without placeholders');
  assert(renderTemplate('{{missing}}', {}) === '{{missing}}', 'renderTemplate keeps unknown params');

  const args = renderArgs({ url: '{{host}}/api', text: 'hello' }, { host: 'https://example.com' });
  assert(args.url === 'https://example.com/api', 'renderArgs replaces in object values');
  assert(args.text === 'hello', 'renderArgs preserves non-template values');
}

// --- generator.js ---

function test_generator() {
  const sandbox = makeSandbox('generator');
  try {
    const { generate } = require(path.join(SKILL_DIR, 'lib/generator'));

    const wf = {
      id: 'wf-gen-test',
      name: 'Login Flow',
      description: 'Auto login to admin',
      params: [
        { id: 'username', label: 'Username', type: 'text', required: true, default: 'admin' },
        { id: 'password', label: 'Password', type: 'password', required: true },
      ],
      steps: [
        { seq: 1, command: 'navigate', args: { url: 'https://admin.example.com' }, locators: null },
        { seq: 2, command: 'type', args: { ref: 'e10', text: '{{username}}' }, locators: { ref: 'e10', css: '#user' } },
        { seq: 3, command: 'click', args: { ref: 'e15', element: 'Login' }, locators: { ref: 'e15', text: 'Login' } },
      ],
      createdAt: '2026-02-23T10:00:00Z',
      updatedAt: '2026-02-23T10:00:05Z',
    };

    const dest = generate(wf, 'login-admin', sandbox);
    assert(dest === sandbox, 'generate returns target path');

    assert(fs.existsSync(path.join(sandbox, 'SKILL.md')), 'generates SKILL.md');
    assert(fs.existsSync(path.join(sandbox, 'tool.js')), 'generates tool.js');
    assert(fs.existsSync(path.join(sandbox, 'workflow.json')), 'generates workflow.json');
    assert(fs.existsSync(path.join(sandbox, 'package.json')), 'generates package.json');

    const pkg = JSON.parse(fs.readFileSync(path.join(sandbox, 'package.json'), 'utf-8'));
    assert(pkg.name === 'login-admin', 'package.json has correct name');

    const skillMd = fs.readFileSync(path.join(sandbox, 'SKILL.md'), 'utf-8');
    assert(skillMd.includes('login-admin'), 'SKILL.md contains skill name');
    assert(skillMd.includes('username'), 'SKILL.md contains param name');
    assert(skillMd.includes('Login Flow'), 'SKILL.md contains workflow name');

    const wfJson = JSON.parse(fs.readFileSync(path.join(sandbox, 'workflow.json'), 'utf-8'));
    assert(wfJson.steps.length === 3, 'workflow.json has 3 steps');

    const toolJs = fs.readFileSync(path.join(sandbox, 'tool.js'), 'utf-8');
    assert(toolJs.includes('findPlaywright'), 'tool.js contains findPlaywright');
    assert(toolJs.includes('renderArgs'), 'tool.js contains renderArgs');
  } finally {
    cleanSandbox(sandbox);
  }
}

// --- exporter.js ---

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

function main() {
  console.log('test_response:');
  test_response();

  console.log('\ntest_store:');
  test_store();

  console.log('\ntest_recorder:');
  test_recorder();

  console.log('\ntest_replayer_template:');
  test_replayer_template();

  console.log('\ntest_generator:');
  test_generator();

  console.log('\ntest_exporter:');
  test_exporter();

  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
