'use strict';

async function pressKey(context, params, response) {
  const tab = context.currentTabOrDie();
  response.addCode(`await page.keyboard.press('${params.key}');`);
  if (params.key === 'Enter') {
    response.setIncludeSnapshot();
    await tab.waitForCompletion(async () => {
      await tab.page.keyboard.press('Enter');
    });
  } else {
    await tab.page.keyboard.press(params.key);
  }
}

async function type(context, params, response) {
  const tab = context.currentTabOrDie();
  const { locator, resolved } = await tab.refLocator(params);

  await tab.waitForCompletion(async () => {
    if (params.slowly) {
      response.setIncludeSnapshot();
      response.addCode(`await page.${resolved}.pressSequentially('${params.text}');`);
      await locator.pressSequentially(params.text);
    } else {
      response.addCode(`await page.${resolved}.fill('${params.text}');`);
      await locator.fill(params.text);
    }
    if (params.submit) {
      response.setIncludeSnapshot();
      response.addCode(`await page.${resolved}.press('Enter');`);
      await locator.press('Enter');
    }
  });
}

async function pressSequentially(context, params, response) {
  const tab = context.currentTabOrDie();
  response.addCode(`await page.keyboard.type('${params.text}');`);
  await tab.page.keyboard.type(params.text);
  if (params.submit) {
    response.addCode(`await page.keyboard.press('Enter');`);
    response.setIncludeSnapshot();
    await tab.waitForCompletion(async () => {
      await tab.page.keyboard.press('Enter');
    });
  }
}

async function keydown(context, params, response) {
  const tab = context.currentTabOrDie();
  response.addCode(`await page.keyboard.down('${params.key}');`);
  await tab.page.keyboard.down(params.key);
}

async function keyup(context, params, response) {
  const tab = context.currentTabOrDie();
  response.addCode(`await page.keyboard.up('${params.key}');`);
  await tab.page.keyboard.up(params.key);
}

module.exports = { pressKey, type, pressSequentially, keydown, keyup };
