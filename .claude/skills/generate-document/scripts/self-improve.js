#!/usr/bin/env node

/**
 * self-improve
 *
 * Self-improvement engine: analyzes execution memory + orchestration logs + key nodes,
 * identifies recurring failure modes, checklist gaps, agent effectiveness issues, rule friction points,
 * outputs structured improvement proposal Markdown.
 *
 * Usage:
 *   node scripts/self-improve.js [--since <YYYY-MM-DD>] [--output <path>] [--json]
 *
 * Options:
 *   --since <date>   Analysis start date (default: this Monday)
 *   --output <path>  Save to file (default: stdout)
 *   --json           Output JSON (default: Markdown)
 */

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const { execSync } = require('child_process');
const { getNaturalWeekRange } = require('./natural-week.js');

const SCRIPT_DIR = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '../../..');
const MEMORY_FILE = path.join(REPO_ROOT, 'docs', '.memory', 'execution-memory.jsonl');

function printHelp() {
  console.log(`Usage:
  node scripts/self-improve.js [--since <YYYY-MM-DD>] [--output <path>] [--json]

Options:
  --since <date>   Analysis start date (default: this Monday)
  --output <path>  Save to file (default: stdout)
  --json           Output JSON (default: Markdown)

Examples:
  node scripts/self-improve.js
  node scripts/self-improve.js --since 2026-04-27 --output docs/weekly/2026-04-27~2026-05-03/self-improve-proposal.md
`);
}

function parseArgs(argv) {
  const out = { since: null, output: null, json: false };
  const args = argv.slice(2);
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--help' || a === '-h') { printHelp(); process.exit(0); }
    else if (a === '--since') out.since = args[++i];
    else if (a === '--output') out.output = args[++i];
    else if (a === '--json') out.json = true;
  }
  return out;
}

function getDefaultSince() {
  const now = new Date();
  const day = now.getDay();
  const diff = now.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(now.setDate(diff));
  return monday.toISOString().slice(0, 10);
}

async function readExecutionMemory(sinceDate) {
  const since = new Date(sinceDate + 'T00:00:00.000Z').getTime();
  try {
    const text = await fsp.readFile(MEMORY_FILE, 'utf8');
    return text.split('\n').filter(l => l.trim()).map(l => {
      try { return JSON.parse(l); } catch { return null; }
    }).filter(r => r && new Date(r.timestamp || 0).getTime() >= since);
  } catch {
    return [];
  }
}

async function readWeeklyLogs(weekRange) {
  const logsDir = path.join(REPO_ROOT, 'docs', 'weekly', weekRange);
  const logsPath = path.join(logsDir, 'logs.md');
  const keysPath = path.join(logsDir, 'key-notes.md');
  const logs = { logs: '', keys: '' };
  try { logs.logs = await fsp.readFile(logsPath, 'utf8'); } catch { /* ignore */ }
  try { logs.keys = await fsp.readFile(keysPath, 'utf8'); } catch { /* ignore */ }
  return logs;
}

function analyzePatterns(records) {
  const patterns = {
    recurringDocTypeIssues: {},
    recurringSectionIssues: {},
    agentBadCaseFreq: {},
    changeLevelAccuracy: { correct: 0, total: 0 },
    highRiskFeatures: [],
    checklistGaps: new Set(),
  };

  records.forEach(r => {
    // Change level prediction accuracy
    if (r.planned_change_level && r.actual_change_level) {
      patterns.changeLevelAccuracy.total++;
      if (r.planned_change_level === r.actual_change_level) patterns.changeLevelAccuracy.correct++;
    }

    // Quality issue patterns
    ['P0', 'P1'].forEach(lv => {
      (r.quality_issues?.[lv] || []).forEach(q => {
        const docKey = `${q.doc_type || 'unknown'}::${q.section || 'unknown'}`;
        const secKey = `${q.section || 'unknown'}::${q.issue || 'unknown'}`;
        patterns.recurringDocTypeIssues[docKey] = (patterns.recurringDocTypeIssues[docKey] || 0) + (lv === 'P0' ? 3 : 1);
        patterns.recurringSectionIssues[secKey] = (patterns.recurringSectionIssues[secKey] || 0) + (lv === 'P0' ? 3 : 1);
        patterns.checklistGaps.add(JSON.stringify({ section: q.section, issue: q.issue, doc_type: q.doc_type, level: lv }));
      });
    });

    // Agent bad case frequency
    (r.bad_cases || []).forEach(b => {
      const key = b.agent;
      patterns.agentBadCaseFreq[key] = (patterns.agentBadCaseFreq[key] || 0) + 1;
    });

    // High-risk features (many P0s or blocked)
    const p0Count = r.quality_issues?.P0?.length || 0;
    if (p0Count >= 2 || r.was_blocked) {
      patterns.highRiskFeatures.push({ feature: r.feature, p0: p0Count, blocked: r.was_blocked, reason: r.block_reason });
    }
  });

  return patterns;
}

