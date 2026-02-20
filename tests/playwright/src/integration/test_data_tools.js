#!/usr/bin/env node
'use strict';

const { execSync } = require('child_process');
const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/playwright');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function run(cmd, params = {}) {
  const paramsStr = JSON.stringify(params).replace(/'/g, "'\\''");
  return JSON.parse(execSync(`node tool.js ${cmd} '${paramsStr}'`, {
    cwd: SKILL_DIR, encoding: 'utf-8', timeout: 45000,
    env: { ...process.env, PLAYWRIGHT_SKILL_HEADLESS: 'true' },
  }));
}

function runMeta(cmd) {
  return JSON.parse(execSync(`node tool.js ${cmd}`, {
    cwd: SKILL_DIR, encoding: 'utf-8', timeout: 45000,
    env: { ...process.env, PLAYWRIGHT_SKILL_HEADLESS: 'true' },
  }));
}

function test_cookieList() {
  run('navigate', { url: 'https://example.com' });
  const r = run('cookieList', {});
  assert(r.result !== undefined, 'cookieList returns result');
}

function test_cookieSetGetDelete() {
  run('cookieSet', { name: 'test_cookie', value: 'hello123', domain: 'example.com' });
  const get = run('cookieGet', { name: 'test_cookie' });
  assert(get.result && get.result.includes('hello123'), 'cookieGet returns set value');
  run('cookieDelete', { name: 'test_cookie' });
  const get2 = run('cookieGet', { name: 'test_cookie' });
  assert(get2.result && get2.result.includes('not found'), 'cookieDelete removes cookie');
}

function test_cookieClear() {
  run('cookieSet', { name: 'tmp', value: 'v', domain: 'example.com' });
  run('cookieClear', {});
  const r = run('cookieList', {});
  assert(r.result && r.result.includes('No cookies'), 'cookieClear removes all');
}

function test_localStorageSetGetDelete() {
  run('navigate', { url: 'https://example.com' });
  run('localStorageSet', { key: 'testKey', value: 'testVal' });
  const get = run('localStorageGet', { key: 'testKey' });
  assert(get.result && get.result.includes('testVal'), 'localStorageGet returns set value');
  run('localStorageDelete', { key: 'testKey' });
  const get2 = run('localStorageGet', { key: 'testKey' });
  assert(get2.result && get2.result.includes('not found'), 'localStorageDelete removes key');
}

function test_localStorageListClear() {
  run('localStorageSet', { key: 'a', value: '1' });
  run('localStorageSet', { key: 'b', value: '2' });
  const list = run('localStorageList', {});
  assert(list.result && list.result.includes('a=1'), 'localStorageList shows items');
  run('localStorageClear', {});
  const list2 = run('localStorageList', {});
  assert(list2.result && list2.result.includes('No localStorage'), 'localStorageClear empties');
}

function test_sessionStorageSetGetDelete() {
  run('sessionStorageSet', { key: 'sKey', value: 'sVal' });
  const get = run('sessionStorageGet', { key: 'sKey' });
  assert(get.result && get.result.includes('sVal'), 'sessionStorageGet returns value');
  run('sessionStorageDelete', { key: 'sKey' });
  const get2 = run('sessionStorageGet', { key: 'sKey' });
  assert(get2.result && get2.result.includes('not found'), 'sessionStorageDelete removes');
}

function test_sessionStorageListClear() {
  run('sessionStorageSet', { key: 'x', value: 'y' });
  const list = run('sessionStorageList', {});
  assert(list.result && list.result.includes('x=y'), 'sessionStorageList shows items');
  run('sessionStorageClear', {});
  const list2 = run('sessionStorageList', {});
  assert(list2.result && list2.result.includes('No sessionStorage'), 'sessionStorageClear empties');
}

function test_evaluate() {
  run('navigate', { url: 'https://example.com' });
  const r = run('evaluate', { function: '() => document.title' });
  assert(r.result && r.result.includes('Example Domain'), 'evaluate returns title');
  assert(r.code && r.code.includes('evaluate'), 'evaluate generates code');
}

function test_getConfig() {
  const r = run('getConfig', {});
  assert(r.result && r.result.includes('chromium'), 'getConfig returns config');
}

function test_route() {
  run('navigate', { url: 'https://example.com' });
  const r = run('route', { pattern: '**/api/test', status: 200, body: '{"ok":true}', contentType: 'application/json' });
  assert(r.result && r.result.includes('Route added'), 'route returns success');
}

function test_routeList() {
  const r = run('routeList', {});
  assert(r.result !== undefined, 'routeList returns result');
}

function test_unroute() {
  const r = run('unroute', {});
  assert(r.result && r.result.includes('Removed'), 'unroute returns result');
}

function main() {
  console.log('test_data_tools:');
  try { runMeta('stop'); } catch {}
  try {
    test_cookieList();
    test_cookieSetGetDelete();
    test_cookieClear();
    test_localStorageSetGetDelete();
    test_localStorageListClear();
    test_sessionStorageSetGetDelete();
    test_sessionStorageListClear();
    test_evaluate();
    test_getConfig();
    test_route();
    test_routeList();
    test_unroute();
  } finally {
    try { runMeta('stop'); } catch {}
  }
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
