'use strict';

const fs = require('fs');
const path = require('path');

const CMD_MAP = { fill: 'type', input: 'type' };

function normalizeStep(step) {
  return {
    command: step.command || step.action,
    description: step.description,
    intent: step.intent,
    args: step.args || {},
    locators: step.locators || null,
    waitAfter: step.waitAfter || null,
    condition: step.condition || null,
  };
}

function normalizeParams(params) {
  if (!params) return [];
  if (Array.isArray(params)) return params;
  return Object.entries(params).map(([id, spec]) => ({
    id,
    label: spec.description || id,
    required: spec.required !== false,
    default: spec.default || '',
    type: spec.type || 'string',
  }));
}

function esc(str) {
  if (typeof str !== 'string') return JSON.stringify(str);
  return "'" + str.replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'";
}

function resolveValue(val, hasParams) {
  if (typeof val !== 'string') return JSON.stringify(val);
  if (hasParams && val.includes('{{')) {
    return '`' + val.replace(/\{\{(\w+)\}\}/g, '${params.$1}') + '`';
  }
  return esc(val);
}

function buildLocatorCode(loc, indent) {
  const I = ' '.repeat(indent);
  const entries = [];

  let scopePrefix = '';
  if (loc.context) {
    if (loc.context.type === 'modal') scopePrefix = '[role=dialog] ';
    if (loc.context.type === 'dropdown') scopePrefix = '[role=menu] ';
  }

  if (loc.testId) {
    entries.push(`${I}() => page.getByTestId(${esc(loc.testId)})`);
  }
  if (loc.ariaLabel || loc.label) {
    entries.push(`${I}() => page.getByLabel(${esc(loc.ariaLabel || loc.label)})`);
  }
  if (loc.placeholder) {
    entries.push(`${I}() => page.getByPlaceholder(${esc(loc.placeholder)})`);
  }
  if (loc.text) {
    entries.push(`${I}() => page.getByText(${esc(loc.text)})`);
  }
  if (loc.role && loc.roleName) {
    entries.push(`${I}() => page.getByRole(${esc(loc.role)}, { name: ${esc(loc.roleName)} })`);
  }
  if (loc.role && !loc.roleName) {
    entries.push(`${I}() => page.locator('${scopePrefix}[role="${loc.role}"]')`);
  }
  if (loc.id) {
    const idSuffix = loc.id.includes('_') ? loc.id.split('_').pop() : loc.id;
    entries.push(`${I}() => page.locator('${scopePrefix}[id$="${idSuffix}"]')`);
  }
  if (loc.css) {
    entries.push(`${I}() => page.locator('${scopePrefix}${loc.css.replace(/'/g, "\\'")}')`);
  }

  return entries;
}

function genWaitAfterCode(waitAfter, indent) {
  if (!waitAfter) return [];
  const I = ' '.repeat(indent);
  const t = waitAfter.timeout || 10000;
  const lines = [];

  switch (waitAfter.type) {
    case 'selector':
      lines.push(`${I}await page.waitForSelector(${esc(waitAfter.value)}, { timeout: ${t} }).catch(() => {});`);
      break;
    case 'selectorGone':
      lines.push(`${I}await page.waitForSelector(${esc(waitAfter.value)}, { state: 'hidden', timeout: ${t} }).catch(() => {});`);
      break;
    case 'url':
      lines.push(`${I}await page.waitForURL(${esc('**' + waitAfter.value + '*')}, { timeout: ${t} }).catch(() => {});`);
      break;
    case 'text':
      lines.push(`${I}await page.getByText(${esc(waitAfter.value)}).waitFor({ timeout: ${t} }).catch(() => {});`);
      break;
    case 'textGone':
      lines.push(`${I}await page.getByText(${esc(waitAfter.value)}).waitFor({ state: 'hidden', timeout: ${t} }).catch(() => {});`);
      break;
    case 'networkIdle':
      lines.push(`${I}await page.waitForLoadState('networkidle').catch(() => {});`);
      break;
    case 'time': {
      const ms = (typeof waitAfter.value === 'number' ? waitAfter.value : 2) * 1000;
      lines.push(`${I}await page.waitForTimeout(${ms});`);
      break;
    }
  }
  return lines;
}

