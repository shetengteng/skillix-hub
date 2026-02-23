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

function test_network_monitor() {
  const { NetworkMonitor } = require(path.join(SKILL_DIR, 'lib/network-monitor'));

  const monitor = new NetworkMonitor();
  assert(monitor instanceof NetworkMonitor, 'NetworkMonitor instantiates');

  assert(typeof monitor.start === 'function', 'has start method');
  assert(typeof monitor.stop === 'function', 'has stop method');
  assert(typeof monitor.attachToPage === 'function', 'has attachToPage method');
  assert(typeof monitor.collectRequests === 'function', 'has collectRequests method');
  assert(typeof monitor.getStats === 'function', 'has getStats method');
  assert(typeof monitor.detachAll === 'function', 'has detachAll method');

  const stats = monitor.getStats();
  assert(stats.captured === 0, 'initial captured is 0');
  assert(stats.pending === 0, 'initial pending is 0');

  monitor.start();
  const requests = monitor.collectRequests();
  assert(Array.isArray(requests), 'collectRequests returns array');
  assert(requests.length === 0, 'initial requests is empty');
  monitor.stop();

  assert(monitor._shouldSkip('https://example.com/image.png', 'Image'), 'skips Image resourceType');
  assert(monitor._shouldSkip('https://example.com/style.css', 'Stylesheet'), 'skips Stylesheet resourceType');
  assert(monitor._shouldSkip('https://www.google-analytics.com/collect', 'XHR'), 'skips google-analytics host');
  assert(monitor._shouldSkip('https://fonts.googleapis.com/css', 'Other'), 'skips fonts.googleapis.com');
  assert(!monitor._shouldSkip('https://api.example.com/users', 'Fetch'), 'does not skip API requests');
  assert(!monitor._shouldSkip('https://api.example.com/data', 'XHR'), 'does not skip XHR to API');

  assert(monitor._isTextMime('application/json'), 'json is text mime');
  assert(monitor._isTextMime('text/html'), 'html is text mime');
  assert(monitor._isTextMime('application/xml'), 'xml is text mime');
  assert(!monitor._isTextMime('image/png'), 'png is not text mime');
  assert(!monitor._isTextMime(null), 'null is not text mime');
}

test_network_monitor();
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
