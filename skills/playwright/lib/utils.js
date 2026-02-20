'use strict';

async function waitForCompletion(tab, callback) {
  const requests = [];
  const requestListener = (request) => requests.push(request);
  tab.page.on('request', requestListener);

  let result;
  try {
    result = await callback();
    await tab.waitForTimeout(500);
  } finally {
    tab.page.off('request', requestListener);
  }

  const requestedNavigation = requests.some(r => r.isNavigationRequest());
  if (requestedNavigation) {
    await tab.page.mainFrame().waitForLoadState('load', { timeout: 10000 }).catch(() => {});
    return result;
  }

  const promises = [];
  for (const request of requests) {
    if (['document', 'stylesheet', 'script', 'xhr', 'fetch'].includes(request.resourceType()))
      promises.push(request.response().then(r => r?.finished()).catch(() => {}));
    else
      promises.push(request.response().catch(() => {}));
  }
  const timeout = new Promise(resolve => setTimeout(resolve, 5000));
  await Promise.race([Promise.all(promises), timeout]);
  if (requests.length)
    await tab.waitForTimeout(500);

  return result;
}

module.exports = { waitForCompletion };