function toPlaywrightScript(workflow) {
  const params = normalizeParams(workflow.params);
  const hasParams = params.length > 0;
  const lines = [];

  lines.push(`'use strict';`);
  lines.push(``);
  lines.push(`const { chromium } = require('playwright');`);
  lines.push(``);
  lines.push(`// ${workflow.name}`);
  if (workflow.description) lines.push(`// ${workflow.description}`);
  lines.push(`// Generated: ${new Date().toISOString()}`);
  lines.push(``);

  if (hasParams) {
    lines.push(`const params = {`);
    for (const p of params) {
      const envKey = p.id.replace(/([A-Z])/g, '_$1').toUpperCase();
      const def = p.default ? esc(p.default) : "''";
      lines.push(`  ${p.id}: process.env.${envKey} || ${def},`);
    }
    lines.push(`};`);
    lines.push(``);
  }

  lines.push(`async function tryLocators(locatorFns, action) {`);
  lines.push(`  for (const fn of locatorFns) {`);
  lines.push(`    try {`);
  lines.push(`      const el = fn();`);
  lines.push(`      await el.waitFor({ state: 'visible', timeout: 5000 });`);
  lines.push(`      await action(el);`);
  lines.push(`      return true;`);
  lines.push(`    } catch {}`);
  lines.push(`  }`);
  lines.push(`  return false;`);
  lines.push(`}`);
  lines.push(``);

  lines.push(`(async () => {`);
  lines.push(`  const browser = await chromium.launch({ headless: false });`);
  lines.push(`  const context = await browser.newContext();`);
  lines.push(`  const page = await context.newPage();`);
  lines.push(`  const results = [];`);
  lines.push(``);

  for (let i = 0; i < workflow.steps.length; i++) {
    const raw = workflow.steps[i];
    const step = normalizeStep(raw);
    const cmd = CMD_MAP[step.command] || step.command;
    const stepNum = i + 1;
    const desc = step.description || cmd;

    lines.push(`  // Step ${stepNum}: ${desc}`);

    if (step.condition) {
      const condVal = resolveValue(step.condition, hasParams);
      lines.push(`  if (${condVal}) {`);
      lines.push(`    results.push({ step: ${stepNum}, skipped: true, reason: 'condition not met' });`);
      lines.push(`  } else {`);
    }

    lines.push(`  try {`);

    switch (cmd) {
      case 'navigate':
        lines.push(`    await page.goto(${resolveValue(step.args.url, hasParams)});`);
        if (!step.waitAfter) {
          lines.push(`    await page.waitForLoadState('networkidle').catch(() => {});`);
        }
        break;

      case 'click':
      case 'type':
      case 'fill':
      case 'input': {
        const loc = step.locators;
        if (loc) {
          const locFns = buildLocatorCode(loc, 6);
          if (locFns.length > 0) {
            lines.push(`    const ok = await tryLocators([`);
            lines.push(locFns.join(',\n'));
            lines.push(`    ], async (el) => {`);
            if (cmd === 'click') {
              lines.push(`      await el.click();`);
            } else {
              const text = resolveValue(step.args.text || '', hasParams);
              lines.push(`      await el.fill(${text});`);
            }
            lines.push(`    });`);
            lines.push(`    if (!ok) throw new Error('All locators failed for step ${stepNum}');`);
          } else {
            lines.push(`    // No locators available`);
            lines.push(`    throw new Error('No locators for step ${stepNum}');`);
          }
        } else if (cmd === 'click') {
          lines.push(`    // No locators — manual intervention needed`);
          lines.push(`    throw new Error('No locators for click at step ${stepNum}');`);
        }
        break;
      }

      case 'selectOption': {
        const loc = step.locators;
        const value = resolveValue(step.args.value || step.args.values?.[0] || '', hasParams);
        if (loc) {
          const locFns = buildLocatorCode(loc, 6);
          if (locFns.length > 0) {
            lines.push(`    const ok = await tryLocators([`);
            lines.push(locFns.join(',\n'));
            lines.push(`    ], async (el) => {`);
            lines.push(`      await el.selectOption(${value});`);
            lines.push(`    });`);
            lines.push(`    if (!ok) throw new Error('All locators failed for step ${stepNum}');`);
          }
        }
        break;
      }

      case 'check':
      case 'uncheck': {
        const loc = step.locators;
        if (loc) {
          const locFns = buildLocatorCode(loc, 6);
          if (locFns.length > 0) {
            lines.push(`    const ok = await tryLocators([`);
            lines.push(locFns.join(',\n'));
            lines.push(`    ], async (el) => {`);
            lines.push(`      await el.${cmd}();`);
            lines.push(`    });`);
            lines.push(`    if (!ok) throw new Error('All locators failed for step ${stepNum}');`);
          }
        }
        break;
      }

      case 'pressKey':
        lines.push(`    await page.keyboard.press(${esc(step.args.key || step.args.text || 'Enter')});`);
        break;

      case 'hover': {
        const loc = step.locators;
        if (loc) {
          const locFns = buildLocatorCode(loc, 6);
          if (locFns.length > 0) {
            lines.push(`    const ok = await tryLocators([`);
            lines.push(locFns.join(',\n'));
            lines.push(`    ], async (el) => {`);
            lines.push(`      await el.hover();`);
            lines.push(`    });`);
            lines.push(`    if (!ok) throw new Error('All locators failed for step ${stepNum}');`);
          }
        }
        break;
      }

      case 'waitFor':
      case 'waitForAuth':
        if (step.args.selector) {
          lines.push(`    await page.waitForSelector(${resolveValue(step.args.selector, hasParams)}, { timeout: ${step.args.timeout || 30000} });`);
        } else if (step.args.url) {
          lines.push(`    await page.waitForURL(${resolveValue(step.args.url, hasParams)}, { timeout: ${step.args.timeout || 30000} });`);
        } else {
          lines.push(`    await page.waitForTimeout(${step.args.timeout || step.args.time || 5000});`);
        }
        break;

      case 'screenshot':
        lines.push(`    await page.screenshot({ path: 'step-${stepNum}.png' });`);
        break;

      default:
        lines.push(`    // Unsupported: ${cmd} ${JSON.stringify(step.args)}`);
    }

    if (step.waitAfter) {
      const waitLines = genWaitAfterCode(step.waitAfter, 4);
      lines.push(...waitLines);
    }

    lines.push(`    results.push({ step: ${stepNum}, success: true });`);
    lines.push(`  } catch (e) {`);
    lines.push(`    console.error('Step ${stepNum} failed:', e.message);`);
    lines.push(`    await page.screenshot({ path: 'fail-step-${stepNum}.png' }).catch(() => {});`);
    lines.push(`    results.push({ step: ${stepNum}, success: false, error: e.message });`);
    lines.push(`  }`);

    if (step.condition) {
      lines.push(`  }`);
    }

    lines.push(``);
  }

  lines.push(`  await browser.close();`);
  lines.push(``);
  lines.push(`  const failed = results.filter(r => !r.success && !r.skipped);`);
  lines.push(`  console.log(JSON.stringify({ completed: failed.length === 0, results }, null, 2));`);
  lines.push(`  process.exit(failed.length > 0 ? 1 : 0);`);
  lines.push(`})();`);

  return lines.join('\n');
}

function exportScript(workflow, outputPath) {
  const script = toPlaywrightScript(workflow);
  const resolved = path.resolve(outputPath.replace(/^~/, process.env.HOME || ''));
  const dir = path.dirname(resolved);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(resolved, script);
  return resolved;
}

module.exports = { exportScript, toPlaywrightScript };
