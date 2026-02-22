#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/agent-interact');
const DialogManager = require(path.join(SKILL_DIR, 'lib/dialog-manager'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

async function test_create_and_respond() {
  const dm = new DialogManager();
  const promise = dm.create({ type: 'confirm', title: 'test', timeout: 5 });

  const list = dm.list();
  assert(list.length === 1, 'dialog appears in list after create');
  assert(list[0].type === 'confirm', 'dialog type is correct');

  const id = list[0].id;
  dm.respond(id, { action: 'ok', data: null });

  const result = await promise;
  assert(result.dialogId === id, 'result contains correct dialogId');
  assert(result.action === 'ok', 'result contains correct action');
  assert(dm.list().length === 0, 'dialog removed from list after respond');
}

async function test_cancel() {
  const dm = new DialogManager();
  const promise = dm.create({ type: 'wait', title: 'cancel test', timeout: 5 });

  const id = dm.list()[0].id;
  const ok = dm.cancel(id);
  assert(ok === true, 'cancel returns true for existing dialog');

  const result = await promise;
  assert(result.action === '__cancelled', 'cancelled dialog has __cancelled action');

  const ok2 = dm.cancel('nonexistent');
  assert(ok2 === false, 'cancel returns false for nonexistent dialog');
}

async function test_timeout() {
  const dm = new DialogManager();
  const promise = dm.create({ type: 'confirm', title: 'timeout test', timeout: 1 });

  const result = await promise;
  assert(result.action === '__timeout', 'timed out dialog has __timeout action');
  assert(dm.list().length === 0, 'timed out dialog removed from list');
}

async function test_shutdown() {
  const dm = new DialogManager();
  const p1 = dm.create({ type: 'confirm', title: 'a', timeout: 30 });
  const p2 = dm.create({ type: 'wait', title: 'b', timeout: 30 });

  assert(dm.list().length === 2, 'two dialogs active before shutdown');
  dm.shutdown();

  const r1 = await p1;
  const r2 = await p2;
  assert(r1.action === '__shutdown', 'first dialog resolved with __shutdown');
  assert(r2.action === '__shutdown', 'second dialog resolved with __shutdown');
  assert(dm.list().length === 0, 'no dialogs after shutdown');
}

async function test_broadcast_to_ws_clients() {
  const dm = new DialogManager();
  const messages = [];
  const fakeWs = { readyState: 1, send: (msg) => messages.push(JSON.parse(msg)) };

  dm.addClient(fakeWs);
  const promise = dm.create({ type: 'confirm', title: 'broadcast', timeout: 5 });

  assert(messages.length === 1, 'one message broadcast on create');
  assert(messages[0].event === 'dialog:open', 'broadcast event is dialog:open');

  const id = dm.list()[0].id;
  dm.respond(id, { action: 'done', data: null });
  await promise;

  assert(messages.length === 2, 'two messages total after respond');
  assert(messages[1].event === 'dialog:close', 'second broadcast is dialog:close');

  dm.removeClient(fakeWs);
}

async function test_duplicate_respond() {
  const dm = new DialogManager();
  const promise = dm.create({ type: 'confirm', title: 'dup', timeout: 5 });

  const id = dm.list()[0].id;
  const ok1 = dm.respond(id, { action: 'first', data: null });
  const ok2 = dm.respond(id, { action: 'second', data: null });

  assert(ok1 === true, 'first respond returns true');
  assert(ok2 === false, 'second respond returns false');

  const result = await promise;
  assert(result.action === 'first', 'only first respond takes effect');
}

async function main() {
  console.log('test_create_and_respond:');
  await test_create_and_respond();

  console.log('\ntest_cancel:');
  await test_cancel();

  console.log('\ntest_timeout:');
  await test_timeout();

  console.log('\ntest_shutdown:');
  await test_shutdown();

  console.log('\ntest_broadcast_to_ws_clients:');
  await test_broadcast_to_ws_clients();

  console.log('\ntest_duplicate_respond:');
  await test_duplicate_respond();

  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
