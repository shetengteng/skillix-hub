#!/usr/bin/env node
'use strict';

/**
 * E2E test: record → status → stop → save → list → show → delete
 *
 * Requires Playwright Skill installed and a browser available.
 * Launches a browser, records user actions on a test page,
 * then verifies the full lifecycle through tool.js CLI.
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/web-automation-builder');
const TOOL = path.join(SKILL_DIR, 'tool.js');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function run(command, params = {}) {
  const cmd = `node "${TOOL}" ${command} '${JSON.stringify(params).replace(/'/g, "'\\''")}'`;
  const output = execSync(cmd, { encoding: 'utf-8', timeout: 60000 });
  return JSON.parse(output);
}

async function test_record_flow() {
  let workflowId = null;

  try {
    // 1. record
    console.log('  Step 1: record');
    const recordResult = run('record', { name: 'E2E Test Flow' });
    assert(recordResult.error === null, 'record succeeds');
    assert(recordResult.result.id.startsWith('wf-'), 'record returns wf- id');
    workflowId = recordResult.result.id;

    // 2. status (should be recording)
    console.log('  Step 2: status');
    const statusResult = run('status');
    assert(statusResult.result.recording === true, 'status shows recording=true');
    assert(statusResult.result.id === workflowId, 'status shows correct id');

    // Wait briefly for some events to accumulate
    await new Promise((r) => setTimeout(r, 2000));

    // 3. stop
    console.log('  Step 3: stop');
    const stopResult = run('stop');
    assert(stopResult.error === null, 'stop succeeds');
    assert(stopResult.result.id === workflowId, 'stop returns correct id');
    assert(typeof stopResult.result.eventCount === 'number', 'stop returns eventCount');
    assert(Array.isArray(stopResult.result.rawEvents), 'stop returns rawEvents array');

    // 4. status after stop (should not be recording)
    console.log('  Step 4: status after stop');
    const statusAfter = run('status');
    assert(statusAfter.result.recording === false, 'status shows recording=false after stop');

    // 5. save a mock workflow
    console.log('  Step 5: save');
    const mockWorkflow = {
      name: 'E2E Test Flow',
      description: 'E2E test workflow',
      params: [{ id: 'url', label: 'URL', type: 'text', required: true, default: 'https://example.com' }],
      steps: [
        { seq: 1, command: 'navigate', args: { url: '{{url}}' }, locators: null },
      ],
      createdAt: new Date().toISOString(),
    };
    const saveResult = run('save', { id: workflowId, workflow: mockWorkflow });
    assert(saveResult.error === null, 'save succeeds');
    assert(saveResult.result.id === workflowId, 'save returns correct id');

    // 6. list
    console.log('  Step 6: list');
    const listResult = run('list');
    assert(listResult.result.count >= 1, 'list shows at least 1 workflow');
    const found = listResult.result.workflows.find((w) => w.id === workflowId);
    assert(found !== undefined, 'list contains saved workflow');

    // 7. show
    console.log('  Step 7: show');
    const showResult = run('show', { id: workflowId });
    assert(showResult.error === null, 'show succeeds');
    assert(showResult.result.name === 'E2E Test Flow', 'show returns correct name');
    assert(showResult.result.steps.length === 1, 'show returns correct step count');

    // 8. delete
    console.log('  Step 8: delete');
    const deleteResult = run('delete', { id: workflowId });
    assert(deleteResult.error === null, 'delete succeeds');

    // 9. verify deleted
    console.log('  Step 9: verify deleted');
    try {
      run('show', { id: workflowId });
      assert(false, 'show should fail for deleted workflow');
    } catch (e) {
      const output = e.stdout || '';
      assert(output.includes('Workflow not found'), 'show returns error for deleted workflow');
    }

  } catch (e) {
    failed++;
    console.error(`  FAIL: unexpected error: ${e.message}`);
    if (e.stdout) console.error(`  stdout: ${e.stdout}`);
    if (e.stderr) console.error(`  stderr: ${e.stderr}`);

    if (workflowId) {
      try { run('stop'); } catch { /* ok */ }
      try { run('delete', { id: workflowId }); } catch { /* ok */ }
    }
  }
}

(async () => {
  await test_record_flow();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
})();
