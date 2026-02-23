#!/usr/bin/env node
'use strict';

const path = require('path');
const fs = require('fs');

const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/doc-skill-generator');
const TESTDATA_DIR = path.resolve(__dirname, '../../testdata/runtime');

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function makeSandbox(label) {
  const id = `${label}-${Date.now()}`;
  const dir = path.join(TESTDATA_DIR, id);
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function cleanSandbox(dir) {
  try { fs.rmSync(dir, { recursive: true, force: true }); } catch { /* ok */ }
}

// --- response.js ---

function test_response() {
  const { success, error } = require(path.join(SKILL_DIR, 'lib/response'));
  const s = success({ msg: 'ok' });
  assert(s.result && s.result.msg === 'ok', 'success wraps data');
  assert(s.error === null, 'success error is null');

  const e = error('fail');
  assert(e.result === null, 'error result is null');
  assert(e.error === 'fail', 'error wraps message');
}

// --- extractor.js ---

function test_extractor() {
  const { summarizeExtract, extractToMarkdown, estimateTokens } = require(path.join(SKILL_DIR, 'lib/extractor'));

  assert(estimateTokens('hello world') === 3, 'estimateTokens basic');
  assert(estimateTokens('') === 0, 'estimateTokens empty');
  assert(estimateTokens(null) === 0, 'estimateTokens null');

  const extract = {
    id: 'ext-test',
    status: 'completed',
    documents: [{
      source: 'test.md',
      type: 'markdown',
      title: 'Test Doc',
      sections: [
        { heading: 'Intro', level: 1, content: 'Hello world', codeBlocks: [{ language: 'js', code: 'console.log(1)' }], tables: [] },
        { heading: 'Details', level: 2, content: 'More info', codeBlocks: [], tables: [[['Col1', 'Col2'], ['a', 'b']]] },
      ],
    }],
    createdAt: '2026-02-23T10:00:00Z',
  };

  const summary = summarizeExtract(extract);
  assert(summary.includes('ext-test'), 'summary contains id');
  assert(summary.includes('Test Doc'), 'summary contains title');
  assert(summary.includes('Intro'), 'summary contains heading');

  const md = extractToMarkdown(extract);
  assert(md.includes('# Test Doc'), 'markdown contains title');
  assert(md.includes('console.log(1)'), 'markdown contains code');
  assert(md.includes('Col1'), 'markdown contains table');

  const mdTruncated = extractToMarkdown(extract, 5);
  assert(mdTruncated.includes('Truncated') || mdTruncated.length < md.length, 'markdown respects token limit');
}

// --- analyzer.js ---

function test_analyzer() {
  const { detectDocType, extractApiEndpoints, extractCliCommands } = require(path.join(SKILL_DIR, 'lib/analyzer'));

  const apiExtract = {
    documents: [{
      sections: [
        { heading: 'Users', level: 2, content: 'GET /api/users returns a list of users. POST /api/users creates a user. Authorization: Bearer token', codeBlocks: [], tables: [] },
        { heading: 'Auth', level: 2, content: 'All endpoints require bearer token in Authorization header', codeBlocks: [], tables: [] },
      ],
    }],
  };

  const apiType = detectDocType(apiExtract);
  assert(apiType.primary === 'api-reference', 'detects API reference');
  assert(apiType.confidence === 'high' || apiType.confidence === 'medium', 'reasonable confidence for API');

  const endpoints = extractApiEndpoints(apiExtract);
  assert(endpoints.length >= 2, 'extracts at least 2 endpoints');
  assert(endpoints.some(e => e.method === 'GET' && e.path.includes('/api/users')), 'finds GET /api/users');
  assert(endpoints.some(e => e.method === 'POST'), 'finds POST endpoint');

  const cliExtract = {
    documents: [{
      sections: [
        { heading: 'Commands', level: 2, content: 'CLI tool with subcommands', codeBlocks: [
          { language: 'bash', code: '$ myapp init\n$ myapp build --output dist\n$ myapp deploy staging' },
        ], tables: [] },
      ],
    }],
  };

  const cliType = detectDocType(cliExtract);
  assert(cliType.primary === 'cli-reference', 'detects CLI reference');

  const cmds = extractCliCommands(cliExtract);
  assert(cmds.length >= 2, 'extracts CLI commands');
}

// --- generator.js ---

function test_generator() {
  const sandbox = makeSandbox('generator');
  try {
    const { generate, sanitizeName } = require(path.join(SKILL_DIR, 'lib/generator'));

    assert(sanitizeName('hello-world') === 'hello_world', 'sanitizeName replaces hyphens');
    assert(sanitizeName('123abc') === '_123abc', 'sanitizeName prefixes digits');

    const extract = {
      id: 'ext-gen-test',
      sources: [{ type: 'url', value: 'https://example.com' }],
      documents: [{
        title: 'Example API',
        sections: [{ heading: 'Users', level: 2, content: 'GET /api/users', codeBlocks: [], tables: [] }],
      }],
      summary: { totalDocuments: 1, totalSections: 1, totalCodeBlocks: 0, totalTables: 0, estimatedTokens: 100 },
    };

    const analysis = {
      docType: { primary: 'api-reference' },
      suggestedCommands: [
        { name: 'users', description: 'GET /api/users', method: 'GET', path: '/api/users' },
      ],
    };

    const dest = generate(extract, analysis, 'test-api', sandbox);
    assert(dest === sandbox, 'generate returns target path');
    assert(fs.existsSync(path.join(sandbox, 'SKILL.md')), 'generates SKILL.md');
    assert(fs.existsSync(path.join(sandbox, 'tool.js')), 'generates tool.js');
    assert(fs.existsSync(path.join(sandbox, 'package.json')), 'generates package.json');
    assert(fs.existsSync(path.join(sandbox, 'doc-source.json')), 'generates doc-source.json');

    const pkg = JSON.parse(fs.readFileSync(path.join(sandbox, 'package.json'), 'utf-8'));
    assert(pkg.name === 'test-api', 'package.json has correct name');

    const skillMd = fs.readFileSync(path.join(sandbox, 'SKILL.md'), 'utf-8');
    assert(skillMd.includes('test-api'), 'SKILL.md contains skill name');
    assert(skillMd.includes('api-reference'), 'SKILL.md contains doc type');

    const toolJs = fs.readFileSync(path.join(sandbox, 'tool.js'), 'utf-8');
    assert(toolJs.includes('users'), 'tool.js contains command name');
    assert(toolJs.includes('/api/users'), 'tool.js contains API path');
  } finally {
    cleanSandbox(sandbox);
  }
}

// --- fetcher.js (local file only, no Playwright) ---

function test_fetcher_local() {
  const sandbox = makeSandbox('fetcher');
  try {
    const configMod = require(path.join(SKILL_DIR, 'lib/config'));
    const savedExtracts = configMod.EXTRACTS_DIR;
    configMod.EXTRACTS_DIR = path.join(sandbox, 'extracts');
    fs.mkdirSync(configMod.EXTRACTS_DIR, { recursive: true });

    delete require.cache[require.resolve(path.join(SKILL_DIR, 'lib/fetcher'))];
    const { fetchAll, loadExtract, listExtracts, deleteExtract } = require(path.join(SKILL_DIR, 'lib/fetcher'));

    const testFile = path.join(sandbox, 'test.md');
    fs.writeFileSync(testFile, '# Test\n\nHello world\n', 'utf-8');

    return (async () => {
      const extract = await fetchAll([{ type: 'file', value: testFile }]);
      assert(extract.id.startsWith('ext-'), 'fetch returns id with ext- prefix');
      assert(extract.status === 'completed', 'fetch status is completed');
      assert(extract.summary.totalDocuments === 1, 'fetch has 1 document');

      const loaded = loadExtract(extract.id);
      assert(loaded !== null, 'loadExtract returns data');
      assert(loaded.id === extract.id, 'loadExtract preserves id');

      const items = listExtracts();
      assert(items.length === 1, 'listExtracts returns 1 item');

      const removed = deleteExtract(extract.id);
      assert(removed === true, 'deleteExtract returns true');

      const items2 = listExtracts();
      assert(items2.length === 0, 'listExtracts returns 0 after delete');

      configMod.EXTRACTS_DIR = savedExtracts;
    })();
  } catch (e) {
    cleanSandbox(sandbox);
    throw e;
  }
}

async function main() {
  console.log('test_response:');
  test_response();

  console.log('\ntest_extractor:');
  test_extractor();

  console.log('\ntest_analyzer:');
  test_analyzer();

  console.log('\ntest_generator:');
  test_generator();

  console.log('\ntest_fetcher_local:');
  await test_fetcher_local();

  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
