'use strict';

async function route(context, params, response) {
  const addHeaders = params.headers ? Object.fromEntries(params.headers.map(h => {
    const idx = h.indexOf(':');
    return [h.substring(0, idx).trim(), h.substring(idx + 1).trim()];
  })) : undefined;
  const removeHeaders = params.removeHeaders ? params.removeHeaders.split(',').map(h => h.trim()) : undefined;

  const handler = async (rt) => {
    if (params.body !== undefined || params.status !== undefined) {
      await rt.fulfill({ status: params.status ?? 200, contentType: params.contentType, body: params.body });
      return;
    }
    const headers = { ...rt.request().headers() };
    if (addHeaders) for (const [k, v] of Object.entries(addHeaders)) headers[k] = v;
    if (removeHeaders) for (const h of removeHeaders) delete headers[h.toLowerCase()];
    await rt.continue({ headers });
  };

  await context.addRoute({
    pattern: params.pattern, status: params.status, body: params.body,
    contentType: params.contentType, addHeaders, removeHeaders, handler,
  });
  response.addTextResult(`Route added for pattern: ${params.pattern}`);
}

async function routeList(context, params, response) {
  const routes = context.routes();
  if (routes.length === 0) { response.addTextResult('No active routes'); return; }
  const lines = routes.map((r, i) => {
    const details = [];
    if (r.status !== undefined) details.push(`status=${r.status}`);
    if (r.body !== undefined) details.push(`body=${r.body.length > 50 ? r.body.substring(0, 50) + '...' : r.body}`);
    if (r.contentType) details.push(`contentType=${r.contentType}`);
    return `${i + 1}. ${r.pattern}${details.length ? ` (${details.join(', ')})` : ''}`;
  });
  response.addTextResult(lines.join('\n'));
}

async function unroute(context, params, response) {
  const removed = await context.removeRoute(params.pattern);
  response.addTextResult(params.pattern ? `Removed ${removed} route(s) for pattern: ${params.pattern}` : `Removed all ${removed} route(s)`);
}

module.exports = { route, routeList, unroute };
