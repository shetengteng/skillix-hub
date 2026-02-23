'use strict';

const fs = require('fs');
const path = require('path');

const TEMPLATES_DIR = path.join(__dirname, '..', 'templates');

let _injectScript = null;
let _collectScript = null;

function buildInjectionScript() {
  if (!_injectScript) {
    _injectScript = fs.readFileSync(path.join(TEMPLATES_DIR, 'inject.js.tpl'), 'utf-8');
  }
  return _injectScript;
}

function getCollectScript() {
  if (!_collectScript) {
    _collectScript = fs.readFileSync(path.join(TEMPLATES_DIR, 'collect.js.tpl'), 'utf-8');
  }
  return _collectScript;
}

const COLLECT_SCRIPT = getCollectScript();

module.exports = { buildInjectionScript, COLLECT_SCRIPT };
