#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/api-tracer');
const { analyze, inferSchema, groupEndpoints } = require(path.join(SKILL_DIR, 'lib/analyzer'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function deepEqual(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function test_inferSchema_primitives() {
  assert(inferSchema('hello') === 'string', 'string schema');
  assert(inferSchema(42) === 'number', 'number schema');
  assert(inferSchema(true) === 'boolean', 'boolean schema');
  assert(inferSchema(null) === 'null', 'null schema');
}

function test_inferSchema_object() {
  const schema = inferSchema({ name: 'test', age: 25, active: true });
  assert(schema.name === 'string', 'object string field');
  assert(schema.age === 'number', 'object number field');
  assert(schema.active === 'boolean', 'object boolean field');
}

function test_inferSchema_array() {
  const schema = inferSchema([{ id: 1, name: 'a' }]);
  assert(Array.isArray(schema), 'array schema is array');
  assert(schema[0].id === 'number', 'array element schema');
}

function test_inferSchema_nested() {
  const schema = inferSchema({ data: { list: [{ id: 1 }], total: 10 } });
  assert(schema.data.total === 'number', 'nested number');
  assert(Array.isArray(schema.data.list), 'nested array');
}

function test_groupEndpoints_basic() {
  const requests = [
    { url: 'https://api.example.com/users', method: 'GET', resourceType: 'Fetch', mimeType: 'application/json' },
    { url: 'https://api.example.com/users', method: 'GET', resourceType: 'Fetch', mimeType: 'application/json' },
    { url: 'https://api.example.com/users', method: 'POST', resourceType: 'Fetch', mimeType: 'application/json' },
    { url: 'https://cdn.example.com/style.css', method: 'GET', resourceType: 'Stylesheet', mimeType: 'text/css' },
  ];
  const groups = groupEndpoints(requests);
  assert(groups.length === 2, 'groups by method+url (2 unique)');
  const getGroup = groups.find(g => g.method === 'GET');
  assert(getGroup.calls.length === 2, 'GET group has 2 calls');
}

function test_analyze_full() {
  const sessionData = {
    session: { name: 'test', startTime: '2026-01-01', endTime: '2026-01-01', totalRequests: 3 },
    requests: [
      {
        url: 'https://api.example.com/login',
        method: 'POST',
        resourceType: 'Fetch',
        requestHeaders: { authorization: 'Bearer token123', 'content-type': 'application/json' },
        postData: '{"username":"test","password":"pass"}',
        status: 200,
        mimeType: 'application/json',
        responseBody: '{"token":"abc","user":{"id":1}}',
      },
      {
        url: 'https://api.example.com/users',
        method: 'GET',
        resourceType: 'Fetch',
        requestHeaders: { authorization: 'Bearer token123' },
        status: 200,
        mimeType: 'application/json',
        responseBody: '{"data":[{"id":1,"name":"test"}],"total":1}',
      },
      {
        url: 'https://cdn.example.com/app.js',
        method: 'GET',
        resourceType: 'Script',
        requestHeaders: {},
        status: 200,
        mimeType: 'application/javascript',
      },
    ],
  };

  const report = analyze(sessionData);
  assert(report.endpoints.length === 2, 'analyze finds 2 API endpoints');
  assert(report.authentication?.type === 'bearer_token', 'detects bearer token auth');
  assert(report.summary.apiRequests === 2, 'counts 2 API requests');
  assert(report.summary.totalRequests === 3, 'counts 3 total requests');

  const loginEndpoint = report.endpoints.find(e => e.url.includes('login'));
  assert(loginEndpoint?.requestBody?.type === 'json', 'login has JSON request body');
  assert(loginEndpoint?.responseFormat?.type === 'json', 'login has JSON response');
  assert(loginEndpoint?.requestBody?.schema?.username === 'string', 'login schema has username');
}

function test_analyze_empty() {
  const report = analyze({ session: { name: 'empty' }, requests: [] });
  assert(report.endpoints.length === 0, 'empty session has no endpoints');
  assert(report.authentication === null, 'empty session has no auth');
}

async function main() {
  console.log('test_analyzer:');
  test_inferSchema_primitives();
  test_inferSchema_object();
  test_inferSchema_array();
  test_inferSchema_nested();
  test_groupEndpoints_basic();
  test_analyze_full();
  test_analyze_empty();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
