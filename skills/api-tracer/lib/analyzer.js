'use strict';

function inferSchema(value) {
  if (value === null || value === undefined) return 'null';
  if (Array.isArray(value)) {
    if (value.length === 0) return '[]';
    return [inferSchema(value[0])];
  }
  if (typeof value === 'object') {
    const schema = {};
    for (const [k, v] of Object.entries(value)) {
      schema[k] = inferSchema(v);
    }
    return schema;
  }
  return typeof value;
}

function tryParseJson(str) {
  if (!str || typeof str !== 'string') return null;
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
}

function extractCookies(headers) {
  const cookieHeader = headers?.cookie || headers?.Cookie || '';
  if (!cookieHeader) return [];
  return cookieHeader.split(';').map(c => c.trim().split('=')[0]).filter(Boolean);
}

function normalizeUrl(url) {
  try {
    const u = new URL(url);
    return `${u.origin}${u.pathname}`;
  } catch {
    return url;
  }
}

function groupEndpoints(requests) {
  const apiRequests = requests.filter(r =>
    r.resourceType === 'Fetch' || r.resourceType === 'XHR' ||
    r.resourceType === 'fetch' || r.resourceType === 'xhr' ||
    (r.mimeType && r.mimeType.includes('json'))
  );

  const groups = new Map();

  for (const req of apiRequests) {
    const key = `${req.method} ${normalizeUrl(req.url)}`;
    if (!groups.has(key)) {
      groups.set(key, {
        url: normalizeUrl(req.url),
        method: req.method,
        calls: [],
      });
    }
    groups.get(key).calls.push(req);
  }

  return Array.from(groups.values());
}

function analyzeEndpoint(group) {
  const { url, method, calls } = group;
  const first = calls[0];

  const requestHeaders = {};
  const importantHeaders = [
    'authorization', 'content-type', 'accept', 'x-requested-with',
    'x-csrf-token', 'x-api-key', 'origin', 'referer',
  ];
  for (const [k, v] of Object.entries(first.requestHeaders || {})) {
    if (importantHeaders.includes(k.toLowerCase())) {
      requestHeaders[k] = v;
    }
  }

  const cookies = extractCookies(first.requestHeaders);

  let requestBody = null;
  if (first.postData) {
    const parsed = tryParseJson(first.postData);
    if (parsed) {
      requestBody = { type: 'json', schema: inferSchema(parsed), example: first.postData };
    } else {
      requestBody = { type: 'text', example: first.postData };
    }
  }

  let responseFormat = null;
  const firstWithBody = calls.find(c => c.responseBody);
  if (firstWithBody?.responseBody) {
    const parsed = tryParseJson(firstWithBody.responseBody);
    if (parsed) {
      responseFormat = { type: 'json', schema: inferSchema(parsed) };
    } else {
      responseFormat = { type: firstWithBody.mimeType || 'text' };
    }
  }

  const statusCodes = [...new Set(calls.map(c => c.status).filter(Boolean))].sort();

  return {
    url,
    method,
    pattern: new URL(url).pathname,
    requestHeaders,
    cookies,
    requestBody,
    responseFormat,
    statusCodes,
    callCount: calls.length,
  };
}

function detectAuthentication(requests) {
  for (const req of requests) {
    const auth = req.requestHeaders?.authorization || req.requestHeaders?.Authorization;
    if (auth) {
      if (auth.startsWith('Bearer ')) return { type: 'bearer_token', headerName: 'Authorization' };
      if (auth.startsWith('Basic ')) return { type: 'basic_auth', headerName: 'Authorization' };
      return { type: 'custom', headerName: 'Authorization', pattern: auth.split(' ')[0] };
    }
    const apiKey = req.requestHeaders?.['x-api-key'] || req.requestHeaders?.['X-Api-Key'];
    if (apiKey) return { type: 'api_key', headerName: 'x-api-key' };
  }
  return null;
}

function analyze(sessionData) {
  const { requests } = sessionData;
  const groups = groupEndpoints(requests);
  const endpoints = groups.map(analyzeEndpoint);
  const authentication = detectAuthentication(requests);

  const allCookies = new Set();
  for (const req of requests) {
    for (const c of extractCookies(req.requestHeaders)) {
      allCookies.add(c);
    }
  }

  return {
    session: {
      ...sessionData.session,
      apiEndpoints: endpoints.length,
    },
    endpoints,
    authentication,
    cookies: [...allCookies],
    summary: {
      totalRequests: requests.length,
      apiRequests: requests.filter(r =>
        r.resourceType === 'Fetch' || r.resourceType === 'XHR' ||
        r.resourceType === 'fetch' || r.resourceType === 'xhr'
      ).length,
      uniqueEndpoints: endpoints.length,
      methods: [...new Set(endpoints.map(e => e.method))],
    },
  };
}

module.exports = { analyze, inferSchema, groupEndpoints };
