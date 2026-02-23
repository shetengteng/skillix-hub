'use strict';

const fs = require('fs');
const { RECORDING_FILE } = require('./config');

function isRecording() {
  if (!fs.existsSync(RECORDING_FILE)) return false;
  try {
    const state = JSON.parse(fs.readFileSync(RECORDING_FILE, 'utf-8'));
    return state.active === true;
  } catch {
    return false;
  }
}

function getState() {
  if (!fs.existsSync(RECORDING_FILE)) return null;
  try {
    return JSON.parse(fs.readFileSync(RECORDING_FILE, 'utf-8'));
  } catch {
    return null;
  }
}

function start(name) {
  if (isRecording()) {
    const state = getState();
    return { started: false, reason: `Already recording: ${state.name} (${state.id})` };
  }

  const id = `wf-${Date.now()}`;
  const state = {
    active: true,
    id,
    name: name || 'Untitled',
    startedAt: new Date().toISOString(),
    steps: [],
  };

  fs.writeFileSync(RECORDING_FILE, JSON.stringify(state, null, 2));
  return { started: true, id, name: state.name };
}

function addStep(command, args, playwrightResult) {
  const state = getState();
  if (!state || !state.active) return null;

  const step = {
    seq: state.steps.length + 1,
    command,
    args: { ...args },
    locators: extractLocators(command, args),
    timestamp: new Date().toISOString(),
  };

  if (playwrightResult) {
    step.resultSummary = summarizeResult(playwrightResult);
  }

  state.steps.push(step);
  fs.writeFileSync(RECORDING_FILE, JSON.stringify(state, null, 2));
  return step;
}

function stop() {
  const state = getState();
  if (!state || !state.active) {
    return null;
  }

  const workflow = {
    id: state.id,
    name: state.name,
    description: '',
    params: [],
    steps: state.steps,
    metadata: {
      startedAt: state.startedAt,
      stoppedAt: new Date().toISOString(),
      stepCount: state.steps.length,
    },
    createdAt: state.startedAt,
    updatedAt: new Date().toISOString(),
  };

  try { fs.unlinkSync(RECORDING_FILE); } catch { /* ok */ }

  return workflow;
}

function extractLocators(command, args) {
  const interactiveCommands = new Set([
    'click', 'type', 'fillForm', 'selectOption', 'check', 'uncheck',
    'hover', 'drag', 'pressKey',
  ]);

  if (!interactiveCommands.has(command)) return null;

  return {
    ref: args.ref || null,
    text: args.element || args.text || null,
    role: null,
    css: args.selector || null,
    ariaLabel: null,
    placeholder: null,
  };
}

function summarizeResult(result) {
  if (!result) return null;
  if (typeof result === 'string') return result.slice(0, 200);
  if (result.result) {
    const r = result.result;
    if (typeof r === 'string') return r.slice(0, 200);
    if (r.url) return `url: ${r.url}`;
    if (r.title) return `title: ${r.title}`;
    return JSON.stringify(r).slice(0, 200);
  }
  return null;
}

module.exports = { isRecording, getState, start, addStep, stop };
