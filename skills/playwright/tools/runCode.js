'use strict';

const vm = require('vm');

async function runCode(context, params, response) {
  const tab = context.currentTabOrDie();
  response.addCode(`await (${params.code})(page);`);

  let resolveEnd, rejectEnd;
  const endPromise = new Promise((resolve, reject) => {
    resolveEnd = resolve;
    rejectEnd = reject;
  });

  const sandbox = {
    page: tab.page,
    __resolve__: resolveEnd,
    __reject__: rejectEnd,
  };
  vm.createContext(sandbox);

  await tab.waitForCompletion(async () => {
    const snippet = `(async () => {
      try {
        const result = await (${params.code})(page);
        __resolve__(JSON.stringify(result));
      } catch (e) {
        __reject__(e);
      }
    })()`;
    vm.runInContext(snippet, sandbox);
    const result = await endPromise;
    if (typeof result === 'string')
      response.addTextResult(result);
  });
}

module.exports = { runCode };
