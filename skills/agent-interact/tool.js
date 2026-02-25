#!/usr/bin/env node
'use strict';

const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');
const { success, error } = require('./lib/response');
const path = require('path');
const { execSync } = require('child_process');
const { DEFAULT_PORT, PORT_RANGE, PID_FILE } = require('./lib/config');

const os = require('os');

const UI_DIR = path.join(__dirname, 'ui');
const UI_DIST = path.join(UI_DIR, 'dist');
const ELECTRON_MAIN = path.join(__dirname, 'electron', 'main.js');

function electronPidFile(port) {
  return path.join(os.tmpdir(), `agent-interact-electron-${port}.pid`);
}

function getPort(params) {
  return params.port || DEFAULT_PORT;
}

function isPortFree(port) {
  return new Promise((resolve) => {
    const net = require('net');
    const srv = net.createServer();
    srv.once('error', () => resolve(false));
    srv.once('listening', () => { srv.close(); resolve(true); });
    srv.listen(port, '127.0.0.1');
  });
}

async function findFreePort(startPort) {
  for (let p = startPort; p < startPort + PORT_RANGE; p++) {
    if (await isPortFree(p)) return p;
  }
  return null;
}

function ensureUiBuild() {
  if (fs.existsSync(path.join(UI_DIST, 'index.html'))) return;
  if (!fs.existsSync(path.join(UI_DIR, 'package.json'))) return;
  const nmPath = path.join(UI_DIR, 'node_modules');
  if (!fs.existsSync(nmPath)) {
    execSync('npm install', { cwd: UI_DIR, stdio: 'ignore' });
  }
  execSync('npm run build', { cwd: UI_DIR, stdio: 'ignore' });
}

function getElectronBin() {
  try {
    return require('electron');
  } catch {
    return null;
  }
}

function isElectronRunning(port) {
  const pidFile = electronPidFile(port);
  if (!fs.existsSync(pidFile)) return false;
  const pid = parseInt(fs.readFileSync(pidFile, 'utf-8').trim(), 10);
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    try { fs.unlinkSync(pidFile); } catch { /* ok */ }
    return false;
  }
}

function startElectron(port) {
  const electronBin = getElectronBin();
  if (!electronBin || !fs.existsSync(ELECTRON_MAIN)) return null;

  const child = spawn(electronBin, [ELECTRON_MAIN, String(port)], {
    detached: true,
    stdio: 'ignore',
    env: { ...process.env, ELECTRON_DISABLE_SECURITY_WARNINGS: 'true' },
  });
  child.unref();

  try {
    fs.writeFileSync(electronPidFile(port), String(child.pid));
  } catch { /* ok */ }

  return child.pid;
}

function stopElectron(port) {
  const pidFile = electronPidFile(port);
  if (!fs.existsSync(pidFile)) return;
  const pid = parseInt(fs.readFileSync(pidFile, 'utf-8').trim(), 10);
  try { process.kill(pid, 'SIGTERM'); } catch { /* already dead */ }
  try { fs.unlinkSync(pidFile); } catch { /* ok */ }
}

function openBrowserFallback(url) {
  if (process.platform === 'darwin') {
    try {
      execSync(
        `osascript -e 'tell application "Google Chrome" to make new window' -e 'tell application "Google Chrome" to set URL of active tab of front window to "${url}"' -e 'tell application "Google Chrome" to activate'`,
        { stdio: 'ignore' }
      );
      return;
    } catch { /* fallback */ }
    try { execSync(`open -n "${url}"`, { stdio: 'ignore' }); return; } catch { /* ok */ }
  }
  const cmd = process.platform === 'win32' ? 'start' : 'xdg-open';
  try { execSync(`${cmd} "${url}"`, { stdio: 'ignore' }); } catch { /* ok */ }
}

