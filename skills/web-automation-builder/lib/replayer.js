'use strict';

const { execSync } = require('child_process');
const { getPlaywrightTool } = require('./config');

function renderTemplate(text, params) {
  if (typeof text !== 'string') return text;
  return text.replace(/\{\{(\w+)\}\}/g, (match, key) => {
    return params.hasOwnProperty(key) ? params[key] : match;
  });
}

function renderArgs(args, params) {
  const rendered = {};
  for (const [key, value] of Object.entries(args)) {
    if (typeof value === 'string') {
      rendered[key] = renderTemplate(value, params);
    } else if (typeof value === 'object' && value !== null) {
      rendered[key] = renderArgs(value, params);
    } else {
      rendered[key] = value;
    }
  }
  return rendered;
}

function executeStep(step, params, playwrightTool) {
  const args = params ? renderArgs(step.args, params) : step.args;
  const argsJson = JSON.stringify(args);
  const cmd = `node "${playwrightTool}" ${step.command} '${argsJson.replace(/'/g, "'\\''")}'`;

  try {
    const output = execSync(cmd, { encoding: 'utf-8', timeout: 60000 });
    let result;
    try { result = JSON.parse(output); } catch { result = output; }
    return { success: true, step: step.seq, command: step.command, result };
  } catch (e) {
    return { success: false, step: step.seq, command: step.command, error: e.message };
  }
}

function replay(workflow, params) {
  const playwrightTool = getPlaywrightTool();
  if (!playwrightTool) {
    return { success: false, error: 'Playwright Skill not found' };
  }

  const results = [];
  let failed = false;

  for (const step of workflow.steps) {
    const result = executeStep(step, params || {}, playwrightTool);
    results.push(result);

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

module.exports = { replay, renderTemplate, renderArgs };
