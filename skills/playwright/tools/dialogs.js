'use strict';

async function handleDialog(context, params, response) {
  const tab = context.currentTabOrDie();
  const dialogState = tab.modalStates().find(s => s.type === 'dialog');
  if (!dialogState)
    throw new Error('No dialog visible');

  tab.clearModalState(dialogState);
  await tab.waitForCompletion(async () => {
    if (params.accept)
      await dialogState.dialog.accept(params.promptText);
    else
      await dialogState.dialog.dismiss();
  });
}

module.exports = { handleDialog };
