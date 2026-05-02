#!/usr/bin/env node

/**
 * Append generate-document / implement-code orchestration interactions with .claude skills, agents, MCP, etc.
 * as Markdown to repo root `docs/weekly/<YYYY-MM-DD~YYYY-MM-DD>/logs.md`.
 * Each record contains "operation scenario" and "dialogue and interaction summary"; optional --case / --tags / --lesson
 * to mark good case / bad case, for docs/logs/CASE-STANDARD.md and subsequent improvements to skills, rules, agents.
 * Usage see each skill's SKILL.md "orchestration session logs".
 */

const fsp = require('fs').promises;
const path = require('path');
const { getNaturalWeekRange } = require('./natural-week.js');

const SKILL_VALUES = new Set(['generate-document', 'implement-code']);
const KIND_VALUES = new Set([
  'skill',
  'agent',
  'mcp',
  'memory',
  'shared',
  'other',
]);

const CASE_VALUES = new Set(['good', 'bad', 'neutral']);

function printHelp(stream) {
  const out = stream || process.stdout;
  out.write(`Usage:
  node .claude/scripts/log-orchestration.js --skill <generate-document|implement-code> \\
    --kind <skill|agent|mcp|memory|shared|other> [--name <identifier>] \\
    [--scenario "<operation scenario>"] \\
    [--case <good|bad|neutral>] \\
    [--tags "<tag1,tag2>"] \\
    [--lesson "<one-sentence follow-up improvement>"] \\
    [--text "<summary; single line>"]

  When --text is not provided, read body from stdin (newlines preserved, used as dialogue and interaction summary).
  good/bad standards see docs/logs/CASE-STANDARD.md.
  Log directory: <repo-root>/docs/weekly/<natural-week-start-end>/
  Filename: logs.md (appended per week)

Examples:
  node .claude/scripts/log-orchestration.js --skill generate-document --kind agent --name spec-retriever \\
    --scenario "User initiated /generate-document Foo; this step retrieves applicable specs" \\
    --case good --tags "evidence-ok,stage-contract-met" \\
    --text "Returned applicable spec list: rules/requirement-document.md ..."
`);
}

function usage() {
  printHelp(process.stderr);
  process.exit(2);
}

function parseArgs(argv) {
  const out = {
    skill: null,
    kind: null,
    name: '',
    text: null,
    scenario: null,
    case: null,
    tags: null,
    lesson: null,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') {
      printHelp();
      process.exit(0);
    }
    else if (a === '--skill') out.skill = argv[++i];
    else if (a === '--kind') out.kind = argv[++i];
    else if (a === '--name') out.name = argv[++i] || '';
    else if (a === '--text') out.text = argv[++i] || '';
    else if (a === '--scenario') out.scenario = argv[++i] || '';
    else if (a === '--case') out.case = argv[++i] || '';
    else if (a === '--tags') out.tags = argv[++i] || '';
    else if (a === '--lesson') out.lesson = argv[++i] || '';
    else usage();
  }
  return out;
}

