'use strict';

const cheerio = require('cheerio');

const SPA_PLACEHOLDERS = [
  '#app', '#root', '#__nuxt', '#__next', '#main-app',
  '[data-app]', '[data-reactroot]',
];

const NOSCRIPT_HINTS = [
  'enable javascript',
  'javascript is required',
  'javascript is disabled',
  'you need to enable javascript',
  'this app requires javascript',
  'please enable javascript',
];

const SSR_MARKERS = [
  'data-server-rendered',
  'data-reactroot',
  '__NEXT_DATA__',
  '__NUXT__',
];

function detect(html, config) {
  const $ = cheerio.load(html);
  let score = 0;

  $('script, style, noscript, svg').remove();
  const bodyText = $('body').text().replace(/\s+/g, ' ').trim();

  if (bodyText.length < 50) score += 0.35;
  else if (bodyText.length < 150) score += 0.15;

  for (const sel of SPA_PLACEHOLDERS) {
    const el = $(sel);
    if (el.length > 0 && el.text().trim().length < 20) {
      score += 0.25;
      break;
    }
  }

  const $full = cheerio.load(html);
  const scriptCount = $full('script').length;
  if (scriptCount > 3 && bodyText.length < 200) score += 0.2;

  const noscriptText = $full('noscript').text().toLowerCase();
  for (const hint of NOSCRIPT_HINTS) {
    if (noscriptText.includes(hint)) {
      score += 0.3;
      break;
    }
  }

  for (const marker of SSR_MARKERS) {
    if (html.includes(marker)) {
      score -= 0.3;
      break;
    }
  }

  score = Math.max(0, Math.min(1, score));

  return {
    isSPA: score >= (config.spaThreshold || 0.6),
    score,
    bodyTextLength: bodyText.length,
  };
}

module.exports = { detect };
