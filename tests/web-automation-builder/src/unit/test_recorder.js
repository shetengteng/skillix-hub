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

function test_recorder() {
  const recorderMod = require(path.join(SKILL_DIR, 'lib/recorder'));

  assert(typeof recorderMod.Recorder === 'function', 'exports Recorder class');
  assert(typeof recorderMod.readState === 'function', 'exports readState');
  assert(typeof recorderMod.getState === 'function', 'exports getState');
  assert(typeof recorderMod.requestStop === 'function', 'exports requestStop');
  assert(typeof recorderMod.waitForResult === 'function', 'exports waitForResult');
  assert(typeof recorderMod.cleanupFiles === 'function', 'exports cleanupFiles');
  assert(typeof recorderMod.isProcessAlive === 'function', 'exports isProcessAlive');

  const recorder = new recorderMod.Recorder();
  assert(!recorder.isRecording(), 'initially not recording');

  const status = recorder.getStatus();
  assert(status.recording === false, 'initial status.recording is false');

  assert(recorderMod.readState() === null || recorderMod.readState()?.active !== true,
    'readState returns null or inactive when no recording');

  assert(recorderMod.isProcessAlive(process.pid) === true, 'isProcessAlive returns true for current process');
  assert(recorderMod.isProcessAlive(999999999) === false, 'isProcessAlive returns false for non-existent pid');
}

test_recorder();
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
