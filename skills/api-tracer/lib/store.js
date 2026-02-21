'use strict';

const fs = require('fs');
const path = require('path');
const { TRACER_STATE_DIR, ensureDir, readJson, writeJson } = require('./config');

const SESSIONS_DIR = path.join(TRACER_STATE_DIR, 'sessions');

function sessionPath(name) {
  return path.join(SESSIONS_DIR, `${name}.json`);
}

async function saveSession(name, data) {
  await ensureDir(SESSIONS_DIR);
  await writeJson(sessionPath(name), data);
}

async function loadSession(name) {
  return await readJson(sessionPath(name));
}

async function listSessions() {
  await ensureDir(SESSIONS_DIR);
  const files = await fs.promises.readdir(SESSIONS_DIR);
  const sessions = [];
  for (const file of files) {
    if (!file.endsWith('.json')) continue;
    const data = await readJson(path.join(SESSIONS_DIR, file));
    if (data) {
      sessions.push({
        name: path.basename(file, '.json'),
        target: data.session?.target || 'unknown',
        startTime: data.session?.startTime,
        endTime: data.session?.endTime,
        totalRequests: data.requests?.length || 0,
      });
    }
  }
  return sessions;
}

async function deleteSession(name) {
  try {
    await fs.promises.unlink(sessionPath(name));
    return true;
  } catch {
    return false;
  }
}

module.exports = { saveSession, loadSession, listSessions, deleteSession, sessionPath, SESSIONS_DIR };
