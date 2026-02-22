'use strict';

const path = require('path');

const DEFAULT_PORT = 7890;
const PORT_RANGE = 10;
const DEFAULT_TIMEOUT = 60;
const MAX_TIMEOUT = 600;
const PID_FILE = path.join(__dirname, '..', '.server.pid');
const UI_DIST = path.join(__dirname, '..', 'ui', 'dist');

module.exports = {
  DEFAULT_PORT,
  PORT_RANGE,
  DEFAULT_TIMEOUT,
  MAX_TIMEOUT,
  PID_FILE,
  UI_DIST,
};
