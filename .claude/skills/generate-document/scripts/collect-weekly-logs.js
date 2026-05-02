#!/usr/bin/env node

/**
 * collect-weekly-logs
 *
 * Goal: automatically read this week's docs/weekly/<week>/ key-notes.md and logs.md,
 * extracting key nodes (milestones / gates / external notifications) and orchestration session logs
 * (skill / agent / MCP interactions), producing a structured summary for weekly report review.
 *
 * Usage:
 *   node scripts/collect-weekly-logs.js [--week <YYYY-MM-DD>] [--json] [--output <path>]
 *
 * Options:
 *   --week <date>   Specify a date, automatically mapped to its natural week (default: today)
 *   --json          Output JSON format (default: Markdown)
 *   --output <path> Save to file (default: stdout)
 *   --key-only      Output key nodes only
 *   --logs-only     Output orchestration session logs only
 *
 * Exit codes:
 *   0 success
 *   1 runtime error
 *   2 argument error
 */

const fs = require('fs');
const path = require('path');
const { getNaturalWeekRange } = require('./natural-week.js');

function printHelp(stream) {
  const out = stream || process.stdout;
  out.write(`Usage:
  node scripts/collect-weekly-logs.js [--week <YYYY-MM-DD>] [--json] [--output <path>]

Options:
  --week <date>   Specify a date, automatically mapped to its natural week (default: today)
  --json          Output JSON format (default: Markdown)
  --output <path> Save to file (default: stdout)
  --key-only      Output key nodes only
  --logs-only     Output orchestration session logs only

Examples:
  node scripts/collect-weekly-logs.js
  node scripts/collect-weekly-logs.js --week 2026-04-29 --json --output /tmp/logs.json
`);
}

function usage() {
  printHelp(process.stderr);
  process.exit(2);
}

function parseArgs(argv) {
  const out = { week: null, json: false, output: null, keyOnly: false, logsOnly: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') {
      printHelp();
      process.exit(0);
    }
    else if (a === '--week') out.week = argv[++i];
    else if (a === '--json') out.json = true;
    else if (a === '--output') out.output = argv[++i];
    else if (a === '--key-only') out.keyOnly = true;
    else if (a === '--logs-only') out.logsOnly = true;
    else usage();
  }
  return out;
}

function readFileUtf8(p) {
  try {
    return fs.readFileSync(p, 'utf8');
  } catch {
    return null;
  }
}

// ---------- key-notes.md parser ----------

