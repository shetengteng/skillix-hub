'use strict';

async function close(context, params, response) {
  await context.closeBrowserContext();
  response.addTextResult('Browser closed.');
  response.addCode(`await page.close();`);
}

async function resize(context, params, response) {
  const tab = context.currentTabOrDie();
  response.addCode(`await page.setViewportSize({ width: ${params.width}, height: ${params.height} });`);
  await tab.page.setViewportSize({ width: params.width, height: params.height });
}

module.exports = { close, resize };
