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

function test_response() {
  const { success, error } = require(path.join(SKILL_DIR, 'lib/response'));

  const s = success({ msg: 'ok' });
  assert(s.result && s.result.msg === 'ok', 'success wraps data in result');
  assert(s.error === null, 'success sets error to null');

  const e = error('fail');
  assert(e.result === null, 'error sets result to null');
  assert(e.error === 'fail', 'error wraps message');
}

test_response();
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
