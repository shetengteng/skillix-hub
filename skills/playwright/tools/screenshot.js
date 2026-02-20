'use strict';

const fs = require('fs');

async function screenshot(context, params, response) {
  const tab = context.currentTabOrDie();
  const fileType = params.type || 'png';
  const options = {
    type: fileType,
    quality: fileType === 'png' ? undefined : 90,
    scale: 'css',
    ...(params.fullPage !== undefined && { fullPage: params.fullPage }),
  };

  if (params.fullPage && params.ref)
    throw new Error('fullPage cannot be used with element screenshots.');

  let data;
  let ref = null;
  if (params.ref) {
    ref = await tab.refLocator({ element: params.element || '', ref: params.ref });
    data = await ref.locator.screenshot(options);
  } else {
    data = await tab.page.screenshot(options);
  }

  const resolvedFile = await response.resolveClientFile(
    { prefix: ref ? 'element' : 'page', ext: fileType, suggestedFilename: params.filename },
    `Screenshot`
  );

  await fs.promises.writeFile(resolvedFile.fileName, data);
  response.addTextResult(resolvedFile.printableLink);
  await response.registerImageResult(data, fileType);
}

module.exports = { screenshot };
