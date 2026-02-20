'use strict';

async function getConfig(context, params, response) {
  response.addTextResult(JSON.stringify(context.config, null, 2));
}

module.exports = { getConfig };
