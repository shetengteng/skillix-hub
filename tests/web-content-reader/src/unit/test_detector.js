#!/usr/bin/env node
'use strict';

const path = require('path');
const SKILL_DIR = process.env.SKILL_DIR || path.resolve(__dirname, '../../../../skills/web-content-reader');
const { detect } = require(path.join(SKILL_DIR, 'lib/detector'));
const { defaults } = require(path.join(SKILL_DIR, 'lib/config'));

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) { passed++; console.log(`  PASS: ${msg}`); }
  else { failed++; console.error(`  FAIL: ${msg}`); }
}

function test_staticPage() {
  const html = `<html><head><title>Test</title></head><body>
    <h1>Hello World</h1>
    <p>This is a static page with plenty of text content for testing purposes.
    It has multiple paragraphs and enough content to not trigger SPA detection.</p>
    <p>More content here to ensure the body text length is sufficient.</p>
  </body></html>`;
  const result = detect(html, defaults);
  assert(!result.isSPA, 'static page is not detected as SPA');
  assert(result.score < defaults.spaThreshold, 'static page score below threshold');
  assert(result.bodyTextLength > 50, 'static page has body text');
}

function test_vueSPA() {
  const html = `<html><head><title>Vue App</title></head><body>
    <div id="app"></div>
    <script src="/js/chunk-vendors.js"></script>
    <script src="/js/app.js"></script>
    <script src="/js/chunk-common.js"></script>
    <script src="/js/chunk-page.js"></script>
    <noscript>You need to enable JavaScript to run this app.</noscript>
  </body></html>`;
  const result = detect(html, defaults);
  assert(result.isSPA, 'Vue SPA detected');
  assert(result.score >= defaults.spaThreshold, 'Vue SPA score above threshold');
}

function test_reactSPA() {
  const html = `<html><head><title>React App</title></head><body>
    <div id="root"></div>
    <script src="/static/js/bundle.js"></script>
    <script src="/static/js/main.js"></script>
    <script src="/static/js/vendor.js"></script>
    <script src="/static/js/runtime.js"></script>
    <noscript>You need to enable JavaScript to run this app.</noscript>
  </body></html>`;
  const result = detect(html, defaults);
  assert(result.isSPA, 'React SPA detected');
  assert(result.score >= defaults.spaThreshold, 'React SPA score above threshold');
}

function test_ssrPage() {
  const html = `<html><head><title>SSR Page</title></head><body>
    <div id="app" data-server-rendered="true">
      <h1>Server Rendered Content</h1>
      <p>This page was rendered on the server and has real content.</p>
    </div>
    <script src="/js/app.js"></script>
  </body></html>`;
  const result = detect(html, defaults);
  assert(!result.isSPA, 'SSR page not detected as SPA');
}

function test_nextjsSSR() {
  const html = `<html><head><title>Next.js App</title></head><body>
    <div id="__next">
      <h1>Next.js Page</h1>
      <p>This is a server-rendered Next.js page with content.</p>
    </div>
    <script id="__NEXT_DATA__" type="application/json">{"props":{}}</script>
  </body></html>`;
  const result = detect(html, defaults);
  assert(!result.isSPA, 'Next.js SSR page not detected as SPA');
}

function test_emptyBody() {
  const html = `<html><head><title>Empty</title></head><body></body></html>`;
  const result = detect(html, defaults);
  assert(result.bodyTextLength < 50, 'empty body has low text length');
  assert(result.score > 0, 'empty body has positive score');
}

function test_scoreRange() {
  const htmls = [
    '<html><body><p>Content</p></body></html>',
    '<html><body><div id="app"></div></body></html>',
    '<html><body><div id="root"></div><noscript>Enable JS</noscript></body></html>',
  ];
  for (const html of htmls) {
    const result = detect(html, defaults);
    assert(result.score >= 0 && result.score <= 1, `score ${result.score} is in [0, 1]`);
  }
}

function main() {
  console.log('test_detector:');
  test_staticPage();
  test_vueSPA();
  test_reactSPA();
  test_ssrPage();
  test_nextjsSSR();
  test_emptyBody();
  test_scoreRange();
  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main();