/** stdin: preserve newlines to avoid dialogue excerpts being compressed into one line */
function normalizeMultiline(s) {
  return String(s ?? '')
    .replace(/\r\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

/** --text: single-line summary */
function normalizeOneLine(s) {
  return String(s ?? '')
    .replace(/\r\n/g, '\n')
    .replace(/\n+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString('utf8');
}

/**
 * Convert summary to blockquote to avoid # in body breaking Markdown structure; remains readable.
 */
function formatSummaryBody(body) {
  return body.split('\n').map((line) => `> ${line}`).join('\n');
}

function parseTags(raw) {
  if (raw == null || String(raw).trim() === '') return [];
  return String(raw)
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean);
}

function normalizeCaseArg(raw) {
  if (raw == null || String(raw).trim() === '') return null;
  const c = String(raw).trim().toLowerCase();
  if (!CASE_VALUES.has(c)) {
    console.error(`log-orchestration: --case must be good | bad | neutral, received: ${raw}`);
    process.exit(1);
  }
  return c;
}

/**
 * @param {'good'|'bad'|'neutral'|null} caseNorm
 * @param {string[]} tagsArr
 * @param {string|null|undefined} lessonRaw
 */
function formatEvaluationBlock(caseNorm, tagsArr, lessonRaw) {
  const lesson = lessonRaw != null ? String(lessonRaw).trim() : '';
  if (!caseNorm && tagsArr.length === 0 && !lesson) return '';

  const lines = ['', '**Evaluation**'];
  const grade = caseNorm || 'neutral';
  lines.push(`- **Grade**: ${grade}`);
  if (tagsArr.length) {
    lines.push(`- **Tags**: ${tagsArr.map((t) => `\`${t}\``).join(' · ')}`);
  }
  if (lesson) {
    lines.push(`- **Follow-up**: ${lesson}`);
  }

  return `${lines.join('\n')}\n`;
}

function headingCaseBadge(caseNorm) {
  if (caseNorm === 'good') return ' · **good case**';
  if (caseNorm === 'bad') return ' · **bad case**';
  return '';
}

async function ensureMarkdownPreamble(logFile, weekRange) {
  let needHeader = true;
  try {
    const st = await fsp.stat(logFile);
    needHeader = st.size === 0;
  } catch {
    needHeader = true;
  }
  if (!needHeader) return;

  const preamble = `---
log_type: orchestration
week: ${weekRange}
---

# Orchestration Session Logs · ${weekRange}

This file is appended by \`node .claude/scripts/log-orchestration.js\`, recording this week's orchestration interaction summaries.
Each record contains operation scenario, interaction summary, and optional evaluation annotation (good/bad case reference \`docs/logs/CASE-STANDARD.md\`).

---

`;

  await fsp.writeFile(logFile, preamble, 'utf8');
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.skill || !SKILL_VALUES.has(args.skill)) usage();
  if (!args.kind || !KIND_VALUES.has(args.kind)) usage();

  let body = args.text;
  if (body == null || body === '') {
    body = await readStdin();
    body = normalizeMultiline(body);
  } else {
    body = normalizeOneLine(body);
  }

  if (!body) {
    console.error('log-orchestration: body is empty (provide --text or stdin)');
    process.exit(1);
  }

  const repoRoot = path.resolve(__dirname, '../../..');
  const week = getNaturalWeekRange(new Date());
  const logsDir = path.join(repoRoot, 'docs', 'weekly', week.range);
  await fsp.mkdir(logsDir, { recursive: true });
  const logFile = path.join(logsDir, 'logs.md');

  await ensureMarkdownPreamble(logFile, week.range);

  const caseNorm = normalizeCaseArg(args.case);
  const tagsArr = parseTags(args.tags);
  const lessonRaw = args.lesson;

  if (caseNorm === 'bad' && (!lessonRaw || !String(lessonRaw).trim())) {
    console.warn(
      'log-orchestration: bad case recommended with --lesson describing follow-up improvement points (see docs/logs/CASE-STANDARD.md)'
    );
  }

  const iso = new Date().toISOString();
  const category = args.name ? `${args.skill}:${args.kind}/${args.name}` : `${args.skill}:${args.kind}`;
  const scenario =
    args.scenario != null && String(args.scenario).trim() !== ''
      ? String(args.scenario).trim()
      : '(Operation scenario not annotated; please pass `--scenario` in next invocation, referencing eval user story description)';

  const evalBlock = formatEvaluationBlock(caseNorm, tagsArr, lessonRaw);
  const badge = headingCaseBadge(caseNorm);

  const block = `### \`${iso}\` · \`${category}\`${badge}

**Scenario**: ${scenario}

**Dialogue and Interaction Summary**

${formatSummaryBody(body)}
${evalBlock}
---

`;

  await fsp.appendFile(logFile, block, 'utf8');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
