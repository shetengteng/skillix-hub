#!/usr/bin/env node
'use strict';

const path = require('path');
const http = require('http');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/agent-interact');
const { createServer } = require(path.join(SKILL_DIR, 'lib/server'));
const WebSocket = require(path.join(SKILL_DIR, 'node_modules/ws'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function httpReq(method, urlPath, port, body) {
  return new Promise((resolve, reject) => {
    const opts = { hostname: '127.0.0.1', port, path: urlPath, method, headers: { 'Content-Type': 'application/json' } };
    const req = http.request(opts, (res) => {
      let data = '';
      res.on('data', (c) => (data += c));
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, body: data }); }
      });
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

function connectWs(port) {
  return new Promise((resolve) => {
    const ws = new WebSocket(`ws://127.0.0.1:${port}/ws`);
    ws.on('open', () => resolve(ws));
  });
}

const TEST_PORT = 18901;

async function test_status_endpoint() {
  const { status, body } = await httpReq('GET', '/api/status', TEST_PORT);
  assert(status === 200, 'GET /api/status returns 200');
  assert(body.status === 'running', 'status is running');
}

async function test_invalid_dialog_type() {
  const { status, body } = await httpReq('POST', '/api/dialog', TEST_PORT, { type: 'invalid' });
  assert(status === 400, 'invalid type returns 400');
  assert(body.error.includes('Invalid type'), 'error message mentions invalid type');
}

async function test_missing_type() {
  const { status, body } = await httpReq('POST', '/api/dialog', TEST_PORT, {});
  assert(status === 400, 'missing type returns 400');
}

async function test_full_dialog_flow() {
  const ws = await connectWs(TEST_PORT);
  const wsMessages = [];
  ws.on('message', (raw) => wsMessages.push(JSON.parse(raw.toString())));

  await new Promise((r) => setTimeout(r, 100));

  const dialogPromise = httpReq('POST', '/api/dialog', TEST_PORT, {
    type: 'confirm', title: 'e2e test', options: [{ id: 'a', label: 'A' }], timeout: 10,
  });

  await new Promise((r) => setTimeout(r, 200));

  assert(wsMessages.length >= 1, 'WS received dialog:open');
  const openMsg = wsMessages.find((m) => m.event === 'dialog:open');
  assert(openMsg !== undefined, 'dialog:open event received');

  const dialogId = openMsg.data.id;

  ws.send(JSON.stringify({ event: 'dialog:response', data: { id: dialogId, action: 'a' } }));

  const { status, body } = await dialogPromise;
  assert(status === 200, 'POST /api/dialog returns 200 after response');
  assert(body.result.action === 'a', 'result action matches user response');
  assert(body.result.dialogId === dialogId, 'result dialogId matches');

  ws.close();
}

async function test_cancel_dialog() {
  const ws = await connectWs(TEST_PORT);
  ws.on('message', () => {});
  await new Promise((r) => setTimeout(r, 100));

  const dialogPromise = httpReq('POST', '/api/dialog', TEST_PORT, {
    type: 'wait', title: 'cancel test', timeout: 10,
  });

  await new Promise((r) => setTimeout(r, 200));

  const listRes = await httpReq('GET', '/api/dialogs', TEST_PORT);
  assert(listRes.body.length === 1, 'one active dialog in list');

  const dialogId = listRes.body[0].id;
  const cancelRes = await httpReq('DELETE', `/api/dialog/${dialogId}`, TEST_PORT);
  assert(cancelRes.body.cancelled === true, 'cancel returns true');

  const { body } = await dialogPromise;
  assert(body.result.action === '__cancelled', 'cancelled dialog returns __cancelled');

  ws.close();
}

let srv;

async function main() {
  srv = createServer(TEST_PORT);
  await new Promise((resolve) => srv.start(resolve));

  console.log('test_status_endpoint:');
  await test_status_endpoint();

  console.log('\ntest_invalid_dialog_type:');
  await test_invalid_dialog_type();

  console.log('\ntest_missing_type:');
  await test_missing_type();

  console.log('\ntest_full_dialog_flow:');
  await test_full_dialog_flow();

  console.log('\ntest_cancel_dialog:');
  await test_cancel_dialog();

  srv.stop();

  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
