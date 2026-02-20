'use strict';

async function localStorageList(context, params, response) {
  const tab = context.currentTabOrDie();
  const items = await tab.page.evaluate(() => {
    const r = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key !== null) r.push({ key, value: localStorage.getItem(key) || '' });
    }
    return r;
  });
  response.addTextResult(items.length === 0 ? 'No localStorage items found' : items.map(i => `${i.key}=${i.value}`).join('\n'));
}

async function localStorageGet(context, params, response) {
  const tab = context.currentTabOrDie();
  const value = await tab.page.evaluate(key => localStorage.getItem(key), params.key);
  response.addTextResult(value === null ? `localStorage key '${params.key}' not found` : `${params.key}=${value}`);
}

async function localStorageSet(context, params, response) {
  const tab = context.currentTabOrDie();
  await tab.page.evaluate(({ key, value }) => localStorage.setItem(key, value), params);
  response.addTextResult(`localStorage '${params.key}' set.`);
}

async function localStorageDelete(context, params, response) {
  const tab = context.currentTabOrDie();
  await tab.page.evaluate(key => localStorage.removeItem(key), params.key);
  response.addTextResult(`localStorage '${params.key}' deleted.`);
}

async function localStorageClear(context, params, response) {
  const tab = context.currentTabOrDie();
  await tab.page.evaluate(() => localStorage.clear());
  response.addTextResult('localStorage cleared.');
}

async function sessionStorageList(context, params, response) {
  const tab = context.currentTabOrDie();
  const items = await tab.page.evaluate(() => {
    const r = [];
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key !== null) r.push({ key, value: sessionStorage.getItem(key) || '' });
    }
    return r;
  });
  response.addTextResult(items.length === 0 ? 'No sessionStorage items found' : items.map(i => `${i.key}=${i.value}`).join('\n'));
}

async function sessionStorageGet(context, params, response) {
  const tab = context.currentTabOrDie();
  const value = await tab.page.evaluate(key => sessionStorage.getItem(key), params.key);
  response.addTextResult(value === null ? `sessionStorage key '${params.key}' not found` : `${params.key}=${value}`);
}

async function sessionStorageSet(context, params, response) {
  const tab = context.currentTabOrDie();
  await tab.page.evaluate(({ key, value }) => sessionStorage.setItem(key, value), params);
  response.addTextResult(`sessionStorage '${params.key}' set.`);
}

async function sessionStorageDelete(context, params, response) {
  const tab = context.currentTabOrDie();
  await tab.page.evaluate(key => sessionStorage.removeItem(key), params.key);
  response.addTextResult(`sessionStorage '${params.key}' deleted.`);
}

async function sessionStorageClear(context, params, response) {
  const tab = context.currentTabOrDie();
  await tab.page.evaluate(() => sessionStorage.clear());
  response.addTextResult('sessionStorage cleared.');
}

module.exports = {
  localStorageList, localStorageGet, localStorageSet, localStorageDelete, localStorageClear,
  sessionStorageList, sessionStorageGet, sessionStorageSet, sessionStorageDelete, sessionStorageClear,
};
