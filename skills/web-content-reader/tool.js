#!/usr/bin/env node
'use strict';

const { resolveConfig } = require('./lib/config');
const { fetchPage } = require('./lib/fetcher');
const { detect } = require('./lib/detector');
const { renderPage } = require('./lib/renderer');
const { extract } = require('./lib/extractor');
const response = require('./lib/response');

async function read(params, config) {
  const { url, mode = 'auto', selector, output = 'text', waitSelector, timeout } = params;

  if (!url) {
    return response.error('url is required');
  }

  const start = Date.now();
  const extractOpts = { selector, output, noiseTags: config.noiseTags };

  if (mode === 'browser') {
    return await readViaBrowser(url, config, extractOpts, { waitSelector, timeout }, start);
  }

  const fetchResult = await fetchPage(url, config);

  if (mode === 'fetch') {
    if (fetchResult.error) {
      return response.error(fetchResult.error, url);
    }
    const data = extract(fetchResult.html, extractOpts);
    return response.success(data, 'fetch', url, Date.now() - start);
  }

  // auto mode
  if (fetchResult.html) {
    const detection = detect(fetchResult.html, config);

    if (!detection.isSPA) {
      const data = extract(fetchResult.html, extractOpts);
      return response.success(data, 'fetch', url, Date.now() - start);
    }
  }

  return await readViaBrowser(url, config, extractOpts, { waitSelector, timeout }, start);
}

async function readViaBrowser(url, config, extractOpts, renderOpts, start) {
  try {
    const renderResult = await renderPage(url, config, renderOpts);

    if (renderResult.error) {
      return response.error(`Browser render failed: ${renderResult.error}`, url);
    }

    const data = extract(renderResult.html, extractOpts);
    return response.success(data, 'browser', url, Date.now() - start);
  } catch (e) {
    return response.error(`Browser render failed: ${e.message}`, url);
  }
}

const COMMANDS = { read };

async function main() {
  const [command, argsJson] = [process.argv[2], process.argv[3]];

  if (!command) {
    console.log(JSON.stringify(response.error("Usage: node tool.js <command> '{json_params}'")));
    process.exit(1);
  }

  const handler = COMMANDS[command];
  if (!handler) {
    console.log(JSON.stringify(response.error(`Unknown command: ${command}. Available: ${Object.keys(COMMANDS).join(', ')}`)));
    process.exit(1);
  }

  let params = {};
  if (argsJson) {
    try {
      params = JSON.parse(argsJson);
    } catch {
      console.log(JSON.stringify(response.error(`Invalid JSON params: ${argsJson}`)));
      process.exit(1);
    }
  }

  const config = resolveConfig();

  try {
    const result = await handler(params, config);
    console.log(JSON.stringify(result, null, 2));
    process.exit(0);
  } catch (e) {
    console.log(JSON.stringify(response.error(e.message)));
    process.exit(1);
  }
}

main();
