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

function test_config() {
  const config = require(path.join(SKILL_DIR, 'lib/config'));

  assert(typeof config.SKILL_DIR === 'string', 'SKILL_DIR is string');
  assert(typeof config.DATA_DIR === 'string', 'DATA_DIR is string');
  assert(typeof config.WORKFLOWS_DIR === 'string', 'WORKFLOWS_DIR is string');
  assert(typeof config.RECORDINGS_DIR === 'string', 'RECORDINGS_DIR is string');
  assert(typeof config.RECORDING_FILE === 'string', 'RECORDING_FILE is string');
  assert(typeof config.STOP_SIGNAL_FILE === 'string', 'STOP_SIGNAL_FILE is string');
  assert(typeof config.RECORDING_RESULT_FILE === 'string', 'RECORDING_RESULT_FILE is string');
  assert(typeof config.BROWSER_STATE_FILE === 'string', 'BROWSER_STATE_FILE is string');
  assert(typeof config.MAX_BODY_SIZE === 'number', 'MAX_BODY_SIZE is number');
  assert(config.MAX_BODY_SIZE === 512 * 1024, 'MAX_BODY_SIZE is 512KB');
  assert(config.NETWORK_SKIP_EXTENSIONS instanceof Set, 'NETWORK_SKIP_EXTENSIONS is Set');
  assert(config.NETWORK_SKIP_EXTENSIONS.has('.js'), 'NETWORK_SKIP_EXTENSIONS contains .js');
  assert(config.NETWORK_SKIP_EXTENSIONS.has('.css'), 'NETWORK_SKIP_EXTENSIONS contains .css');
  assert(config.NETWORK_SKIP_HOSTS instanceof Set, 'NETWORK_SKIP_HOSTS is Set');
  assert(config.NETWORK_SKIP_HOSTS.has('www.google-analytics.com'), 'NETWORK_SKIP_HOSTS contains google-analytics');
  assert(typeof config.EVENT_POLL_INTERVAL_MS === 'number', 'EVENT_POLL_INTERVAL_MS is number');
  assert(typeof config.getPlaywrightTool === 'function', 'getPlaywrightTool is function');
  assert(typeof config.getBrowserWsEndpoint === 'function', 'getBrowserWsEndpoint is function');
}

test_config();
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
