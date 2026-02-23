'use strict';

const fs = require('fs');
const path = require('path');

function generateToolJs(skillName, analysis, extract) {
  const commands = analysis.suggestedCommands || [];
  const docType = analysis.docType?.primary || 'unknown';

  const commandEntries = commands.slice(0, 30).map(cmd => {
    if (cmd.method && cmd.path) {
      return `
  async ${sanitizeName(cmd.name)}(params) {
    const url = BASE_URL + renderPath('${cmd.path}', params);
    const resp = await fetch(url, {
      method: '${cmd.method}',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders(params) },
      ${cmd.method !== 'GET' ? "body: params.body ? JSON.stringify(params.body) : undefined," : ''}
    });
    const data = await resp.json().catch(() => resp.text());
    return success({ status: resp.status, data });
  },`;
    }
    return `
  async ${sanitizeName(cmd.name)}(params) {
    // TODO: implement ${cmd.description || cmd.name}
    return success({ message: '${cmd.name} executed', params });
  },`;
  });

  return `#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.BASE_URL || '';

function success(data) { return { result: data, error: null }; }
function error(msg) { return { result: null, error: msg }; }

function renderPath(template, params) {
  return template.replace(/\\{(\\w+)\\}/g, (_, key) => params[key] || key);
}

function getAuthHeaders(params) {
  if (params.token) return { Authorization: 'Bearer ' + params.token };
  return {};
}

const COMMANDS = {${commandEntries.join('')}

  async install(params) {
    if (!params.target) return error('target is required');
    const srcDir = __dirname;
    const destDir = path.resolve(params.target.replace(/^~/, process.env.HOME || ''));
    fs.mkdirSync(destDir, { recursive: true });
    for (const item of ['SKILL.md', 'tool.js', 'package.json', 'doc-source.json']) {
      const src = path.join(srcDir, item);
      if (fs.existsSync(src)) fs.cpSync(src, path.join(destDir, item), { recursive: true, force: true });
    }
    return success({ message: 'Installed to ' + destDir, path: destDir });
  },

  async update(params) {
    return COMMANDS.install(params);
  },
};

async function main() {
  const [command, argsJson] = [process.argv[2], process.argv[3]];
  if (!command) {
    console.log(JSON.stringify(error('Usage: node tool.js <command> \\'{json_params}\\'')));
    process.exit(1);
  }
  const handler = COMMANDS[command];
  if (!handler) {
    console.log(JSON.stringify(error('Unknown command: ' + command + '. Available: ' + Object.keys(COMMANDS).join(', '))));
    process.exit(1);
  }
  let params = {};
  if (argsJson) {
    try { params = JSON.parse(argsJson); }
    catch { console.log(JSON.stringify(error('Invalid JSON: ' + argsJson))); process.exit(1); }
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
`;
}

function generateSkillMd(skillName, analysis, extract) {
  const commands = analysis.suggestedCommands || [];
  const docType = analysis.docType?.primary || 'unknown';
  const sources = (extract.sources || []).map(s => s.value).join(', ');

  const commandDocs = commands.slice(0, 30).map(cmd => {
    const params = cmd.method && cmd.path
      ? `'{"token":"YOUR_TOKEN"}'`
      : `'{}'`;
    return `\`\`\`bash\nnode tool.js ${sanitizeName(cmd.name)} ${params}\n\`\`\`\n${cmd.description || ''}\n`;
  }).join('\n');

  return `---
name: ${skillName}
description: |
  Auto-generated from documentation. Type: ${docType}.
  Source: ${sources}
---

# ${skillName}

Generated from: ${sources}
Document type: ${docType}

## Commands

${commandDocs}

## Install / Update

\`\`\`bash
node tool.js install '{"target":"~/.cursor/skills/${skillName}"}'
node tool.js update '{"target":"~/.cursor/skills/${skillName}"}'
\`\`\`
`;
}

function generatePackageJson(skillName) {
  return JSON.stringify({ name: skillName, version: '1.0.0', private: true }, null, 2) + '\n';
}

function generateDocSource(extract) {
  return JSON.stringify({
    sources: extract.sources || [],
    generatedAt: new Date().toISOString(),
    extractId: extract.id,
  }, null, 2) + '\n';
}

function sanitizeName(name) {
  return name.replace(/[^a-zA-Z0-9_]/g, '_').replace(/^(\d)/, '_$1');
}

function generate(extract, analysis, skillName, targetDir) {
  const dest = path.resolve(targetDir.replace(/^~/, process.env.HOME || ''));
  fs.mkdirSync(dest, { recursive: true });

  fs.writeFileSync(path.join(dest, 'tool.js'), generateToolJs(skillName, analysis, extract), 'utf-8');
  fs.writeFileSync(path.join(dest, 'SKILL.md'), generateSkillMd(skillName, analysis, extract), 'utf-8');
  fs.writeFileSync(path.join(dest, 'package.json'), generatePackageJson(skillName), 'utf-8');
  fs.writeFileSync(path.join(dest, 'doc-source.json'), generateDocSource(extract), 'utf-8');

  return dest;
}

module.exports = { generate, generateToolJs, generateSkillMd, sanitizeName };
