#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/playwright');
const { type } = require(path.join(SKILL_DIR, 'tools/keyboard'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function createMock(fillBehavior) {
  const calls = { fill: false, innerFill: false, click: false, pressSeq: false, press: false };
  const innerFill = fillBehavior === 'inner-success'
    ? async () => { calls.innerFill = true; }
    : async () => { calls.innerFill = true; throw new Error('No inner input'); };

  const locator = {
    fill: async (v) => {
      calls.fill = true;
      if (fillBehavior !== 'success') throw new Error('Not an input');
    },
    click: async () => { calls.click = true; },
    pressSequentially: async (v) => { calls.pressSeq = true; },
    press: async (k) => { calls.press = true; },
    locator: () => ({ first: () => ({ fill: innerFill }) }),
  };
  const tab = {
    refLocator: async () => ({ locator, resolved: "getByRole('textbox')" }),
    waitForCompletion: async (cb) => cb(),
  };
  const context = { currentTabOrDie: () => tab };
  const response = { setIncludeSnapshot: () => {}, addCode: () => {} };
  return { context, response, calls };
}

async function test_fillSuccess() {
  const { context, response, calls } = createMock('success');
  await type(context, { ref: 'e1', text: 'hello' }, response);
  assert(calls.fill, 'fill called');
  assert(!calls.pressSeq, 'pressSequentially not called on success');
}

async function test_slowlyMode() {
  const { context, response, calls } = createMock('success');
  await type(context, { ref: 'e1', text: 'hello', slowly: true }, response);
  assert(calls.pressSeq, 'slowly mode uses pressSequentially');
  assert(!calls.fill, 'slowly mode skips fill');
}

async function test_fallbackToInnerInput() {
  const { context, response, calls } = createMock('inner-success');
  await type(context, { ref: 'e1', text: 'hello' }, response);
  assert(calls.fill, 'fill attempted first');
  assert(calls.innerFill, 'inner input fill attempted');
  assert(!calls.pressSeq, 'pressSequentially not needed');
}

async function test_fallbackToPressSequentially() {
  const { context, response, calls } = createMock('all-fail');
  await type(context, { ref: 'e1', text: 'hello' }, response);
  assert(calls.fill, 'fill attempted first');
  assert(calls.click, 'click called before pressSequentially');
  assert(calls.pressSeq, 'pressSequentially used as final fallback');
}

async function test_submitPressesEnter() {
  const { context, response, calls } = createMock('success');
  await type(context, { ref: 'e1', text: 'hello', submit: true }, response);
  assert(calls.fill, 'fill called');
  assert(calls.press, 'Enter pressed after fill');
}

async function main() {
  console.log('test_type_fallback:');
  await test_fillSuccess();
  await test_slowlyMode();
  await test_fallbackToInnerInput();
  await test_fallbackToPressSequentially();
  await test_submitPressesEnter();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
