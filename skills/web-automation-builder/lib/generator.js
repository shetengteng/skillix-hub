'use strict';

const fs = require('fs');
const path = require('path');

const TEMPLATES_DIR = path.join(__dirname, '..', 'templates');

function readTemplate(name) {
  return fs.readFileSync(path.join(TEMPLATES_DIR, name), 'utf-8');
}

function generateToolJs(workflow) {
  const hasParams = workflow.params && workflow.params.length > 0;

  const paramsValidation = hasParams
    ? `const missing = wf.params.filter(p => p.required && !params[p.id]).map(p => p.id);
    if (missing.length) return error('Missing required params: ' + missing.join(', '));`
    : '';

  let tpl = readTemplate('tool.js.tpl');
  tpl = tpl.replace('{{PARAMS_VALIDATION}}', paramsValidation);
  return tpl;
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

  let tpl = readTemplate('SKILL.md.tpl');
  tpl = tpl.replace(/\{\{SKILL_NAME\}\}/g, skillName);
  tpl = tpl.replace(/\{\{WORKFLOW_NAME\}\}/g, workflow.name);
  tpl = tpl.replace('{{DESCRIPTION}}', workflow.description || `自动执行 ${workflow.name} 工作流。`);
  tpl = tpl.replace('{{PARAM_TABLE}}', paramTable);
  tpl = tpl.replace('{{STEPS_DESC}}', stepsDesc);
  tpl = tpl.replace('{{PARAMS_EXAMPLE}}', paramsExample);
  return tpl;
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
