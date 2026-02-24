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

// 按稳定性优先级构建 locator 尝试链（参考设计文档 3.4 节）
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

function execPW(pw, cmd, args, timeout) {
  const escaped = JSON.stringify(args).replace(/'/g, "'\\''");
  const out = execSync(`node "${pw}" ${cmd} '${escaped}'`, { encoding: 'utf-8', timeout: timeout || 60000 });
  try { return JSON.parse(out); } catch { return out; }
}

// 执行 waitAfter 条件
// Playwright tool waitFor 仅支持 text/textGone/time，selector 类型通过 evaluate 轮询实现
function execWait(pw, waitAfter) {
  if (!waitAfter) return;
  const t = waitAfter.timeout || 10000;
  switch (waitAfter.type) {
    case 'selector': {
      const pollCode = `async (page) => { const start = Date.now(); while (Date.now() - start < ${t}) { if (await page.$('${waitAfter.value.replace(/'/g, "\\'")}')) return true; await new Promise(r => setTimeout(r, 500)); } return false; }`;
      execPW(pw, 'runCode', { code: pollCode }, t + 5000);
      break;
    }
    case 'selectorGone': {
      const pollCode = `async (page) => { const start = Date.now(); while (Date.now() - start < ${t}) { if (!(await page.$('${waitAfter.value.replace(/'/g, "\\'")}')) ) return true; await new Promise(r => setTimeout(r, 500)); } return false; }`;
      execPW(pw, 'runCode', { code: pollCode }, t + 5000);
      break;
    }
    case 'url':          execPW(pw, 'waitFor', { text: waitAfter.value, timeout: t }); break;
    case 'text':         execPW(pw, 'waitFor', { text: waitAfter.value, timeout: t }); break;
    case 'textGone':     execPW(pw, 'waitFor', { textGone: waitAfter.value, timeout: t }); break;
    case 'networkIdle':  execPW(pw, 'waitFor', { time: Math.min(5, t / 1000) }); break;
    case 'time':         execPW(pw, 'waitFor', { time: waitAfter.value }); break;
    default:             break;
  }
}

const COMMANDS = {
  async run(params) {
    const pw = findPlaywright();
    if (!pw) return error('Playwright Skill not found. Install it first.');

    const wf = JSON.parse(fs.readFileSync(WORKFLOW_FILE, 'utf-8'));

    {{PARAMS_VALIDATION}}

    const results = [];
    // startFrom: 支持从指定步骤恢复（1-based，转为 0-based 索引）
    const startIndex = Math.max(0, (params.startFrom || 1) - 1);

    for (let i = startIndex; i < wf.steps.length; i++) {
      const step = wf.steps[i];
      const cmd = CMD_MAP[step.command] || step.command;
      const renderedLocators = step.locators ? renderValue(step.locators, params) : null;
      const renderedArgs = step.args ? renderValue(step.args, params) : {};
      const stepTimeout = cmd === 'navigate' ? 60000 : 30000;

      // 构建 locator 优先级链
      const chain = buildLocatorChain(renderedLocators);

      let stepSuccess = false;
      let lastError = null;

      if (chain.length === 0) {
        // 无 locator 的步骤（如 navigate）直接执行
        try {
          execPW(pw, cmd, renderedArgs, stepTimeout);
          stepSuccess = true;
        } catch (e) {
          lastError = e;
        }
      } else {
        // 按优先级逐一尝试 locator
        for (const locArgs of chain) {
          const args = Object.assign({}, locArgs, renderedArgs);
          try {
            execPW(pw, cmd, args, stepTimeout);
            stepSuccess = true;
            break;
          } catch (e) {
            lastError = e;
          }
        }
      }

      if (stepSuccess) {
        let warning = null;

        if (step.waitAfter) {
          try { execWait(pw, step.waitAfter); } catch (waitErr) {
            warning = 'waitAfter timeout: ' + (waitErr.message || '').slice(0, 200);
          }
        } else if (cmd === 'navigate') {
          try { execPW(pw, 'waitFor', { time: 2 }); } catch { /* best-effort */ }
        }

        const stepResult = { step: i + 1, command: cmd, description: step.description, success: true };
        if (warning) stepResult.warning = warning;
        results.push(stepResult);
      } else {
        // 所有 locator 均失败，尝试截图（best-effort）
        let screenshotPath = null;
        try {
          screenshotPath = path.join(__dirname, `fail-step${i + 1}-${Date.now()}.png`);
          execPW(pw, 'screenshot', { path: screenshotPath });
        } catch { screenshotPath = null; }

        results.push({ step: i + 1, command: cmd, description: step.description, success: false, error: lastError?.message });

        return success({
          completed: false,
          failedAt: i + 1,
          failedStep: {
            intent: step.intent || step.description,
            allLocators: step.locators,
            error: lastError?.message,
            screenshot: screenshotPath,
          },
          completedSteps: results.filter(r => r.success),
          recovery: {
            hint: `使用 playwright snapshot 查看当前页面状态，根据 intent 定位目标元素并手动执行，完成后调用 run startFrom: ${i + 2} 继续`,
            nextStartFrom: i + 2,
          },
        });
      }
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
