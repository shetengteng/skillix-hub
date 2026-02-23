'use strict';

const DOC_TYPE_PATTERNS = {
  'api-reference': {
    keywords: ['endpoint', 'request', 'response', 'status code', 'authorization', 'bearer',
      'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'api', 'REST', 'GraphQL',
      'header', 'query param', 'path param', 'body'],
    weight: 1,
  },
  'cli-reference': {
    keywords: ['command', 'flag', 'option', '--', 'usage:', 'synopsis', 'argument',
      'subcommand', 'stdin', 'stdout', 'exit code', 'CLI'],
    weight: 1,
  },
  'sdk-library': {
    keywords: ['import', 'require', 'class', 'method', 'constructor', 'instance',
      'npm install', 'pip install', 'package', 'module', 'interface', 'type'],
    weight: 1,
  },
  'tutorial': {
    keywords: ['step', 'first', 'then', 'next', 'finally', 'example', 'guide',
      'getting started', 'quickstart', 'walkthrough', 'how to'],
    weight: 0.8,
  },
  'configuration': {
    keywords: ['config', 'setting', 'parameter', 'default', 'environment variable',
      'env', 'yaml', 'json', 'toml', 'ini', '.env'],
    weight: 0.8,
  },
};

function detectDocType(extract) {
  const allText = (extract.documents || [])
    .flatMap(d => (d.sections || []).map(s => (s.heading + ' ' + s.content).toLowerCase()))
    .join(' ');

  const scores = {};
  for (const [type, config] of Object.entries(DOC_TYPE_PATTERNS)) {
    let count = 0;
    for (const kw of config.keywords) {
      const regex = new RegExp(kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
      const matches = allText.match(regex);
      if (matches) count += matches.length;
    }
    scores[type] = count * config.weight;
  }

  const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  return {
    primary: sorted[0]?.[0] || 'unknown',
    scores: Object.fromEntries(sorted),
    confidence: sorted[0]?.[1] > 10 ? 'high' : sorted[0]?.[1] > 3 ? 'medium' : 'low',
  };
}

function extractApiEndpoints(extract) {
  const endpoints = [];
  const methodPattern = /\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(\/[\w/{}:?&=.-]+)/gi;

  for (const doc of (extract.documents || [])) {
    for (const section of (doc.sections || [])) {
      const text = section.content || '';
      let match;
      while ((match = methodPattern.exec(text)) !== null) {
        endpoints.push({
          method: match[1].toUpperCase(),
          path: match[2],
          section: section.heading,
        });
      }
      for (const cb of (section.codeBlocks || [])) {
        while ((match = methodPattern.exec(cb.code)) !== null) {
          endpoints.push({
            method: match[1].toUpperCase(),
            path: match[2],
            section: section.heading,
          });
        }
      }
    }
  }

  const seen = new Set();
  return endpoints.filter(ep => {
    const key = `${ep.method} ${ep.path}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function extractCliCommands(extract) {
  const commands = [];
  const cmdPattern = /^\s*(?:\$\s+)?(\w[\w-]*)\s+([\w-]+)/gm;

  for (const doc of (extract.documents || [])) {
    for (const section of (doc.sections || [])) {
      for (const cb of (section.codeBlocks || [])) {
        if (cb.language === 'bash' || cb.language === 'sh' || cb.language === 'shell' || !cb.language) {
          let match;
          while ((match = cmdPattern.exec(cb.code)) !== null) {
            commands.push({ tool: match[1], subcommand: match[2], section: section.heading });
          }
        }
      }
    }
  }

  return commands;
}

function analyze(extract) {
  const docType = detectDocType(extract);
  const result = {
    docType,
    summary: extract.summary,
    suggestedSkillName: null,
    suggestedCommands: [],
  };

  if (docType.primary === 'api-reference') {
    result.endpoints = extractApiEndpoints(extract);
    result.suggestedCommands = result.endpoints.map(ep => ({
      name: ep.path.split('/').filter(Boolean).pop()?.replace(/[{}:]/g, '') || 'call',
      description: `${ep.method} ${ep.path}`,
      method: ep.method,
      path: ep.path,
    }));
  }

  if (docType.primary === 'cli-reference') {
    result.cliCommands = extractCliCommands(extract);
    result.suggestedCommands = result.cliCommands.map(cmd => ({
      name: cmd.subcommand,
      description: `${cmd.tool} ${cmd.subcommand}`,
    }));
  }

  const firstTitle = extract.documents?.[0]?.title || '';
  result.suggestedSkillName = firstTitle
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .substring(0, 40) || 'generated-skill';

  return result;
}

module.exports = { analyze, detectDocType, extractApiEndpoints, extractCliCommands };
