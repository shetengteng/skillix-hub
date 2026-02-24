'use strict';

const fs = require('fs');
const path = require('path');

function generateOptimizations(trace, workflow) {
  const opts = [];

  for (const st of (trace.steps || [])) {
    const idx = st.step - 1;
    const wfStep = workflow.steps[idx];
    if (!wfStep) continue;

    if (st.method === 'llm-manual' && st.successLocator) {
      const newLoc = buildUpdatedLocators(wfStep.locators, st.successLocator);
      opts.push({
        type: 'locator-update',
        step: st.step,
        description: wfStep.description,
        reason: (st.issues || []).join('; ') || 'LLM 手动操作成功，发现更稳定的 locator',
        before: wfStep.locators,
        after: newLoc,
      });
    }

    const hasWaitIssue = (st.issues || []).some(i =>
      /waitAfter|timeout/i.test(i) && !/失败|failed/i.test(i)
    );
    if (hasWaitIssue && wfStep.waitAfter) {
      opts.push({
        type: 'waitAfter-fix',
        step: st.step,
        description: wfStep.description,
        reason: 'waitAfter 超时但步骤实际成功',
        before: wfStep.waitAfter,
        after: { type: 'time', value: 3 },
      });
    }

    if (st.method === 'llm-manual' && st.hint) {
      opts.push({
        type: 'step-hint',
        step: st.step,
        description: wfStep.description,
        reason: st.hint,
        before: wfStep.intent || wfStep.description,
        after: `${wfStep.intent || wfStep.description}（注意：${st.hint}）`,
      });
    }
  }

  return opts;
}

function buildUpdatedLocators(existing, successLocator) {
  const updated = existing ? JSON.parse(JSON.stringify(existing)) : {};

  switch (successLocator.type) {
    case 'ariaLabel':
      updated.ariaLabel = successLocator.value;
      break;
    case 'css':
      updated.css = successLocator.value;
      break;
    case 'text':
      updated.text = successLocator.value;
      break;
    case 'role':
      if (successLocator.name) {
        updated.role = successLocator.value;
        updated.roleName = successLocator.name;
      } else {
        updated.role = successLocator.value;
      }
      break;
    case 'testId':
      updated.testId = successLocator.value;
      break;
    case 'id':
      updated.id = successLocator.value;
      break;
    default:
      break;
  }

  return updated;
}

function applyOptimizations(workflowPath, optimizations) {
  const wf = JSON.parse(fs.readFileSync(workflowPath, 'utf-8'));
  const applied = [];

  for (const opt of optimizations) {
    const idx = opt.step - 1;
    if (idx < 0 || idx >= wf.steps.length) continue;

    switch (opt.type) {
      case 'locator-update':
        wf.steps[idx].locators = opt.after;
        applied.push(opt);
        break;
      case 'waitAfter-fix':
        wf.steps[idx].waitAfter = opt.after;
        applied.push(opt);
        break;
      case 'step-hint':
        wf.steps[idx].intent = opt.after;
        applied.push(opt);
        break;
      case 'context-update':
        if (wf.steps[idx].locators) {
          wf.steps[idx].locators.context = opt.after;
        }
        applied.push(opt);
        break;
      default:
        break;
    }
  }

  fs.writeFileSync(workflowPath, JSON.stringify(wf, null, 2));
  return { applied: applied.length, details: applied };
}

function appendToJsonl(filePath, record) {
  const line = JSON.stringify({ ...record, timestamp: new Date().toISOString() }) + '\n';
  fs.appendFileSync(filePath, line);
}

module.exports = { generateOptimizations, applyOptimizations, appendToJsonl };
