'use strict';

const { execSync } = require('child_process');
const path = require('path');
const os = require('os');
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

// 按稳定性优先级构建 locator 尝试链（设计文档 3.4 节）
// context-aware: modal/dropdown 内的元素自动限定作用域
function buildLocatorChain(loc) {
  const chain = [];
  if (!loc) return chain;

  let scopePrefix = '';
  if (loc.context) {
    if (loc.context.type === 'modal')    scopePrefix = '[role=dialog] ';
    if (loc.context.type === 'dropdown') scopePrefix = '[role=menu] ';
  }

  if (loc.testId)                    chain.push({ testId: loc.testId });
  if (loc.ariaLabel || loc.label)    chain.push({ label: loc.ariaLabel || loc.label });
  if (loc.placeholder)               chain.push({ placeholder: loc.placeholder });
  if (loc.text)                      chain.push({ text: loc.text });
  if (loc.role && loc.roleName)      chain.push({ role: loc.role, name: loc.roleName });
  if (loc.role && !loc.roleName)     chain.push({ selector: `${scopePrefix}[role="${loc.role}"]` });
  if (loc.id) {
    const idSuffix = loc.id.includes('_') ? loc.id.split('_').pop() : loc.id;
    chain.push({ selector: `${scopePrefix}[id$="${idSuffix}"]` });
  }
  if (loc.css)                       chain.push({ selector: `${scopePrefix}${loc.css}` });
  return chain;
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

// 执行 waitAfter 条件
// Playwright tool waitFor 仅支持 text/textGone/time，selector 类型通过 evaluate 轮询实现
function execWait(playwrightTool, waitAfter) {
  if (!waitAfter) return;
  const t = waitAfter.timeout || 10000;
  switch (waitAfter.type) {
    case 'selector': {
      const pollCode = `async (page) => { const start = Date.now(); while (Date.now() - start < ${t}) { if (await page.$('${waitAfter.value.replace(/'/g, "\\'")}')) return true; await new Promise(r => setTimeout(r, 500)); } return false; }`;
      execPlaywright(playwrightTool, 'runCode', { code: pollCode }, t + 5000);
      break;
    }
    case 'selectorGone': {
      const pollCode = `async (page) => { const start = Date.now(); while (Date.now() - start < ${t}) { if (!(await page.$('${waitAfter.value.replace(/'/g, "\\'")}')) ) return true; await new Promise(r => setTimeout(r, 500)); } return false; }`;
      execPlaywright(playwrightTool, 'runCode', { code: pollCode }, t + 5000);
      break;
    }
    case 'url':          execPlaywright(playwrightTool, 'waitFor', { text: waitAfter.value, timeout: t }); break;
    case 'text':         execPlaywright(playwrightTool, 'waitFor', { text: waitAfter.value, timeout: t }); break;
    case 'textGone':     execPlaywright(playwrightTool, 'waitFor', { textGone: waitAfter.value, timeout: t }); break;
    case 'networkIdle':  execPlaywright(playwrightTool, 'waitFor', { time: Math.min(5, t / 1000) }); break;
    case 'time':         execPlaywright(playwrightTool, 'waitFor', { time: waitAfter.value }); break;
    default:             break;
  }
}

function executeStep(step, index, params, playwrightTool, prevCmd) {
  const cmd = CMD_MAP[step.command] || step.command;
  const renderedLocators = step.locators ? renderValue(step.locators, params) : null;
  const renderedArgs = step.args ? renderValue(step.args, params) : {};
  const stepTimeout = cmd === 'navigate' ? 60000 : 30000;

  const chain = buildLocatorChain(renderedLocators);

  let stepSuccess = false;
  let lastError = null;
  let locatorIndex = null;

  if (chain.length === 0) {
    // navigate 等无 locator 的步骤
    try {
      execPlaywright(playwrightTool, cmd, renderedArgs, stepTimeout);
      stepSuccess = true;
    } catch (e) {
      lastError = e;
    }
  } else {
    for (let li = 0; li < chain.length; li++) {
      const args = Object.assign({}, chain[li], renderedArgs);
      try {
        execPlaywright(playwrightTool, cmd, args, stepTimeout);
        stepSuccess = true;
        locatorIndex = li;
        break;
      } catch (e) {
        lastError = e;
      }
    }
  }

  if (stepSuccess) {
    let warning = null;

    if (step.waitAfter) {
      try { execWait(playwrightTool, step.waitAfter); } catch (waitErr) {
        warning = 'waitAfter timeout: ' + (waitErr.message || '').slice(0, 200);
      }
    } else if (cmd === 'navigate' && prevCmd !== null) {
      try { execPlaywright(playwrightTool, 'waitFor', { time: 2 }); } catch { /* best-effort */ }
    }

    const result = {
      success: true,
      step: index + 1,
      command: cmd,
      description: step.description,
    };
    if (warning) result.warning = warning;
    if (locatorIndex !== null) result.locatorIndex = locatorIndex;
    return result;
  } else {
    // 失败截图（best-effort）
    let screenshotPath = null;
    try {
      screenshotPath = path.join(os.tmpdir(), `wab-fail-step${index + 1}-${Date.now()}.png`);
      execPlaywright(playwrightTool, 'screenshot', { path: screenshotPath });
    } catch { screenshotPath = null; }

    return {
      success: false,
      step: index + 1,
      command: cmd,
      description: step.description,
      error: lastError?.message,
      failedStep: {
        intent: step.intent || step.description,
        allLocators: step.locators,
        error: lastError?.message,
        screenshot: screenshotPath,
      },
      recovery: {
        hint: `使用 playwright snapshot 查看当前页面状态，根据 intent 定位目标元素并手动执行，完成后调用 replay startFrom: ${index + 2} 继续`,
        nextStartFrom: index + 2,
      },
    };
  }
}

function replay(workflow, params, startFrom) {
  const playwrightTool = getPlaywrightTool();
  if (!playwrightTool) {
    return { success: false, error: 'Playwright Skill not found' };
  }

  const results = [];
  const startIndex = Math.max(0, (startFrom || 1) - 1);
  let prevCmd = null;

  for (let i = startIndex; i < workflow.steps.length; i++) {
    const step = workflow.steps[i];
    const result = executeStep(step, i, params || {}, playwrightTool, prevCmd);
    results.push(result);
    prevCmd = CMD_MAP[step.command] || step.command;

    if (!result.success) {
      return {
        success: false,
        workflowId: workflow.id,
        workflowName: workflow.name,
        totalSteps: workflow.steps.length,
        executedSteps: results.length,
        failedAt: result.step,
        failedStep: result.failedStep,
        recovery: result.recovery,
        results,
      };
    }
  }

  return {
    success: true,
    workflowId: workflow.id,
    workflowName: workflow.name,
    totalSteps: workflow.steps.length,
    executedSteps: results.length,
    results,
  };
}

function getSteps(workflow) {
  return {
    name: workflow.name,
    totalSteps: workflow.steps.length,
    params: workflow.params || [],
    steps: workflow.steps.map((s, i) => ({
      step: i + 1,
      intent: s.intent || s.description,
      description: s.description,
      command: s.command,
      locators: s.locators || null,
      args: s.args || null,
      waitAfter: s.waitAfter || null,
    })),
  };
}

module.exports = { replay, executeStep, getSteps, renderValue, buildLocatorChain, CMD_MAP };
