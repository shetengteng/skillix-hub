'use strict';

const fs = require('fs');
const path = require('path');

class Response {
  constructor(context) {
    this._context = context;
    this._results = [];
    this._errors = [];
    this._code = [];
    this._includeSnapshot = false;
    this._includeFullSnapshot = false;
    this._snapshotFileName = undefined;
  }

  addTextResult(text) {
    this._results.push(text);
  }

  addError(error) {
    this._errors.push(error);
  }

  addCode(code) {
    this._code.push(code);
  }

  setIncludeSnapshot() {
    this._includeSnapshot = true;
  }

  setIncludeFullSnapshot(fileName) {
    this._includeFullSnapshot = true;
    this._snapshotFileName = fileName;
  }

  async addResult(title, data, fileTemplate) {
    if (typeof data === 'string') {
      this.addTextResult(data);
    } else {
      const filePath = await this._resolveFile(fileTemplate);
      await fs.promises.writeFile(filePath, data);
      this.addTextResult(`[${title}](${filePath})`);
    }
  }

  async addFileResult(filePath, data) {
    if (typeof data === 'string')
      await fs.promises.writeFile(filePath, data, 'utf-8');
    else if (data)
      await fs.promises.writeFile(filePath, data);
    this.addTextResult(`File saved: ${filePath}`);
  }

  addFileLink(title, fileName) {
    this.addTextResult(`[${title}](${fileName})`);
  }

  async resolveClientFile(template, title) {
    const { outputFile } = require('./config');
    const fileName = await outputFile(
      this._context.config,
      template.prefix || 'output',
      template.ext || 'bin',
      template.suggestedFilename
    );
    return { fileName, relativeName: fileName, printableLink: `[${title}](${fileName})` };
  }

  async registerImageResult(data, imageType) {
    const { outputFile } = require('./config');
    const fileName = await outputFile(
      this._context.config,
      'screenshot',
      imageType,
      undefined
    );
    await fs.promises.writeFile(fileName, data);
  }

  async _resolveFile(template) {
    const { outputFile } = require('./config');
    return outputFile(
      this._context.config,
      template.prefix || 'output',
      template.ext || 'bin',
      template.suggestedFilename
    );
  }

  async serialize() {
    const output = {};

    if (this._errors.length)
      output.error = this._errors.join('\n');

    if (this._results.length)
      output.result = this._results.join('\n');

    if (this._code.length)
      output.code = this._code.join('\n');

    if (this._includeSnapshot || this._includeFullSnapshot) {
      const tab = this._context.currentTab();
      if (tab) {
        try {
          const snapshot = await tab.captureSnapshot();
          output.snapshot = snapshot;
        } catch (_e) {
          // snapshot capture can fail if page is navigating
        }
      }
    }

    const tabs = this._context.tabs();
    if (tabs.length > 0) {
      output.tabs = await Promise.all(tabs.map(async (tab, i) => {
        const title = await tab.safeTitle();
        const url = tab.page.url();
        const current = tab === this._context.currentTab();
        return `${i}:${current ? ' (current)' : ''} [${title}](${url})`;
      }));
    }

    return output;
  }
}

module.exports = { Response };
