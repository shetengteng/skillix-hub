#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/playwright');
const { fillForm } = require(path.join(SKILL_DIR, 'tools/form'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function createMock({ textboxFill = 'success', comboboxSelect = 'success' } = {}) {
  const calls = { fill: false, innerFill: false, click: 0, pressSeq: false, selectOption: false, setChecked: false, optionClick: false };

  const optionLocator = {
    waitFor: async () => {},
    click: async () => { calls.optionClick = true; },
  };
  const page = {
    getByRole: () => ({ first: () => optionLocator }),
  };

  const innerFill = textboxFill === 'inner-success'
    ? async () => { calls.innerFill = true; }
    : async () => { calls.innerFill = true; throw new Error('No inner input'); };

  const locator = {
    fill: async () => {
      calls.fill = true;
      if (textboxFill !== 'success') throw new Error('Not an input');
    },
    click: async () => { calls.click++; },
    pressSequentially: async () => { calls.pressSeq = true; },
    setChecked: async () => { calls.setChecked = true; },
    selectOption: async () => {
      calls.selectOption = true;
      if (comboboxSelect !== 'success') throw new Error('Not a select');
    },
    locator: () => ({ first: () => ({ fill: innerFill }) }),
  };

  const tab = {
    refLocator: async () => ({ locator, resolved: "getByRole('textbox')" }),
    page,
  };
  const context = {
    currentTabOrDie: () => tab,
    config: { timeouts: { action: 5000, navigation: 60000 } },
  };
  const response = { addCode: () => {} };
  return { context, response, calls };
}

async function test_textbox_fillSuccess() {
  const { context, response, calls } = createMock();
  await fillForm(context, { fields: [{ name: 'Email', type: 'textbox', ref: 'e1', value: 'test@test.com' }] }, response);
  assert(calls.fill, 'textbox fill called');
  assert(!calls.pressSeq, 'pressSequentially not needed');
}

async function test_textbox_fallbackInner() {
  const { context, response, calls } = createMock({ textboxFill: 'inner-success' });
  await fillForm(context, { fields: [{ name: 'Name', type: 'textbox', ref: 'e1', value: 'John' }] }, response);
  assert(calls.fill, 'fill attempted');
  assert(calls.innerFill, 'inner input fill attempted');
}

async function test_textbox_fallbackPressSeq() {
  const { context, response, calls } = createMock({ textboxFill: 'all-fail' });
  await fillForm(context, { fields: [{ name: 'Name', type: 'textbox', ref: 'e1', value: 'John' }] }, response);
  assert(calls.click > 0, 'click called before pressSequentially');
  assert(calls.pressSeq, 'pressSequentially used as final fallback');
}

async function test_checkbox() {
  const { context, response, calls } = createMock();
  await fillForm(context, { fields: [{ name: 'Agree', type: 'checkbox', ref: 'e1', value: 'true' }] }, response);
  assert(calls.setChecked, 'setChecked called for checkbox');
}

async function test_combobox_nativeSelect() {
  const { context, response, calls } = createMock();
  await fillForm(context, { fields: [{ name: 'Country', type: 'combobox', ref: 'e1', value: 'China' }] }, response);
  assert(calls.selectOption, 'selectOption called for native select');
  assert(!calls.optionClick, 'option click not needed');
}

async function test_combobox_customFallback() {
  const { context, response, calls } = createMock({ comboboxSelect: 'fail' });
  await fillForm(context, { fields: [{ name: 'Tenant', type: 'combobox', ref: 'e1', value: 'meetings' }] }, response);
  assert(calls.selectOption, 'selectOption attempted first');
  assert(calls.click > 0, 'click called to expand dropdown');
  assert(calls.optionClick, 'option clicked in fallback flow');
}

async function main() {
  console.log('test_form_fallback:');
  await test_textbox_fillSuccess();
  await test_textbox_fallbackInner();
  await test_textbox_fallbackPressSeq();
  await test_checkbox();
  await test_combobox_nativeSelect();
  await test_combobox_customFallback();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
