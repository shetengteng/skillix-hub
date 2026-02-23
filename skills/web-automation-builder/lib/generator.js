'use strict';

const fs = require('fs');
const path = require('path');

function generateToolJs(workflow) {
  const hasParams = workflow.params && workflow.params.length > 0;
  const paramsList = hasParams
    ? workflow.params.map(p => `${p.id}${p.required ? ' (required)' : ''}`).join(', ')
    : 'none';

  return `#!/usr/bin/env node
'use strict';

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const WORKFLOW_FILE = path.join(__dirname, 'workflow.json');

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

function renderArgs(args, params) {
  const rendered = {};
  for (const [key, value] of Object.entries(args)) {
    if (typeof value === 'string') {
      rendered[key] = value.replace(/\\{\\{(\\w+)\\}\\}/g, (m, k) => params.hasOwnProperty(k) ? params[k] : m);
    } else if (typeof value === 'object' && value !== null) {
      rendered[key] = renderArgs(value, params);
    } else {
      rendered[key] = value;
    }
  }
  return rendered;
}

const COMMANDS = {
  async run(params) {
    const pw = findPlaywright();
    if (!pw) return error('Playwright Skill not found. Install it first.');

    const wf = JSON.parse(fs.readFileSync(WORKFLOW_FILE, 'utf-8'));

    ${hasParams ? `const missing = wf.params.filter(p => p.required && !params[p.id]).map(p => p.id);
    if (missing.length) return error('Missing required params: ' + missing.join(', '));` : ''}

    const results = [];
    for (const step of wf.steps) {
      const args = renderArgs(step.args, params);
      const argsJson = JSON.stringify(args);
      const cmd = \`node "\${pw}" \${step.command} '\${argsJson.replace(/'/g, "'\\\\\\\\''")}'\`;
      try {
        const out = execSync(cmd, { encoding: 'utf-8', timeout: 60000 });
        let r; try { r = JSON.parse(out); } catch { r = out; }
        results.push({ step: step.seq, command: step.command, success: true });
      } catch (e) {
        results.push({ step: step.seq, command: step.command, success: false, error: e.message });
        return success({ completed: false, failedAt: step.seq, results });
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
    console.log(JSON.stringify(error('Usage: node tool.js <run|info> \\'{json_params}\\'')));
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
`;
}

function generatePackageJson(skillName, description) {
  return JSON.stringify({
    name: skillName,
    version: '1.0.0',
    description: description || `Auto-generated workflow skill: ${skillName}`,
    main: 'tool.js',
  }, null, 2);
}

function generateSkillMd(workflow, skillName) {
  const paramTable = workflow.params && workflow.params.length > 0
    ? '| 参数 | 说明 | 必填 | 默认值 |\n|------|------|------|--------|\n' +
      workflow.params.map(p =>
        `| ${p.id} | ${p.label || p.id} | ${p.required ? '是' : '否'} | ${p.default || '—'} |`
      ).join('\n')
    : '无参数。';

  const stepsDesc = workflow.steps.map(s =>
    `${s.seq}. \`${s.command}\`${s.args.url ? ` → ${s.args.url}` : ''}${s.args.text ? ` → "${s.args.text}"` : ''}${s.locators?.text ? ` → [${s.locators.text}]` : ''}`
  ).join('\n');

  const paramsExample = workflow.params && workflow.params.length > 0
    ? JSON.stringify(Object.fromEntries(workflow.params.map(p => [p.id, p.default || `<${p.label || p.id}>`])))
    : '{}';

  return `---
name: ${skillName}
description: |
  自动化工作流：${workflow.name}。
  由 web-automation-builder 录制生成。
---

# ${workflow.name}

${workflow.description || `自动执行 ${workflow.name} 工作流。`}

## 参数

${paramTable}

## 操作步骤

${stepsDesc}

## 使用

\`\`\`bash
node tool.js run '${paramsExample}'
\`\`\`

## 触发词

- ${workflow.name}
- 执行${workflow.name}
`;
}

function generate(workflow, skillName, targetDir) {
  const dest = path.resolve(targetDir.replace(/^~/, process.env.HOME || ''));
  fs.mkdirSync(dest, { recursive: true });

  fs.writeFileSync(path.join(dest, 'tool.js'), generateToolJs(workflow));
  fs.writeFileSync(path.join(dest, 'package.json'), generatePackageJson(skillName, workflow.description));
  fs.writeFileSync(path.join(dest, 'workflow.json'), JSON.stringify(workflow, null, 2));
  fs.writeFileSync(path.join(dest, 'SKILL.md'), generateSkillMd(workflow, skillName));

  return dest;
}

module.exports = { generate };
