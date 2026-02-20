'use strict';

const fs = require('fs');

async function storageState(context, params, response) {
  const bc = await context.ensureBrowserContext();
  const state = await bc.storageState();
  const serialized = JSON.stringify(state, null, 2);
  const resolvedFile = await response.resolveClientFile(
    { prefix: 'storage-state', ext: 'json', suggestedFilename: params.filename },
    'Storage state'
  );
  await fs.promises.writeFile(resolvedFile.fileName, serialized, 'utf-8');
  response.addTextResult(resolvedFile.printableLink);
}

async function setStorageState(context, params, response) {
  const bc = await context.ensureBrowserContext();
  await bc.setStorageState(params.filename);
  response.addTextResult(`Storage state restored from ${params.filename}`);
}

module.exports = { storageState, setStorageState };
