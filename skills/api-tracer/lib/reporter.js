'use strict';

function toMarkdown(report) {
  const lines = [];
  const { session, endpoints, authentication, cookies, summary } = report;

  lines.push(`# API Trace Report: ${session.name || 'Unnamed'}`);
  lines.push('');
  lines.push(`- **Start**: ${session.startTime}`);
  lines.push(`- **End**: ${session.endTime}`);
  lines.push(`- **Total Requests**: ${summary.totalRequests}`);
  lines.push(`- **API Requests**: ${summary.apiRequests}`);
  lines.push(`- **Unique Endpoints**: ${summary.uniqueEndpoints}`);
  lines.push(`- **HTTP Methods**: ${summary.methods.join(', ')}`);
  lines.push('');

  if (authentication) {
    lines.push('## Authentication');
    lines.push('');
    lines.push(`- **Type**: ${authentication.type}`);
    lines.push(`- **Header**: ${authentication.headerName}`);
    lines.push('');
  }

  if (cookies.length > 0) {
    lines.push('## Cookies');
    lines.push('');
    lines.push(cookies.map(c => `- \`${c}\``).join('\n'));
    lines.push('');
  }

  lines.push('## API Endpoints');
  lines.push('');

  for (const ep of endpoints) {
    lines.push(`### ${ep.method} ${ep.pattern}`);
    lines.push('');
    lines.push(`- **URL**: \`${ep.url}\``);
    lines.push(`- **Calls**: ${ep.callCount}`);
    lines.push(`- **Status Codes**: ${ep.statusCodes.join(', ')}`);

    if (ep.cookies.length > 0) {
      lines.push(`- **Cookies**: ${ep.cookies.join(', ')}`);
    }

    if (Object.keys(ep.requestHeaders).length > 0) {
      lines.push('');
      lines.push('**Request Headers**:');
      lines.push('```json');
      lines.push(JSON.stringify(ep.requestHeaders, null, 2));
      lines.push('```');
    }

    if (ep.requestBody) {
      lines.push('');
      lines.push(`**Request Body** (${ep.requestBody.type}):`);
      lines.push('```json');
      lines.push(JSON.stringify(ep.requestBody.schema, null, 2));
      lines.push('```');
    }

    if (ep.responseFormat) {
      lines.push('');
      lines.push(`**Response Format** (${ep.responseFormat.type}):`);
      if (ep.responseFormat.schema) {
        lines.push('```json');
        lines.push(JSON.stringify(ep.responseFormat.schema, null, 2));
        lines.push('```');
      }
    }

    lines.push('');
    lines.push('---');
    lines.push('');
  }

  return lines.join('\n');
}

function toCurl(report) {
  const commands = [];
  for (const ep of report.endpoints) {
    const parts = [`curl -X ${ep.method}`];
    for (const [k, v] of Object.entries(ep.requestHeaders)) {
      parts.push(`  -H '${k}: ${v}'`);
    }
    if (ep.requestBody?.example) {
      parts.push(`  -d '${ep.requestBody.example}'`);
    }
    parts.push(`  '${ep.url}'`);
    commands.push(parts.join(' \\\n'));
  }
  return commands.join('\n\n');
}

module.exports = { toMarkdown, toCurl };
