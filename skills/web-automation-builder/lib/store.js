'use strict';

const fs = require('fs');
const path = require('path');
const { WORKFLOWS_DIR } = require('./config');

function ensureDir() {
  if (!fs.existsSync(WORKFLOWS_DIR)) {
    fs.mkdirSync(WORKFLOWS_DIR, { recursive: true });
  }
}

function filePath(id) {
  return path.join(WORKFLOWS_DIR, `${id}.json`);
}

function save(workflow) {
  ensureDir();
  fs.writeFileSync(filePath(workflow.id), JSON.stringify(workflow, null, 2));
}

function load(id) {
  const p = filePath(id);
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf-8'));
}

function list() {
  ensureDir();
  const files = fs.readdirSync(WORKFLOWS_DIR).filter(f => f.endsWith('.json'));
  return files.map(f => {
    const wf = JSON.parse(fs.readFileSync(path.join(WORKFLOWS_DIR, f), 'utf-8'));
    return {
      id: wf.id,
      name: wf.name,
      stepCount: wf.steps ? wf.steps.length : 0,
      paramCount: wf.params ? wf.params.length : 0,
      createdAt: wf.createdAt,
    };
  });
}

function remove(id) {
  const p = filePath(id);
  if (!fs.existsSync(p)) return false;
  fs.unlinkSync(p);
  return true;
}

module.exports = { save, load, list, remove };
