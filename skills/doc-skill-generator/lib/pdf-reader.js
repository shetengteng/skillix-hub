'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const https = require('https');
const http = require('http');

function downloadFile(url) {
  return new Promise((resolve, reject) => {
    const tmpPath = path.join(os.tmpdir(), `doc-gen-${Date.now()}.pdf`);
    const proto = url.startsWith('https') ? https : http;
    const file = fs.createWriteStream(tmpPath);

    proto.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        file.close();
        fs.unlinkSync(tmpPath);
        return downloadFile(res.headers.location).then(resolve).catch(reject);
      }
      if (res.statusCode !== 200) {
        file.close();
        fs.unlinkSync(tmpPath);
        return reject(new Error(`HTTP ${res.statusCode} for ${url}`));
      }
      res.pipe(file);
      file.on('finish', () => { file.close(); resolve(tmpPath); });
    }).on('error', (e) => {
      file.close();
      try { fs.unlinkSync(tmpPath); } catch { /* ok */ }
      reject(e);
    });
  });
}

async function readPdf(source) {
  let pdfParse;
  try {
    pdfParse = require('pdf-parse');
  } catch {
    throw new Error('pdf-parse not installed. Run: npm install (in doc-skill-generator dir)');
  }

  let filePath = source;
  let isTemp = false;

  if (source.startsWith('http://') || source.startsWith('https://')) {
    filePath = await downloadFile(source);
    isTemp = true;
  }

  if (!fs.existsSync(filePath)) {
    throw new Error(`PDF file not found: ${filePath}`);
  }

  try {
    const buffer = fs.readFileSync(filePath);
    const data = await pdfParse(buffer);

    const lines = data.text.split('\n');
    const sections = [];
    let currentSection = null;

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      const isHeading = /^[A-Z\u4e00-\u9fff]/.test(trimmed)
        && trimmed.length < 100
        && !trimmed.includes('.')
        && trimmed === trimmed.replace(/[a-z]{20,}/, '');

      if (isHeading && trimmed.length < 80) {
        if (currentSection) sections.push(currentSection);
        currentSection = { heading: trimmed, level: 2, content: '', codeBlocks: [], tables: [], links: [] };
      } else if (currentSection) {
        currentSection.content += trimmed + '\n';
      } else {
        currentSection = { heading: '', level: 1, content: trimmed + '\n', codeBlocks: [], tables: [], links: [] };
      }
    }
    if (currentSection) sections.push(currentSection);

    return {
      source,
      type: 'pdf',
      title: data.info?.Title || path.basename(filePath, '.pdf'),
      sections,
      metadata: {
        pages: data.numpages,
        author: data.info?.Author || null,
        creator: data.info?.Creator || null,
        estimatedTokens: Math.ceil(data.text.length / 4),
      },
    };
  } finally {
    if (isTemp) {
      try { fs.unlinkSync(filePath); } catch { /* ok */ }
    }
  }
}

module.exports = { readPdf, downloadFile };
