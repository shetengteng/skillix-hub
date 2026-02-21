'use strict';

function success(data, method, url, elapsed) {
  return {
    result: data,
    method,
    url,
    elapsed,
    error: null,
  };
}

function error(message, url) {
  return {
    result: null,
    method: null,
    url: url || null,
    elapsed: null,
    error: message,
  };
}

module.exports = { success, error };
