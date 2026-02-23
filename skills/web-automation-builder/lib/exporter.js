'use strict';

const fs = require('fs');
const path = require('path');

function toPlaywrightScript(workflow) {
  const lines = [
    `'use strict';`,
    ``,
    `const { chromium } = require('playwright');`,
    ``,
    `// Auto-generated from workflow: ${workflow.name}`,
    `// ID: ${workflow.id}`,
    `// Created: ${workflow.createdAt}`,
    ``,
  ];

  if (workflow.params && workflow.params.length > 0) {
    lines.push(`// Parameters (pass via CLI args or environment variables):`);
    for (const p of workflow.params) {
      lines.push(`//   ${p.id}: ${p.label || p.id}${p.required ? ' (required)' : ''}`);
    }
    lines.push(``);
    lines.push(`const params = {`);
    for (const p of workflow.params) {
      const envKey = p.id.toUpperCase();
      const def = p.default ? `'${p.default}'` : `''`;
      lines.push(`  ${p.id}: process.env.${envKey} || ${def},`);
    }
    lines.push(`};`);
    lines.push(``);
  }

  lines.push(`(async () => {`);
  lines.push(`  const browser = await chromium.launch({ headless: false });`);
  lines.push(`  const context = await browser.newContext();`);
  lines.push(`  const page = await context.newPage();`);
  lines.push(``);

  const resolveValue = (val) => {
    if (typeof val !== 'string') return JSON.stringify(val);
    if (workflow.params && val.includes('{{')) {
      return '`' + val.replace(/\{\{(\w+)\}\}/g, '${params.$1}') + '`';
    }
    return `'${val.replace(/'/g, "\\'")}'`;
  };

  for (let i = 0; i < workflow.steps.length; i++) {
    const step = workflow.steps[i];
    lines.push(`  // Step ${i + 1}: ${step.description || step.command}`);

    switch (step.command) {
      case 'navigate':
        lines.push(`  await page.goto(${resolveValue(step.args.url)});`);
        lines.push(`  await page.waitForLoadState('networkidle').catch(() => {});`);
        break;
      case 'click': {
        const loc = step.locators;
        if (loc?.text) {
          lines.push(`  await page.getByText(${resolveValue(loc.text)}).click();`);
        } else if (loc?.css) {
          lines.push(`  await page.locator(${resolveValue(loc.css)}).click();`);
        } else if (loc?.role) {
          const nameOpt = loc.name ? `, { name: ${resolveValue(loc.name)} }` : '';
          lines.push(`  await page.getByRole('${loc.role}'${nameOpt}).click();`);
        } else {
          lines.push(`  // TODO: manual locator needed for click`);
        }
        break;
      }
      case 'fill':
      case 'type':
      case 'input': {
        const loc = step.locators;
        const text = resolveValue(step.args?.text || '');
        if (loc?.placeholder) {
          lines.push(`  await page.getByPlaceholder(${resolveValue(loc.placeholder)}).fill(${text});`);
        } else if (loc?.ariaLabel || loc?.label) {
          lines.push(`  await page.getByLabel(${resolveValue(loc.ariaLabel || loc.label)}).fill(${text});`);
        } else if (loc?.css) {
          lines.push(`  await page.locator(${resolveValue(loc.css)}).fill(${text});`);
        } else if (loc?.id) {
          lines.push(`  await page.locator('#${loc.id}').fill(${text});`);
        } else {
          lines.push(`  // TODO: manual locator needed for fill`);
        }
        break;
      }
      case 'selectOption': {
        const loc = step.locators;
        const value = resolveValue(step.args?.value || step.args?.values?.[0] || '');
        if (loc?.css) {
          lines.push(`  await page.locator(${resolveValue(loc.css)}).selectOption(${value});`);
        } else {
          lines.push(`  // TODO: manual locator needed for selectOption`);
        }
        break;
      }
      case 'check':
      case 'uncheck': {
        const loc = step.locators;
        const method = step.command;
        if (loc?.css) {
          lines.push(`  await page.locator(${resolveValue(loc.css)}).${method}();`);
        } else if (loc?.text) {
          lines.push(`  await page.getByText(${resolveValue(loc.text)}).${method}();`);
        } else {
          lines.push(`  // TODO: manual locator needed for ${method}`);
        }
        break;
      }
      case 'pressKey':
        lines.push(`  await page.keyboard.press('${step.args?.key || step.args?.text || ''}');`);
        break;
      case 'hover': {
        const loc = step.locators;
        if (loc?.text) {
          lines.push(`  await page.getByText(${resolveValue(loc.text)}).hover();`);
        } else if (loc?.css) {
          lines.push(`  await page.locator(${resolveValue(loc.css)}).hover();`);
        }
        break;
      }
      case 'waitFor':
        if (step.args?.selector) {
          lines.push(`  await page.waitForSelector(${resolveValue(step.args.selector)});`);
        } else if (step.args?.url) {
          lines.push(`  await page.waitForURL(${resolveValue(step.args.url)});`);
        } else {
          lines.push(`  await page.waitForTimeout(${step.args?.timeout || 1000});`);
        }
        break;
      case 'screenshot':
        lines.push(`  await page.screenshot({ path: 'screenshot-step${i + 1}.png' });`);
        break;
      default:
        lines.push(`  // Unsupported command: ${step.command} ${JSON.stringify(step.args || {})}`);
    }
    lines.push(``);
  }

  lines.push(`  await browser.close();`);
  lines.push(`})();`);

  return lines.join('\n');
}

function exportScript(workflow, outputPath) {
  const script = toPlaywrightScript(workflow);
  const resolved = path.resolve(outputPath.replace(/^~/, process.env.HOME || ''));
  fs.writeFileSync(resolved, script);
  return resolved;
}

module.exports = { exportScript, toPlaywrightScript };
