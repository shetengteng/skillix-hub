'use strict';

async function waitFor(context, params, response) {
  if (!params.text && !params.textGone && !params.time)
    throw new Error('Either time, text or textGone must be provided');

  const timeout = params.timeout || context.config.timeouts.navigation;

  if (params.time) {
    response.addCode(`await new Promise(f => setTimeout(f, ${params.time} * 1000));`);
    await new Promise(f => setTimeout(f, Math.min(30000, params.time * 1000)));
  }

  const tab = context.currentTabOrDie();

  if (params.textGone) {
    const goneLocator = tab.page.getByText(params.textGone).first();
    response.addCode(`await page.getByText(${JSON.stringify(params.textGone)}).first().waitFor({ state: 'hidden', timeout: ${timeout} });`);
    await goneLocator.waitFor({ state: 'hidden', timeout });
  }

  if (params.text) {
    const locator = tab.page.getByText(params.text).first();
    response.addCode(`await page.getByText(${JSON.stringify(params.text)}).first().waitFor({ state: 'visible', timeout: ${timeout} });`);
    await locator.waitFor({ state: 'visible', timeout });
  }

  response.addTextResult(`Waited for ${params.text || params.textGone || params.time}`);
  response.setIncludeSnapshot();
}

module.exports = { waitFor };
