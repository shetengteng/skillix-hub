'use strict';

const fs = require('fs');
const path = require('path');
const { extractToMarkdown, estimateTokens } = require('./extractor');
const { loadTemplate, renderTemplate } = require('./template');
const { GENERATED_DIR } = require('./config');

function urlToFilename(url) {
  try {
    const u = new URL(url);
    let name = u.pathname.replace(/^\/|\/$/g, '').replace(/\//g, '-').replace(/\.html?$/, '');
    if (!name) name = 'index';
    return name.replace(/[^a-zA-Z0-9_-]/g, '_').substring(0, 80) + '.md';
  } catch {
    return 'page.md';
  }
}

function pageToMarkdown(page) {
  const parts = [];
  parts.push(`# ${page.title || page.url}\n`);
  parts.push(`> Source: ${page.url}\n`);

  for (const section of (page.sections || [])) {
    const heading = '#'.repeat(Math.min((section.level || 1) + 1, 6)) + ' ' + (section.heading || '');
    parts.push(heading);
    if (section.content) parts.push(section.content);
    for (const cb of (section.codeBlocks || [])) {
      parts.push(`\`\`\`${cb.language || ''}\n${cb.code}\n\`\`\``);
    }
    for (const table of (section.tables || [])) {
      if (table.length === 0) continue;
      const header = table[0];
      parts.push('| ' + header.join(' | ') + ' |');
      parts.push('| ' + header.map(() => '---').join(' | ') + ' |');
      for (let i = 1; i < table.length; i++) {
        parts.push('| ' + table[i].join(' | ') + ' |');
      }
    }
    parts.push('');
  }
  return parts.join('\n');
}

function generateToolJs(skillName, analysis, extract) {
  const commands = analysis.suggestedCommands || [];

  const commandEntries = commands.slice(0, 30).map(cmd => {
    if (cmd.method && cmd.path) {
      return `
  async ${sanitizeName(cmd.name)}(params) {
    const url = BASE_URL + renderPath('${cmd.path}', params);
    const resp = await fetch(url, {
      method: '${cmd.method}',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders(params) },
      ${cmd.method !== 'GET' ? "body: params.body ? JSON.stringify(params.body) : undefined," : ''}
    });
    const data = await resp.json().catch(() => resp.text());
    return success({ status: resp.status, data });
  },`;
    }
    return `
  async ${sanitizeName(cmd.name)}(params) {
    // TODO: implement ${cmd.description || cmd.name}
    return success({ message: '${cmd.name} executed', params });
  },`;
  });

  return renderTemplate('tool-js.tpl.js', {
    COMMAND_ENTRIES: commandEntries.join(''),
  });
}

function buildDescription(extract, docFiles, docType) {
  const docs = extract.documents || [];
  const firstDoc = docs[0];
  const mainTitle = firstDoc?.title || firstDoc?.source || '';

  const topics = docFiles
    .filter(f => f.sections > 1 && f.tokens > 50)
    .map(f => f.title)
    .filter(t => t && t.length < 60)
    .slice(0, 10);

  const totalTokens = docFiles.reduce((s, f) => s + f.tokens, 0);

  const lines = [];
  if (mainTitle) lines.push(mainTitle + ' documentation reference.');
  lines.push(`Contains ${docFiles.length} pages (~${totalTokens} tokens) of ${docType} documentation.`);
  if (topics.length > 0) {
    lines.push('Covers: ' + topics.join(', ') + '.');
  }
  lines.push('Read the docs/ files for detailed API, usage examples, and configuration.');
  return lines.join('\n  ');
}

function buildOverview(extract, docFiles) {
  const docs = extract.documents || [];
  const firstDoc = docs[0];
  const pages = firstDoc?.pages || [];

  const contentPages = pages.filter(p => p.sections && p.sections.length > 1);
  if (contentPages.length === 0) return '';

  const firstPage = contentPages[0];
  const contentSections = (firstPage.sections || []).filter(s => s.content && s.content.length > 20);
  const overview = contentSections.slice(0, 3).map(s => {
    const text = s.content.replace(/\\n/g, ' ').trim();
    return text.length > 300 ? text.substring(0, 300) + '...' : text;
  }).join('\n\n');

  return overview || '';
}

function generateSkillMd(skillName, analysis, extract, docFiles) {
  const commands = analysis.suggestedCommands || [];
  const docType = analysis.docType?.primary || 'unknown';
  const sources = (extract.sources || []).map(s => s.value).join(', ');
  const description = buildDescription(extract, docFiles, docType);
  const overview = buildOverview(extract, docFiles);

  const commandDocs = commands.slice(0, 30).map(cmd => {
    const params = cmd.method && cmd.path
      ? `'{"token":"YOUR_TOKEN"}'`
      : `'{}'`;
    return `\`\`\`bash\nnode tool.js ${sanitizeName(cmd.name)} ${params}\n\`\`\`\n${cmd.description || ''}\n`;
  }).join('\n');

  const docIndex = docFiles.map(f =>
    `- [${f.title}](docs/${f.filename}) (${f.sections} sections, ~${f.tokens} tokens)`
  ).join('\n');

  return renderTemplate('skill-md.tpl.md', {
    SKILL_NAME: skillName,
    DESCRIPTION: description,
    OVERVIEW: overview ? overview + '\n\n' : '',
    SOURCES: sources,
    DOC_TYPE: docType,
    PAGE_COUNT: String(docFiles.length),
    COMMANDS_SECTION: commandDocs ? '## Commands\n\n' + commandDocs + '\n' : '',
    DOC_INDEX: docIndex,
  });
}

function generatePackageJson(skillName) {
  return JSON.stringify({ name: skillName, version: '1.0.0', private: true }, null, 2) + '\n';
}

function generateDocSource(extract) {
  return JSON.stringify({
    sources: extract.sources || [],
    generatedAt: new Date().toISOString(),
    extractId: extract.id,
  }, null, 2) + '\n';
}

function sanitizeName(name) {
  return name.replace(/[^a-zA-Z0-9_]/g, '_').replace(/^(\d)/, '_$1');
}

function generate(extract, analysis, skillName) {
  const dest = path.join(GENERATED_DIR, skillName);
  if (fs.existsSync(dest)) fs.rmSync(dest, { recursive: true, force: true });
  const docsDir = path.join(dest, 'docs');
  fs.mkdirSync(docsDir, { recursive: true });

  const docFiles = [];
  const docs = extract.documents || [];

  for (const doc of docs) {
    const pages = doc.pages || [];
    if (pages.length === 0) {
      const filename = urlToFilename(doc.source || 'document');
      const content = pageToMarkdown({
        url: doc.source,
        title: doc.title,
        sections: doc.sections,
      });
      fs.writeFileSync(path.join(docsDir, filename), content, 'utf-8');
      docFiles.push({
        filename,
        title: doc.title || doc.source,
        sections: (doc.sections || []).length,
        tokens: (doc.sections || []).reduce((s, sec) => s + estimateTokens(sec.content), 0),
      });
    } else {
      for (const page of pages) {
        if (!page.sections || page.sections.length === 0) continue;
        const filename = urlToFilename(page.url || 'page');
        const content = pageToMarkdown(page);
        fs.writeFileSync(path.join(docsDir, filename), content, 'utf-8');
        docFiles.push({
          filename,
          title: page.title || page.url,
          sections: page.sections.length,
          tokens: page.sections.reduce((s, sec) => s + estimateTokens(sec.content), 0),
        });
      }
    }
  }

  fs.writeFileSync(path.join(dest, 'tool.js'), generateToolJs(skillName, analysis, extract), 'utf-8');
  fs.writeFileSync(path.join(dest, 'package.json'), generatePackageJson(skillName), 'utf-8');
  fs.writeFileSync(path.join(dest, 'doc-source.json'), generateDocSource(extract), 'utf-8');

  const prompt = buildSkillMdPrompt(skillName, analysis, extract, docFiles, dest);

  return { dest, docFiles, prompt };
}

function buildSkillMdPrompt(skillName, analysis, extract, docFiles, dest) {
  const docType = analysis.docType?.primary || 'unknown';
  const sources = (extract.sources || []).map(s => s.value).join(', ');
  const totalTokens = docFiles.reduce((s, f) => s + f.tokens, 0);

  const docIndex = docFiles.map(f =>
    `- ${f.title} (docs/${f.filename}, ${f.sections} sections, ~${f.tokens} tokens)`
  ).join('\n');

  const topDocs = docFiles
    .filter(f => f.tokens > 50)
    .sort((a, b) => b.tokens - a.tokens)
    .slice(0, 5)
    .map(f => `docs/${f.filename}`)
    .join(', ');

  return renderTemplate('skill-md-prompt.tpl.txt', {
    SKILL_NAME: skillName,
    DEST: dest,
    DOC_COUNT: String(docFiles.length),
    TOTAL_TOKENS: String(totalTokens),
    DOC_TYPE: docType,
    SOURCES: sources,
    DOC_INDEX: docIndex,
    TOP_DOCS: topDocs,
  });
}

module.exports = { generate, generateToolJs, generateSkillMd, sanitizeName, urlToFilename, pageToMarkdown, buildSkillMdPrompt };
