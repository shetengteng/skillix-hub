#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/web-content-reader');
const response = require(path.join(SKILL_DIR, 'lib/response'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function test_success() {
  const data = { title: 'Test', content: 'Hello' };
  const result = response.success(data, 'fetch', 'https://example.com', 100);
  assert(result.result === data, 'success result contains data');
  assert(result.method === 'fetch', 'success method is fetch');
  assert(result.url === 'https://example.com', 'success url correct');
  assert(result.elapsed === 100, 'success elapsed correct');
  assert(result.error === null, 'success error is null');
}

function test_success_browser() {
  const data = { title: 'SPA', content: 'Rendered' };
  const result = response.success(data, 'browser', 'https://spa.com', 2000);
  assert(result.method === 'browser', 'browser method correct');
}

function test_error() {
  const result = response.error('Something went wrong', 'https://example.com');
  assert(result.result === null, 'error result is null');
  assert(result.method === null, 'error method is null');
  assert(result.url === 'https://example.com', 'error url correct');
  assert(result.error === 'Something went wrong', 'error message correct');
}

function test_error_noUrl() {
  const result = response.error('url is required');
  assert(result.url === null, 'error without url has null url');
  assert(result.error === 'url is required', 'error message correct');
}

function main() {
  console.log('test_response:');
  test_success();
  test_success_browser();
  test_error();
  test_error_noUrl();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
