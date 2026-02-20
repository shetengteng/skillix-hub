'use strict';

const { fork } = require('child_process');
const path = require('path');

async function install(context, params, response) {
  const channel = context.config.browser?.launchOptions?.channel ?? context.config.browser?.browserName ?? 'chrome';
  let cliPath;
  try {
    cliPath = path.join(require.resolve('playwright-core/package.json'), '../cli.js');
  } catch {
    cliPath = path.join(require.resolve('playwright/package.json'), '../cli.js');
  }

  const child = fork(cliPath, ['install', channel], { stdio: 'pipe' });
  const output = [];
  child.stdout?.on('data', data => output.push(data.toString()));
  child.stderr?.on('data', data => output.push(data.toString()));
  await new Promise((resolve, reject) => {
    child.on('close', code => {
      if (code === 0) resolve();
      else reject(new Error(`Failed to install browser: ${output.join('')}`));
    });
  });
  response.addTextResult(`Browser ${channel} installed.`);
}

module.exports = { install };
