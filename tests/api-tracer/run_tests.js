#!/usr/bin/env node
'use strict';

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const THIS_DIR = __dirname;
const SRC_DIR = path.join(THIS_DIR, 'src');
const REPORTS_DIR = path.join(THIS_DIR, 'reports');
const SUB_DIRS = ['unit', 'integration', 'e2e'];
const SKILL_DIR = path.resolve(THIS_DIR, '../../skills/api-tracer');

function findTestFiles(subDir) {
  const dir = path.join(SRC_DIR, subDir);
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter(f => f.startsWith('test_') && f.endsWith('.js'))
    .map(f => ({ file: path.join(dir, f), category: subDir }));
}

async function runTest(testFile) {
  const start = Date.now();
  const name = path.basename(testFile, '.js');
  try {
    const output = execSync(`node "${testFile}"`, {
      cwd: SKILL_DIR,
      timeout: 120000,
      env: { ...process.env, SKILL_DIR },
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return { name, status: 'PASS', elapsed: Date.now() - start, output: output.trim() };
  } catch (e) {
    return { name, status: 'FAIL', elapsed: Date.now() - start, output: (e.stdout || '') + '\n' + (e.stderr || e.message) };
  }
}

function nextReportPath() {
  fs.mkdirSync(REPORTS_DIR, { recursive: true });
  const today = new Date().toISOString().slice(0, 10);
  let maxSeq = 0;
  for (const f of fs.readdirSync(REPORTS_DIR)) {
    const match = f.match(new RegExp(`^${today}-(\\d+)-`));
    if (match) maxSeq = Math.max(maxSeq, parseInt(match[1]));
  }
  return path.join(REPORTS_DIR, `${today}-${String(maxSeq + 1).padStart(2, '0')}-test-report.md`);
}

function buildMarkdown(results, elapsed) {
  const passedCount = results.filter(r => r.status === 'PASS').length;
  const failedCount = results.filter(r => r.status === 'FAIL').length;
  const status = failedCount === 0 ? 'PASSED' : 'FAILED';

  const lines = [
    '# API Tracer Skill 测试报告',
    '',
    `> 时间: ${new Date().toISOString().replace('T', ' ').slice(0, 19)}`,
    `> 结果: ${status}`,
    `> 耗时: ${(elapsed / 1000).toFixed(3)}s`,
    '',
    '## 汇总',
    '',
    '| 指标 | 数值 |',
    '|---|---:|',
    `| 总用例 | ${results.length} |`,
    `| 通过 | ${passedCount} |`,
    `| 失败 | ${failedCount} |`,
    '',
  ];

  for (const cat of SUB_DIRS) {
    const catResults = results.filter(r => r.category === cat);
    if (catResults.length === 0) continue;
    const labels = { unit: '单元测试', integration: '集成测试', e2e: '端到端测试' };
    lines.push(`## ${labels[cat]}`, '', '| 用例 | 状态 | 耗时 |', '|---|---|---:|');
    for (const r of catResults)
      lines.push(`| \`${r.name}\` | ${r.status} | ${(r.elapsed / 1000).toFixed(2)}s |`);
    lines.push('');
  }

  const failures = results.filter(r => r.status === 'FAIL');
  if (failures.length) {
    lines.push('## 失败详情', '');
    for (const r of failures) {
      lines.push(`### FAIL: \`${r.name}\``, '', '```text', r.output.trim(), '```', '');
    }
  }

  return lines.join('\n') + '\n';
}

async function main() {
  const start = Date.now();
  const allTests = [];
  for (const sub of SUB_DIRS)
    allTests.push(...findTestFiles(sub));

  if (allTests.length === 0) {
    console.log('No test files found.');
    return 0;
  }

  console.log(`\n${'='.repeat(60)}`);
  console.log(`  Running ${allTests.length} tests`);
  console.log(`${'='.repeat(60)}\n`);

  const results = [];
  for (let i = 0; i < allTests.length; i++) {
    const { file, category } = allTests[i];
    const result = await runTest(file);
    result.category = category;
    results.push(result);
    const icon = result.status === 'PASS' ? 'OK  ' : 'FAIL';
    console.log(`  [${i + 1}/${allTests.length}] ${icon} ${result.name} (${(result.elapsed / 1000).toFixed(2)}s)`);
  }

  const elapsed = Date.now() - start;
  const passedCount = results.filter(r => r.status === 'PASS').length;
  const failedCount = results.filter(r => r.status === 'FAIL').length;

  console.log(`\n${'='.repeat(60)}`);
  console.log(`  ${results.length} tests | ${passedCount} passed | ${failedCount} failed | ${(elapsed / 1000).toFixed(1)}s`);
  console.log(`${'='.repeat(60)}`);

  const report = buildMarkdown(results, elapsed);
  const reportPath = nextReportPath();
  fs.writeFileSync(reportPath, report, 'utf-8');
  console.log(`\nMarkdown report: ${reportPath}`);

  return failedCount > 0 ? 1 : 0;
}

main().then(code => process.exit(code));
