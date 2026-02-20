'use strict';

async function fileUpload(context, params, response) {
  const tab = context.currentTabOrDie();
  response.setIncludeSnapshot();
  const modalState = tab.modalStates().find(s => s.type === 'fileChooser');
  if (!modalState)
    throw new Error('No file chooser visible');

  response.addCode(`await fileChooser.setFiles(${JSON.stringify(params.paths)});`);
  tab.clearModalState(modalState);
  await tab.waitForCompletion(async () => {
    if (params.paths)
      await modalState.fileChooser.setFiles(params.paths);
  });
}

module.exports = { fileUpload };
