'use strict';

async function networkRequests(context, params, response) {
  const tab = context.currentTabOrDie();
  const requests = await tab.requests();
  const lines = [];
  for (const request of requests) {
    if (!params.includeStatic && !isFetch(request) && isSuccessfulResponse(request))
      continue;
    lines.push(renderRequest(request));
  }
  response.addTextResult(lines.join('\n') || 'No network requests.');
}

async function networkClear(context, params, response) {
  const tab = context.currentTabOrDie();
  await tab.clearRequests();
  response.addTextResult('Network requests cleared.');
}

function isFetch(request) {
  return ['fetch', 'xhr'].includes(request.resourceType());
}

function isSuccessfulResponse(request) {
  if (request.failure()) return false;
  const resp = request.response?.() ?? null;
  try {
    const existing = request.existingResponse?.();
    return !!existing && existing.status() < 400;
  } catch {
    return false;
  }
}

function renderRequest(request) {
  const parts = [`[${request.method().toUpperCase()}] ${request.url()}`];
  try {
    const resp = request.existingResponse?.();
    if (resp)
      parts.push(`=> [${resp.status()}] ${resp.statusText()}`);
    else if (request.failure())
      parts.push(`=> [FAILED] ${request.failure()?.errorText ?? 'Unknown error'}`);
  } catch {}
  return parts.join(' ');
}

module.exports = { networkRequests, networkClear };
