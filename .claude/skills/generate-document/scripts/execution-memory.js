#!/usr/bin/env node

/**
 * execution-memory
 *
 * Execution memory system: records the full context and result of each generate-document
 * feature document execution, for doc-planner to query historical similar cases,
 * and for self-improve.js to analyze improvement patterns.
 *
 * Usage:
 *   node scripts/execution-memory.js write <json-file>
 *   node scripts/execution-memory.js query [--feature <name>] [--keyword <k>] [--limit <n>]
 *   node scripts/execution-memory.js stats [--week <YYYY-MM-DD>]
 *   node scripts/execution-memory.js ls [--limit <n>]
 *
 * Storage location: docs/.memory/execution-memory.jsonl (append-only, one JSON object per line)
 */

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const { getNaturalWeekRange } = require('./natural-week.js');

const REPO_ROOT = path.resolve(__dirname, '../../..');
const MEMORY_DIR = path.join(REPO_ROOT, 'docs', '.memory');
const MEMORY_FILE = path.join(MEMORY_DIR, 'execution-memory.jsonl');

function printHelp() {
  console.log(`Usage:
  node scripts/execution-memory.js write <json-file>       Write a single record
  node scripts/execution-memory.js query [options]          Query historical records
  node scripts/execution-memory.js stats [options]          Stats on high-frequency patterns
  node scripts/execution-memory.js ls [options]             List recent records

Options:
  --feature <name>   Match by feature name
  --keyword <k>      Match by keyword (fingerprint, description, bad case lesson)
  --limit <n>        Max results to return (default 10)
  --week <date>      Filter by natural week (YYYY-MM-DD)
  --json             Output JSON (default Markdown)

Examples:
  node scripts/execution-memory.js write /tmp/session.json
  node scripts/execution-memory.js query --feature "User Login" --limit 5
  node scripts/execution-memory.js stats --week 2026-04-29 --json
`);
}

function parseArgs(argv) {
  const out = { command: null, file: null, feature: null, keyword: null, limit: 10, week: null, json: false };
  const args = argv.slice(2);
  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') { printHelp(); process.exit(0); }
  out.command = args[0];
  for (let i = 1; i < args.length; i++) {
    const a = args[i];
    if (a === '--help' || a === '-h') { printHelp(); process.exit(0); }
    else if (a === '--feature') out.feature = args[++i];
    else if (a === '--keyword') out.keyword = args[++i];
    else if (a === '--limit') out.limit = parseInt(args[++i], 10) || 10;
    else if (a === '--week') out.week = args[++i];
    else if (a === '--json') out.json = true;
    else if (!out.file && !a.startsWith('-')) out.file = a;
  }
  return out;
}

async function ensureMemoryFile() {
  await fsp.mkdir(MEMORY_DIR, { recursive: true });
  try {
    await fsp.access(MEMORY_FILE);
  } catch {
    await fsp.writeFile(MEMORY_FILE, '', 'utf8');
  }
}

async function readAllRecords() {
  await ensureMemoryFile();
  const text = await fsp.readFile(MEMORY_FILE, 'utf8');
  const lines = text.split('\n').filter(l => l.trim() !== '');
  return lines.map(l => {
    try { return JSON.parse(l); } catch { return null; }
  }).filter(Boolean);
}

function matchFeature(record, featureName) {
  if (!featureName) return true;
  const f = featureName.toLowerCase();
  return (record.feature || '').toLowerCase().includes(f) ||
    (record.description || '').toLowerCase().includes(f);
}

function matchKeyword(record, keyword) {
  if (!keyword) return true;
  const k = keyword.toLowerCase();
  const haystack = [
    record.feature,
    record.description,
    ...(record.feature_fingerprint || []),
    ...(record.agents_called || []),
    ...(record.bad_cases || []).map(b => `${b.agent} ${b.lesson}`),
    ...(record.quality_issues?.P0 || []).map(q => `${q.doc_type} ${q.section} ${q.issue}`),
    ...(record.quality_issues?.P1 || []).map(q => `${q.doc_type} ${q.section} ${q.issue}`),
  ].join(' ').toLowerCase();
  return haystack.includes(k);
}

