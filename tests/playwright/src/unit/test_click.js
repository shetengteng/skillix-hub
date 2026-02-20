#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/playwright');
const { click } = require(path.join(SKILL_DIR, 'tools/snapshot'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function mockLocator(overrides = {}) {
  return {
    click: async () => {},
    dblclick: async () => {},
    evaluate: async () => {},
    ...overrides,
  };
}

function mockContext(locator) {
  let clickCalled = false, evalCalled = false, dblclickCalled = false;
  const wrappedLocator = {
    click: async (...args) => { clickCalled = true; return locator.click(...args); },
    dblclick: async (...args) => { dblclickCalled = true; return locator.dblclick(...args); },
    evaluate: async (...args) => { evalCalled = true; return locator.evaluate(...args); },
  };
  const tab = {
    refLocator: async () => ({ locator: wrappedLocator, resolved: "getByRole('button')" }),
    waitForCompletion: async (cb) => cb(),
  };
  const context = { currentTabOrDie: () => tab };
  const response = { setIncludeSnapshot: () => {}, addCode: () => {} };
  return { context, response, calls: () => ({ clickCalled, evalCalled, dblclickCalled }) };
}

async function test_normalClick() {
  const { context, response, calls } = mockContext(mockLocator());
  await click(context, { ref: 'e1', element: 'btn' }, response);
  assert(calls().clickCalled, 'normal click calls locator.click');
  assert(!calls().evalCalled, 'normal click does not call evaluate');
}

async function test_forceJsClick() {
  const { context, response, calls } = mockContext(mockLocator());
  await click(context, { ref: 'e1', element: 'btn', forceJsClick: true }, response);
  assert(calls().evalCalled, 'forceJsClick calls evaluate');
  assert(!calls().clickCalled, 'forceJsClick does not call locator.click');
}

async function test_doubleClick() {
  const { context, response, calls } = mockContext(mockLocator());
  await click(context, { ref: 'e1', element: 'btn', doubleClick: true }, response);
  assert(calls().dblclickCalled, 'doubleClick calls locator.dblclick');
  assert(!calls().clickCalled, 'doubleClick does not call locator.click');
}

async function test_forceJsClick_codeOutput() {
  let codeOutput = '';
  const { context } = mockContext(mockLocator());
  const response = { setIncludeSnapshot: () => {}, addCode: (c) => { codeOutput = c; } };
  await click(context, { ref: 'e1', element: 'btn', forceJsClick: true }, response);
  assert(codeOutput.includes('evaluate'), 'forceJsClick code output contains evaluate');
}

async function main() {
  console.log('test_click:');
  await test_normalClick();
  await test_forceJsClick();
  await test_doubleClick();
  await test_forceJsClick_codeOutput();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
