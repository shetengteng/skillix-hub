#!/usr/bin/env node
'use strict';

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const WORKFLOW_FILE = path.join(__dirname, 'workflow.json');
const CMD_MAP = { fill: 'type', input: 'type' };

function success(data) { return { result: data, error: null }; }
function error(msg) { return { result: null, error: msg }; }

function findPlaywright() {
  const candidates = [
    path.resolve(__dirname, '..', 'playwright', 'tool.js'),
    path.join(os.homedir(), '.cursor', 'skills', 'playwright', 'tool.js'),
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) return p;
  }
  return null;
}

function renderValue(value, params) {
  if (typeof value === 'string') {
    return value.replace(/\{\{(\w+)\}\}/g, (m, k) => params.hasOwnProperty(k) ? params[k] : m);
  }
  if (Array.isArray(value)) return value.map(v => renderValue(v, params));
  if (typeof value === 'object' && value !== null) {
    const out = {};
    for (const [k, v] of Object.entries(value)) { out[k] = renderValue(v, params); }
    return out;
  }
  return value;
}

function buildPlaywrightArgs(step, params) {
  const cmd = CMD_MAP[step.command] || step.command;
  const args = {};

  if (step.locators) {
    const loc = renderValue(step.locators, params);
    if (loc.text)             args.text = loc.text;
    else if (loc.css)         args.selector = loc.css;
    else if (loc.role)        { args.role = loc.role; if (loc.name) args.name = loc.name; }
    else if (loc.placeholder) args.placeholder = loc.placeholder;
    else if (loc.label || loc.ariaLabel) args.label = loc.label || loc.ariaLabel;
    else if (loc.testId)      args.testId = loc.testId;
    else if (loc.id)          args.selector = `#${loc.id}`;
  }

  if (step.args) {
    const rendered = renderValue(step.args, params);
    Object.assign(args, rendered);
  }

  if (step.wait?.timeout) args.timeout = step.wait.timeout;

  return { cmd, args };
}

function execPW(pw, cmd, args, timeout) {
  const escaped = JSON.stringify(args).replace(/'/g, "'\\''");
  const out = execSync(`node "${pw}" ${cmd} '${escaped}'`, { encoding: 'utf-8', timeout: timeout || 60000 });
  try { return JSON.parse(out); } catch { return out; }
}

const COMMANDS = {
  async run(params) {
    const pw = findPlaywright();
    if (!pw) return error('Playwright Skill not found. Install it first.');

    const wf = JSON.parse(fs.readFileSync(WORKFLOW_FILE, 'utf-8'));

    {{PARAMS_VALIDATION}}

    const results = [];
    let prevCmd = null;

    for (let i = 0; i < wf.steps.length; i++) {
      const step = wf.steps[i];
      const { cmd, args } = buildPlaywrightArgs(step, params);

      if (prevCmd === 'navigate' && cmd !== 'navigate' && cmd !== 'waitFor') {
        try { execPW(pw, 'waitFor', { time: 2 }); } catch { /* best-effort */ }
      }

      const stepTimeout = step.wait?.timeout || (cmd === 'navigate' ? 60000 : 30000);

      try {
        execPW(pw, cmd, args, stepTimeout);
        results.push({ step: i + 1, command: cmd, description: step.description, success: true });
      } catch (e) {
        results.push({ step: i + 1, command: cmd, description: step.description, success: false, error: e.message });
        return success({ completed: false, failedAt: i + 1, results });
      }
      prevCmd = cmd;
    }
    return success({ completed: true, stepsExecuted: results.length, results });
  },

  async info() {
    const wf = JSON.parse(fs.readFileSync(WORKFLOW_FILE, 'utf-8'));
    return success({
      name: wf.name,
      description: wf.description,
      params: wf.params || [],
      stepCount: wf.steps.length,
      createdAt: wf.createdAt,
    });
  },
};

async function main() {
  const [command, argsJson] = [process.argv[2], process.argv[3]];
  if (!command) {
    console.log(JSON.stringify(error('Usage: node tool.js <run|info> \'{json_params}\'')));
    process.exit(1);
  }
  const handler = COMMANDS[command];
  if (!handler) {
    console.log(JSON.stringify(error('Unknown command: ' + command)));
    process.exit(1);
  }
  let params = {};
  if (argsJson) { try { params = JSON.parse(argsJson); } catch { console.log(JSON.stringify(error('Invalid JSON'))); process.exit(1); } }
  try {
    const result = await handler(params);
    console.log(JSON.stringify(result, null, 2));
    process.exit(result.error ? 1 : 0);
  } catch (e) {
    console.log(JSON.stringify(error(e.message)));
    process.exit(1);
  }
}

main();
