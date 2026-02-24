#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { success, error } = require('./lib/response');
const { getPlaywrightTool, filterNavigations } = require('./lib/config');
const { readState, requestStop, waitForResult, cleanupFiles, isProcessAlive } = require('./lib/recorder');
const store = require('./lib/store');
const { replay } = require('./lib/replayer');
const { generate } = require('./lib/generator');
const { exportScript } = require('./lib/exporter');

const COMMANDS = {
  async record(params) {
    if (!params.name) return error('name is required');

    const state = readState();
    if (state && state.active && state.pid && isProcessAlive(state.pid)) {
      return error(`Already recording: ${state.name} (${state.id})`);
    }

    cleanupFiles();

    const daemon = spawn(process.execPath, [path.join(__dirname, 'lib', 'daemon.js'), params.name], {
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    let startOutput = '';
    const startPromise = new Promise((resolve) => {
      daemon.stdout.on('data', (chunk) => {
        startOutput += chunk.toString();
        if (startOutput.includes('\n')) {
          resolve();
        }
      });
      daemon.stderr.on('data', (chunk) => {
        startOutput += chunk.toString();
        if (startOutput.includes('\n')) {
          resolve();
        }
      });
      setTimeout(resolve, 10000);
    });

    daemon.unref();
    await startPromise;

    daemon.stdout.destroy();
    daemon.stderr.destroy();

    const line = startOutput.trim().split('\n')[0];
    try {
      const result = JSON.parse(line);
      if (result.error) return error(result.error);
      return success(result);
    } catch {
      return error(`Daemon start failed: ${startOutput.trim()}`);
    }
  },

  async stop() {
    const state = readState();
    if (!state || !state.active) return error('No active recording');
    if (state.pid && !isProcessAlive(state.pid)) {
      cleanupFiles();
      return error('Recording process is no longer running');
    }

    requestStop();

    const result = waitForResult(30000);
    if (!result) {
      return error('Stop timed out — daemon may have crashed');
    }

    const domEvents = result.rawEvents.filter((e) => e.type !== 'network' && e.type !== 'navigation');
    const rawNavEvents = result.rawEvents.filter((e) => e.type === 'navigation');
    const navEvents = filterNavigations(rawNavEvents);
    const apiEvents = result.rawEvents.filter((e) =>
      e.type === 'network' && e.request && e.request.resourceType === 'Fetch',
    );

    return success({
      message: `Recording stopped. Captured ${result.eventCount} events (${result.domCount} DOM, ${result.networkCount} network).`,
      id: result.id,
      name: result.name,
      startedAt: result.startedAt,
      stoppedAt: result.stoppedAt,
      eventCount: result.eventCount,
      domCount: result.domCount,
      networkCount: result.networkCount,
      summary: {
        domEvents,
        navigations: navEvents,
        apiRequests: apiEvents.map((e) => ({
          method: e.request.method,
          url: e.request.url,
          status: e.response?.status,
          body: e.request.body,
          responseBody: e.response?.body,
        })),
      },
      rawEventsFile: `recordings/${new Date().toISOString().slice(0, 10)}-${result.id}.json`,
    });
  },

  async save(params) {
    if (!params.id) return error('id is required');
    if (!params.workflow) return error('workflow object is required');

    const workflow = params.workflow;
    workflow.id = params.id;
    workflow.updatedAt = new Date().toISOString();
    if (!workflow.createdAt) workflow.createdAt = workflow.updatedAt;

    store.save(workflow);
    return success({
      message: `Workflow saved: ${workflow.name || params.id}`,
      id: params.id,
      stepCount: workflow.steps ? workflow.steps.length : 0,
    });
  },

  async status() {
    const state = readState();
    if (!state || !state.active) return success({ recording: false });
    if (state.pid && !isProcessAlive(state.pid)) {
      cleanupFiles();
      return success({ recording: false });
    }
    return success({
      recording: true,
      id: state.id,
      name: state.name,
      startedAt: state.startedAt,
      eventCount: state.eventCount || 0,
    });
  },

  async list() {
    const workflows = store.list();
    return success({ workflows, count: workflows.length });
  },

  async show(params) {
    if (!params.id) return error('id is required');
    const wf = store.load(params.id);
    if (!wf) return error(`Workflow not found: ${params.id}`);
    return success(wf);
  },

  async delete(params) {
    if (!params.id) return error('id is required');
    const removed = store.remove(params.id);
    if (!removed) return error(`Workflow not found: ${params.id}`);
    return success({ message: `Deleted: ${params.id}` });
  },

  async replay(params) {
    if (!params.id) return error('id is required');
    const wf = store.load(params.id);
    if (!wf) return error(`Workflow not found: ${params.id}`);

    if (wf.params && wf.params.length > 0) {
      const missing = wf.params
        .filter((p) => p.required && (!params.params || !params.params[p.id]))
        .map((p) => p.id);
      if (missing.length > 0) {
        return error(`Missing required params: ${missing.join(', ')}`);
      }
    }

    const result = replay(wf, params.params || {}, params.startFrom);
    if (result.success) return success(result);

    // 失败时返回结构化上下文（供 LLM 自愈），不用裸 error 字符串
    return success({
      completed: false,
      workflowId: result.workflowId,
      workflowName: result.workflowName,
      failedAt: result.failedAt,
      failedStep: result.failedStep,
      recovery: result.recovery,
      results: result.results,
    });
  },

  async generate(params) {
    if (!params.id) return error('id is required');
    if (!params.skillName) return error('skillName is required');

    const wf = store.load(params.id);
    if (!wf) return error(`Workflow not found: ${params.id}`);

    const target = params.target || `~/.cursor/skills/${params.skillName}`;
    try {
      const dest = generate(wf, params.skillName, target);
      return success({
        message: `Skill generated: ${params.skillName}`,
        path: dest,
        files: ['SKILL.md', 'tool.js', 'workflow.json', 'package.json'],
      });
    } catch (e) {
      return error(`Generate failed: ${e.message}`);
    }
  },

  async export(params) {
    if (!params.id) return error('id is required');
    if (!params.output) return error('output path is required');

    const wf = store.load(params.id);
    if (!wf) return error(`Workflow not found: ${params.id}`);

    try {
      const dest = exportScript(wf, params.output);
      return success({ message: `Exported to ${dest}`, path: dest });
    } catch (e) {
      return error(`Export failed: ${e.message}`);
    }
  },

  // Phase 4: Agent 在录制期间可调用此命令辅助操作（如导航到特定 URL）
  async exec(params) {
    if (!params.command) return error('command is required (e.g. navigate, click, fill)');

    const pw = getPlaywrightTool();
    if (!pw) return error('Playwright Skill not found. Install it first.');

    const { execSync } = require('child_process');
    const args = params.args || {};
    const argsJson = JSON.stringify(args);
    const escaped = argsJson.replace(/'/g, "'\\''");

    try {
      const out = execSync(`node "${pw}" ${params.command} '${escaped}'`, {
        encoding: 'utf-8',
        timeout: params.timeout || 30000,
      });
      let result;
      try { result = JSON.parse(out); } catch { result = out; }
      return success({ command: params.command, args, result });
    } catch (e) {
      return error(`exec failed: ${e.message}`);
    }
  },

  async install(params) {
    const target = params.target;
    if (!target) return error('target is required (e.g. "~/.cursor/skills/web-automation-builder")');

    const srcDir = path.join(__dirname);
    const destDir = path.resolve(target.replace(/^~/, process.env.HOME || ''));
    const COPY_ITEMS = ['SKILL.md', 'tool.js', 'package.json', 'lib', 'templates'];

    try {
      fs.mkdirSync(destDir, { recursive: true });
      for (const item of COPY_ITEMS) {
        const src = path.join(srcDir, item);
        if (!fs.existsSync(src)) continue;
        fs.cpSync(src, path.join(destDir, item), { recursive: true, force: true });
      }

      const pw = getPlaywrightTool();
      const pwStatus = pw ? 'found' : 'NOT FOUND — install Playwright Skill first';

      return success({
        message: `Installed to ${destDir}`,
        path: destDir,
        playwright: pwStatus,
      });
    } catch (e) {
      return error(`Install failed: ${e.message}`);
    }
  },
};

async function main() {
  const [command, argsJson] = [process.argv[2], process.argv[3]];

  if (!command) {
    console.log(JSON.stringify(error(
      "Usage: node tool.js <command> '{json_params}'\n" +
      'Commands: record, stop, save, status, list, show, delete, replay, generate, export, exec, install'
    )));
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
