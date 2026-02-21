#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/web-content-reader');
const { defaults, resolveConfig } = require(path.join(SKILL_DIR, 'lib/config'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function test_defaults() {
  assert(typeof defaults.fetchTimeout === 'number', 'fetchTimeout is number');
  assert(defaults.fetchTimeout > 0, 'fetchTimeout is positive');
  assert(typeof defaults.browserTimeout === 'number', 'browserTimeout is number');
  assert(defaults.browserTimeout > 0, 'browserTimeout is positive');
  assert(typeof defaults.maxContentLength === 'number', 'maxContentLength is number');
  assert(typeof defaults.spaThreshold === 'number', 'spaThreshold is number');
  assert(defaults.spaThreshold > 0 && defaults.spaThreshold < 1, 'spaThreshold is between 0 and 1');
  assert(typeof defaults.userAgent === 'string', 'userAgent is string');
  assert(Array.isArray(defaults.noiseTags), 'noiseTags is array');
  assert(defaults.noiseTags.includes('script'), 'noiseTags includes script');
}

function test_resolveConfig_defaults() {
  const config = resolveConfig();
  assert(config.fetchTimeout === defaults.fetchTimeout, 'resolveConfig returns default fetchTimeout');
  assert(config.browserTimeout === defaults.browserTimeout, 'resolveConfig returns default browserTimeout');
  assert(config.spaThreshold === defaults.spaThreshold, 'resolveConfig returns default spaThreshold');
}

function test_resolveConfig_overrides() {
  const config = resolveConfig({ fetchTimeout: 5000, spaThreshold: 0.8 });
  assert(config.fetchTimeout === 5000, 'override fetchTimeout works');
  assert(config.spaThreshold === 0.8, 'override spaThreshold works');
  assert(config.browserTimeout === defaults.browserTimeout, 'non-overridden values preserved');
}

function main() {
  console.log('test_config:');
  test_defaults();
  test_resolveConfig_defaults();
  test_resolveConfig_overrides();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