function parseKeyNotes(text) {
  if (!text) return { entries: [], note: 'File does not exist' };

  const lines = text.split(/\r?\n/);
  const entries = [];
  let current = null;

  for (const line of lines) {
    // Match heading: ### `ISO` · `category` · Title
    const h = line.match(/^###\s+`([^`]+)`\s+·\s+`([^`]+)`\s+·\s+(.+)$/);
    if (h) {
      if (current) entries.push(current);
      current = {
        timestamp: h[1],
        category: h[2],
        title: h[3].trim(),
        skill: null,
        body: [],
      };
      continue;
    }
    if (!current) continue;

    const skillMatch = line.match(/^\*\*Related Skill\*\*:\s*`([^`]+)`/);
    if (skillMatch) {
      current.skill = skillMatch[1];
      continue;
    }

    // Skip "**Description**" and separators
    if (line.match(/^\*\*Description\*\*/)) continue;
    if (line.match(/^---+$/)) continue;

    // Collect body (strip leading > quote markers)
    const bodyLine = line.replace(/^\s*>\s?/, '');
    if (bodyLine.trim()) {
      current.body.push(bodyLine);
    }
  }

  if (current) entries.push(current);

  return {
    entries: entries.map((e) => ({ ...e, body: e.body.join('\n').trim() })),
    note: `Parsed ${entries.length} key nodes`,
  };
}

// ---------- logs.md parser ----------

function parseLogs(text) {
  if (!text) return { entries: [], note: 'File does not exist' };

  const lines = text.split(/\r?\n/);
  const entries = [];
  let current = null;
  let inSummary = false;
  let inEval = false;

  for (const line of lines) {
    // Match level-3 heading: ### `ISO` · `category`[ · **badge**]
    // category format: skill:kind/name, e.g. generate-document:agent/spec-retriever
    const h = line.match(/^###\s+`([^`]+)`\s+·\s+`([^`]+)`(?:\s+·\s+(.+))?$/);
    if (h) {
      if (current) entries.push(current);
      const category = h[2].trim();
      const kindMatch = category.match(/^[^:]+:\s*([^/]+)\/(.+)$/);
      current = {
        timestamp: h[1],
        category,
        kind: kindMatch ? kindMatch[1].trim() : 'other',
        name: kindMatch ? kindMatch[2].trim() : category,
        badge: h[3] ? h[3].replace(/\*/g, '').trim() : '',
        scenario: null,
        case: null,
        tags: [],
        lesson: null,
        summary: [],
      };
      inSummary = false;
      inEval = false;
      continue;
    }
    if (!current) continue;

    const scenarioMatch = line.match(/^\*\*Scenario\*\*:\s*(.+)$/);
    if (scenarioMatch) {
      current.scenario = scenarioMatch[1].trim();
      continue;
    }

    // Enter Dialogue and Interaction Summary region
    if (line.match(/^\*\*Dialogue and Interaction Summary\*\*/)) {
      inSummary = true;
      inEval = false;
      continue;
    }

    // Enter Evaluation region
    if (line.match(/^\*\*Evaluation\*\*/)) {
      inSummary = false;
      inEval = true;
      continue;
    }

    // Skip empty lines and separators
    if (line.match(/^---+$/)) continue;

    // Parse case/tags/lesson within Evaluation region
    if (inEval) {
      const caseMatch = line.match(/^\s*-\s*\*\*Grade\*\*:\s*(\S+)/);
      if (caseMatch) {
        current.case = caseMatch[1];
        continue;
      }
      const tagsMatch = line.match(/^\s*-\s*\*\*Tags\*\*:\s*(.+)$/);
      if (tagsMatch) {
        current.tags = tagsMatch[1].split(/[·,，]/).map((t) => t.trim().replace(/^`|`$/g, '')).filter(Boolean);
        continue;
      }
      const lessonMatch = line.match(/^\s*-\s*\*\*Follow-up\*\*:\s*(.+)$/);
      if (lessonMatch) {
        current.lesson = lessonMatch[1].trim();
        continue;
      }
    }

    // Collect summary (strip leading > quote markers)
    if (inSummary) {
      const bodyLine = line.replace(/^\s*>\s?/, '');
      current.summary.push(bodyLine);
    }
  }

  if (current) entries.push(current);

  return {
    entries: entries.map((e) => ({ ...e, summary: e.summary.join('\n').trim() })),
    note: `Parsed ${entries.length} orchestration log entries`,
  };
}

// ---------- Aggregation ----------

function aggregateKeyNotes(parsed) {
  const byCategory = {};
  for (const e of parsed.entries) {
    byCategory[e.category] = (byCategory[e.category] || 0) + 1;
  }
  const bySkill = {};
  for (const e of parsed.entries) {
    if (e.skill) {
      bySkill[e.skill] = (bySkill[e.skill] || 0) + 1;
    }
  }
  return { byCategory, bySkill, total: parsed.entries.length };
}

function aggregateLogs(parsed) {
  const byKind = {};
  const byName = {};
  const cases = { good: 0, bad: 0, neutral: 0, unknown: 0 };
  const allTags = {};

  for (const e of parsed.entries) {
    byKind[e.kind] = (byKind[e.kind] || 0) + 1;
    byName[e.name] = (byName[e.name] || 0) + 1;
    if (e.case && cases[e.case] !== undefined) {
      cases[e.case] += 1;
    } else {
      cases.unknown += 1;
    }
    for (const t of e.tags) {
      allTags[t] = (allTags[t] || 0) + 1;
    }
  }

  return { byKind, byName, cases, allTags, total: parsed.entries.length };
}

// ---------- Output formatting ----------

function formatMarkdown(weekRange, keyNotesResult, logsResult) {
  const lines = [];
  lines.push(`# Key Nodes and Orchestration Log Summary (${weekRange.range})`);
  lines.push('');
  lines.push(`> **Generated at**: ${new Date().toISOString()}`);
  lines.push(`> **Data sources**: docs/weekly/${weekRange.range}/key-notes.md + logs.md`);
  lines.push('');

  // Key nodes
  lines.push('## Key Node Statistics');
  lines.push('');
  const keyAgg = aggregateKeyNotes(keyNotesResult);
  if (keyAgg.total === 0) {
    lines.push(`> ${keyNotesResult.note}`);
    lines.push('');
  } else {
    lines.push(`| Metric | Value |`);
    lines.push(`|--------|-------|`);
    lines.push(`| Total nodes | ${keyAgg.total} |`);
    for (const [cat, count] of Object.entries(keyAgg.byCategory).sort((a, b) => b[1] - a[1])) {
      lines.push(`| Category \`${cat}\` | ${count} |`);
    }
    if (Object.keys(keyAgg.bySkill).length > 0) {
      lines.push(`| Related skills | ${Object.entries(keyAgg.bySkill).map(([s, c]) => `\`${s}\`(${c})`).join(', ')} |`);
    }
    lines.push('');

    lines.push('### Node Details');
    lines.push('');
    for (const e of keyNotesResult.entries) {
      lines.push(`- **\`${e.category}\` · ${e.title}**`);
      lines.push(`  - Time: ${e.timestamp}`);
      if (e.skill) lines.push(`  - Skill: \`${e.skill}\``);
      if (e.body) {
        const bodyPreview = e.body.split('\n')[0].slice(0, 80);
        lines.push(`  - Description: ${bodyPreview}${e.body.length > 80 ? '...' : ''}`);
      }
      lines.push('');
    }
  }

  // Orchestration logs
  lines.push('## Orchestration Session Log Statistics');
  lines.push('');
  const logAgg = aggregateLogs(logsResult);
  if (logAgg.total === 0) {
    lines.push(`> ${logsResult.note}`);
    lines.push('');
  } else {
    lines.push(`| Metric | Value |`);
    lines.push(`|--------|-------|`);
    lines.push(`| Total sessions | ${logAgg.total} |`);
    for (const [kind, count] of Object.entries(logAgg.byKind).sort((a, b) => b[1] - a[1])) {
      lines.push(`| kind \`${kind}\` | ${count} |`);
    }
    lines.push(`| case good | ${logAgg.cases.good} |`);
    lines.push(`| case bad | ${logAgg.cases.bad} |`);
    lines.push(`| case neutral | ${logAgg.cases.neutral} |`);
    if (Object.keys(logAgg.allTags).length > 0) {
      const topTags = Object.entries(logAgg.allTags)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([t, c]) => `\`${t}\`(${c})`)
        .join(', ');
      lines.push(`| TOP5 tags | ${topTags} |`);
    }
    lines.push('');

    lines.push('### Session Details');
    lines.push('');
    for (const e of logsResult.entries) {
      const caseBadge = e.case ? `[${e.case}]` : '';
      lines.push(`- **\`${e.kind}\` · ${e.name}** ${caseBadge}`);
      lines.push(`  - Time: ${e.timestamp}`);
      if (e.scenario) lines.push(`  - Scenario: ${e.scenario}`);
      if (e.lesson) lines.push(`  - lesson: ${e.lesson}`);
      if (e.summary) {
        const summaryPreview = e.summary.split('\n')[0].slice(0, 80);
        lines.push(`  - Summary: ${summaryPreview}${e.summary.length > 80 ? '...' : ''}`);
      }
      lines.push('');
    }
  }

  return lines.join('\n');
}

