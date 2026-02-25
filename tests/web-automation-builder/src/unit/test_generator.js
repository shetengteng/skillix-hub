#!/usr/bin/env node
'use strict';

const path = require('path');
const fs = require('fs');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/web-automation-builder');
const TESTDATA_DIR = path.resolve(__dirname, '../../testdata/runtime');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function makeSandbox(label) {
  const id = `${label}-${Date.now()}`;
  const dir = path.join(TESTDATA_DIR, id);
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function cleanSandbox(dir) {
  try { fs.rmSync(dir, { recursive: true, force: true }); } catch { /* ok */ }
}

function test_generator() {
  const sandbox = makeSandbox('generator');
  try {
    const { generate } = require(path.join(SKILL_DIR, 'lib/generator'));

    const wf = {
      id: 'wf-gen-test',
      name: 'Login Flow',
      description: 'Auto login to admin',
      params: [
        { id: 'username', label: 'Username', type: 'text', required: true, default: 'admin' },
        { id: 'password', label: 'Password', type: 'password', required: true },
      ],
      steps: [
        { seq: 1, command: 'navigate', args: { url: 'https://admin.example.com' }, locators: null },
        { seq: 2, command: 'type', args: { ref: 'e10', text: '{{username}}' }, locators: { ref: 'e10', css: '#user' } },
        { seq: 3, command: 'click', args: { ref: 'e15', element: 'Login' }, locators: { ref: 'e15', text: 'Login' } },
      ],
      createdAt: '2026-02-23T10:00:00Z',
      updatedAt: '2026-02-23T10:00:05Z',
    };

    const result = generate(wf, 'login-admin', sandbox);
    assert(result.dest === sandbox, 'generate returns target path');

    assert(fs.existsSync(path.join(sandbox, 'SKILL.md')), 'generates SKILL.md');
    assert(fs.existsSync(path.join(sandbox, 'tool.js')), 'generates tool.js');
    assert(fs.existsSync(path.join(sandbox, 'workflow.json')), 'generates workflow.json');
    assert(fs.existsSync(path.join(sandbox, 'package.json')), 'generates package.json');

    const pkg = JSON.parse(fs.readFileSync(path.join(sandbox, 'package.json'), 'utf-8'));
    assert(pkg.name === 'login-admin', 'package.json has correct name');

    const skillMd = fs.readFileSync(path.join(sandbox, 'SKILL.md'), 'utf-8');
    assert(skillMd.includes('login-admin'), 'SKILL.md contains skill name');
    assert(skillMd.includes('username'), 'SKILL.md contains param name');
    assert(skillMd.includes('Login Flow'), 'SKILL.md contains workflow name');

    const wfJson = JSON.parse(fs.readFileSync(path.join(sandbox, 'workflow.json'), 'utf-8'));
    assert(wfJson.steps.length === 3, 'workflow.json has 3 steps');

    const toolJs = fs.readFileSync(path.join(sandbox, 'tool.js'), 'utf-8');
    assert(toolJs.includes('findPlaywright'), 'tool.js contains findPlaywright');
    assert(toolJs.includes('renderArgs'), 'tool.js contains renderArgs');
  } finally {
    cleanSandbox(sandbox);
  }
}

test_generator();
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
