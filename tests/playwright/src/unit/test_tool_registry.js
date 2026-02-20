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

function test_listCommand() {
  const output = execSync(`node tool.js list`, { cwd: SKILL_DIR, encoding: 'utf-8' });
  const result = JSON.parse(output);
  assert(Array.isArray(result.tools), 'tools is array');
  assert(result.tools.length >= 48, `at least 48 tools registered (got ${result.tools.length})`);
}

function test_expectedToolsPresent() {
  const output = execSync(`node tool.js list`, { cwd: SKILL_DIR, encoding: 'utf-8' });
  const { tools } = JSON.parse(output);
  const expected = [
    'navigate', 'snapshot', 'click', 'type', 'pressKey', 'fillForm',
    'screenshot', 'evaluate', 'waitFor', 'tabs', 'consoleMessages',
    'networkRequests', 'handleDialog', 'cookieList', 'route',
    'localStorageList', 'sessionStorageList', 'pdf', 'runCode',
    'verifyElement', 'verifyText', 'install', 'getConfig',
    'mouseMove', 'mouseClick', 'close', 'resize',
  ];
  for (const name of expected)
    assert(tools.includes(name), `tool '${name}' registered`);
}

function test_unknownCommand() {
  try {
    execSync(`node tool.js nonexistent_command`, { cwd: SKILL_DIR, encoding: 'utf-8', stdio: 'pipe' });
    assert(false, 'should have thrown');
  } catch (e) {
    const output = JSON.parse(e.stdout);
    assert(output.error.includes('Unknown command'), 'unknown command returns error');
  }
}

function test_invalidJson() {
  try {
    execSync(`node tool.js navigate '{bad json'`, { cwd: SKILL_DIR, encoding: 'utf-8', stdio: 'pipe' });
    assert(false, 'should have thrown');
  } catch (e) {
    const output = JSON.parse(e.stdout);
    assert(output.error.includes('Invalid JSON'), 'invalid JSON returns error');
  }
}

function test_noCommand() {
  try {
    execSync(`node tool.js`, { cwd: SKILL_DIR, encoding: 'utf-8', stdio: 'pipe' });
    assert(false, 'should have thrown');
  } catch (e) {
    const output = JSON.parse(e.stdout);
    assert(output.error.includes('Usage'), 'no command returns usage');
  }
}

function main() {
  console.log('test_tool_registry:');
  test_listCommand();
  test_expectedToolsPresent();
  test_unknownCommand();
  test_invalidJson();
  test_noCommand();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