function generateProposals(patterns, records, sinceDate, weekRange) {
  const proposals = [];

  // 1. Checklist gap proposals
  const topDocIssues = Object.entries(patterns.recurringDocTypeIssues)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);
  if (topDocIssues.length > 0) {
    topDocIssues.forEach(([key, score]) => {
      const [docType, section] = key.split('::');
      const evidence = records.filter(r =>
        (r.quality_issues?.P0 || []).some(q => (q.doc_type || '').includes(docType) && (q.section || '').includes(section))
      ).map(r => r.feature);
      proposals.push({
        type: 'checklist',
        priority: score >= 6 ? 'High' : 'Medium',
        target_file: `skills/generate-document/checklists/${docType.replace(/\.md$/, '')}.md`,
        problem_source: `${docType} ${section} recurring quality issues`,
        description: `Add dedicated P0 checklist items in ${section} to prevent recurring defects`,
        reference_standard: 'Defect prevention: solidifying high-frequency failure points into checklists is a foundational quality assurance practice',
        validation: `In the next 3 similar feature deliveries, P0 issues in this section drop to 0`,
        time_dimension: 'Next week',
        depth: 'Quality assurance',
        evidence: [...new Set(evidence)].slice(0, 3),
      });
    });
  }

  // 2. Agent effectiveness proposals
  const topBadAgents = Object.entries(patterns.agentBadCaseFreq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);
  if (topBadAgents.length > 0) {
    topBadAgents.forEach(([agent, count]) => {
      const lessons = [...new Set(records.flatMap(r =>
        (r.bad_cases || []).filter(b => b.agent === agent).map(b => b.lesson)
      ))].slice(0, 3);
      proposals.push({
        type: 'agent',
        priority: count >= 3 ? 'High' : 'Medium',
        target_file: `agents/${agent}.md`,
        problem_source: `${agent} produced ${count} bad cases`,
        description: `Add dedicated review dimensions in ${agent} constraints or required answers for: ${lessons.join('; ')}`,
        reference_standard: 'Expert role continuous evolution: updating review dimensions based on historical error patterns is key to high-quality agent design',
        validation: `Bad case rate for this agent drops 50% over the next 5 invocations`,
        time_dimension: 'This month',
        depth: 'Quality assurance',
        evidence: lessons,
      });
    });
  }

  // 3. Change level prediction proposals
  if (patterns.changeLevelAccuracy.total >= 3) {
    const rate = patterns.changeLevelAccuracy.correct / patterns.changeLevelAccuracy.total;
    if (rate < 0.7) {
      proposals.push({
        type: 'rule',
        priority: 'High',
        target_file: 'skills/generate-document/rules/workflow.md',
        problem_source: `Change level prediction accuracy only ${(rate * 100).toFixed(0)}% (${patterns.changeLevelAccuracy.correct}/${patterns.changeLevelAccuracy.total})`,
        description: 'Strengthen Step 0 (doc-planner) change level determination criteria, add historical similar case comparison dimensions',
        reference_standard: 'Case-based reasoning (CBR): using historical data to assist classification decisions reduces subjective judgment bias',
        validation: 'Prediction accuracy improves to above 80%',
        time_dimension: 'This month',
        depth: 'Process efficiency',
        evidence: [`Accuracy ${(rate * 100).toFixed(0)}%`],
      });
    }
  }

  // 4. High-risk feature early warning proposals
  if (patterns.highRiskFeatures.length > 0) {
    const domains = [...new Set(patterns.highRiskFeatures.map(f => f.feature))];
    proposals.push({
      type: 'system',
      priority: 'Medium',
      target_file: 'skills/generate-document/scripts/execution-memory.js',
      problem_source: `${patterns.highRiskFeatures.length} features had multiple P0 issues or were blocked`,
      description: 'Add automatic high-risk feature tagging to execution-memory, prioritize warnings when doc-planner queries',
      reference_standard: 'Risk-driven testing: increasing review intensity for historically high-risk modules is a common quality assurance practice',
      validation: 'P0 issue count for high-risk features drops 50% in subsequent deliveries',
      time_dimension: 'Next week',
      depth: 'Process efficiency',
      evidence: domains.slice(0, 3),
    });
  }

  // 5. If no records, prompt initialization
  if (records.length === 0) {
    proposals.push({
      type: 'system',
      priority: 'High',
      target_file: 'skills/generate-document/scripts/execution-memory.js',
      problem_source: 'Execution memory is empty, cannot perform improvement analysis',
      description: 'As feature documents are continuously delivered, execution memory will automatically accumulate data; the self-improve engine will output valid proposals once data is available',
      reference_standard: 'Data-driven improvement: the improvement engine depends on real execution data; empty data prompt is normal',
      validation: 'Re-run after completing 3+ feature document deliveries',
      time_dimension: 'Next week',
      depth: 'Process efficiency',
      evidence: [],
    });
  }

  // Sort: high priority first, same priority stable by type
  const order = { 'High': 0, 'Medium': 1, 'Low': 2 };
  proposals.sort((a, b) => (order[a.priority] || 2) - (order[b.priority] || 2));

  return proposals;
}

