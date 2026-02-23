#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { success, error } = require('./lib/response');
const { fetchAll, loadExtract, listExtracts, deleteExtract } = require('./lib/fetcher');
const { summarizeExtract, extractToMarkdown } = require('./lib/extractor');
const { analyze } = require('./lib/analyzer');
const { generate } = require('./lib/generator');
const { SKILL_DIR, EXTRACTS_DIR } = require('./lib/config');

const COMMANDS = {
  async fetch(params) {
    if (!params.sources || !Array.isArray(params.sources) || params.sources.length === 0) {
      return error('sources is required (array of {type, value})');
    }

    const crawlConfig = {
      maxDepth: params.maxDepth || 3,
      maxPages: params.maxPages || 50,
      singlePage: params.singlePage || false,
    };

    try {
      const extract = await fetchAll(params.sources, crawlConfig);
      return success({
        id: extract.id,
        status: extract.status,
        summary: extract.summary,
        errors: extract.errors,
        message: `Fetched ${extract.summary.totalDocuments} document(s), ${extract.summary.totalSections} sections, ~${extract.summary.estimatedTokens} tokens`,
      });
    } catch (e) {
      return error(`Fetch failed: ${e.message}`);
    }
  },

  async 'list-extracts'(params) {
    const items = listExtracts();
    return success({ extracts: items, count: items.length });
  },

  async 'show-extract'(params) {
    if (!params.id) return error('id is required');
    const extract = loadExtract(params.id);
    if (!extract) return error(`Extract not found: ${params.id}`);

    if (params.format === 'markdown') {
      const md = extractToMarkdown(extract, params.maxTokens);
      return success({ id: extract.id, markdown: md });
    }

    const summary = summarizeExtract(extract);
    return success({
      id: extract.id,
      status: extract.status,
      summary: extract.summary,
      text: summary,
      sources: extract.sources,
      createdAt: extract.createdAt,
    });
  },

  async 'delete-extract'(params) {
    if (!params.id) return error('id is required');
    const removed = deleteExtract(params.id);
    if (!removed) return error(`Extract not found: ${params.id}`);
    return success({ message: `Deleted extract ${params.id}` });
  },

  async append(params) {
    if (!params.id) return error('id is required');
    if (!params.sources || !Array.isArray(params.sources)) return error('sources is required');

    const existing = loadExtract(params.id);
    if (!existing) return error(`Extract not found: ${params.id}`);

    const crawlConfig = {
      maxDepth: params.maxDepth || 3,
      maxPages: params.maxPages || 20,
      singlePage: params.singlePage || false,
    };

    try {
      const additional = await fetchAll(params.sources, crawlConfig);

      existing.documents = (existing.documents || []).concat(additional.documents || []);
      existing.sources = (existing.sources || []).concat(additional.sources || []);

      let totalSections = 0, totalCodeBlocks = 0, totalTables = 0, totalTokens = 0;
      for (const doc of existing.documents) {
        for (const s of (doc.sections || [])) {
          totalSections++;
          totalCodeBlocks += (s.codeBlocks || []).length;
          totalTables += (s.tables || []).length;
          totalTokens += Math.ceil((s.content || '').length / 4);
        }
      }
      existing.summary = {
        totalDocuments: existing.documents.length,
        totalSections, totalCodeBlocks, totalTables, estimatedTokens: totalTokens,
      };
      existing.updatedAt = new Date().toISOString();

      const extractPath = path.join(EXTRACTS_DIR, `${params.id}.json`);
      fs.writeFileSync(extractPath, JSON.stringify(existing, null, 2), 'utf-8');

      return success({
        id: params.id,
        appended: additional.summary.totalDocuments,
        summary: existing.summary,
        message: `Appended ${additional.summary.totalDocuments} document(s)`,
      });
    } catch (e) {
      return error(`Append failed: ${e.message}`);
    }
  },

  async analyze(params) {
    if (!params.id) return error('id is required');
    const extract = loadExtract(params.id);
    if (!extract) return error(`Extract not found: ${params.id}`);

    try {
      const result = analyze(extract);
      return success(result);
    } catch (e) {
      return error(`Analyze failed: ${e.message}`);
    }
  },

  async preview(params) {
    if (!params.id) return error('id is required');
    if (!params.skillName) return error('skillName is required');

    const extract = loadExtract(params.id);
    if (!extract) return error(`Extract not found: ${params.id}`);

    const analysis = analyze(extract);
    return success({
      skillName: params.skillName,
      docType: analysis.docType,
      commands: analysis.suggestedCommands?.slice(0, 20),
      files: ['SKILL.md', 'tool.js', 'package.json', 'doc-source.json'],
    });
  },

  async generate(params) {
    if (!params.id) return error('id is required');
    if (!params.skillName) return error('skillName is required');
    if (!params.target) return error('target is required');

    const extract = loadExtract(params.id);
    if (!extract) return error(`Extract not found: ${params.id}`);

    try {
      const analysis = analyze(extract);
      const dest = generate(extract, analysis, params.skillName, params.target);
      return success({
        message: `Generated skill "${params.skillName}" at ${dest}`,
        path: dest,
        docType: analysis.docType?.primary,
        commands: analysis.suggestedCommands?.length || 0,
      });
    } catch (e) {
      return error(`Generate failed: ${e.message}`);
    }
  },

  async update(params) {
    if (!params.target) return error('target is required');
    const dest = path.resolve(params.target.replace(/^~/, process.env.HOME || ''));
    const docSourcePath = path.join(dest, 'doc-source.json');

    if (!fs.existsSync(docSourcePath)) {
      return error(`No doc-source.json found at ${dest}. Cannot update.`);
    }

    const docSource = JSON.parse(fs.readFileSync(docSourcePath, 'utf-8'));
    const sources = docSource.sources || [];

    if (sources.length === 0) {
      return error('No sources found in doc-source.json');
    }

    const fetchResult = await COMMANDS.fetch({ sources });
    if (fetchResult.error) return fetchResult;

    const extractId = fetchResult.result.id;
    const skillName = path.basename(dest);

    return COMMANDS.generate({ id: extractId, skillName, target: params.target });
  },

  async install(params) {
    if (!params.target) return error('target is required');
    const srcDir = SKILL_DIR;
    const destDir = path.resolve(params.target.replace(/^~/, process.env.HOME || ''));
    const COPY_ITEMS = ['SKILL.md', 'tool.js', 'package.json', 'lib'];

    try {
      fs.mkdirSync(destDir, { recursive: true });
      for (const item of COPY_ITEMS) {
        const src = path.join(srcDir, item);
        if (!fs.existsSync(src)) continue;
        fs.cpSync(src, path.join(destDir, item), { recursive: true, force: true });
      }
      return success({ message: `Installed to ${destDir}`, path: destDir });
    } catch (e) {
      return error(`Install failed: ${e.message}`);
    }
  },

  async 'update-self'(params) {
    if (!params.target) return error('target is required');
    const destDir = path.resolve(params.target.replace(/^~/, process.env.HOME || ''));

    if (fs.existsSync(destDir)) {
      const dataDir = path.join(path.dirname(destDir), 'doc-skill-generator-data');
      const entries = fs.readdirSync(destDir);
      for (const entry of entries) {
        fs.rmSync(path.join(destDir, entry), { recursive: true, force: true });
      }
    }

    return COMMANDS.install(params);
  },
};

async function main() {
  const [command, argsJson] = [process.argv[2], process.argv[3]];

  if (!command) {
    console.log(JSON.stringify(error(
      "Usage: node tool.js <command> '{json_params}'\n" +
      'Commands: ' + Object.keys(COMMANDS).join(', ')
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
