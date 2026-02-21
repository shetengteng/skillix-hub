#!/usr/bin/env node
'use strict';

function success(data) {
  return { result: data, error: null };
}

function error(message) {
  return { result: null, error: message };
}

// TODO: implement commands
const COMMANDS = {
  async example(params) {
    return success({ message: 'hello from {{name}}' });
  },
};

async function main() {
  const [command, argsJson] = [process.argv[2], process.argv[3]];

  if (!command) {
    console.log(JSON.stringify(error("Usage: node tool.js <command> '{json_params}'")));
    process.exit(1);
  }

  const handler = COMMANDS[command];
  if (!handler) {
    console.log(JSON.stringify(error(`Unknown command: ${command}. Available: ${Object.keys(COMMANDS).join(', ')}`)));
    process.exit(1);
  }

  let params = {};
  if (argsJson) {
    try {
      params = JSON.parse(argsJson);
    } catch {
      console.log(JSON.stringify(error(`Invalid JSON params: ${argsJson}`)));
      process.exit(1);
    }
  }

  try {
    const result = await handler(params);
    console.log(JSON.stringify(result, null, 2));
    process.exit(0);
  } catch (e) {
    console.log(JSON.stringify(error(e.message)));
    process.exit(1);
  }
}

main();
