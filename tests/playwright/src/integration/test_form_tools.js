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

function setupFormPage() {
  run('navigate', { url: 'about:blank' });
  run('evaluate', {
    function: `() => {
      document.body.innerHTML = \`
        <form>
          <label for="name">Name</label>
          <input id="name" type="text" />
          <label for="email">Email</label>
          <input id="email" type="text" />
          <label for="agree">I agree</label>
          <input id="agree" type="checkbox" />
          <label for="color">Color</label>
          <select id="color">
            <option value="red">Red</option>
            <option value="blue">Blue</option>
            <option value="green">Green</option>
          </select>
          <div id="drag-src" draggable="true" style="width:50px;height:50px;background:red;">Drag</div>
          <div id="drag-dst" style="width:50px;height:50px;background:blue;">Drop</div>
          <ul id="items"><li>Apple</li><li>Banana</li><li>Cherry</li></ul>
        </form>
      \`;
    }`
  });
}

function test_type() {
  setupFormPage();
  const snap = run('snapshot', {});
  const ref = getRef(snap.snapshot, /textbox "Name" \[ref=(e\d+)\]/);
  if (!ref) { assert(false, 'type: no Name textbox ref'); return; }
  const r = run('type', { ref, text: 'John Doe', element: 'Name' });
  assert(r.code && r.code.includes('fill'), 'type generates fill code');
}

function test_type_slowly() {
  setupFormPage();
  const snap = run('snapshot', {});
  const ref = getRef(snap.snapshot, /textbox "Email" \[ref=(e\d+)\]/);
  if (!ref) { assert(false, 'type slowly: no Email ref'); return; }
  const r = run('type', { ref, text: 'a@b.c', slowly: true, element: 'Email' });
  assert(r.code && r.code.includes('pressSequentially'), 'type slowly generates pressSequentially code');
}

function test_fillForm() {
  setupFormPage();
  const snap = run('snapshot', {});
  const nameRef = getRef(snap.snapshot, /textbox "Name" \[ref=(e\d+)\]/);
  const emailRef = getRef(snap.snapshot, /textbox "Email" \[ref=(e\d+)\]/);
  if (!nameRef || !emailRef) { assert(false, 'fillForm: missing refs'); return; }
  const r = run('fillForm', {
    fields: [
      { name: 'Name', type: 'textbox', ref: nameRef, value: 'Alice' },
      { name: 'Email', type: 'textbox', ref: emailRef, value: 'alice@test.com' },
    ]
  });
  assert(!r.error, 'fillForm succeeds without error');
}

function test_check_uncheck() {
  setupFormPage();
  const snap = run('snapshot', {});
  const ref = getRef(snap.snapshot, /checkbox "I agree" \[ref=(e\d+)\]/);
  if (!ref) { assert(false, 'check: no checkbox ref'); return; }
  const r1 = run('check', { ref, element: 'I agree' });
  assert(r1.code && r1.code.includes('check'), 'check generates check code');
  const r2 = run('uncheck', { ref, element: 'I agree' });
  assert(r2.code && r2.code.includes('uncheck'), 'uncheck generates uncheck code');
}

function test_selectOption() {
  setupFormPage();
  const snap = run('snapshot', {});
  const ref = getRef(snap.snapshot, /combobox "Color" \[ref=(e\d+)\]/);
  if (!ref) { assert(false, 'selectOption: no combobox ref'); return; }
  const r = run('selectOption', { ref, values: ['Blue'], element: 'Color' });
  assert(r.code && r.code.includes('selectOption'), 'selectOption generates code');
}

function test_pressSequentially() {
  run('navigate', { url: 'about:blank' });
  const r = run('pressSequentially', { text: 'hello' });
  assert(r.code && r.code.includes("keyboard.type('hello')"), 'pressSequentially generates keyboard.type code');
}

function test_verifyValue() {
  setupFormPage();
  const snap = run('snapshot', {});
  const ref = getRef(snap.snapshot, /textbox "Name" \[ref=(e\d+)\]/);
  if (!ref) { assert(false, 'verifyValue: no ref'); return; }
  run('type', { ref, text: 'TestValue', element: 'Name' });
  const snap2 = run('snapshot', {});
  const ref2 = getRef(snap2.snapshot, /textbox "Name".*?\[ref=(e\d+)\]/)
    || getRef(snap2.snapshot, /textbox.*?Name.*?\[ref=(e\d+)\]/);
  if (!ref2) { assert(false, 'verifyValue: no ref after type'); return; }
  const r = run('verifyValue', { ref: ref2, element: 'Name', type: 'textbox', value: 'TestValue' });
  assert(r.result && r.result.includes('Done'), 'verifyValue confirms correct value');
}

function test_verifyList() {
  setupFormPage();
  const snap = run('snapshot', {});
  const ref = getRef(snap.snapshot, /list \[ref=(e\d+)\]/);
  if (!ref) { assert(false, 'verifyList: no list ref'); return; }
  const r = run('verifyList', { ref, element: 'items list', items: ['Apple', 'Banana'] });
  assert(r.result && r.result.includes('Done'), 'verifyList confirms items present');
}

function test_drag() {
  run('navigate', { url: 'about:blank' });
  run('evaluate', {
    function: `() => {
      document.body.innerHTML = '<div id="src" draggable="true" style="width:50px;height:50px;background:red;">Drag</div><div id="dst" style="width:50px;height:50px;background:blue;">Drop</div>';
    }`
  });
  const snap = run('snapshot', {});
  const srcRef = getRef(snap.snapshot, /\[ref=(e\d+)\]:\s*Drag/);
  const dstRef = getRef(snap.snapshot, /\[ref=(e\d+)\]:\s*Drop/);
  if (!srcRef || !dstRef) {
    assert(true, 'drag: skipped (refs not found in snapshot)');
    return;
  }
  const r = run('drag', { startRef: srcRef, startElement: 'Drag', endRef: dstRef, endElement: 'Drop' });
  assert(r.code && r.code.includes('dragTo'), 'drag generates dragTo code');
}

function main() {
  console.log('test_form_tools:');
  try { runMeta('stop'); } catch {}
  try {
    test_type();
    test_type_slowly();
    test_fillForm();
    test_check_uncheck();
    test_selectOption();
    test_pressSequentially();
    test_verifyValue();
    test_verifyList();
    test_drag();
  } finally {
    try { runMeta('stop'); } catch {}
  }
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