function formatJson(weekRange, keyNotesResult, logsResult) {
  return JSON.stringify(
    {
      weekRange,
      generatedAt: new Date().toISOString(),
      keyNotes: {
        ...keyNotesResult,
        aggregate: aggregateKeyNotes(keyNotesResult),
      },
      logs: {
        ...logsResult,
        aggregate: aggregateLogs(logsResult),
      },
    },
    null,
    2
  );
}

// ---------- Main flow ----------

function main() {
  const args = parseArgs(process.argv);

  let baseDate = new Date();
  if (args.week) {
    const d = new Date(args.week);
    if (isNaN(d.getTime())) {
      console.error(`Error: invalid date "${args.week}"`);
      process.exit(2);
    }
    baseDate = d;
  }

  const weekRange = getNaturalWeekRange(baseDate);
  const REPO_ROOT = path.resolve(__dirname, '../../..');
  const weeklyDir = path.join(REPO_ROOT, 'docs', 'weekly', weekRange.range);

  let keyNotesResult = { entries: [], note: 'Skipped key nodes' };
  let logsResult = { entries: [], note: 'Skipped orchestration logs' };

  if (!args.logsOnly) {
    const keyNotesPath = path.join(weeklyDir, 'key-notes.md');
    const keyNotesText = readFileUtf8(keyNotesPath);
    keyNotesResult = parseKeyNotes(keyNotesText);
  }

  if (!args.keyOnly) {
    const logsPath = path.join(weeklyDir, 'logs.md');
    const logsText = readFileUtf8(logsPath);
    logsResult = parseLogs(logsText);
  }

  const output = args.json
    ? formatJson(weekRange, keyNotesResult, logsResult)
    : formatMarkdown(weekRange, keyNotesResult, logsResult);

  if (args.output) {
    fs.writeFileSync(args.output, output, 'utf8');
    console.error(`Saved to: ${args.output}`);
  } else {
    console.log(output);
  }
}

main();
