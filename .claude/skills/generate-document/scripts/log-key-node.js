#!/usr/bin/env node

/**
 * Key node recorder: Markdown append to repo root
 * `docs/weekly/<YYYY-MM-DD~YYYY-MM-DD>/key-notes.md`.
 * Complements logs.md: focuses on milestones / gates / external notifications and other at-a-glance nodes.
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
  out.write(`Usage:
  node .claude/scripts/log-key-node.js --title "<node title>" \\
    [--category <category, default general>] \\
    [--skill <related skill name>] \\
    [--text "<description; single line>"]

  When --text is not provided, read description from stdin (newlines preserved).

  Log directory: <repo-root>/docs/weekly/<natural-week-start-end>/
  Filename: key-notes.md (appended per week)

Examples:
  node .claude/scripts/log-key-node.js --title "Stage 4 review passed" \\
    --category stage --skill generate-document \\
    --text "code-reviewer: blockers cleared"

  echo "Gate: pnpm test passed" | node .claude/scripts/log-key-node.js \\
    --title "Smoke gate passed" --category gate --skill implement-code
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
    console.error('log-key-node: missing --title');
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
    console.error('log-key-node: description is empty (provide --text or stdin)');
    process.exit(1);
  }

  const repoRoot = path.resolve(__dirname, '../../..');

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