function httpRequest(method, urlPath, port, body) {
  return new Promise((resolve, reject) => {
    const opts = { hostname: '127.0.0.1', port, path: urlPath, method, headers: { 'Content-Type': 'application/json' } };
    const req = http.request(opts, (res) => {
      let data = '';
      res.on('data', (c) => (data += c));
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch { resolve(data); }
      });
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

function isRunning(port) {
  return httpRequest('GET', '/api/status', port)
    .then(() => true)
    .catch(() => false);
}

function ensureElectron(port) {
  if (isElectronRunning(port)) return 'running';
  const pid = startElectron(port);
  if (pid) return 'started';
  openBrowserFallback(`http://127.0.0.1:${port}`);
  return 'browser_fallback';
}

const COMMANDS = {
  async start(params) {
    const requestedPort = getPort(params);
    if (await isRunning(requestedPort)) {
      ensureElectron(requestedPort);
      return success({ message: `Server already running on port ${requestedPort}` });
    }

    ensureUiBuild();

    let port = requestedPort;
    if (!(await isPortFree(port))) {
      const free = await findFreePort(port);
      if (!free) return error(`Ports ${port}-${port + PORT_RANGE - 1} all occupied`);
      port = free;
    }

    const child = spawn(process.execPath, [__filename, '_serve', JSON.stringify({ port })], {
      detached: true,
      stdio: 'ignore',
    });
    child.unref();

    for (let i = 0; i < 20; i++) {
      await new Promise((r) => setTimeout(r, 300));
      if (await isRunning(port)) {
        const url = `http://127.0.0.1:${port}`;
        const msg = port !== requestedPort
          ? `Port ${requestedPort} occupied, started on ${url}`
          : `Server started on ${url}`;

        const electronStatus = ensureElectron(port);
        return success({ message: msg, url, pid: child.pid, electron: electronStatus });
      }
    }
    return error('Server failed to start within timeout');
  },

  async stop(params) {
    const port = getPort(params);
    stopElectron(port);
    if (!(await isRunning(port))) {
      return success({ message: 'Server is not running' });
    }
    if (fs.existsSync(PID_FILE)) {
      const pid = parseInt(fs.readFileSync(PID_FILE, 'utf-8').trim(), 10);
      try { process.kill(pid, 'SIGTERM'); } catch { /* already dead */ }
      try { fs.unlinkSync(PID_FILE); } catch { /* ok */ }
    }
    return success({ message: 'Server stopped' });
  },

  async status(params) {
    const port = getPort(params);
    try {
      const data = await httpRequest('GET', '/api/status', port);
      return success({ ...data, electron: isElectronRunning(port) ? 'running' : 'stopped' });
    } catch {
      return success({ status: 'stopped', electron: isElectronRunning(port) ? 'running' : 'stopped' });
    }
  },

  async dialog(params) {
    const port = getPort(params);

    if (!(await isRunning(port))) {
      const startResult = await COMMANDS.start({ port });
      if (startResult.error) return startResult;
    } else {
      ensureElectron(port);
    }

    const { type, port: _p, ...rest } = params;
    if (!type) return error('type is required');

    const body = { type, ...rest };

    try {
      const result = await httpRequest('POST', '/api/dialog', port, body);
      return result;
    } catch (e) {
      return error(`Failed to create dialog: ${e.message}`);
    }
  },

  async install(params) {
    const target = params.target;
    if (target) {
      const srcDir = __dirname;
      const destDir = path.resolve(target.replace(/^~/, process.env.HOME || ''));
      const destUiDir = path.join(destDir, 'ui');

      const COPY_ITEMS = ['SKILL.md', 'tool.js', 'demo.js', 'package.json', 'package-lock.json', 'lib', 'electron'];

      try {
        fs.mkdirSync(destDir, { recursive: true });

        for (const item of COPY_ITEMS) {
          const src = path.join(srcDir, item);
          if (!fs.existsSync(src)) continue;
          const dest = path.join(destDir, item);
          fs.cpSync(src, dest, { recursive: true, force: true });
        }

        fs.mkdirSync(destUiDir, { recursive: true });
        const uiSrcDir = path.join(srcDir, 'ui');
        const uiEntries = fs.readdirSync(uiSrcDir);
        const UI_SKIP = new Set(['node_modules', 'dist', '.vite']);
        for (const entry of uiEntries) {
          if (UI_SKIP.has(entry)) continue;
          fs.cpSync(path.join(uiSrcDir, entry), path.join(destUiDir, entry), { recursive: true, force: true });
        }

        execSync('npm install', { cwd: destDir, stdio: 'inherit' });
        execSync('npm install', { cwd: destUiDir, stdio: 'inherit' });
        execSync('npm run build', { cwd: destUiDir, stdio: 'inherit' });

        return success({ message: `Installed to ${destDir} (copy + dependencies + UI build)`, path: destDir });
      } catch (e) {
        return error(`Install to ${destDir} failed: ${e.message}`);
      }
    }

    const ROOT_DIR = __dirname;
    try {
      execSync('npm install', { cwd: ROOT_DIR, stdio: 'inherit' });
      execSync('npm install', { cwd: UI_DIR, stdio: 'inherit' });
      execSync('npm run build', { cwd: UI_DIR, stdio: 'inherit' });
      return success({ message: 'Install completed (dependencies + UI build)' });
    } catch (e) {
      return error(`Install failed: ${e.message}`);
    }
  },

  async update(params) {
    const target = params.target;
    const ROOT_DIR = target
      ? path.resolve(target.replace(/^~/, process.env.HOME || ''))
      : __dirname;
    const uiDir = path.join(ROOT_DIR, 'ui');

    if (target) {
      const srcDir = __dirname;
      const COPY_ITEMS = ['SKILL.md', 'tool.js', 'demo.js', 'package.json', 'package-lock.json', 'lib', 'electron'];
      try {
        for (const item of COPY_ITEMS) {
          const src = path.join(srcDir, item);
          if (!fs.existsSync(src)) continue;
          const dest = path.join(ROOT_DIR, item);
          if (fs.existsSync(dest)) fs.rmSync(dest, { recursive: true });
          fs.cpSync(src, dest, { recursive: true, force: true });
        }

        const uiSrcDir = path.join(srcDir, 'ui');
        const uiEntries = fs.readdirSync(uiSrcDir);
        const UI_SKIP = new Set(['node_modules', 'dist', '.vite']);
        for (const entry of uiEntries) {
          if (UI_SKIP.has(entry)) continue;
          const dest = path.join(uiDir, entry);
          if (fs.existsSync(dest)) fs.rmSync(dest, { recursive: true });
          fs.cpSync(path.join(uiSrcDir, entry), dest, { recursive: true, force: true });
        }
      } catch (e) {
        return error(`Update copy failed: ${e.message}`);
      }
    }

    const rootNm = path.join(ROOT_DIR, 'node_modules');
    const uiNm = path.join(uiDir, 'node_modules');
    const uiDist = path.join(uiDir, 'dist');
    try {
      if (fs.existsSync(rootNm)) fs.rmSync(rootNm, { recursive: true });
      if (fs.existsSync(uiNm)) fs.rmSync(uiNm, { recursive: true });
      if (fs.existsSync(uiDist)) fs.rmSync(uiDist, { recursive: true });
      execSync('npm install', { cwd: ROOT_DIR, stdio: 'inherit' });
      execSync('npm install', { cwd: uiDir, stdio: 'inherit' });
      execSync('npm run build', { cwd: uiDir, stdio: 'inherit' });
      return success({ message: `Update completed${target ? ` at ${ROOT_DIR}` : ''} (clean reinstall + UI rebuild)` });
    } catch (e) {
      return error(`Update failed: ${e.message}`);
    }
  },
};

async function main() {
  const [command, argsJson] = [process.argv[2], process.argv[3]];

  if (command === '_serve') {
    const params = argsJson ? JSON.parse(argsJson) : {};
    const { createServer } = require('./lib/server');
    const srv = createServer(params.port || DEFAULT_PORT);
    srv.start((port) => {
      process.stdout.write(`agent-interact server listening on http://127.0.0.1:${port}\n`);
    });
    process.on('SIGTERM', () => { srv.stop(); process.exit(0); });
    process.on('SIGINT', () => { srv.stop(); process.exit(0); });
    return;
  }

  if (!command) {
    console.log(JSON.stringify(error("Usage: node tool.js <command> '{json_params}'\nCommands: start, stop, status, dialog, install, update")));
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
    catch { console.log(JSON.stringify(error(`Invalid JSON params: ${argsJson}`))); process.exit(1); }
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
