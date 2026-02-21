#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/api-tracer');
const { toMarkdown, toCurl } = require(path.join(SKILL_DIR, 'lib/reporter'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

const sampleReport = {
  session: { name: 'test-session', startTime: '2026-01-01T00:00:00Z', endTime: '2026-01-01T01:00:00Z' },
  endpoints: [
    {
      url: 'https://api.example.com/users',
      method: 'GET',
      pattern: '/users',
      requestHeaders: { authorization: 'Bearer token' },
      cookies: ['session_id'],
      requestBody: null,
      responseFormat: { type: 'json', schema: { data: [{ id: 'number', name: 'string' }] } },
      statusCodes: [200],
      callCount: 3,
    },
    {
      url: 'https://api.example.com/users',
      method: 'POST',
      pattern: '/users',
      requestHeaders: { 'content-type': 'application/json' },
      cookies: [],
      requestBody: { type: 'json', schema: { name: 'string' }, example: '{"name":"test"}' },
      responseFormat: { type: 'json', schema: { id: 'number' } },
      statusCodes: [201],
      callCount: 1,
    },
  ],
  authentication: { type: 'bearer_token', headerName: 'Authorization' },
  cookies: ['session_id'],
  summary: { totalRequests: 10, apiRequests: 4, uniqueEndpoints: 2, methods: ['GET', 'POST'] },
};

function test_toMarkdown() {
  const md = toMarkdown(sampleReport);
  assert(md.includes('# API Trace Report: test-session'), 'markdown has title');
  assert(md.includes('GET /users'), 'markdown has GET endpoint');
  assert(md.includes('POST /users'), 'markdown has POST endpoint');
  assert(md.includes('bearer_token'), 'markdown has auth type');
  assert(md.includes('session_id'), 'markdown has cookies');
  assert(md.includes('**Calls**: 3'), 'markdown has call count');
  assert(md.includes('"name": "string"'), 'markdown has schema');
}

function test_toMarkdown_empty() {
  const md = toMarkdown({
    session: { name: 'empty' },
    endpoints: [],
    authentication: null,
    cookies: [],
    summary: { totalRequests: 0, apiRequests: 0, uniqueEndpoints: 0, methods: [] },
  });
  assert(md.includes('# API Trace Report: empty'), 'empty report has title');
  assert(!md.includes('## Authentication'), 'empty report has no auth section');
}

function test_toCurl() {
  const curl = toCurl(sampleReport);
  assert(curl.includes('curl -X GET'), 'curl has GET command');
  assert(curl.includes('curl -X POST'), 'curl has POST command');
  assert(curl.includes("'authorization: Bearer token'"), 'curl has auth header');
  assert(curl.includes("-d '{\"name\":\"test\"}'"), 'curl has POST body');
  assert(curl.includes("'https://api.example.com/users'"), 'curl has URL');
}

async function main() {
  console.log('test_reporter:');
  test_toMarkdown();
  test_toMarkdown_empty();
  test_toCurl();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