function matchWeek(record, weekDate) {
  if (!weekDate) return true;
  const weekRange = getNaturalWeekRange(new Date(weekDate));
  const ts = new Date(record.timestamp || 0);
  const recordWeek = getNaturalWeekRange(ts);
  return recordWeek.range === weekRange.range;
}

function scoreRelevance(record, featureName, keyword) {
  let score = 0;
  if (featureName) {
    const f = featureName.toLowerCase();
    if ((record.feature || '').toLowerCase() === f) score += 100;
    else if ((record.feature || '').toLowerCase().includes(f)) score += 50;
  }
  if (keyword) {
    const k = keyword.toLowerCase();
    const fp = (record.feature_fingerprint || []).join(' ').toLowerCase();
    if (fp.includes(k)) score += 30;
  }
  score += (record.quality_issues?.P0?.length || 0) * 5;
  score += (record.bad_cases?.length || 0) * 3;
  return score;
}

async function cmdWrite(filePath) {
  if (!filePath) { console.error('Error: write command requires json-file argument'); process.exit(1); }
  const raw = await fsp.readFile(filePath, 'utf8');
  const record = JSON.parse(raw);
  if (!record.session_id) record.session_id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  if (!record.timestamp) record.timestamp = new Date().toISOString();
  await ensureMemoryFile();
  const line = JSON.stringify(record);
  await fsp.appendFile(MEMORY_FILE, line + '\n', 'utf8');
  console.log(`✓ Execution memory written (session_id: ${record.session_id})`);
}

async function cmdQuery(opts) {
  const records = await readAllRecords();
  let filtered = records.filter(r => matchFeature(r, opts.feature) && matchKeyword(r, opts.keyword) && matchWeek(r, opts.week));
  filtered.sort((a, b) => scoreRelevance(b, opts.feature, opts.keyword) - scoreRelevance(a, opts.feature, opts.keyword));
  filtered = filtered.slice(0, opts.limit);

  if (opts.json) {
    console.log(JSON.stringify(filtered, null, 2));
    return;
  }

  console.log(`# Execution Memory Query Results (${filtered.length} records)\n`);
  if (filtered.length === 0) {
    console.log('> No matching records.');
    return;
  }
  filtered.forEach((r, i) => {
    console.log(`## ${i + 1}. ${r.feature || 'Unnamed'} · ${r.actual_change_level || '?'} · ${r.timestamp ? r.timestamp.slice(0, 10) : 'Unknown date'}`);
    console.log(`- **session_id**: ${r.session_id}`);
    console.log(`- **Description**: ${r.description || 'None'}`);
    console.log(`- **Fingerprint**: ${(r.feature_fingerprint || []).join(', ') || 'None'}`);
    console.log(`- **Change level**: planned=${r.planned_change_level || '?'} / actual=${r.actual_change_level || '?'}`);
    console.log(`- **Agents called**: ${(r.agents_called || []).join(', ') || 'None'}`);
    const p0 = r.quality_issues?.P0?.length || 0;
    const p1 = r.quality_issues?.P1?.length || 0;
    const p2 = r.quality_issues?.P2?.length || 0;
    console.log(`- **Quality issues**: P0=${p0} / P1=${p1} / P2=${p2}`);
    if (r.was_blocked) console.log(`- **Blocked**: ${r.block_reason || 'Not specified'}`);
    if ((r.bad_cases || []).length > 0) {
      console.log(`- **Bad cases**:`);
      r.bad_cases.forEach(b => console.log(`  - ${b.agent}: ${b.lesson}`));
    }
    console.log('');
  });
}

