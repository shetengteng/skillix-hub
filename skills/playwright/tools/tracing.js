'use strict';

async function tracingStart(context, params, response) {
  const bc = await context.ensureBrowserContext();
  await bc.tracing.start({ screenshots: true, snapshots: true });
  response.addTextResult('Trace recording started.');
}

async function tracingStop(context, params, response) {
  const bc = await context.ensureBrowserContext();
  const resolvedFile = await response.resolveClientFile(
    { prefix: 'trace', ext: 'zip', suggestedFilename: params.filename },
    'Trace'
  );
  await bc.tracing.stop({ path: resolvedFile.fileName });
  response.addTextResult(`Trace saved: ${resolvedFile.printableLink}`);
}

module.exports = { tracingStart, tracingStop };
