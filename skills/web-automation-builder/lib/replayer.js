'use strict';

const { execSync } = require('child_process');
const { getPlaywrightTool } = require('./config');

const CMD_MAP = { fill: 'type', input: 'type' };

function renderValue(value, params) {
  if (typeof value === 'string') {
    return value.replace(/\{\{(\w+)\}\}/g, (m, k) =>
      params.hasOwnProperty(k) ? params[k] : m,
    );
  }
  if (Array.isArray(value)) return value.map((v) => renderValue(v, params));
  if (typeof value === 'object' && value !== null) {
    const out = {};
    for (const [k, v] of Object.entries(value)) {
      out[k] = renderValue(v, params);
    }
    return out;
  }
  return value;
}

function buildPlaywrightArgs(step, params) {
  const cmd = CMD_MAP[step.command] || step.command;
  const args = {};

  if (step.locators) {
    const loc = renderValue(step.locators, params);
    if (loc.text) {
      args.text = loc.text;
    } else if (loc.css) {
      args.selector = loc.css;
    } else if (loc.role) {
      args.role = loc.role;
      if (loc.name) args.name = loc.name;
    } else if (loc.placeholder) {
      args.placeholder = loc.placeholder;
    } else if (loc.label || loc.ariaLabel) {
      args.label = loc.label || loc.ariaLabel;
    } else if (loc.testId) {
      args.testId = loc.testId;
    } else if (loc.id) {
      args.selector = `#${loc.id}`;
    }
  }

  if (step.args) {
    const rendered = renderValue(step.args, params);
    Object.assign(args, rendered);
  }

  if (step.wait?.timeout) {
    args.timeout = step.wait.timeout;
  }

  return { cmd, args };
}

function execPlaywright(playwrightTool, cmd, args, timeout) {
  const argsJson = JSON.stringify(args);
  const escaped = argsJson.replace(/'/g, "'\\''");
  const command = `node "${playwrightTool}" ${cmd} '${escaped}'`;

  const output = execSync(command, {
    encoding: 'utf-8',
    timeout: timeout || 60000,
  });
  try {
    return JSON.parse(output);
  } catch {
    return output;
  }
}

function executeStep(step, index, params, playwrightTool, prevCmd) {
  const { cmd, args } = buildPlaywrightArgs(step, params);

  if (step.wait?.type === 'text' && step.wait.value) {
    try {
      execPlaywright(playwrightTool, 'waitFor', {
        text: step.wait.value,
        timeout: step.wait.timeout || 10000,
      });
    } catch { /* best-effort wait */ }
  } else if (step.wait?.type === 'url' && step.wait.pattern) {
    try {
      execPlaywright(playwrightTool, 'waitFor', {
        text: step.wait.pattern,
        timeout: step.wait.timeout || 30000,
      });
    } catch { /* best-effort wait */ }
  } else if (prevCmd === 'navigate' && cmd !== 'navigate' && cmd !== 'waitFor') {
    try {
      execPlaywright(playwrightTool, 'waitFor', { time: 2 });
    } catch { /* best-effort wait */ }
  }

  const stepTimeout = step.wait?.timeout || (cmd === 'navigate' ? 60000 : 30000);

  try {
    const result = execPlaywright(playwrightTool, cmd, args, stepTimeout);
    return {
      success: true,
      step: index + 1,
      command: cmd,
      description: step.description,
      result,
    };
  } catch (e) {
    return {
      success: false,
      step: index + 1,
      command: cmd,
      description: step.description,
      error: e.message,
    };
  }
}

function replay(workflow, params) {
  const playwrightTool = getPlaywrightTool();
  if (!playwrightTool) {
    return { success: false, error: 'Playwright Skill not found' };
  }

  const results = [];
  let failed = false;
  let prevCmd = null;

  for (let i = 0; i < workflow.steps.length; i++) {
    const step = workflow.steps[i];
    const result = executeStep(step, i, params || {}, playwrightTool, prevCmd);
    results.push(result);
    prevCmd = CMD_MAP[step.command] || step.command;

    if (!result.success) {
      failed = true;
      break;
    }
  }

  return {
    success: !failed,
    workflowId: workflow.id,
    workflowName: workflow.name,
    totalSteps: workflow.steps.length,
    executedSteps: results.length,
    results,
  };
}

module.exports = { replay, renderValue, buildPlaywrightArgs, CMD_MAP };
