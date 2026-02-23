#!/usr/bin/env node
'use strict';

const { Recorder } = require('./recorder');

async function main() {
  const name = process.argv[2] || 'Untitled';
  const recorder = new Recorder();

  const startResult = await recorder.start(name);
  if (!startResult.started) {
    console.log(JSON.stringify({ error: startResult.reason }));
    process.exit(1);
  }

  console.log(JSON.stringify({
    message: `Recording started: ${startResult.name}`,
    id: startResult.id,
    pid: process.pid,
    hint: 'Browser is open. User can now operate freely. Call stop when done.',
  }));

  await recorder.runDaemon();
  process.exit(0);
}

main().catch((e) => {
  console.error(JSON.stringify({ error: e.message }));
  process.exit(1);
});