async function cmdStats(opts) {
  const records = await readAllRecords();
  const filtered = records.filter(r => matchWeek(r, opts.week));

  const total = filtered.length;
  const blocked = filtered.filter(r => r.was_blocked).length;
  const changeLevels = { T1: 0, T2: 0, T3: 0 };
  const agentFreq = {};
  const docTypeIssues = {};
  const sectionIssues = {};
  const lessonFreq = {};

  filtered.forEach(r => {
    if (r.actual_change_level) changeLevels[r.actual_change_level] = (changeLevels[r.actual_change_level] || 0) + 1;
    (r.agents_called || []).forEach(a => { agentFreq[a] = (agentFreq[a] || 0) + 1; });
    ['P0', 'P1', 'P2'].forEach(lv => {
      (r.quality_issues?.[lv] || []).forEach(q => {
        const key = `${q.doc_type || 'unknown'}::${q.section || 'unknown'}`;
        docTypeIssues[key] = (docTypeIssues[key] || 0) + 1;
      });
    });
    ['P0', 'P1', 'P2'].forEach(lv => {
      (r.quality_issues?.[lv] || []).forEach(q => {
        const key = `${q.section || 'unknown'}::${q.issue || 'unknown'}`;
        sectionIssues[key] = (sectionIssues[key] || 0) + 1;
      });
    });
    (r.bad_cases || []).forEach(b => {
      const key = `${b.agent}::${b.lesson}`;
      lessonFreq[key] = (lessonFreq[key] || 0) + 1;
    });
  });

  const topDocTypeIssues = Object.entries(docTypeIssues).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const topSectionIssues = Object.entries(sectionIssues).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const topLessons = Object.entries(lessonFreq).sort((a, b) => b[1] - a[1]).slice(0, 5);

  if (opts.json) {
    console.log(JSON.stringify({ total, blocked, changeLevels, agentFreq, topDocTypeIssues, topSectionIssues, topLessons }, null, 2));
    return;
  }

  console.log(`# Execution Memory Statistics${opts.week ? ' · ' + getNaturalWeekRange(new Date(opts.week)).range : ''}\n`);
  console.log(`- **Total records**: ${total}`);
  console.log(`- **Blocked count**: ${blocked}`);
  console.log(`- **Change level distribution**: T1=${changeLevels.T1}, T2=${changeLevels.T2}, T3=${changeLevels.T3}`);
  console.log(`\n## Agent Invocation Frequency`);
  Object.entries(agentFreq).sort((a, b) => b[1] - a[1]).forEach(([a, c]) => console.log(`- ${a}: ${c}`));
  console.log(`\n## High-Frequency Quality Issues (doc type::section)`);
  topDocTypeIssues.forEach(([k, c]) => console.log(`- ${k}: ${c} times`));
  console.log(`\n## High-Frequency Section Issues (section::issue description)`);
  topSectionIssues.forEach(([k, c]) => console.log(`- ${k}: ${c} times`));
  console.log(`\n## High-Frequency Bad Case Lessons (agent::lesson)`);
  topLessons.forEach(([k, c]) => console.log(`- ${k}: ${c} times`));
}

async function cmdLs(opts) {
  const records = await readAllRecords();
  const filtered = records.filter(r => matchWeek(r, opts.week)).slice(-opts.limit);
  if (opts.json) {
    console.log(JSON.stringify(filtered, null, 2));
    return;
  }
  console.log(`# Recent ${filtered.length} Execution Memory Records\n`);
  filtered.forEach((r, i) => {
    const p0 = r.quality_issues?.P0?.length || 0;
    const flag = r.was_blocked ? '❌ Blocked' : (p0 > 0 ? '⚠️ P0' : '✅');
    console.log(`${i + 1}. [${flag}] ${r.feature || 'Unnamed'} · ${r.actual_change_level || '?'} · ${r.timestamp ? r.timestamp.slice(0, 10) : '?'}`);
  });
}

async function main() {
  const opts = parseArgs(process.argv);
  switch (opts.command) {
    case 'write': await cmdWrite(opts.file); break;
    case 'query': await cmdQuery(opts); break;
    case 'stats': await cmdStats(opts); break;
    case 'ls': await cmdLs(opts); break;
    default:
      console.error(`Error: unknown command ${opts.command}`);
      printHelp();
      process.exit(1);
  }
}

main().catch(err => { console.error(err); process.exit(1); });
