'use strict';

const cheerio = require('cheerio');

function extract(html, options = {}) {
  const $ = cheerio.load(html);
  const { selector, output = 'text', noiseTags = [] } = options;

  let scope = $;
  if (selector) {
    const selected = $(selector);
    if (selected.length > 0) {
      scope = cheerio.load(selected.html());
    }
  }

  const title = extractTitle($);
  const meta = extractMeta($);

  for (const tag of noiseTags) {
    scope(tag).remove();
  }

  const content = scope('body').text().replace(/\s+/g, ' ').trim()
    || scope.root().text().replace(/\s+/g, ' ').trim();

  if (output === 'text') {
    return { title, content, meta };
  }

  const cleanHtml = selector
    ? $(selector).html() || ''
    : scope('body').html() || scope.root().html() || '';

  if (output === 'html') {
    return { title, content, html: cleanHtml, meta };
  }

  const tables = extractTables($, selector);
  const links = extractLinks($, selector);

  return { title, content, html: cleanHtml, tables, links, meta };
}

function extractTitle($) {
  const ogTitle = $('meta[property="og:title"]').attr('content');
  if (ogTitle) return ogTitle;
  return $('title').text().trim() || null;
}

function extractMeta($) {
  const meta = {};
  const desc = $('meta[name="description"]').attr('content')
    || $('meta[property="og:description"]').attr('content');
  if (desc) meta.description = desc;

  const ogTitle = $('meta[property="og:title"]').attr('content');
  if (ogTitle) meta.ogTitle = ogTitle;

  const ogImage = $('meta[property="og:image"]').attr('content');
  if (ogImage) meta.ogImage = ogImage;

  const ogUrl = $('meta[property="og:url"]').attr('content');
  if (ogUrl) meta.ogUrl = ogUrl;

  const canonical = $('link[rel="canonical"]').attr('href');
  if (canonical) meta.canonical = canonical;

  return meta;
}

function extractTables($, selector) {
  const tables = [];
  const root = selector ? $(selector) : $('body');

  root.find('table').each((_, table) => {
    const headers = [];
    $(table).find('thead th, thead td, tr:first-child th').each((__, th) => {
      headers.push($(th).text().trim());
    });

    const rows = [];
    const rowSelector = headers.length > 0 ? 'tbody tr' : 'tr';
    $(table).find(rowSelector).each((i, tr) => {
      if (headers.length === 0 && i === 0) return;
      const row = [];
      $(tr).find('td, th').each((__, td) => {
        row.push($(td).text().trim());
      });
      if (row.length > 0) rows.push(row);
    });

    if (headers.length > 0 || rows.length > 0) {
      tables.push({ headers, rows });
    }
  });

  return tables;
}

function extractLinks($, selector) {
  const links = [];
  const root = selector ? $(selector) : $('body');
  const seen = new Set();

  root.find('a[href]').each((_, a) => {
    const href = $(a).attr('href');
    const text = $(a).text().trim();
    if (href && !seen.has(href) && !href.startsWith('#') && !href.startsWith('javascript:')) {
      seen.add(href);
      links.push({ text: text || null, href });
    }
  });

  return links;
}

module.exports = { extract };
