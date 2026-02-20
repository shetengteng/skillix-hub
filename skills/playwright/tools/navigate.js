'use strict';

async function navigate(context, params, response) {
  const tab = await context.ensureTab();
  let url = params.url;
  try { new URL(url); } catch {
    url = url.startsWith('localhost') ? 'http://' + url : 'https://' + url;
  }
  await tab.navigate(url);
  response.setIncludeSnapshot();
  response.addCode(`await page.goto('${params.url}');`);
}

async function goBack(context, params, response) {
  const tab = context.currentTabOrDie();
  await tab.page.goBack();
  response.setIncludeSnapshot();
  response.addCode(`await page.goBack();`);
}

async function goForward(context, params, response) {
  const tab = context.currentTabOrDie();
  await tab.page.goForward();
  response.setIncludeSnapshot();
  response.addCode(`await page.goForward();`);
}

async function reload(context, params, response) {
  const tab = context.currentTabOrDie();
  await tab.page.reload();
  response.setIncludeSnapshot();
  response.addCode(`await page.reload();`);
}

module.exports = { navigate, goBack, goForward, reload };
