'use strict';

async function evaluate(context, params, response) {
  const tab = context.currentTabOrDie();
  let fn = params.function;
  if (!fn.includes('=>'))
    fn = `() => (${fn})`;

  let locatorInfo;
  if (params.ref) {
    locatorInfo = await tab.refLocator({ ref: params.ref, element: params.element || 'element' });
    response.addCode(`await page.${locatorInfo.resolved}.evaluate(${JSON.stringify(fn)});`);
  } else {
    response.addCode(`await page.evaluate(${JSON.stringify(fn)});`);
  }

  await tab.waitForCompletion(async () => {
    const receiver = locatorInfo?.locator ?? tab.page;
    const result = await receiver.evaluate(new Function('return ' + fn)());
    const text = JSON.stringify(result, null, 2) || 'undefined';
    response.addTextResult(text);
  });
}

module.exports = { evaluate };
