#!/usr/bin/env node
'use strict';

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/skill-builder');
const SCAFFOLD = path.join(SKILL_DIR, 'scaffold.js');
const TESTDATA_DIR = path.resolve(__dirname, '../../testdata/runtime');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function run(args) {
  try {
    const out = execSync(`node "${SCAFFOLD}" ${args}`, { encoding: 'utf-8', timeout: 10000 });
    return JSON.parse(out);
  } catch (e) {
    try { return JSON.parse(e.stdout); }
    catch { return { error: e.message }; }
  }
}

function test_noCommand() {
  const result = run('');
  assert(result.error !== null, 'no command returns error');
}

function test_unknownCommand() {
  const result = run('unknown');
  assert(result.error && result.error.includes('Unknown command'), 'unknown command returns error');
}

function test_missingName() {
  const result = run("init '{}'");
  assert(result.error === 'name is required', 'missing name returns error');
}

function test_invalidName() {
  const result = run('init \'{"name":"INVALID"}\'');
  assert(result.error && result.error.includes('Invalid name'), 'invalid name returns error');
}

function test_invalidNameWithSpaces() {
  const result = run('init \'{"name":"has space"}\'');
  assert(result.error && result.error.includes('Invalid name'), 'name with spaces returns error');
}

function makeSandbox(label) {
  const id = `${label}-${Date.now()}`;
  const dir = path.join(TESTDATA_DIR, id);
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function runInSandbox(sandboxDir, args) {
  return execSync(
    `node "${SCAFFOLD}" ${args}`,
    { encoding: 'utf-8', timeout: 10000, env: { ...process.env, PROJECT_ROOT: sandboxDir } }
  );
}

function test_validInit() {
  const sandbox = makeSandbox('valid-init');

  try {
    const out = runInSandbox(sandbox, 'init \'{"name":"test-abc","description":"Test skill"}\'');
    const result = JSON.parse(out);

    assert(result.error === null, 'valid init returns no error');
    assert(result.result.name === 'test-abc', 'result name matches');
    assert(result.result.tech === 'node', 'default tech is node');
    assert(Array.isArray(result.result.created), 'created is array');
    assert(result.result.created.length > 0, 'created has files');

    assert(result.result.created.includes('skills/test-abc/SKILL.md'), 'created SKILL.md');
    assert(result.result.created.includes('skills/test-abc/tool.js'), 'created tool.js');
    assert(result.result.created.includes('skills/test-abc/package.json'), 'created package.json');
    assert(result.result.created.includes('tests/test-abc/run_tests.js'), 'created run_tests.js');
  } finally {
    fs.rmSync(sandbox, { recursive: true, force: true });
  }
}

function test_duplicateInit() {
  const sandbox = makeSandbox('dup-init');

  try {
    runInSandbox(sandbox, 'init \'{"name":"dup-test"}\'');

    const out = runInSandbox(sandbox, 'init \'{"name":"dup-test"}\'');
    const result = JSON.parse(out);
    assert(result.error && result.error.includes('already exists'), 'duplicate init returns error');
  } catch (e) {
    const result = JSON.parse(e.stdout || '{}');
    assert(result.error && result.error.includes('already exists'), 'duplicate init returns error');
  } finally {
    fs.rmSync(sandbox, { recursive: true, force: true });
  }
}

function test_pythonTech() {
  const sandbox = makeSandbox('python-tech');

  try {
    const out = runInSandbox(sandbox, 'init \'{"name":"py-skill","tech":"python"}\'');
    const result = JSON.parse(out);

    assert(result.error === null, 'python init returns no error');
    assert(result.result.tech === 'python', 'tech is python');
    assert(result.result.created.includes('skills/py-skill/requirements.txt'), 'created requirements.txt');
    assert(!result.result.created.includes('skills/py-skill/tool.js'), 'no tool.js for python');
    assert(!result.result.created.includes('skills/py-skill/package.json'), 'no package.json for python');
  } finally {
    fs.rmSync(sandbox, { recursive: true, force: true });
  }
}

function test_templateRendering() {
  const sandbox = makeSandbox('tpl-render');

  try {
    runInSandbox(sandbox, 'init \'{"name":"tpl-check","description":"Template test"}\'');

    const skillMd = fs.readFileSync(path.join(sandbox, 'skills/tpl-check/SKILL.md'), 'utf-8');
    assert(skillMd.includes('name: tpl-check'), 'SKILL.md has correct name');
    assert(skillMd.includes('Template test'), 'SKILL.md has correct description');
    assert(!skillMd.includes('{{name}}'), 'SKILL.md has no unresolved placeholders');

    const toolJs = fs.readFileSync(path.join(sandbox, 'skills/tpl-check/tool.js'), 'utf-8');
    assert(toolJs.includes('tpl-check'), 'tool.js has skill name');
    assert(!toolJs.includes('{{name}}'), 'tool.js has no unresolved placeholders');
  } finally {
    fs.rmSync(sandbox, { recursive: true, force: true });
  }
}

function main() {
  console.log('test_scaffold:');
  test_noCommand();
  test_unknownCommand();
  test_missingName();
  test_invalidName();
  test_invalidNameWithSpaces();
  test_validInit();
  test_duplicateInit();
  test_pythonTech();
  test_templateRendering();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
