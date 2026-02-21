#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/web-content-reader');
const { extract } = require(path.join(SKILL_DIR, 'lib/extractor'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function test_extractTitle() {
  const html = '<html><head><title>My Page</title></head><body><p>Hello</p></body></html>';
  const result = extract(html, { output: 'text' });
  assert(result.title === 'My Page', 'extracts title from <title> tag');
}

function test_extractTitle_og() {
  const html = '<html><head><meta property="og:title" content="OG Title"><title>Fallback</title></head><body><p>Hello</p></body></html>';
  const result = extract(html, { output: 'text' });
  assert(result.title === 'OG Title', 'prefers og:title over <title>');
}

function test_extractContent() {
  const html = '<html><body><h1>Title</h1><p>Paragraph text</p><script>var x=1;</script></body></html>';
  const result = extract(html, { output: 'text', noiseTags: ['script'] });
  assert(result.content.includes('Title'), 'content includes heading');
  assert(result.content.includes('Paragraph text'), 'content includes paragraph');
  assert(!result.content.includes('var x'), 'content excludes script');
}

function test_extractMeta() {
  const html = `<html><head>
    <meta name="description" content="Page description">
    <meta property="og:title" content="OG Title">
    <meta property="og:image" content="https://img.example.com/pic.jpg">
    <meta property="og:url" content="https://example.com/page">
    <link rel="canonical" href="https://example.com/page">
  </head><body><p>Content</p></body></html>`;
  const result = extract(html, { output: 'text' });
  assert(result.meta.description === 'Page description', 'extracts description');
  assert(result.meta.ogTitle === 'OG Title', 'extracts ogTitle');
  assert(result.meta.ogImage === 'https://img.example.com/pic.jpg', 'extracts ogImage');
  assert(result.meta.canonical === 'https://example.com/page', 'extracts canonical');
}

function test_extractTables() {
  const html = `<html><body>
    <table>
      <thead><tr><th>Name</th><th>Age</th></tr></thead>
      <tbody>
        <tr><td>Alice</td><td>30</td></tr>
        <tr><td>Bob</td><td>25</td></tr>
      </tbody>
    </table>
  </body></html>`;
  const result = extract(html, { output: 'json' });
  assert(result.tables.length === 1, 'extracts one table');
  assert(result.tables[0].headers.length === 2, 'table has 2 headers');
  assert(result.tables[0].headers[0] === 'Name', 'first header is Name');
  assert(result.tables[0].rows.length === 2, 'table has 2 rows');
  assert(result.tables[0].rows[0][0] === 'Alice', 'first row first cell is Alice');
}

function test_extractLinks() {
  const html = `<html><body>
    <a href="https://example.com">Example</a>
    <a href="/about">About</a>
    <a href="#section">Section</a>
    <a href="javascript:void(0)">JS Link</a>
  </body></html>`;
  const result = extract(html, { output: 'json' });
  assert(result.links.length === 2, 'extracts 2 valid links (excludes # and javascript:)');
  assert(result.links[0].text === 'Example', 'first link text correct');
  assert(result.links[0].href === 'https://example.com', 'first link href correct');
}

function test_extractWithSelector() {
  const html = `<html><body>
    <div class="sidebar">Sidebar content</div>
    <div class="main">Main content here</div>
  </body></html>`;
  const result = extract(html, { selector: '.main', output: 'text' });
  assert(result.content.includes('Main content'), 'selector extracts target area');
  assert(!result.content.includes('Sidebar'), 'selector excludes other areas');
}

function test_outputText() {
  const html = '<html><body><p>Hello</p></body></html>';
  const result = extract(html, { output: 'text' });
  assert(result.title !== undefined, 'text output has title');
  assert(result.content !== undefined, 'text output has content');
  assert(result.meta !== undefined, 'text output has meta');
  assert(result.html === undefined, 'text output has no html');
  assert(result.tables === undefined, 'text output has no tables');
}

function test_outputHtml() {
  const html = '<html><body><p>Hello</p></body></html>';
  const result = extract(html, { output: 'html' });
  assert(result.html !== undefined, 'html output has html');
  assert(result.tables === undefined, 'html output has no tables');
}

function test_outputJson() {
  const html = '<html><body><p>Hello</p></body></html>';
  const result = extract(html, { output: 'json' });
  assert(result.html !== undefined, 'json output has html');
  assert(result.tables !== undefined, 'json output has tables');
  assert(result.links !== undefined, 'json output has links');
}

function test_deduplicateLinks() {
  const html = `<html><body>
    <a href="https://example.com">Link 1</a>
    <a href="https://example.com">Link 2</a>
  </body></html>`;
  const result = extract(html, { output: 'json' });
  assert(result.links.length === 1, 'duplicate links are deduplicated');
}

function main() {
  console.log('test_extractor:');
  test_extractTitle();
  test_extractTitle_og();
  test_extractContent();
  test_extractMeta();
  test_extractTables();
  test_extractLinks();
  test_extractWithSelector();
  test_outputText();
  test_outputHtml();
  test_outputJson();
  test_deduplicateLinks();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
