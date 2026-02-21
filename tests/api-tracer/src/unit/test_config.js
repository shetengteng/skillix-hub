#!/usr/bin/env node
'use strict';

const path = require('path');
const fs = require('fs');
const os = require('os');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/api-tracer');
const { TRACER_STATE_DIR, ensureDir, readJson, writeJson, getBrowserWsEndpoint } = require(path.join(SKILL_DIR, 'lib/config'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function test_constants() {
  assert(TRACER_STATE_DIR.includes('api-tracer'), 'TRACER_STATE_DIR contains api-tracer');
}

async function test_ensureDir() {
  const tmpDir = path.join(os.tmpdir(), 'api-tracer-test-' + Date.now());
  const result = await ensureDir(tmpDir);
  assert(fs.existsSync(result), 'ensureDir creates directory');
  fs.rmdirSync(tmpDir);
}

async function test_readWriteJson() {
  const tmpFile = path.join(os.tmpdir(), `api-tracer-test-${Date.now()}.json`);
  const data = { foo: 'bar', num: 42 };
  await writeJson(tmpFile, data);
  const loaded = await readJson(tmpFile);
  assert(loaded.foo === 'bar', 'readJson returns correct string value');
  assert(loaded.num === 42, 'readJson returns correct number value');
  fs.unlinkSync(tmpFile);
}

async function test_readJson_missing() {
  const result = await readJson('/tmp/nonexistent-api-tracer-test.json');
  assert(result === null, 'readJson returns null for missing file');
}

async function test_getBrowserWsEndpoint_noBrowser() {
  const result = await getBrowserWsEndpoint();
  assert(typeof result === 'string' || result === null, 'getBrowserWsEndpoint returns string or null');
}

async function main() {
  console.log('test_config:');
  test_constants();
  await test_ensureDir();
  await test_readWriteJson();
  await test_readJson_missing();
  await test_getBrowserWsEndpoint_noBrowser();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
