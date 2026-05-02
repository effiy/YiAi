#!/usr/bin/env node

// 兼容旧入口：调用新脚本
const { spawn } = require('child_process');
const path = require('path');

const scriptPath = path.join(__dirname, 'skills', 'import-docs', 'scripts', 'import-docs.js');

const child = spawn('node', [scriptPath, ...process.argv.slice(2)], {
  stdio: 'inherit'
});

child.on('close', (code) => {
  process.exit(code);
});
