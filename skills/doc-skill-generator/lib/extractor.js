'use strict';

function estimateTokens(text) {
  if (!text) return 0;
  return Math.ceil(text.length / 4);
}

function summarizeExtract(extract) {
  const docs = extract.documents || [];
  const lines = [];

  lines.push(`# Extract Summary: ${extract.id}`);
  lines.push(`Status: ${extract.status}`);
  lines.push(`Created: ${extract.createdAt}`);
  lines.push(`Documents: ${docs.length}`);
  lines.push('');

  for (const doc of docs) {
    lines.push(`## ${doc.title || doc.source}`);
    lines.push(`  Type: ${doc.type}`);
    lines.push(`  Source: ${doc.source}`);
    lines.push(`  Sections: ${(doc.sections || []).length}`);
    lines.push('');

    for (const section of (doc.sections || [])) {
      const prefix = '  '.repeat(section.level || 1);
      lines.push(`${prefix}### ${section.heading || '(untitled)'}`);
      const contentPreview = (section.content || '').substring(0, 200);
      if (contentPreview) lines.push(`${prefix}  ${contentPreview}...`);
      if (section.codeBlocks?.length) lines.push(`${prefix}  [${section.codeBlocks.length} code block(s)]`);
      if (section.tables?.length) lines.push(`${prefix}  [${section.tables.length} table(s)]`);
    }
    lines.push('');
  }

  if (extract.errors?.length) {
    lines.push('## Errors');
    for (const err of extract.errors) {
      lines.push(`  - ${err.source}: ${err.error}`);
    }
  }

  return lines.join('\n');
}

function extractToMarkdown(extract, maxTokens) {
  const docs = extract.documents || [];
  const parts = [];
  let currentTokens = 0;

  for (const doc of docs) {
    parts.push(`# ${doc.title || doc.source}\n`);
    parts.push(`> Source: ${doc.source} | Type: ${doc.type}\n`);

    for (const section of (doc.sections || [])) {
      const heading = '#'.repeat(Math.min(section.level + 1, 6)) + ' ' + (section.heading || '');
      const sectionTokens = estimateTokens(section.content) +
        (section.codeBlocks || []).reduce((s, cb) => s + estimateTokens(cb.code), 0);

      if (maxTokens && currentTokens + sectionTokens > maxTokens) {
        parts.push(`\n> [Truncated: ${estimateTokens(section.content)} tokens remaining]\n`);
        break;
      }

      parts.push(heading);
      if (section.content) parts.push(section.content);

      for (const cb of (section.codeBlocks || [])) {
        parts.push(`\`\`\`${cb.language || ''}\n${cb.code}\n\`\`\``);
      }

      for (const table of (section.tables || [])) {
        if (table.length === 0) continue;
        const header = table[0];
        parts.push('| ' + header.join(' | ') + ' |');
        parts.push('| ' + header.map(() => '---').join(' | ') + ' |');
        for (let i = 1; i < table.length; i++) {
          parts.push('| ' + table[i].join(' | ') + ' |');
        }
      }

      parts.push('');
      currentTokens += sectionTokens;
    }
  }

  return parts.join('\n');
}

module.exports = { summarizeExtract, extractToMarkdown, estimateTokens };
