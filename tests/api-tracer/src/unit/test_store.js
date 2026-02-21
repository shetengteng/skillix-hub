#!/usr/bin/env node
'use strict';

const path = require('path');
const fs = require('fs');
const os = require('os');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/api-tracer');
const { saveSession, loadSession, listSessions, deleteSession, SESSIONS_DIR } = require(path.join(SKILL_DIR, 'lib/store'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

const TEST_SESSION = {
  session: { name: 'unit-test', startTime: '2026-01-01', endTime: '2026-01-01', totalRequests: 1 },
  requests: [{ url: 'https://example.com', method: 'GET', status: 200 }],
};

async function test_saveAndLoad() {
  await saveSession('unit-test-session', TEST_SESSION);
  const loaded = await loadSession('unit-test-session');
  assert(loaded !== null, 'loadSession returns data');
  assert(loaded.session.name === 'unit-test', 'loaded session name matches');
  assert(loaded.requests.length === 1, 'loaded requests count matches');
}

async function test_listSessions() {
  const sessions = await listSessions();
  const found = sessions.find(s => s.name === 'unit-test-session');
  assert(found !== undefined, 'listSessions includes saved session');
  assert(found.totalRequests === 1, 'listSessions shows correct request count');
}

async function test_loadMissing() {
  const result = await loadSession('nonexistent-session-xyz');
  assert(result === null, 'loadSession returns null for missing session');
}

async function test_deleteSession() {
  const ok = await deleteSession('unit-test-session');
  assert(ok === true, 'deleteSession returns true');
  const loaded = await loadSession('unit-test-session');
  assert(loaded === null, 'deleted session is gone');
}

async function test_deleteNonexistent() {
  const ok = await deleteSession('nonexistent-session-xyz');
  assert(ok === false, 'deleteSession returns false for missing session');
}

async function main() {
  console.log('test_store:');
  await test_saveAndLoad();
  await test_listSessions();
  await test_loadMissing();
  await test_deleteSession();
  await test_deleteNonexistent();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
