#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/playwright');
const { waitFor } = require(path.join(SKILL_DIR, 'tools/wait'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function createMock() {
  let lastWaitForArgs = null;
  const locator = {
    waitFor: async (opts) => { lastWaitForArgs = opts; },
  };
  const page = {
    getByText: () => ({ first: () => locator }),
  };
  const tab = { page };
  const context = {
    currentTabOrDie: () => tab,
    config: { timeouts: { action: 5000, navigation: 60000 } },
  };
  const response = { addCode: () => {}, addTextResult: () => {}, setIncludeSnapshot: () => {} };
  return { context, response, getLastWaitArgs: () => lastWaitForArgs };
}

async function test_throwsWithoutParams() {
  const { context, response } = createMock();
  let threw = false;
  try {
    await waitFor(context, {}, response);
  } catch (e) {
    threw = e.message.includes('Either time, text or textGone');
  }
  assert(threw, 'throws error when no params provided');
}

async function test_textUsesNavigationTimeout() {
  const { context, response, getLastWaitArgs } = createMock();
  await waitFor(context, { text: 'Hello' }, response);
  assert(getLastWaitArgs().timeout === 60000, 'text uses navigation timeout (60000ms)');
  assert(getLastWaitArgs().state === 'visible', 'text waits for visible state');
}

async function test_textGoneUsesNavigationTimeout() {
  const { context, response, getLastWaitArgs } = createMock();
  await waitFor(context, { textGone: 'Loading...' }, response);
  assert(getLastWaitArgs().timeout === 60000, 'textGone uses navigation timeout (60000ms)');
  assert(getLastWaitArgs().state === 'hidden', 'textGone waits for hidden state');
}

async function test_customTimeoutOverride() {
  const { context, response, getLastWaitArgs } = createMock();
  await waitFor(context, { text: 'Done', timeout: 30000 }, response);
  assert(getLastWaitArgs().timeout === 30000, 'custom timeout overrides default');
}

async function test_timeWait() {
  const { context, response } = createMock();
  const start = Date.now();
  await waitFor(context, { time: 0.1 }, response);
  const elapsed = Date.now() - start;
  assert(elapsed < 2000, 'time wait completes quickly for small values');
}

async function main() {
  console.log('test_wait:');
  await test_throwsWithoutParams();
  await test_textUsesNavigationTimeout();
  await test_textGoneUsesNavigationTimeout();
  await test_customTimeoutOverride();
  await test_timeWait();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
