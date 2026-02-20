'use strict';

const fs = require('fs');

async function pdf(context, params, response) {
  const tab = context.currentTabOrDie();
  const data = await tab.page.pdf();
  const resolvedFile = await response.resolveClientFile(
    { prefix: 'page', ext: 'pdf', suggestedFilename: params.filename },
    'Page as PDF'
  );
  await fs.promises.writeFile(resolvedFile.fileName, data);
  response.addTextResult(resolvedFile.printableLink);
}

module.exports = { pdf };
