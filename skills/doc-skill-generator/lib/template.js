'use strict';

const fs = require('fs');
const path = require('path');

const TEMPLATES_DIR = path.join(path.dirname(__dirname), 'templates');
const cache = new Map();

function loadTemplate(name) {
  if (cache.has(name)) return cache.get(name);
  const content = fs.readFileSync(path.join(TEMPLATES_DIR, name), 'utf-8');
  cache.set(name, content);
  return content;
}

function renderTemplate(name, vars) {
  let content = loadTemplate(name);
  for (const [key, value] of Object.entries(vars)) {
    content = content.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value ?? '');
  }
  return content;
}

module.exports = { loadTemplate, renderTemplate };
