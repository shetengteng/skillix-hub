'use strict';

const http = require('http');

const PORT = process.env.PORT || 7890;
const BASE = `http://127.0.0.1:${PORT}`;

function post(path, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = http.request(`${BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) },
    }, (res) => {
      let buf = '';
      res.on('data', (c) => buf += c);
      res.on('end', () => {
        try { resolve(JSON.parse(buf)); } catch { resolve(buf); }
      });
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

const demos = [
  {
    name: 'notification (success)',
    data: {
      type: 'notification', level: 'success',
      title: '部署成功', message: 'v2.0 已成功部署到生产环境',
      autoClose: 8,
    },
  },
  {
    name: 'notification (warning)',
    data: {
      type: 'notification', level: 'warning',
      title: '磁盘空间不足', message: '剩余空间不足 10%，请及时清理',
      autoClose: 8,
    },
  },
  {
    name: 'confirm',
    data: {
      type: 'confirm',
      title: '请选择部署环境',
      message: '即将执行部署，请选择目标环境：',
      options: [
        { id: 'dev', label: '开发环境', description: 'dev.example.com' },
        { id: 'staging', label: '预发布环境', description: 'staging.example.com' },
        { id: 'prod', label: '生产环境', description: 'prod.example.com' },
      ],
      timeout: 120,
    },
  },
  {
    name: 'wait',
    data: {
      type: 'wait',
      title: '等待指纹验证',
      message: '请在手机上完成指纹验证后点击确认',
      confirmText: '已完成验证',
      cancelText: '取消',
      timeout: 120,
    },
  },
  {
    name: 'form',
    data: {
      type: 'form',
      title: '数据库连接配置',
      message: '请填写数据库连接信息：',
      fields: [
        { id: 'host', label: '主机地址', type: 'text', default: 'localhost', required: true },
        { id: 'port', label: '端口', type: 'number', default: 5432, required: true },
        { id: 'database', label: '数据库名', type: 'text', placeholder: '输入数据库名', required: true },
        { id: 'engine', label: '数据库类型', type: 'select', options: ['PostgreSQL', 'MySQL', 'SQLite'] },
        { id: 'notes', label: '备注', type: 'textarea', placeholder: '可选备注信息' },
        { id: 'ssl', label: 'SSL 连接', type: 'checkbox', default: true },
      ],
      submitText: '连接',
      cancelText: '取消',
      timeout: 120,
    },
  },
  {
    name: 'approval',
    data: {
      type: 'approval',
      title: '确认删除数据库',
      message: '此操作将永久删除指定数据库，且不可恢复。',
      severity: 'critical',
      details: {
        '操作': 'DROP DATABASE',
        '目标': 'production_db',
        '影响行数': '约 1,200,000 行',
        '备份状态': '最近备份：2 小时前',
      },
      approveText: '确认删除',
      rejectText: '取消',
      timeout: 120,
    },
  },
  {
    name: 'progress',
    data: {
      type: 'progress',
      title: '项目部署进度',
      message: '正在执行自动化部署流程...',
      steps: [
        { id: 'deps', label: '安装依赖', status: 'completed' },
        { id: 'build', label: '构建项目', status: 'completed' },
        { id: 'test', label: '运行测试', status: 'running' },
        { id: 'deploy', label: '部署到服务器', status: 'pending' },
        { id: 'verify', label: '健康检查', status: 'pending' },
      ],
      percent: 45,
      actions: [{ id: 'ok', label: '了解' }],
      timeout: 120,
    },
  },
  {
    name: 'chart (line)',
    data: {
      type: 'chart',
      title: 'API 响应时间趋势',
      chartType: 'line',
      data: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [
          { label: 'P50 (ms)', data: [45, 52, 48, 61, 55, 42, 38] },
          { label: 'P99 (ms)', data: [120, 180, 150, 220, 190, 110, 95] },
        ],
      },
      actions: [{ id: 'close', label: '关闭' }],
      timeout: 120,
    },
  },
];

async function main() {
  console.log(`\n  Agent Interact Demo — 打开浏览器访问 ${BASE}\n`);
  console.log('  将依次展示 7 种交互类型，每种等待你在浏览器中操作后继续。\n');

  for (let i = 0; i < demos.length; i++) {
    const d = demos[i];
    console.log(`  [${i + 1}/${demos.length}] ${d.name} ...`);
    const result = await post('/api/dialog', d.data);
    console.log(`    → 响应: ${JSON.stringify(result.result || result)}`);
    await sleep(500);
  }

  console.log('\n  Demo 完成！\n');
}

main().catch((e) => {
  console.error(`  错误: ${e.message}`);
  console.error('  请先启动服务: node skills/agent-interact/tool.js start');
  process.exit(1);
});
