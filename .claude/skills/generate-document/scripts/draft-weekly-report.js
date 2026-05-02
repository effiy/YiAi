#!/usr/bin/env node

/**
 * draft-weekly-report
 *
 * Goal: integrate collect-weekly-kpi.js output with the weekly-analyzer framework,
 * generating a semi-automated weekly report draft markdown, reducing manual collation effort.
 *
 * Usage:
 *   node scripts/draft-weekly-report.js [--week <YYYY-MM-DD>] [--output <path>]
 *
 * Options:
 *   --week <date>   Specify a date, automatically mapped to its natural week (default: today)
 *   --output <path> Save to file (default: stdout)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { getNaturalWeekRange } = require('./natural-week.js');

const SCRIPT_DIR = path.dirname(__filename);

function parseArgs(argv) {
  const out = { week: null, output: null };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') {
      console.log(`Usage:
  node scripts/draft-weekly-report.js [--week <YYYY-MM-DD>] [--output <path>]

Options:
  --week <date>   Specify a date, automatically mapped to its natural week (default: today)
  --output <path> Save to file (default: stdout)

Examples:
  node scripts/draft-weekly-report.js
  node scripts/draft-weekly-report.js --week 2026-04-29 --output docs/weekly/2026-04-27~2026-05-03/weekly-report.md
`);
      process.exit(0);
    } else if (a === '--week') out.week = argv[++i];
    else if (a === '--output') out.output = argv[++i];
  }
  return out;
}

function safeExec(cmd, defaultVal = '') {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();
  } catch {
    return defaultVal;
  }
}

function runCollectKPI(week) {
  const script = path.join(SCRIPT_DIR, 'collect-weekly-kpi.js');
  const weekArg = week ? `--week ${week}` : '';
  try {
    const out = execSync(`node "${script}" ${weekArg} --json`, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
    }).trim();
    return JSON.parse(out);
  } catch (err) {
    console.error(`Warning: collect-weekly-kpi.js execution failed: ${err.message}`);
    return null;
  }
}

function runCollectLogs(week) {
  const script = path.join(SCRIPT_DIR, 'collect-weekly-logs.js');
  const weekArg = week ? `--week ${week}` : '';
  try {
    const out = execSync(`node "${script}" ${weekArg}`, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
    }).trim();
    return JSON.parse(out);
  } catch {
    return null;
  }
}

function runSelfImprove(weekRange) {
  const script = path.join(SCRIPT_DIR, 'self-improve.js');
  const since = weekRange.start;
  try {
    const out = execSync(`node "${script}" --since ${since} --json`, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
    }).trim();
    const data = JSON.parse(out);
    if (!data.proposals || data.proposals.length === 0) {
      return '\n---\n\n## System Self-Improvement Proposals\n\n> No execution memory records yet; improvement proposals will auto-generate once data accumulates.';
    }
    const lines = [];
    lines.push('---');
    lines.push('');
    lines.push('## System Self-Improvement Proposals');
    lines.push('');
    lines.push(`> **Data source**: execution-memory (${data.record_count} records) + orchestration logs + key nodes`);
    lines.push(`> **Analysis period**: ${data.since} to present`);
    lines.push('');
    lines.push('| Priority | Type | Problem Source | Improvement Description | Target File | Validation Method | Time Horizon | Depth |');
    lines.push('|----------|------|----------------|-------------------------|-------------|-------------------|--------------|-------|');
    data.proposals.forEach((p) => {
      const desc = p.description.replace(/\|/g, '\\|').replace(/\n/g, ' ');
      const source = p.problem_source.replace(/\|/g, '\\|');
      const target = p.target_file.replace(/\|/g, '\\|');
      const val = p.validation.replace(/\|/g, '\\|');
      lines.push(`| ${p.priority} | ${p.type} | ${source} | ${desc} | ${target} | ${val} | ${p.time_dimension} | ${p.depth} |`);
    });
    lines.push('');
    lines.push('> **Execution recommendation**: Review proposals from high to low priority, confirm manually before editing target files, then observe validation metrics in the next delivery round.');
    return lines.join('\n');
  } catch {
    return '\n---\n\n## System Self-Improvement Proposals\n\n> Self-improve engine failed; investigate and trigger manually.';
  }
}

function analyzeGitCommits(weekRange) {
  const since = `${weekRange.start}T00:00:00`;
  const until = `${weekRange.end}T23:59:59`;

  // Categorize commits by type
  const featCommits = safeExec(
    `git log --since="${since}" --until="${until}" --oneline --grep="^feat" | head -20`,
    ''
  );
  const fixCommits = safeExec(
    `git log --since="${since}" --until="${until}" --oneline --grep="^fix" | head -10`,
    ''
  );
  const refactorCommits = safeExec(
    `git log --since="${since}" --until="${until}" --oneline --grep="^refactor" | head -10`,
    ''
  );

  // Most changed files
  const topFiles = safeExec(
    `git log --since="${since}" --until="${until}" --name-only --pretty=format: | grep -v '^$' | sort | uniq -c | sort -rn | head -10`,
    ''
  );

  return {
    featList: featCommits.split('\n').filter(Boolean),
    fixList: fixCommits.split('\n').filter(Boolean),
    refactorList: refactorCommits.split('\n').filter(Boolean),
    topFiles: topFiles.split('\n').filter(Boolean),
  };
}

function generateHighlights(gitAnalysis, kpiData) {
  const highlights = [];

  // Extract highlights from feat commits
  gitAnalysis.featList.slice(0, 3).forEach((line) => {
    const msg = line.replace(/^\S+\s+/, '');
    if (msg) highlights.push(`New feature / capability: ${msg}`);
  });

  // Extract highlights from refactor commits
  gitAnalysis.refactorList.slice(0, 2).forEach((line) => {
    const msg = line.replace(/^\S+\s+/, '');
    if (msg) highlights.push(`Architecture / rule optimization: ${msg}`);
  });

  // Extract highlights from Git stats
  if (kpiData?.git) {
    const g = kpiData.git;
    if (g.commitCount > 20) {
      highlights.push(`High-frequency iteration: ${g.commitCount} commits this week, ${g.filesChanged} files changed`);
    }
    if (g.authors.length > 1) {
      highlights.push(`Multi-person collaboration: ${g.authors.length} contributors`);
    }
  }

  return highlights.length > 0 ? highlights : ['This week focused on rule optimization and document iteration'];
}

function generateProblems(gitAnalysis, kpiData) {
  const problems = [];

  // Extract problems from fix commits
  gitAnalysis.fixList.slice(0, 3).forEach((line) => {
    const msg = line.replace(/^\S+\s+/, '');
    if (msg) problems.push(`Fixed issue: ${msg}`);
  });

  // Extract problems from KPI data
  if (kpiData?.features) {
    const weakFeatures = kpiData.features.filter((f) => {
      return (f.deliveryRate !== null && f.deliveryRate < 80) ||
             (f.p0Rate !== null && f.p0Rate < 90) ||
             (f.fixRounds !== null && f.fixRounds > 2);
    });
    weakFeatures.forEach((f) => {
      problems.push(`Feature "${f.featureName}" KPI weak: delivery ${f.deliveryRate ?? '—'}%/P0 ${f.p0Rate ?? '—'}%/rounds ${f.fixRounds ?? '—'}`);
    });
  }

  // No feature directories
  if (kpiData?.features?.length === 0) {
    problems.push('No feature-level delivery this week; work focused on collaborative rule iteration, KPI cannot be measured by feature dimension');
  }

  return problems.length > 0 ? problems : ['No significant issues found this week'];
}

function generatePlanning(kpiData, gitAnalysis) {
  const plans = [];

  // Generate plans based on weak KPI
  if (kpiData?.features) {
    const weakest = kpiData.features
      .filter((f) => f.deliveryRate !== null || f.p0Rate !== null)
      .sort((a, b) => {
        const scoreA = (a.deliveryRate || 100) + (a.p0Rate || 100) - (a.fixRounds || 0) * 10;
        const scoreB = (b.deliveryRate || 100) + (b.p0Rate || 100) - (b.fixRounds || 0) * 10;
        return scoreA - scoreB;
      })[0];

    if (weakest) {
      plans.push({
        type: 'Project',
        source: `Weak KPI: ${weakest.featureName}`,
        desc: `Improve "${weakest.featureName}" delivery quality, target delivery rate ≥80%, P0 pass rate ≥90%`,
        standard: 'User-story-driven development, closed-loop validation from requirement to acceptance',
        verify: `Delivery rate ≥80% and P0 pass rate ≥90%, evidence paths: ${weakest.evidencePaths.join(', ')}`,
        time: 'Next week',
        depth: 'Quality assurance',
      });
    }
  }

  // Generate plans based on commit distribution
  if (gitAnalysis.featList.length === 0 && gitAnalysis.refactorList.length > 10) {
    plans.push({
      type: 'System',
      source: 'Work rhythm imbalance',
      desc: 'Break large tasks into daily-completable subtasks, establish a stable iteration rhythm',
      standard: 'Daily standup rhythm, small batches frequent commits',
      verify: 'At least 1 meaningful commit per day this week, evenly distributed commit times',
      time: 'This week',
      depth: 'Team collaboration',
    });
  }

  // No feature directories
  if (!kpiData?.features || kpiData.features.length === 0) {
    plans.push({
      type: 'System',
      source: 'No feature-level delivery',
      desc: 'Select one minimal feature scenario each for generate-document and implement-code, produce a complete document set as pilot',
      standard: 'User-story-driven development, validate rule effectiveness',
      verify: 'Produce at least 1 complete feature directory (01-07) and complete code implementation',
      time: 'Next week',
      depth: 'Process efficiency',
    });
  }

  return plans;
}

function generateReport(weekRange, kpiData, logsData, gitAnalysis) {
  const lines = [];
  const today = new Date().toISOString().split('T')[0];

  lines.push(`# Weekly Report ${weekRange.range}`);
  lines.push('');
  lines.push(`> **Version**: v1.0  `);
  lines.push(`> **Maintainer**: Claude  `);
  lines.push(`> **Coverage period**: ${weekRange.start} (Mon) ~ ${weekRange.end} (Sun)  `);
  lines.push(`> **Generated at**: ${today}`);
  lines.push('');

  // Related feature directories
  lines.push('## Related Feature Directories');
  lines.push('');
  if (kpiData?.features && kpiData.features.length > 0) {
    kpiData.features.forEach((f) => {
      lines.push(`- \`docs/${f.featureName}/\``);
    });
  } else {
    lines.push('> No active feature directories this week (no feature document sets under `docs/`)');
  }
  lines.push('');

  // KPI quantitative summary
  lines.push('## KPI Quantitative Summary');
  lines.push('');
  if (kpiData?.features && kpiData.features.length > 0) {
    lines.push(`| Feature Directory | Delivery Rate | P0 Pass Rate | Anti-Hallucination | Fix Rounds | Rule Coverage | Overall |`);
    lines.push(`|-------------------|---------------|--------------|--------------------|------------|---------------|---------|`);
    for (const f of kpiData.features) {
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
      lines.push(`| ${f.featureName} | ${dr} | ${p0} | ${ah} | ${fr} | ${rc} | ${overall} |`);
    }
    lines.push('');
    lines.push('**Criteria**: delivery ≥80% ✅ | P0 ≥90% ✅ | rounds ≤2 ✅');
  } else {
    lines.push('> No feature-level delivery this week; standard feature-dimension KPI not applicable.');
  }
  lines.push('');

  // Git statistics
  if (kpiData?.git) {
    const g = kpiData.git;
    lines.push('### Git Statistics');
    lines.push('');
    lines.push(`| Metric | Value |`);
    lines.push(`|--------|-------|`);
    lines.push(`| Commits | ${g.commitCount} |`);
    lines.push(`| Files changed | ${g.filesChanged} |`);
    lines.push(`| Insertions | ${g.insertions} |`);
    lines.push(`| Deletions | ${g.deletions} |`);
    lines.push('');
    if (g.authors.length > 0) {
      lines.push('**Contributor distribution**: ' + g.authors.map((a) => `${a.name}(${a.commits})`).join(', '));
      lines.push('');
    }
  }

  // This week retrospective
  lines.push('## This Week Retrospective');
  lines.push('');

  const highlights = generateHighlights(gitAnalysis, kpiData);
  lines.push('### Progress Highlights');
  lines.push('');
  highlights.forEach((h, i) => lines.push(`${i + 1}. ${h}`));
  lines.push('');

  const problems = generateProblems(gitAnalysis, kpiData);
  lines.push('### Root Cause Analysis');
  lines.push('');
  lines.push('| Symptom | Inference | Evidence Path |');
  lines.push('|---------|-----------|---------------|');
  problems.forEach((p) => {
    lines.push(`| ${p} | TBD | git log / collect-weekly-kpi.js output |`);
  });
  if (problems.length === 0 || problems[0] === 'No significant issues found this week') {
    lines.push('| No significant issues this week | — | — |');
  }
  lines.push('');

  // KPI → retrospective → planning chain
  lines.push('## KPI → Retrospective → Planning Chain Overview');
  lines.push('');
  lines.push('```mermaid');
  lines.push('flowchart LR');
  lines.push('    A["KPI Analysis"] --> B["Retrospective Root Cause"] --> C["Future Planning"]');
  lines.push('```');
  lines.push('');

  // Future planning and improvements
  lines.push('## Future Planning and Improvements');
  lines.push('');
  lines.push('**Principle**: Demand-driven, reference industry standards but do not apply complex methodologies blindly.');
  lines.push('');

  const plans = generatePlanning(kpiData, gitAnalysis);
  if (plans.length > 0) {
    lines.push('### Improvement Priority Summary');
    lines.push('');
    lines.push(`| Type | Problem Source | Improvement Description | Reference Standard | Validation Method | Time Horizon | Depth |`);
    lines.push(`|------|----------------|-------------------------|--------------------|-------------------|--------------|-------|`);
    plans.forEach((p) => {
      lines.push(`| ${p.type} | ${p.source} | ${p.desc} | ${p.standard} | ${p.verify} | ${p.time} | ${p.depth} |`);
    });
    lines.push('');
  } else {
    lines.push('> Insufficient data to generate specific improvement items this week; TBD.');
    lines.push('');
  }

  // Workflow standardization review (placeholder)
  lines.push('### Workflow Standardization Review');
  lines.push('');
  lines.push('1. **Repetitive labor identification**: TBD');
  lines.push('2. **Decision criteria gaps**: TBD');
  lines.push('3. **Information silos**: TBD');
  lines.push('4. **Feedback loop**: TBD');
  lines.push('');

  // System architecture evolution (placeholder)
  lines.push('### System Architecture Evolution');
  lines.push('');
  lines.push('> Fill only when there is architecture-related delivery this week.');
  lines.push('');

  // AI chain quality statistics (placeholder)
  lines.push('## AI Chain Quality Statistics');
  lines.push('');
  lines.push(`| Dimension | Value | Notes |`);
  lines.push(`|-----------|-------|-------|`);
  lines.push(`| Agent invocations | TBD | |`);
  lines.push(`| Document generation rounds | TBD | |`);
  lines.push(`| P0 issues | TBD | |`);
  lines.push(`| Fix rounds | TBD | |`);
  lines.push('');

  // Anti-hallucination disclaimer
  lines.push('> **Anti-Hallucination Disclaimer**: KPI values are auto-extracted by `collect-weekly-kpi.js`; Git stats come from `git log`; retrospective highlights and problems are auto-inferred from commit categorization; planning suggestions are auto-generated from weak KPIs. Manual supplement items are marked "TBD".');
  lines.push('');

  return lines.join('\n');
}

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

  // 1. Collect KPI data
  const kpiData = runCollectKPI(args.week);

  // 2. Collect log data (optional)
  const logsData = runCollectLogs(args.week);

  // 3. Analyze Git commits
  const gitAnalysis = analyzeGitCommits(weekRange);

  // 4. Generate weekly report draft
  let report = generateReport(weekRange, kpiData, logsData, gitAnalysis);

  // 5. Trigger self-improvement engine and append to report
  const selfImproveOutput = runSelfImprove(weekRange);
  if (selfImproveOutput) {
    report += '\n\n' + selfImproveOutput;
  }

  if (args.output) {
    const dir = path.dirname(args.output);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(args.output, report, 'utf8');
    console.error(`Weekly report draft saved to: ${args.output}`);
  } else {
    console.log(report);
  }
}

main();
