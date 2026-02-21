#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = process.env.PROJECT_ROOT || path.resolve(__dirname, '../..');
const TEMPLATES_DIR = path.join(__dirname, 'templates');
const NAME_RE = /^[a-z][a-z0-9]*(-[a-z0-9]+)*$/;

function success(data) {
  return { result: data, error: null };
}

function error(message) {
  return { result: null, error: message };
}

function toPascalCase(name) {
  return name.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function renderTemplate(content, vars) {
  let out = content;
  for (const [key, value] of Object.entries(vars)) {
    out = out.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value);
  }
  return out;
}

function readTemplate(name) {
  return fs.readFileSync(path.join(TEMPLATES_DIR, name), 'utf-8');
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function writeIfNotExists(filePath, content) {
  if (fs.existsSync(filePath)) return false;
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, content, 'utf-8');
  return true;
}

function todayPrefix() {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}

async function init(params) {
  const { name, tech = 'node', description = '' } = params;

  if (!name) return error('name is required');
  if (!NAME_RE.test(name)) return error(`Invalid name "${name}". Use lowercase letters, numbers, hyphens (e.g. my-skill).`);

  const skillDir = path.join(PROJECT_ROOT, 'skills', name);
  if (fs.existsSync(skillDir) && fs.readdirSync(skillDir).length > 0) {
    return error(`Directory skills/${name}/ already exists and is not empty.`);
  }

  const vars = {
    name,
    Name: toPascalCase(name),
    description: description || `TODO: describe ${name}`,
  };

  const created = [];

  const dirs = [
    path.join(PROJECT_ROOT, 'skills', name, 'lib'),
    path.join(PROJECT_ROOT, 'design', name),
    path.join(PROJECT_ROOT, 'tests', name, 'src', 'unit'),
    path.join(PROJECT_ROOT, 'tests', name, 'reports'),
  ];
  for (const d of dirs) ensureDir(d);

  if (writeIfNotExists(
    path.join(skillDir, 'SKILL.md'),
    renderTemplate(readTemplate('SKILL.md.tpl'), vars)
  )) created.push(`skills/${name}/SKILL.md`);

  if (tech === 'node') {
    const pkg = JSON.stringify({ name, version: '1.0.0', description: vars.description, main: 'tool.js' }, null, 2) + '\n';
    if (writeIfNotExists(path.join(skillDir, 'package.json'), pkg))
      created.push(`skills/${name}/package.json`);

    if (writeIfNotExists(
      path.join(skillDir, 'tool.js'),
      renderTemplate(readTemplate('tool.js.tpl'), vars)
    )) created.push(`skills/${name}/tool.js`);
  } else if (tech === 'python') {
    if (writeIfNotExists(path.join(skillDir, 'requirements.txt'), ''))
      created.push(`skills/${name}/requirements.txt`);
  }

  const designPath = path.join(PROJECT_ROOT, 'design', name, `${todayPrefix()}-01-设计文档.md`);
  if (writeIfNotExists(designPath, renderTemplate(readTemplate('design-doc.md.tpl'), vars)))
    created.push(`design/${name}/${path.basename(designPath)}`);

  const testsDir = path.join(PROJECT_ROOT, 'tests', name);
  if (writeIfNotExists(
    path.join(testsDir, 'run_tests.js'),
    renderTemplate(readTemplate('run_tests.js.tpl'), vars)
  )) created.push(`tests/${name}/run_tests.js`);

  if (writeIfNotExists(
    path.join(testsDir, 'src', 'unit', 'test_example.js'),
    renderTemplate(readTemplate('test_unit.js.tpl'), vars)
  )) created.push(`tests/${name}/src/unit/test_example.js`);

  return success({
    name,
    tech,
    created,
    directories: [
      `skills/${name}/`,
      `skills/${name}/lib/`,
      `design/${name}/`,
      `tests/${name}/src/unit/`,
      `tests/${name}/reports/`,
    ],
  });
}

const COMMANDS = { init };

async function main() {
  const [command, argsJson] = [process.argv[2], process.argv[3]];

  if (!command) {
    console.log(JSON.stringify(error("Usage: node scaffold.js init '{\"name\":\"my-skill\"}'")));
    process.exit(1);
  }

  const handler = COMMANDS[command];
  if (!handler) {
    console.log(JSON.stringify(error(`Unknown command: ${command}. Available: ${Object.keys(COMMANDS).join(', ')}`)));
    process.exit(1);
  }

  let params = {};
  if (argsJson) {
    try { params = JSON.parse(argsJson); }
    catch { console.log(JSON.stringify(error(`Invalid JSON: ${argsJson}`))); process.exit(1); }
  }

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
