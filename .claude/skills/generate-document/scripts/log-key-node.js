#!/usr/bin/env node

/**
 * 关键节点记录：Markdown 追加写入仓库根目录
 * `docs/周报/<YYYY-MM-DD~YYYY-MM-DD>/key-notes.md`。
 * 与 logs.md 互补：此处侧重里程碑 / 门禁 / 对外通知等可一眼扫描的节点。
 */

const path = require('path');
const { appendKeyNodeRecord } = require('./append-key-node.js');

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString('utf8');
}

function normalizeMultiline(s) {
  return String(s ?? '')
    .replace(/\r\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function normalizeOneLine(s) {
  return String(s ?? '')
    .replace(/\r\n/g, '\n')
    .replace(/\n+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function printHelp(stream) {
  const out = stream || process.stdout;
  out.write(`用法:
  node .claude/scripts/log-key-node.js --title "<节点标题>" \\
    [--category <分类，默认 general>] \\
    [--skill <关联技能名>] \\
    [--text "<说明；单行>"]

  未提供 --text 时从 stdin 读取说明（保留换行）。

  日志目录：<仓库根>/docs/周报/<自然周起止日期>/
  文件名：key-notes.md（按周追加）

示例:
  node .claude/scripts/log-key-node.js --title "阶段 4 审查通过" \\
    --category stage --skill generate-document \\
    --text "code-reviewer：阻断项已清零"

  echo "门禁：pnpm test 通过" | node .claude/scripts/log-key-node.js \\
    --title "冒烟门禁通过" --category gate --skill implement-code
`);
}

function usage() {
  printHelp(process.stderr);
  process.exit(2);
}

function parseArgs(argv) {
  const out = {
    title: null,
    category: null,
    skill: null,
    text: null,
    help: false,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--title') out.title = argv[++i];
    else if (a === '--category') out.category = argv[++i];
    else if (a === '--skill') out.skill = argv[++i];
    else if (a === '--text') out.text = argv[++i] || '';
    else if (a === '--help' || a === '-h') out.help = true;
    else usage();
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    printHelp();
    process.exit(0);
  }
  if (!args.title || String(args.title).trim() === '') {
    console.error('log-key-node: 缺少 --title');
    usage();
  }

  let body = args.text;
  if (body == null || body === '') {
    body = await readStdin();
    body = normalizeMultiline(body);
  } else {
    body = normalizeOneLine(body);
  }

  if (!body) {
    console.error('log-key-node: 说明为空（提供 --text 或 stdin）');
    process.exit(1);
  }

  // 本仓库中 scripts/ 位于仓库根目录下：<repo>/scripts
  const repoRoot = path.resolve(__dirname, '..');

  await appendKeyNodeRecord(repoRoot, {
    title: args.title,
    category: args.category,
    skill: args.skill,
    body,
  });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
