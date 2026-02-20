#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/playwright');
const { Response } = require(path.join(SKILL_DIR, 'lib/response'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

async function test_basicResult() {
  const mockContext = { currentTab: () => null, tabs: () => [], config: { outputDir: '/tmp/pw-test' } };
  const response = new Response(mockContext);
  response.addTextResult('hello');
  response.addCode('await page.goto("x");');
  const output = await response.serialize();
  assert(output.result === 'hello', 'result text correct');
  assert(output.code === 'await page.goto("x");', 'code correct');
  assert(!output.error, 'no error');
}

async function test_errorResult() {
  const mockContext = { currentTab: () => null, tabs: () => [], config: { outputDir: '/tmp/pw-test' } };
  const response = new Response(mockContext);
  response.addError('something went wrong');
  const output = await response.serialize();
  assert(output.error === 'something went wrong', 'error text correct');
}

async function test_multipleResults() {
  const mockContext = { currentTab: () => null, tabs: () => [], config: { outputDir: '/tmp/pw-test' } };
  const response = new Response(mockContext);
  response.addTextResult('line1');
  response.addTextResult('line2');
  const output = await response.serialize();
  assert(output.result === 'line1\nline2', 'multiple results joined');
}

async function main() {
  console.log('test_response:');
  await test_basicResult();
  await test_errorResult();
  await test_multipleResults();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
