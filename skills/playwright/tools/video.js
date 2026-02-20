'use strict';

const fs = require('fs');

let _videoPages = null;

async function startVideo(context, params, response) {
  if (_videoPages) throw new Error('Video recording already started.');
  _videoPages = new Set();
  const bc = await context.ensureBrowserContext();
  const listener = (page) => {
    _videoPages.add(page);
    page.video()?.start(params.size ? { size: params.size } : {}).catch(() => {});
  };
  bc.pages().forEach(listener);
  bc.on('page', listener);
  bc._videoListener = listener;
  response.addTextResult('Video recording started.');
}

async function stopVideo(context, params, response) {
  if (!_videoPages) throw new Error('Video recording not started.');
  const bc = await context.ensureBrowserContext();
  if (bc._videoListener) {
    bc.off('page', bc._videoListener);
    delete bc._videoListener;
  }
  for (const page of bc.pages())
    await page.video()?.stop().catch(() => {});

  let index = 0;
  for (const page of _videoPages) {
    const video = page.video();
    if (!video) continue;
    const suffix = index ? `-${index}` : '';
    const resolvedFile = await response.resolveClientFile(
      { prefix: `video${suffix}`, ext: 'webm', suggestedFilename: params.filename },
      'Video'
    );
    await video.saveAs(resolvedFile.fileName).catch(() => {});
    response.addTextResult(resolvedFile.printableLink);
    index++;
  }
  _videoPages = null;
  if (index === 0) response.addTextResult('No videos were recorded.');
}

module.exports = { startVideo, stopVideo };
