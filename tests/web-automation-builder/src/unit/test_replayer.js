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

test_replayer_template();
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
