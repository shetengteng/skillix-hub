'use strict';

async function tabs(context, params, response) {
  switch (params.action) {
    case 'list':
      await context.ensureTab();
      break;
    case 'new':
      await context.newTab();
      break;
    case 'close':
      await context.closeTab(params.index);
      break;
    case 'select':
      if (params.index === undefined) throw new Error('Tab index is required');
      await context.selectTab(params.index);
      break;
  }
  const lines = [];
  const allTabs = context.tabs();
  for (let i = 0; i < allTabs.length; i++) {
    const tab = allTabs[i];
    const title = await tab.safeTitle();
    const current = tab.isCurrentTab() ? ' (current)' : '';
    lines.push(`${i}:${current} [${title}](${tab.page.url()})`);
  }
  response.addTextResult(lines.join('\n') || 'No open tabs.');
}

module.exports = { tabs };
