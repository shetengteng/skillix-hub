#!/usr/bin/env node
'use strict';

const { spawn } = require('child_process');
const path = require('path');
const { readJson, writeJson, TRACER_STATE_FILE, getBrowserWsEndpoint } = require('./lib/config');
const { loadSession, listSessions, deleteSession } = require('./lib/store');
const { analyze } = require('./lib/analyzer');
const { toMarkdown, toCurl } = require('./lib/reporter');

const DAEMON_SCRIPT = path.join(__dirname, 'lib', 'daemon.js');

const commands = {
  async start(params) {
    const state = await readJson(TRACER_STATE_FILE);
    if (state?.recording && state?.pid) {
      try {
        process.kill(state.pid, 0);
        return { error: `Already recording session "${state.sessionName}". Stop it first.` };
      } catch {}
    }

    const wsEndpoint = params.wsEndpoint || await getBrowserWsEndpoint();
    if (!wsEndpoint) {
      return {
        error: 'No browser found. Start Playwright browser first:\n' +
               '  node skills/playwright/tool.js navigate \'{"url":"https://example.com"}\'',
      };
    }

    const daemonArgs = JSON.stringify({
      name: params.name || `trace-${Date.now()}`,
      wsEndpoint,
      filter: params.filter || null,
    });

    const child = spawn(process.execPath, [DAEMON_SCRIPT, daemonArgs], {
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    const result = await new Promise((resolve, reject) => {
      let data = '';
      const timeout = setTimeout(() => reject(new Error('Daemon startup timeout')), 10000);
      child.stdout.on('data', chunk => {
        data += chunk.toString();
        const nl = data.indexOf('\n');
        if (nl !== -1) {
          clearTimeout(timeout);
          try {
            resolve(JSON.parse(data.substring(0, nl)));
          } catch (e) {
            reject(new Error('Invalid daemon response: ' + data));
          }
        }
      });
      child.stderr.on('data', chunk => { data += chunk.toString(); });
      child.on('error', e => { clearTimeout(timeout); reject(e); });
      child.on('exit', code => {
        clearTimeout(timeout);
        reject(new Error(`Daemon exited with code ${code}: ${data}`));
      });
    });

    child.stdout.destroy();
    child.stderr.destroy();
    child.unref();

    return { result: `Recording started: ${result.sessionName}`, ...result };
  },

  async stop(params) {
    const state = await readJson(TRACER_STATE_FILE);
    if (!state?.recording || !state?.pid) {
      return { error: 'No active recording.' };
    }

    try {
      process.kill(state.pid, 'SIGTERM');
    } catch (e) {
      return { error: `Failed to stop daemon (pid ${state.pid}): ${e.message}` };
    }

    await new Promise(r => setTimeout(r, 1500));

    const newState = await readJson(TRACER_STATE_FILE);
    return {
      result: `Recording stopped: ${state.sessionName}`,
      sessionName: state.sessionName,
      capturedRequests: state.capturedRequests || 0,
      saved: !newState?.recording,
    };
  },

  async status(params) {
    const state = await readJson(TRACER_STATE_FILE);
    if (!state) return { recording: false };

    if (state.recording && state.pid) {
      try {
        process.kill(state.pid, 0);
        return {
          recording: true,
          sessionName: state.sessionName,
          startTime: state.startTime,
          capturedRequests: state.capturedRequests || 0,
          pendingRequests: state.pendingRequests || 0,
        };
      } catch {
        return { recording: false, note: 'Daemon process not found.' };
      }
    }

    return { recording: false, lastSession: state.lastSession || null };
  },

  async sessions(params) {
    const sessions = await listSessions();
    if (sessions.length === 0) return { result: 'No recorded sessions.' };
    return { sessions };
  },

  async detail(params) {
    if (!params.name) return { error: 'Missing required parameter: name' };
    const session = await loadSession(params.name);
    if (!session) return { error: `Session "${params.name}" not found.` };

    if (params.index !== undefined) {
      const req = session.requests?.[params.index];
      if (!req) return { error: `Request index ${params.index} not found.` };
      return req;
    }

    const requests = (session.requests || []).map((r, i) => ({
      index: i,
      method: r.method,
      url: r.url,
      status: r.status,
      resourceType: r.resourceType,
      mimeType: r.mimeType,
    }));

    if (params.filter) {
      const filtered = requests.filter(r => r.url.includes(params.filter));
      return { session: session.session, requests: filtered, total: requests.length, filtered: filtered.length };
    }

    return { session: session.session, requests, total: requests.length };
  },

  async report(params) {
    if (!params.name) return { error: 'Missing required parameter: name' };
    const session = await loadSession(params.name);
    if (!session) return { error: `Session "${params.name}" not found.` };

    const report = analyze(session);
    const format = params.format || 'json';

    if (format === 'markdown' || format === 'md') {
      return { result: toMarkdown(report) };
    }
    if (format === 'curl') {
      return { result: toCurl(report) };
    }
    return report;
  },

  async delete(params) {
    if (!params.name) return { error: 'Missing required parameter: name' };
    const ok = await deleteSession(params.name);
    return ok
      ? { result: `Session "${params.name}" deleted.` }
      : { error: `Session "${params.name}" not found.` };
  },
};

async function main() {
  const [command, argsJson] = [process.argv[2], process.argv[3]];

  if (!command) {
    console.log(JSON.stringify({
      error: 'Usage: node tool.js <command> [json_params]',
      commands: Object.keys(commands),
    }));
    process.exit(1);
  }

  const handler = commands[command];
  if (!handler) {
    console.log(JSON.stringify({
      error: `Unknown command: ${command}`,
      commands: Object.keys(commands),
    }));
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

  try {
    const result = await handler(params);
    console.log(JSON.stringify(result, null, 2));
  } catch (e) {
    console.log(JSON.stringify({ error: e.message }));
    process.exit(1);
  }
}

main();
