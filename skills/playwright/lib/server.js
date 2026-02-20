#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const net = require('net');
const { spawn } = require('child_process');
const { resolveConfig, ensureDir } = require('./config');

const STATE_FILE = 'browser-state.json';

async function findFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
    server.on('error', reject);
  });
}

async function main() {
  const config = resolveConfig();
  const stateDir = config.stateDir;
  const browserName = config.browser.browserName || 'chromium';
  const channel = config.browser.launchOptions.channel || 'chrome';
  const headless = config.browser.launchOptions.headless;

  const cdpPort = await findFreePort();

  let execPath;
  try {
    const pw = require('playwright-core');
    const registry = require('playwright-core/lib/server').registry;
    const descriptor = registry.findExecutable(channel) || registry.findExecutable(browserName);
    execPath = descriptor?.executablePath();
  } catch {}

  if (!execPath) {
    const pw = require('playwright-core');
    const bt = pw[browserName];
    execPath = bt?.executablePath(channel);
  }

  if (!execPath) {
    process.stderr.write(`Cannot find browser executable for ${channel || browserName}\n`);
    process.exit(1);
  }

  const args = [
    `--remote-debugging-port=${cdpPort}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-networking',
    '--disable-default-apps',
    '--disable-sync',
  ];
  if (headless) args.push('--headless=new');

  const child = spawn(execPath, args, {
    detached: true,
    stdio: 'ignore',
  });
  child.unref();

  await new Promise(r => setTimeout(r, 1500));

  await ensureDir(stateDir);
  const stateFile = path.join(stateDir, STATE_FILE);
  const cdpEndpoint = `http://127.0.0.1:${cdpPort}`;

  fs.writeFileSync(stateFile, JSON.stringify({
    wsEndpoint: cdpEndpoint,
    pid: child.pid,
    browserName,
    startedAt: new Date().toISOString(),
  }, null, 2));

  process.stdout.write(JSON.stringify({ wsEndpoint: cdpEndpoint, pid: child.pid }) + '\n');
}

main().catch(e => {
  process.stderr.write(e.message + '\n');
  process.exit(1);
});
