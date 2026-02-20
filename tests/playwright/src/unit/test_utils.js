#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/playwright');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function test_utilsExports() {
  const utils = require(path.join(SKILL_DIR, 'lib/utils'));
  assert(typeof utils.waitForCompletion === 'function', 'waitForCompletion is exported');
}

function test_contextExports() {
  const { Context } = require(path.join(SKILL_DIR, 'lib/context'));
  assert(typeof Context === 'function', 'Context class is exported');
}

function test_tabExports() {
  const { Tab } = require(path.join(SKILL_DIR, 'lib/tab'));
  assert(typeof Tab === 'function', 'Tab class is exported');
}

function test_browserManagerExports() {
  const { BrowserManager } = require(path.join(SKILL_DIR, 'lib/browser-manager'));
  assert(typeof BrowserManager === 'function', 'BrowserManager class is exported');
}

function main() {
  console.log('test_utils:');
  test_utilsExports();
  test_contextExports();
  test_tabExports();
  test_browserManagerExports();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
