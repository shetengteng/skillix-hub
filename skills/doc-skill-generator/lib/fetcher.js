'use strict';

const fs = require('fs');
const path = require('path');
const { EXTRACTS_DIR } = require('./config');
const { readPdf } = require('./pdf-reader');
const { crawlBFS, crawlSinglePage } = require('./crawler');

function generateId() {
  return `ext-${Date.now()}`;
}

function readLocalFile(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`File not found: ${filePath}`);
  }
  const content = fs.readFileSync(filePath, 'utf-8');
  const ext = path.extname(filePath).toLowerCase();
  const title = path.basename(filePath, ext);

  return {
    source: filePath,
    type: ext === '.md' ? 'markdown' : 'text',
    title,
    sections: [{ heading: title, level: 1, content, codeBlocks: [], tables: [], links: [] }],
    metadata: { estimatedTokens: Math.ceil(content.length / 4) },
  };
}

function detectSourceType(source) {
  if (source.type) return source.type;
  const val = source.value || source;
  if (typeof val !== 'string') return 'unknown';
  if (val.endsWith('.pdf') || val.includes('.pdf?')) return 'pdf';
  if (val.startsWith('http://') || val.startsWith('https://')) return 'url';
  if (val.endsWith('.md') || val.endsWith('.txt') || val.endsWith('.json')) return 'file';
  if (fs.existsSync(val)) return 'file';
  return 'url';
}

async function fetchSource(source, crawlConfig) {
  const type = detectSourceType(source);
  const value = source.value || source;

  switch (type) {
    case 'pdf':
      return await readPdf(value);

    case 'url': {
      const result = crawlConfig?.singlePage
        ? { rootUrl: value, pages: [crawlSinglePage(value)], totalPages: 1 }
        : crawlBFS(value, crawlConfig);

      const allSections = [];
      for (const page of result.pages) {
        for (const section of (page.sections || [])) {
          allSections.push(section);
        }
      }

      return {
        source: value,
        type: 'webpage',
        title: result.pages[0]?.title || value,
        sections: allSections,
        pages: result.pages,
        metadata: {
          totalPages: result.totalPages,
          estimatedTokens: allSections.reduce((sum, s) => sum + Math.ceil((s.content || '').length / 4), 0),
        },
      };
    }

    case 'file':
      return readLocalFile(value);

    default:
      throw new Error(`Unsupported source type: ${type} for ${value}`);
  }
}

async function fetchAll(sources, crawlConfig) {
  const id = generateId();
  const results = [];
  const errors = [];

  for (const source of sources) {
    try {
      const result = await fetchSource(source, crawlConfig);
      result.fetchedAt = new Date().toISOString();
      results.push(result);
    } catch (e) {
      errors.push({ source: source.value || source, error: e.message });
    }
  }

  let totalSections = 0;
  let totalCodeBlocks = 0;
  let totalTables = 0;
  let totalTokens = 0;

  for (const r of results) {
    for (const s of (r.sections || [])) {
      totalSections++;
      totalCodeBlocks += (s.codeBlocks || []).length;
      totalTables += (s.tables || []).length;
      totalTokens += Math.ceil((s.content || '').length / 4);
    }
  }

  const extract = {
    id,
    status: errors.length > 0 ? 'partial' : 'completed',
    sources: sources.map(s => ({ type: detectSourceType(s), value: s.value || s })),
    documents: results,
    summary: { totalDocuments: results.length, totalSections, totalCodeBlocks, totalTables, estimatedTokens: totalTokens },
    errors: errors.length > 0 ? errors : undefined,
    createdAt: new Date().toISOString(),
  };

  const extractPath = path.join(EXTRACTS_DIR, `${id}.json`);
  fs.writeFileSync(extractPath, JSON.stringify(extract, null, 2), 'utf-8');

  return extract;
}

function loadExtract(id) {
  const filePath = path.join(EXTRACTS_DIR, `${id}.json`);
  if (!fs.existsSync(filePath)) return null;
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

function listExtracts() {
  if (!fs.existsSync(EXTRACTS_DIR)) return [];
  return fs.readdirSync(EXTRACTS_DIR)
    .filter(f => f.endsWith('.json') && !f.endsWith('.meta.json'))
    .map(f => {
      const data = JSON.parse(fs.readFileSync(path.join(EXTRACTS_DIR, f), 'utf-8'));
      return {
        id: data.id,
        status: data.status,
        sources: data.sources,
        summary: data.summary,
        createdAt: data.createdAt,
      };
    })
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

function deleteExtract(id) {
  const filePath = path.join(EXTRACTS_DIR, `${id}.json`);
  if (!fs.existsSync(filePath)) return false;
  fs.unlinkSync(filePath);
  return true;
}

module.exports = { fetchAll, fetchSource, loadExtract, listExtracts, deleteExtract, generateId };
