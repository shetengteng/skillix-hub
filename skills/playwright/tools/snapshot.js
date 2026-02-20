'use strict';

const { formatObject } = require('playwright-core/lib/utils');

async function snapshot(context, params, response) {
  await context.ensureTab();
  response.setIncludeFullSnapshot(params.filename);
}

async function click(context, params, response) {
  const tab = context.currentTabOrDie();
  response.setIncludeSnapshot();
  const { locator, resolved } = await tab.refLocator(params);
  const options = { button: params.button, modifiers: params.modifiers };
  const formatted = formatObject(options, ' ', 'oneline');
  const optionsAttr = formatted !== '{}' ? formatted : '';

  if (params.doubleClick)
    response.addCode(`await page.${resolved}.dblclick(${optionsAttr});`);
  else
    response.addCode(`await page.${resolved}.click(${optionsAttr});`);

  await tab.waitForCompletion(async () => {
    if (params.doubleClick)
      await locator.dblclick(options);
    else
      await locator.click(options);
  });
}

async function drag(context, params, response) {
  const tab = context.currentTabOrDie();
  response.setIncludeSnapshot();
  const [start, end] = await tab.refLocators([
    { ref: params.startRef, element: params.startElement },
    { ref: params.endRef, element: params.endElement },
  ]);
  await tab.waitForCompletion(async () => {
    await start.locator.dragTo(end.locator);
  });
  response.addCode(`await page.${start.resolved}.dragTo(page.${end.resolved});`);
}

async function hover(context, params, response) {
  const tab = context.currentTabOrDie();
  response.setIncludeSnapshot();
  const { locator, resolved } = await tab.refLocator(params);
  response.addCode(`await page.${resolved}.hover();`);
  await tab.waitForCompletion(async () => {
    await locator.hover();
  });
}

async function selectOption(context, params, response) {
  const tab = context.currentTabOrDie();
  response.setIncludeSnapshot();
  const { locator, resolved } = await tab.refLocator(params);
  response.addCode(`await page.${resolved}.selectOption(${formatObject(params.values)});`);
  await tab.waitForCompletion(async () => {
    await locator.selectOption(params.values);
  });
}

async function check(context, params, response) {
  const tab = context.currentTabOrDie();
  const { locator, resolved } = await tab.refLocator(params);
  response.addCode(`await page.${resolved}.check();`);
  await locator.check();
}

async function uncheck(context, params, response) {
  const tab = context.currentTabOrDie();
  const { locator, resolved } = await tab.refLocator(params);
  response.addCode(`await page.${resolved}.uncheck();`);
  await locator.uncheck();
}

module.exports = { snapshot, click, drag, hover, selectOption, check, uncheck };
