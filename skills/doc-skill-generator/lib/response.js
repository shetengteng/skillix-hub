'use strict';

function success(data) {
  return { result: data, error: null };
}

function error(message) {
  return { result: null, error: message };
}

module.exports = { success, error };
