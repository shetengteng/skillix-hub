'use strict';

async function consoleMessages(context, params, response) {
  const tab = context.currentTabOrDie();
  const count = await tab.consoleMessageCount();
  const header = [`Total messages: ${count.total} (Errors: ${count.errors}, Warnings: ${count.warnings})`];
  const messages = await tab.consoleMessages(params.level || 'info');
  if (messages.length !== count.total)
    header.push(`Returning ${messages.length} messages for level "${params.level}"`);
  const text = [...header, '', ...messages.map(m => m.toString())].join('\n');
  response.addTextResult(text);
}

async function consoleClear(context, params, response) {
  const tab = context.currentTabOrDie();
  await tab.clearConsoleMessages();
  response.addTextResult('Console cleared.');
}

module.exports = { consoleMessages, consoleClear };
