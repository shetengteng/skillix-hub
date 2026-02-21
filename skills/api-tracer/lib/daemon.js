'use strict';

const { Recorder } = require('./recorder');
const { saveSession } = require('./store');
const { writeJson, TRACER_STATE_FILE } = require('./config');

async function runDaemon(options) {
  const recorder = new Recorder();

  process.on('SIGTERM', async () => {
    const sessionData = recorder.buildSessionData();
    const stopInfo = await recorder.stop();
    await saveSession(stopInfo.sessionName, sessionData);
    await writeJson(TRACER_STATE_FILE, {
      recording: false,
      lastSession: stopInfo.sessionName,
    });
    process.exit(0);
  });

  process.on('SIGINT', async () => {
    const sessionData = recorder.buildSessionData();
    const stopInfo = await recorder.stop();
    await saveSession(stopInfo.sessionName, sessionData);
    await writeJson(TRACER_STATE_FILE, {
      recording: false,
      lastSession: stopInfo.sessionName,
    });
    process.exit(0);
  });

  const startInfo = await recorder.start(options);

  const stateUpdate = setInterval(async () => {
    const status = recorder.getStatus();
    await writeJson(TRACER_STATE_FILE, {
      recording: true,
      sessionName: status.sessionName,
      startTime: status.startTime,
      capturedRequests: status.capturedRequests,
      pendingRequests: status.pendingRequests,
      pid: process.pid,
    });
  }, 2000);

  console.log(JSON.stringify({ started: true, ...startInfo }));

  await new Promise(() => {});
}

if (require.main === module) {
  const args = JSON.parse(process.argv[2] || '{}');
  runDaemon(args).catch(e => {
    console.error(JSON.stringify({ error: e.message }));
    process.exit(1);
  });
}

module.exports = { runDaemon };
