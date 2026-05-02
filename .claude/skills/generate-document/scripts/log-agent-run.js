#!/usr/bin/env node

/**
 * log-agent-run
 *
 * Purpose: accumulate agent invocation success/failure records under `.claude/agents/memory/`,
 * providing retrievable data for subsequent orchestration optimization (failure reasons, stage distribution, retry effectiveness, etc.).
 *
 * Output file:
 *   .claude/agents/memory/<agent>.runs.md
 *
 * Usage:
 *   node scripts/log-agent-run.js --agent <name> --status <success|failure>
 *     --skill <generate-document|implement-code|other> --stage <stage-id>
 *     [--doc_type <doc type>] [--feature <feature name or summary>]
 *     [--notes "<one-line summary>"] [--error "<failure reason>"] [--evidence "<evidence path or command>"]
 *
 * Exit codes:
 *   0 success
 *   2 argument error
 */

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');

const STATUS_VALUES = new Set(['success', 'failure']);

function printHelp(stream) {
  const out = stream || process.stdout;
  out.write(`Usage:
  node scripts/log-agent-run.js --agent <agent-name> --status <success|failure> \\
    --skill <skill-name> --stage <stage-id> \\
    [--doc_type <doc type>] [--feature <feature name or summary>] \\
    [--notes "<one-line summary>"] [--error "<failure reason>"] [--evidence "<evidence path or command>"]
`);
}

function usage() {
  printHelp(process.stderr);
  process.exit(2);
}

function parseArgs(argv) {
  const out = {
    agent: null,
    status: null,
    skill: null,
    stage: null,
    doc_type: 'N/A',
    feature: 'N/A',
    notes: '',
    error: '',
    evidence: '',
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') {
      printHelp();
      process.exit(0);
    }
    else if (a === '--agent') out.agent = argv[++i];
    else if (a === '--status') out.status = argv[++i];
    else if (a === '--skill') out.skill = argv[++i];
    else if (a === '--stage') out.stage = argv[++i];
    else if (a === '--doc_type') out.doc_type = argv[++i] || 'N/A';
    else if (a === '--feature') out.feature = argv[++i] || 'N/A';
    else if (a === '--notes') out.notes = argv[++i] || '';
    else if (a === '--error') out.error = argv[++i] || '';
    else if (a === '--evidence') out.evidence = argv[++i] || '';
    else usage();
  }
  return out;
}

function normalizeOneLine(s) {
  return String(s ?? '')
    .replace(/\r\n/g, '\n')
    .replace(/\n+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function nowIso() {
  return new Date().toISOString();
}

function ensureDirSync(p) {
  fs.mkdirSync(p, { recursive: true });
}

function parseFrontmatter(md) {
  const m = /^---\n([\s\S]*?)\n---\n/.exec(md);
  if (!m) return { frontmatter: null, body: md };
  return { frontmatter: m[1], body: md.slice(m[0].length) };
}

function parseYamlKV(frontmatter) {
  const out = {};
  const lines = String(frontmatter ?? '').split('\n');
  for (const line of lines) {
    const mm = /^([A-Za-z0-9_]+):\s*(.*)\s*$/.exec(line);
    if (!mm) continue;
    out[mm[1]] = mm[2];
  }
  return out;
}

function buildFrontmatter(agent, stats) {
  return `---\nagent: ${agent}\nlast_updated: ${stats.last_updated}\nsuccess_count: ${stats.success_count}\nfailure_count: ${stats.failure_count}\nentry_count: ${stats.entry_count}\n---\n\n`;
}

function buildEntry(args) {
  const iso = nowIso();
  const statusBadge = args.status === 'success' ? '✅ success' : '❌ failure';
  const lines = [];
  lines.push(`### \`${iso}\` · ${statusBadge}`);
  lines.push(`- **skill**: \`${normalizeOneLine(args.skill)}\``);
  lines.push(`- **stage**: \`${normalizeOneLine(args.stage)}\``);
  lines.push(`- **doc_type**: ${normalizeOneLine(args.doc_type) || 'N/A'}`);
  lines.push(`- **feature**: ${normalizeOneLine(args.feature) || 'N/A'}`);
  if (args.notes && normalizeOneLine(args.notes)) {
    lines.push(`- **notes**: ${normalizeOneLine(args.notes)}`);
  }
  if (args.status === 'failure') {
    lines.push(`- **error**: ${normalizeOneLine(args.error) || '(not provided)'}`);
  }
  if (args.evidence && normalizeOneLine(args.evidence)) {
    lines.push(`- **evidence**: ${normalizeOneLine(args.evidence)}`);
  }
  lines.push('');
  return `${lines.join('\n')}\n`;
}

async function ensureFile(filePath, agent) {
  try {
    await fsp.stat(filePath);
    return;
  } catch {
    // create
  }

  const init = buildFrontmatter(agent, {
    last_updated: nowIso(),
    success_count: 0,
    failure_count: 0,
    entry_count: 0,
  });

  const body = `## Run Log\n\n(No records yet, waiting for first invocation)\n\n`;
  await fsp.writeFile(filePath, init + body, 'utf8');
}

async function main() {
  const args = parseArgs(process.argv);
  const agent = normalizeOneLine(args.agent);
  const status = normalizeOneLine(args.status);
  const skill = normalizeOneLine(args.skill);
  const stage = normalizeOneLine(args.stage);

  if (!agent) usage();
  if (!status || !STATUS_VALUES.has(status)) usage();
  if (!skill) usage();
  if (!stage) usage();

  // Write location: <repo>/.claude/agents/memory/<agent>.runs.md
  const repoRoot = path.resolve(__dirname, '../../..');
  const memDir = path.join(repoRoot, '.claude', 'agents', 'memory');
  ensureDirSync(memDir);
  const filePath = path.join(memDir, `${agent}.runs.md`);

  await ensureFile(filePath, agent);

  const raw = await fsp.readFile(filePath, 'utf8');
  const { frontmatter, body } = parseFrontmatter(raw);
  const kv = parseYamlKV(frontmatter || '');

  const stats = {
    last_updated: nowIso(),
    success_count: Number(kv.success_count || 0) || 0,
    failure_count: Number(kv.failure_count || 0) || 0,
    entry_count: Number(kv.entry_count || 0) || 0,
  };

  if (status === 'success') stats.success_count += 1;
  else stats.failure_count += 1;
  stats.entry_count += 1;

  const cleanedBody = String(body || '')
    // Compatible with half-width and full-width placeholder text
    .replace(/\(No records yet, waiting for first invocation\)\s*/g, '')
    .replace(/（暂无记录，等待首次调用）\s*/g, '');
  const entry = buildEntry({ ...args, status, skill, stage });

  const next =
    buildFrontmatter(agent, stats) +
    (cleanedBody.trim() ? cleanedBody.trimEnd() + '\n\n' : '## Run Log\n\n') +
    entry;

  await fsp.writeFile(filePath, next, 'utf8');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
