'use strict';

async function devtoolsStart(context, params, response) {
  const bc = await context.ensureBrowserContext();
  try {
    const { url } = await bc._devtoolsStart();
    response.addTextResult('DevTools server listening on: ' + url);
  } catch {
    response.addError('DevTools not supported for this browser configuration.');
  }
}

module.exports = { devtoolsStart };
