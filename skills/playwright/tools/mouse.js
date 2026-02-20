'use strict';

async function mouseMove(context, params, response) {
  const tab = context.currentTabOrDie();
  response.addCode(`await page.mouse.move(${params.x}, ${params.y});`);
  await tab.waitForCompletion(async () => {
    await tab.page.mouse.move(params.x, params.y);
  });
}

async function mouseClick(context, params, response) {
  const tab = context.currentTabOrDie();
  response.setIncludeSnapshot();
  response.addCode(`await page.mouse.move(${params.x}, ${params.y});`);
  response.addCode(`await page.mouse.down();`);
  response.addCode(`await page.mouse.up();`);
  await tab.waitForCompletion(async () => {
    await tab.page.mouse.move(params.x, params.y);
    await tab.page.mouse.down();
    await tab.page.mouse.up();
  });
}

async function mouseDrag(context, params, response) {
  const tab = context.currentTabOrDie();
  response.setIncludeSnapshot();
  response.addCode(`await page.mouse.move(${params.startX}, ${params.startY});`);
  response.addCode(`await page.mouse.down();`);
  response.addCode(`await page.mouse.move(${params.endX}, ${params.endY});`);
  response.addCode(`await page.mouse.up();`);
  await tab.waitForCompletion(async () => {
    await tab.page.mouse.move(params.startX, params.startY);
    await tab.page.mouse.down();
    await tab.page.mouse.move(params.endX, params.endY);
    await tab.page.mouse.up();
  });
}

async function mouseDown(context, params, response) {
  const tab = context.currentTabOrDie();
  response.addCode(`await page.mouse.down({ button: '${params.button || 'left'}' });`);
  await tab.page.mouse.down({ button: params.button });
}

async function mouseUp(context, params, response) {
  const tab = context.currentTabOrDie();
  response.addCode(`await page.mouse.up({ button: '${params.button || 'left'}' });`);
  await tab.page.mouse.up({ button: params.button });
}

async function mouseWheel(context, params, response) {
  const tab = context.currentTabOrDie();
  const dx = params.deltaX || 0;
  const dy = params.deltaY || 0;
  response.addCode(`await page.mouse.wheel(${dx}, ${dy});`);
  await tab.page.mouse.wheel(dx, dy);
}

module.exports = { mouseMove, mouseClick, mouseDrag, mouseDown, mouseUp, mouseWheel };
