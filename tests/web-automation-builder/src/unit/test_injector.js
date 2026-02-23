#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/web-automation-builder');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function test_injector() {
  const { buildInjectionScript, COLLECT_SCRIPT } = require(path.join(SKILL_DIR, 'lib/injector'));

  const script = buildInjectionScript();
  assert(typeof script === 'string', 'buildInjectionScript returns string');
  assert(script.includes('__WAB_INJECTED__'), 'script checks __WAB_INJECTED__');
  assert(script.includes('__WAB_EVENTS__'), 'script uses __WAB_EVENTS__ array');
  assert(script.includes('addEventListener'), 'script adds event listeners');
  assert(script.includes("'click'"), 'script listens for click events');
  assert(script.includes("'input'"), 'script listens for input events');
  assert(script.includes("'change'"), 'script listens for change events');
  assert(script.includes("'submit'"), 'script listens for submit events');
  assert(script.includes("'keydown'"), 'script listens for keydown events');
  assert(script.includes('popstate'), 'script listens for popstate (SPA navigation)');
  assert(script.includes('hashchange'), 'script listens for hashchange');
  assert(script.includes('cssSelector'), 'script generates CSS selectors');
  assert(script.includes('aria-label'), 'script extracts aria-label');
  assert(script.includes('placeholder'), 'script extracts placeholder');
  assert(script.includes('data-testid'), 'script extracts data-testid');

  assert(typeof COLLECT_SCRIPT === 'string', 'COLLECT_SCRIPT is string');
  assert(COLLECT_SCRIPT.includes('__WAB_EVENTS__'), 'COLLECT_SCRIPT reads __WAB_EVENTS__');
  assert(COLLECT_SCRIPT.includes('JSON.stringify'), 'COLLECT_SCRIPT serializes events');
}

test_injector();
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
