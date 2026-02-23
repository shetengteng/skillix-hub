#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { success, error } = require('./lib/response');
const { getPlaywrightTool } = require('./lib/config');
const recorder = require('./lib/recorder');
const store = require('./lib/store');
const { replay } = require('./lib/replayer');
const { generate } = require('./lib/generator');
const { exportScript } = require('./lib/exporter');

function execPlaywright(command, args) {
  const tool = getPlaywrightTool();
  if (!tool) throw new Error('Playwright Skill not found');

  const argsJson = JSON.stringify(args);
  const cmd = `node "${tool}" ${command} '${argsJson.replace(/'/g, "'\\''")}'`;
  const output = execSync(cmd, { encoding: 'utf-8', timeout: 60000 });
  try { return JSON.parse(output); } catch { return output; }
}

const COMMANDS = {
  async record(params) {
    if (!params.name) return error('name is required');
    const result = recorder.start(params.name);
    if (!result.started) return error(result.reason);
    return success({ message: `Recording started: ${result.name}`, id: result.id });
  },

  async stop() {
    const workflow = recorder.stop();
    if (!workflow) return error('No active recording');
    store.save(workflow);
    return success({
      message: `Recording stopped. Saved ${workflow.steps.length} steps.`,
      id: workflow.id,
      name: workflow.name,
      stepCount: workflow.steps.length,
    });
  },

  async status() {
    const state = recorder.getState();
    if (!state || !state.active) {
      return success({ recording: false });
    }
    return success({
      recording: true,
      id: state.id,
      name: state.name,
      stepCount: state.steps.length,
      startedAt: state.startedAt,
    });
  },

  async exec(params) {
    const { command, args } = params;
    if (!command) return error('command is required');

    let playwrightResult;
    try {
      playwrightResult = execPlaywright(command, args || {});
    } catch (e) {
      return error(`Playwright command failed: ${e.message}`);
    }

    if (recorder.isRecording()) {
      recorder.addStep(command, args || {}, playwrightResult);
    }

    if (typeof playwrightResult === 'object' && playwrightResult !== null) {
      return playwrightResult;
    }
    return success(playwrightResult);
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
        .filter(p => p.required && (!params.params || !params.params[p.id]))
        .map(p => p.id);
      if (missing.length > 0) {
        return error(`Missing required params: ${missing.join(', ')}`);
      }
    }

    const result = replay(wf, params.params || {});
    return result.success ? success(result) : error(result.error || `Replay failed at step ${result.results?.length || '?'}`);
  },

  async analyze(params) {
    if (!params.id) return error('id is required');
    const wf = store.load(params.id);
    if (!wf) return error(`Workflow not found: ${params.id}`);

    const suggestions = [];
    for (const step of wf.steps) {
      if (step.command === 'type' && step.args.text) {
        suggestions.push({
          stepSeq: step.seq,
          field: 'args.text',
          currentValue: step.args.text,
          suggestedParam: guessParamName(step),
          reason: 'Text input — likely a variable value',
        });
      }
      if (step.command === 'navigate' && step.args.url) {
        const url = step.args.url;
        if (url.includes('?') || /\/\d+/.test(url)) {
          suggestions.push({
            stepSeq: step.seq,
            field: 'args.url',
            currentValue: url,
            suggestedParam: 'targetUrl',
            reason: 'URL contains query params or numeric IDs',
          });
        }
      }
    }

    return success({
      workflowId: wf.id,
      workflowName: wf.name,
      totalSteps: wf.steps.length,
      suggestions,
      hint: 'Use these suggestions to parameterize the workflow. Replace values with {{paramName}} syntax.',
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

  async install(params) {
    const target = params.target;
    if (!target) return error('target is required (e.g. "~/.cursor/skills/web-automation-builder")');

    const srcDir = path.join(__dirname);
    const destDir = path.resolve(target.replace(/^~/, process.env.HOME || ''));
    const COPY_ITEMS = ['SKILL.md', 'tool.js', 'package.json', 'lib'];

    try {
      fs.mkdirSync(destDir, { recursive: true });
      for (const item of COPY_ITEMS) {
        const src = path.join(srcDir, item);
        if (!fs.existsSync(src)) continue;
        fs.cpSync(src, path.join(destDir, item), { recursive: true, force: true });
      }

      fs.mkdirSync(path.join(destDir, 'workflows'), { recursive: true });

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

  async update(params) {
    const target = params.target;
    if (!target) return error('target is required');

    const destDir = path.resolve(target.replace(/^~/, process.env.HOME || ''));

    if (fs.existsSync(destDir)) {
      const wfDir = path.join(destDir, 'workflows');
      let savedWorkflows = null;
      if (fs.existsSync(wfDir)) {
        savedWorkflows = path.join(destDir, '.wf-backup-' + Date.now());
        fs.cpSync(wfDir, savedWorkflows, { recursive: true });
      }

      const entries = fs.readdirSync(destDir);
      for (const entry of entries) {
        if (entry === 'workflows' || entry.startsWith('.wf-backup-')) continue;
        fs.rmSync(path.join(destDir, entry), { recursive: true, force: true });
      }

      const installResult = await COMMANDS.install({ target });
      if (installResult.error) return installResult;

      if (savedWorkflows) {
        fs.cpSync(savedWorkflows, path.join(destDir, 'workflows'), { recursive: true, force: true });
        fs.rmSync(savedWorkflows, { recursive: true, force: true });
      }

      return success({
        message: `Updated at ${destDir} (workflows preserved)`,
        path: destDir,
        playwright: installResult.result.playwright,
      });
    }

    return COMMANDS.install({ target });
  },
};

function guessParamName(step) {
  const locators = step.locators || {};
  if (locators.ariaLabel) return locators.ariaLabel.replace(/\s+/g, '_').toLowerCase();
  if (locators.placeholder) return locators.placeholder.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase().replace(/_+/g, '_').replace(/^_|_$/g, '');
  if (locators.css) {
    const idMatch = locators.css.match(/#([\w-]+)/);
    if (idMatch) return idMatch[1];
    const nameMatch = locators.css.match(/\[name="?([\w-]+)"?\]/);
    if (nameMatch) return nameMatch[1];
  }
  return `input_${step.seq}`;
}

async function main() {
  const [command, argsJson] = [process.argv[2], process.argv[3]];

  if (!command) {
    console.log(JSON.stringify(error(
      "Usage: node tool.js <command> '{json_params}'\n" +
      'Commands: record, stop, status, exec, list, show, delete, replay, analyze, generate, export, install, update'
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
