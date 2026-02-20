#!/usr/bin/env node
'use strict';

const { resolveConfig } = require('./lib/config');
const { BrowserManager } = require('./lib/browser-manager');
const { Context } = require('./lib/context');
const { Response } = require('./lib/response');

const toolRegistry = {};

function registerTools(modulePath) {
  const tools = require(modulePath);
  for (const [name, handler] of Object.entries(tools))
    toolRegistry[name] = handler;
}

registerTools('./tools/navigate');
registerTools('./tools/snapshot');
registerTools('./tools/keyboard');
registerTools('./tools/mouse');
registerTools('./tools/form');
registerTools('./tools/evaluate');
registerTools('./tools/screenshot');
registerTools('./tools/wait');
registerTools('./tools/common');
registerTools('./tools/tabs');
registerTools('./tools/console');
registerTools('./tools/network');
registerTools('./tools/dialogs');
registerTools('./tools/files');
registerTools('./tools/cookies');
registerTools('./tools/storage');
registerTools('./tools/webstorage');
registerTools('./tools/route');
registerTools('./tools/pdf');
registerTools('./tools/tracing');
registerTools('./tools/video');
registerTools('./tools/verify');
registerTools('./tools/devtools');
registerTools('./tools/install');
registerTools('./tools/config');
registerTools('./tools/runCode');

const META_COMMANDS = {
  async start() {
    const config = resolveConfig();
    const manager = new BrowserManager(config);
    const { reused } = await manager.connect();
    if (reused)
      return { result: 'Browser already running.' };
    return { result: 'Browser started.' };
  },

  async stop() {
    const config = resolveConfig();
    const manager = new BrowserManager(config);
    await manager.close();
    return { result: 'Browser stopped.' };
  },

  async status() {
    const config = resolveConfig();
    const manager = new BrowserManager(config);
    return await manager.status();
  },

  async list() {
    return { tools: Object.keys(toolRegistry).sort() };
  },
};

async function main() {
  const [command, argsJson] = [process.argv[2], process.argv[3]];

  if (!command) {
    console.log(JSON.stringify({ error: 'Usage: node tool.js <command> [json_params]' }));
    process.exit(1);
  }

  if (META_COMMANDS[command]) {
    try {
      const result = await META_COMMANDS[command]();
      console.log(JSON.stringify(result, null, 2));
      process.exit(0);
    } catch (e) {
      console.log(JSON.stringify({ error: e.message }));
      process.exit(1);
    }
    return;
  }

  const handler = toolRegistry[command];
  if (!handler) {
    console.log(JSON.stringify({ error: `Unknown command: ${command}. Run 'node tool.js list' to see available commands.` }));
    process.exit(1);
  }

  let params = {};
  if (argsJson) {
    try {
      params = JSON.parse(argsJson);
    } catch {
      console.log(JSON.stringify({ error: `Invalid JSON params: ${argsJson}` }));
      process.exit(1);
    }
  }

  const config = resolveConfig();
  const manager = new BrowserManager(config);

  try {
    const { browserContext } = await manager.connect();
    const context = new Context(config, browserContext);
    const response = new Response(context);

    await handler(context, params, response);

    const output = await response.serialize();
    console.log(JSON.stringify(output, null, 2));
    process.exit(0);
  } catch (e) {
    console.log(JSON.stringify({ error: e.message }));
    process.exit(1);
  }
}

main();
