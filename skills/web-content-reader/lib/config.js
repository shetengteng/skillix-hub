'use strict';

const defaults = {
  fetchTimeout: 10000,
  browserTimeout: 15000,
  maxContentLength: 200000,
  spaThreshold: 0.6,
  userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  noiseTags: ['script', 'style', 'noscript', 'svg', 'nav', 'footer', 'header', 'iframe'],
};

function resolveConfig(overrides = {}) {
  return { ...defaults, ...overrides };
}

module.exports = { defaults, resolveConfig };
