#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.BASE_URL || '';

function success(data) { return { result: data, error: null }; }
function error(msg) { return { result: null, error: msg }; }

function renderPath(template, params) {
  return template.replace(/\{(\w+)\}/g, (_, key) => params[key] || key);
}

function getAuthHeaders(params) {
  if (params.token) return { Authorization: 'Bearer ' + params.token };
  return {};
}

const COMMANDS = {
{{COMMAND_ENTRIES}}

  async install(params) {
    if (!params.target) return error('target is required');
    const srcDir = __dirname;
    const destDir = path.resolve(params.target.replace(/^~/, process.env.HOME || ''));
    fs.cpSync(srcDir, destDir, { recursive: true, force: true });
    return success({ message: 'Installed to ' + destDir, path: destDir });
  },

  async update(params) {
    return COMMANDS.install(params);
  },
};

async function main() {
  const [command, argsJson] = [process.argv[2], process.argv[3]];
  if (!command) {
    console.log(JSON.stringify(error('Usage: node tool.js <command> \'{json_params}\'')));
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