function formatMarkdown(proposals, records, sinceDate, weekRange) {
  const lines = [];
  lines.push('# System Self-Improvement Proposals');
  lines.push('');
  lines.push(`> **Analysis period**: ${sinceDate} to present`);
  lines.push(`> **Data sources**: execution-memory (${records.length} records) + orchestration logs + key nodes`);
  lines.push(`> **Generated at**: ${new Date().toISOString()}`);
  lines.push('');

  if (records.length === 0) {
    lines.push('> No execution memory records yet. As feature documents accumulate, this engine will automatically identify improvement opportunities.');
    lines.push('');
  }

  lines.push('## Problem Pattern Summary');
  lines.push('');

  const docIssues = Object.entries(analyzePatterns(records).recurringDocTypeIssues)
    .sort((a, b) => b[1] - a[1]).slice(0, 5);
  if (docIssues.length > 0) {
    lines.push('### High-Frequency Document Quality Issues');
    docIssues.forEach(([k, v]) => lines.push(`- ${k}: weighted ${v} times`));
    lines.push('');
  }

  const agentBad = Object.entries(analyzePatterns(records).agentBadCaseFreq)
    .sort((a, b) => b[1] - a[1]).slice(0, 5);
  if (agentBad.length > 0) {
    lines.push('### High-Frequency Agent Bad Cases');
    agentBad.forEach(([k, v]) => lines.push(`- ${k}: ${v} times`));
    lines.push('');
  }

  lines.push('---');
  lines.push('');
  lines.push('## Improvement Proposal Summary');
  lines.push('');
  lines.push('| Priority | Type | Problem Source | Improvement Description | Target File | Reference Standard | Validation Method | Time Horizon | Depth |');
  lines.push('|----------|------|----------------|-------------------------|-------------|--------------------|-------------------|--------------|-------|');

  proposals.forEach(p => {
    const desc = p.description.replace(/\|/g, '\\|').replace(/\n/g, ' ');
    const source = p.problem_source.replace(/\|/g, '\\|');
    const target = p.target_file.replace(/\|/g, '\\|');
    const ref = p.reference_standard.replace(/\|/g, '\\|');
    const val = p.validation.replace(/\|/g, '\\|');
    lines.push(`| ${p.priority} | ${p.type} | ${source} | ${desc} | ${target} | ${ref} | ${val} | ${p.time_dimension} | ${p.depth} |`);
  });

  lines.push('');
  lines.push('## Detailed Proposals');
  lines.push('');

  proposals.forEach((p, i) => {
    lines.push(`### ${i + 1}. [${p.priority}] ${p.type} — ${p.problem_source}`);
    lines.push('');
    lines.push(`- **Target file**: ${p.target_file}`);
    lines.push(`- **Improvement description**: ${p.description}`);
    lines.push(`- **Reference standard**: ${p.reference_standard}`);
    lines.push(`- **Validation method**: ${p.validation}`);
    lines.push(`- **Time horizon**: ${p.time_dimension}`);
    lines.push(`- **Depth**: ${p.depth}`);
    if (p.evidence && p.evidence.length > 0) {
      lines.push(`- **Evidence**: ${p.evidence.join(', ')}`);
    }
    lines.push('');
  });

  lines.push('---');
  lines.push('');
  lines.push('## Execution Recommendations');
  lines.push('');
  lines.push('1. Review proposals from high to low priority');
  lines.push('2. Each proposal must be manually confirmed before editing the target file (self-improve engine does not auto-overwrite)');
  lines.push('3. After modification, observe validation metric changes in the next generate-document round');
  lines.push('4. This proposal auto-updates when running `/generate-document weekly` each week');
  lines.push('');

  return lines.join('\n');
}

async function main() {
  const opts = parseArgs(process.argv);
  const since = opts.since || getDefaultSince();
  const week = getNaturalWeekRange(new Date());

  const records = await readExecutionMemory(since);
  const logs = await readWeeklyLogs(week.range);

  // Also incorporate bad cases and lessons from logs (simple extraction)
  const logBadCases = [];
  if (logs.logs) {
    const badMatches = logs.logs.matchAll(/bad case[\s\S]*?Follow-up[：:]\s*(.+?)(?=\n|$)/gi);
    for (const m of badMatches) {
      logBadCases.push(m[1].trim());
    }
  }

  const patterns = analyzePatterns(records);
  const proposals = generateProposals(patterns, records, since, week.range);

  if (opts.json) {
    const out = { since, week: week.range, record_count: records.length, log_bad_cases: logBadCases, proposals };
    const text = JSON.stringify(out, null, 2);
    if (opts.output) {
      await fsp.writeFile(opts.output, text, 'utf8');
      console.log(`✓ Saved to ${opts.output}`);
    } else {
      console.log(text);
    }
    return;
  }

  const md = formatMarkdown(proposals, records, since, week.range);
  if (opts.output) {
    await fsp.mkdir(path.dirname(opts.output), { recursive: true });
    await fsp.writeFile(opts.output, md, 'utf8');
    console.log(`✓ Saved to ${opts.output}`);
  } else {
    console.log(md);
  }
}

main().catch(err => { console.error(err); process.exit(1); });
