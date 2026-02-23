#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/{{name}}');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

// Each test file should test ONE module only.
// Rename this file to test_<module>.js and add test cases for that module.
// Example: test_response.js tests lib/response.js, test_store.js tests lib/store.js

function test_example() {
  assert(true, 'example test passes');
}

test_example();
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
