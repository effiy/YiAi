#!/usr/bin/env node

/**
 * collect-weekly-kpi
 *
 * Goal: automatically scan docs/<feature>/ directories, extracting five KPI dimensions
 * from 05_dynamic-checklist.md, 06_process-summary.md, 07_project-report.md,
 * plus Git statistics, producing a structured KPI summary.
 *
 * Usage:
 *   node scripts/collect-weekly-kpi.js [--week <YYYY-MM-DD>] [--json] [--output <path>]
 *
 * Options:
 *   --week <date>   Specify a date, automatically mapped to its natural week (default: today)
 *   --json          Output JSON format (default: Markdown)
 *   --output <path> Save to file (default: stdout)
 *   --git-only      Output Git stats only, skip docs/ scan
 *   --docs-only     Output docs/ KPI summary only, skip Git stats
 *   --with-logs     Also output key nodes and orchestration log summary (calls collect-weekly-logs.js)
 *   --with-memory   Also output execution memory stats (new records this week, top 3 issue patterns)
 *
 * Exit codes:
 *   0 success
 *   1 runtime error
 *   2 argument error
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { getNaturalWeekRange } = require('./natural-week.js');

const REPO_ROOT = path.resolve(__dirname, '../../..');
const DOCS_DIR = path.join(REPO_ROOT, 'docs');
const KPI_FILES = ['05_dynamic-checklist.md', '06_process-summary.md', '07_project-report.md'];

function printHelp(stream) {
  const out = stream || process.stdout;
  out.write(`Usage:
  node scripts/collect-weekly-kpi.js [--week <YYYY-MM-DD>] [--json] [--output <path>]

Options:
  --week <date>   Specify a date, automatically mapped to its natural week (default: today)
  --json          Output JSON format (default: Markdown)
  --output <path> Save to file (default: stdout)
  --git-only      Output Git stats only
  --docs-only     Output docs/ KPI summary only
  --with-logs     Also output key nodes and orchestration log summary
  --with-memory   Also output execution memory stats

Examples:
  node scripts/collect-weekly-kpi.js
  node scripts/collect-weekly-kpi.js --week 2026-04-29 --json --output /tmp/kpi.json
`);
}

function usage() {
  printHelp(process.stderr);
  process.exit(2);
}

function parseArgs(argv) {
  const out = { week: null, json: false, output: null, gitOnly: false, docsOnly: false, withLogs: false, withMemory: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') {
      printHelp();
      process.exit(0);
    }
    else if (a === '--week') out.week = argv[++i];
    else if (a === '--json') out.json = true;
    else if (a === '--output') out.output = argv[++i];
    else if (a === '--git-only') out.gitOnly = true;
    else if (a === '--docs-only') out.docsOnly = true;
    else if (a === '--with-logs') out.withLogs = true;
    else if (a === '--with-memory') out.withMemory = true;
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

function safeExec(cmd, defaultVal = '') {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();
  } catch {
    return defaultVal;
  }
}

// ---------- Text extractors ----------

function extractPercent(text, keywords) {
  for (const kw of keywords) {
    const re = new RegExp(`${kw}\\s*[:：]\\s*([0-9]+)\\s*%`, 'i');
    const m = text.match(re);
    if (m) return parseInt(m[1], 10);
  }
  return null;
}

function extractNumber(text, keywords) {
  for (const kw of keywords) {
    const re = new RegExp(`${kw}\\s*[:：]\\s*([0-9]+)`, 'i');
    const m = text.match(re);
    if (m) return parseInt(m[1], 10);
  }
  return null;
}

function countChecklistItems(text) {
  const total = (text.match(/^\\s*[-*]\\s+/gm) || []).length;
  const passed = (text.match(/^\\s*[-*]\\s*.*[✅√]/gm) || []).length;
  return { total: Math.max(total, 0), passed: Math.max(passed, 0) };
}

function countP0Items(text) {
  const lines = text.split(/\r?\n/);
  let inP0 = false;
  let total = 0;
  let passed = 0;
  for (const line of lines) {
    const h = line.match(/^#{2,4}\\s*P0/i);
    if (h) {
      inP0 = true;
      continue;
    }
    const nextH = line.match(/^#{2,4}\\s/);
    if (nextH && !line.match(/^#{2,4}\\s*P0/i)) {
      inP0 = false;
      continue;
    }
    if (inP0 && line.match(/^\\s*[-*]\\s+/)) {
      total++;
      if (line.match(/[✅√]/)) passed++;
    }
  }
  return { total, passed };
}

// ---------- KPI scan ----------

function scanFeatureKPI(featureDir) {
  const featureName = path.basename(featureDir);
  const files = {};
  KPI_FILES.forEach((f) => {
    const p = path.join(featureDir, f);
    files[f] = readFileUtf8(p);
  });

  const checklistText = files['05_dynamic-checklist.md'] || '';
  const summaryText = files['06_process-summary.md'] || '';
  const reportText = files['07_project-report.md'] || '';
  const allText = [checklistText, summaryText, reportText].join('\n');

  // P0 pass rate
  const p0 = countP0Items(checklistText);
  let p0Rate = p0.total > 0 ? Math.round((p0.passed / p0.total) * 100) : null;

  // Delivery completion rate (bilingual for backward compatibility)
  let deliveryRate = extractPercent(allText, [
    'delivery completion rate', 'completion rate', 'delivery rate',
    '交付完成率', '完成率', '交付率'
  ]);

  // Anti-hallucination rate (bilingual)
  let antiHallucinationRate = extractPercent(allText, [
    'anti-hallucination rate', 'hallucination prevention rate', 'hallucination rate',
    '防幻觉率', '防幻觉', '幻觉率'
  ]);

  // Fix rounds (bilingual)
  let fixRounds = extractNumber(allText, [
    'fix rounds', 'revision rounds', 'iterations',
    '修复轮次', '迭代轮次', '修改轮次', '轮次'
  ]);

  // Rule coverage: from checklist statistics
  const checklistTotal = (checklistText.match(/^\s*[-*]\s+/gm) || []).length;
  let ruleCoverage = null;
  if (checklistTotal > 0) {
    const ruleItems = (checklistText.match(/^\s*[-*]\s*.*(?:rule|规则)/gm) || []).length;
    ruleCoverage = Math.round((ruleItems / checklistTotal) * 100);
  }

  // Evidence paths (existing files)
  const evidencePaths = KPI_FILES.filter((f) => files[f] !== null).map((f) => `docs/${featureName}/${f}`);

  return {
    featureName,
    deliveryRate,
    p0Rate,
    antiHallucinationRate,
    fixRounds,
    ruleCoverage,
    p0Details: p0,
    evidencePaths,
    hasData: evidencePaths.length > 0,
  };
}

function scanAllFeatures() {
  if (!fs.existsSync(DOCS_DIR)) {
    return { features: [], note: 'docs/ directory does not exist' };
  }
  const entries = fs.readdirSync(DOCS_DIR, { withFileTypes: true });
  const featureDirs = entries
    .filter((e) => e.isDirectory() && !e.name.startsWith('.') && !e.name.startsWith('weekly') && !e.name.startsWith('99_'))
    .map((e) => path.join(DOCS_DIR, e.name));

  if (featureDirs.length === 0) {
    return { features: [], note: 'No feature directories under docs/' };
  }

  const features = featureDirs.map(scanFeatureKPI).filter((f) => f.hasData);
  if (features.length === 0) {
    return { features: [], note: 'No feature directories with KPI data under docs/ (05/06/07 files all missing)' };
  }
  return { features, note: `Scanned ${features.length} feature directories with KPI data` };
}

// ---------- Git statistics ----------

function collectGitStats(weekRange) {
  const since = weekRange.start;
  const until = weekRange.end;
  const sinceIso = `${since}T00:00:00`;
  const untilIso = `${until}T23:59:59`;

  // Commit count
  const commitCount = safeExec(
    `git log --since="${sinceIso}" --until="${untilIso}" --oneline | wc -l`,
    '0'
  );

  // Use --shortstat to accumulate diff stats per commit this week, avoiding changes from before this week
  let filesChanged = 0;
  let insertions = 0;
  let deletions = 0;

  const shortStatLines = safeExec(
    `git log --since="${sinceIso}" --until="${untilIso}" --shortstat --format=''`,
    ''
  )
    .split('\n')
    .filter(Boolean);

  for (const line of shortStatLines) {
    const m = line.match(/(\d+) files? changed(?:, (\d+) insertions?\(\+\))?(?:, (\d+) deletions?\(-\))?/);
    if (m) {
      filesChanged += parseInt(m[1], 10) || 0;
      insertions += parseInt(m[2], 10) || 0;
      deletions += parseInt(m[3], 10) || 0;
    }
  }

  // Author stats
  const authorLines = safeExec(
    `git log --since="${sinceIso}" --until="${untilIso}" --format='%an' | sort | uniq -c | sort -rn`,
    ''
  );
  const authors = authorLines
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)
    .map((l) => {
      const m = l.match(/^\s*(\d+)\s+(.+)$/);
      return m ? { commits: parseInt(m[1], 10), name: m[2] } : null;
    })
    .filter(Boolean);

  return {
    weekRange,
    commitCount: parseInt(commitCount, 10) || 0,
    filesChanged,
    insertions,
    deletions,
    authors,
  };
}

function collectMemoryStats(weekRange) {
  const memoryScript = path.join(__dirname, 'execution-memory.js');
  const weekArg = `--week ${weekRange.start}`;
  try {
    const out = execSync(`node "${memoryScript}" stats ${weekArg} --json`, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
    }).trim();
    return JSON.parse(out);
  } catch {
    return null;
  }
}

// ---------- Output formatting ----------

function formatMarkdown(featureResult, gitResult, memoryResult) {
  const { features, note } = featureResult;
  const lines = [];

  lines.push(`# KPI Auto-Summary (${gitResult.weekRange.range})`);
  lines.push('');
  lines.push(`> **Generated at**: ${new Date().toISOString()}`);
  lines.push(`> **Data sources**: docs/<feature>/ 05/06/07 files + git log`);
  lines.push('');

  // Git stats
  lines.push('## Git Statistics');
  lines.push('');
  lines.push(`| Metric | Value |`);
  lines.push(`|--------|-------|`);
  lines.push(`| Commits | ${gitResult.commitCount} |`);
  lines.push(`| Files changed | ${gitResult.filesChanged} |`);
  lines.push(`| Insertions | ${gitResult.insertions} |`);
  lines.push(`| Deletions | ${gitResult.deletions} |`);
  lines.push('');
  if (gitResult.authors.length > 0) {
    lines.push('**Contributor distribution**: ' + gitResult.authors.map((a) => `${a.name}(${a.commits})`).join(', '));
    lines.push('');
  }

  // Feature KPI
  lines.push('## Feature Dimension KPI');
  lines.push('');
  if (features.length === 0) {
    lines.push(`> ${note}`);
    lines.push('');
  } else {
    lines.push(`| Feature / Case | Delivery Rate | P0 Pass Rate | Anti-Hallucination | Fix Rounds | Rule Coverage | Overall |`);
    lines.push(`|----------------|---------------|--------------|--------------------|------------|---------------|---------|`);
    for (const f of features) {
      const dr = f.deliveryRate !== null ? `${f.deliveryRate}%` : '—';
      const p0 = f.p0Rate !== null ? `${f.p0Rate}%` : '—';
      const ah = f.antiHallucinationRate !== null ? `${f.antiHallucinationRate}%` : '—';
      const fr = f.fixRounds !== null ? `${f.fixRounds}` : '—';
      const rc = f.ruleCoverage !== null ? `${f.ruleCoverage}%` : '—';
      let overall = '—';
      if (f.deliveryRate !== null || f.p0Rate !== null) {
        const scores = [
          f.deliveryRate !== null ? (f.deliveryRate >= 80 ? 1 : f.deliveryRate >= 50 ? 0.5 : 0) : null,
          f.p0Rate !== null ? (f.p0Rate >= 90 ? 1 : f.p0Rate >= 70 ? 0.5 : 0) : null,
          f.fixRounds !== null ? (f.fixRounds <= 2 ? 1 : f.fixRounds === 3 ? 0.5 : 0) : null,
        ].filter((v) => v !== null);
        const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0.5;
        overall = avg >= 0.8 ? '✅' : avg >= 0.5 ? '🟡' : '❌';
      }
      lines.push(`| **${f.featureName}** | ${dr} | ${p0} | ${ah} | ${fr} | ${rc} | ${overall} |`);
    }
    lines.push('');
    lines.push('**Dimension criteria**: ✅ ≥80% delivery / ≥90% P0 / ≤2 fix rounds | 🟡 medium range | ❌ below threshold');
    lines.push('');

    // Per-feature details
    lines.push('## Feature Details and Evidence');
    lines.push('');
    for (const f of features) {
      lines.push(`### ${f.featureName}`);
      lines.push('');
      if (f.evidencePaths.length === 0) {
        lines.push('- No document evidence (05/06/07 files do not exist)');
      } else {
        f.evidencePaths.forEach((p) => lines.push(`- ${p}`));
      }
      if (f.p0Details.total > 0) {
        lines.push(`- P0 checklist items: ${f.p0Details.passed}/${f.p0Details.total} passed`);
      }
      lines.push('');
    }
  }

  // Execution memory stats
  if (memoryResult) {
    lines.push('## Execution Memory Statistics');
    lines.push('');
    lines.push(`- **New records this week**: ${memoryResult.total || 0}`);
    lines.push(`- **Blocked count**: ${memoryResult.blocked || 0}`);
    lines.push(`- **Change level distribution**: T1=${memoryResult.changeLevels?.T1 || 0}, T2=${memoryResult.changeLevels?.T2 || 0}, T3=${memoryResult.changeLevels?.T3 || 0}`);
    if (memoryResult.topDocTypeIssues && memoryResult.topDocTypeIssues.length > 0) {
      lines.push('- **Top 3 issue patterns**:');
      memoryResult.topDocTypeIssues.slice(0, 3).forEach(([k, v]) => {
        lines.push(`  - ${k}: ${v} times`);
      });
    }
    lines.push('');
  }

  return lines.join('\n');
}

function formatJson(featureResult, gitResult, memoryResult) {
  return JSON.stringify(
    {
      weekRange: gitResult.weekRange,
      generatedAt: new Date().toISOString(),
      git: {
        commitCount: gitResult.commitCount,
        filesChanged: gitResult.filesChanged,
        insertions: gitResult.insertions,
        deletions: gitResult.deletions,
        authors: gitResult.authors,
      },
      features: featureResult.features,
      note: featureResult.note,
      memory: memoryResult,
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

  let featureResult = { features: [], note: 'Skipped docs/ scan' };
  let gitResult = { weekRange, commitCount: 0, filesChanged: 0, insertions: 0, deletions: 0, authors: [] };
  let memoryResult = null;

  if (!args.gitOnly) {
    featureResult = scanAllFeatures();
  }
  if (!args.docsOnly) {
    gitResult = collectGitStats(weekRange);
  }
  if (args.withMemory) {
    memoryResult = collectMemoryStats(weekRange);
  }

  let output = args.json ? formatJson(featureResult, gitResult, memoryResult) : formatMarkdown(featureResult, gitResult, memoryResult);

  if (args.withLogs) {
    const logsScript = path.join(__dirname, 'collect-weekly-logs.js');
    const weekArg = args.week ? `--week ${args.week}` : '';
    let logsOutput;
    try {
      logsOutput = execSync(`node "${logsScript}" ${weekArg}`, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();
    } catch (err) {
      console.error(`Warning: collect-weekly-logs.js execution failed: ${err.message}`);
      logsOutput = '';
    }
    if (!logsOutput) {
      console.error('Warning: collect-weekly-logs.js output is empty; weekly log file may not exist or parsing failed');
    }
    if (args.json) {
      try {
        const kpiObj = JSON.parse(output);
        const logsObj = logsOutput ? JSON.parse(logsOutput) : {};
        output = JSON.stringify({ ...kpiObj, logs: logsObj }, null, 2);
      } catch {
        output = output + '\n\n/* --- logs --- */\n\n' + (logsOutput || '{}');
      }
    } else {
      output = output + '\n\n---\n\n' + (logsOutput || '> No orchestration log data this week');
    }
  }

  if (args.output) {
    fs.writeFileSync(args.output, output, 'utf8');
    console.error(`Saved to: ${args.output}`);
  } else {
    console.log(output);
  }
}

main();
