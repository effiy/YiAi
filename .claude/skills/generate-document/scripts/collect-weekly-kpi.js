#!/usr/bin/env node

/**
 * collect-weekly-kpi
 *
 * 目标：自动扫描 docs/<功能名>/ 目录，从 05_动态检查清单.md、06_实施总结.md、07_项目报告.md
 * 中提取五个 KPI 维度数据，并汇总 Git 统计，输出结构化 KPI 汇总。
 *
 * 用法：
 *   node scripts/collect-weekly-kpi.js [--week <YYYY-MM-DD>] [--json] [--output <path>]
 *
 * 选项：
 *   --week <date>   指定日期，自动归到其所在自然周（默认今天）
 *   --json          输出 JSON 格式（默认 Markdown）
 *   --output <path> 保存到文件（默认 stdout）
 *   --git-only      仅输出 Git 统计，跳过 docs/ 扫描
 *   --docs-only     仅输出 docs/ KPI 汇总，跳过 Git 统计
 *   --with-logs     同时输出关键节点与编排日志汇总（调用 collect-weekly-logs.js）
 *
 * 退出码：
 *   0 成功
 *   1 运行错误
 *   2 参数错误
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { getNaturalWeekRange } = require('./natural-week.js');

const DOCS_DIR = path.resolve('docs');
const KPI_FILES = ['05_动态检查清单.md', '06_实施总结.md', '07_项目报告.md'];

function printHelp(stream) {
  const out = stream || process.stdout;
  out.write(`用法:
  node scripts/collect-weekly-kpi.js [--week <YYYY-MM-DD>] [--json] [--output <path>]

选项:
  --week <date>   指定日期，自动归到其所在自然周（默认今天）
  --json          输出 JSON 格式（默认 Markdown）
  --output <path> 保存到文件（默认 stdout）
  --git-only      仅输出 Git 统计
  --docs-only     仅输出 docs/ KPI 汇总
  --with-logs     同时输出关键节点与编排日志汇总

示例:
  node scripts/collect-weekly-kpi.js
  node scripts/collect-weekly-kpi.js --week 2026-04-29 --json --output /tmp/kpi.json
`);
}

function usage() {
  printHelp(process.stderr);
  process.exit(2);
}

function parseArgs(argv) {
  const out = { week: null, json: false, output: null, gitOnly: false, docsOnly: false, withLogs: false };
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

// ---------- 文本提取器 ----------

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
  const total = (text.match(/^\s*[-*]\s+/gm) || []).length;
  const passed = (text.match(/^\s*[-*]\s*.*[✅√]/gm) || []).length;
  return { total: Math.max(total, 0), passed: Math.max(passed, 0) };
}

function countP0Items(text) {
  const lines = text.split(/\r?\n/);
  let inP0 = false;
  let total = 0;
  let passed = 0;
  for (const line of lines) {
    const h = line.match(/^#{2,4}\s*P0/i);
    if (h) {
      inP0 = true;
      continue;
    }
    const nextH = line.match(/^#{2,4}\s/);
    if (nextH && !line.match(/^#{2,4}\s*P0/i)) {
      inP0 = false;
      continue;
    }
    if (inP0 && line.match(/^\s*[-*]\s+/)) {
      total++;
      if (line.match(/[✅√]/)) passed++;
    }
  }
  return { total, passed };
}

// ---------- KPI 扫描 ----------

function scanFeatureKPI(featureDir) {
  const featureName = path.basename(featureDir);
  const files = {};
  KPI_FILES.forEach((f) => {
    const p = path.join(featureDir, f);
    files[f] = readFileUtf8(p);
  });

  const checklistText = files['05_动态检查清单.md'] || '';
  const summaryText = files['06_实施总结.md'] || '';
  const reportText = files['07_项目报告.md'] || '';
  const allText = [checklistText, summaryText, reportText].join('\n');

  // P0 通过率
  const p0 = countP0Items(checklistText);
  let p0Rate = p0.total > 0 ? Math.round((p0.passed / p0.total) * 100) : null;

  // 交付完成率
  let deliveryRate = extractPercent(allText, ['交付完成率', '完成率', '交付率']);

  // 防幻觉率
  let antiHallucinationRate = extractPercent(allText, ['防幻觉率', '防幻觉', '幻觉率']);

  // 修复轮次
  let fixRounds = extractNumber(allText, ['修复轮次', '迭代轮次', '修改轮次', '轮次']);

  // 规则覆盖率：从检查清单统计
  const checklistTotal = (checklistText.match(/^\s*[-*]\s+/gm) || []).length;
  let ruleCoverage = null;
  if (checklistTotal > 0) {
    const ruleItems = (checklistText.match(/^\s*[-*]\s*.*规则/gm) || []).length;
    ruleCoverage = Math.round((ruleItems / checklistTotal) * 100);
  }

  // 证据路径（取存在的文件）
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
    return { features: [], note: 'docs/ 目录不存在' };
  }
  const entries = fs.readdirSync(DOCS_DIR, { withFileTypes: true });
  const featureDirs = entries
    .filter((e) => e.isDirectory() && !e.name.startsWith('.') && !e.name.startsWith('周报') && !e.name.startsWith('99_'))
    .map((e) => path.join(DOCS_DIR, e.name));

  if (featureDirs.length === 0) {
    return { features: [], note: 'docs/ 下无功能目录' };
  }

  const features = featureDirs.map(scanFeatureKPI).filter((f) => f.hasData);
  if (features.length === 0) {
    return { features: [], note: 'docs/ 下无含 KPI 数据的功能目录（05/06/07 文件均不存在）' };
  }
  return { features, note: `扫描到 ${features.length} 个含 KPI 数据的功能目录` };
}

// ---------- Git 统计 ----------

function collectGitStats(weekRange) {
  const since = weekRange.start;
  const until = weekRange.end;
  const sinceIso = `${since}T00:00:00`;
  const untilIso = `${until}T23:59:59`;

  // 提交数
  const commitCount = safeExec(
    `git log --since="${sinceIso}" --until="${untilIso}" --oneline | wc -l`,
    '0'
  );

  // 使用 --shortstat 累加本周每个提交的 diff 统计，避免包含本周之前的变更
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

  // 作者统计
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

// ---------- 输出格式化 ----------

function formatMarkdown(featureResult, gitResult) {
  const { features, note } = featureResult;
  const lines = [];

  lines.push(`# KPI 自动汇总（${gitResult.weekRange.range}）`);
  lines.push('');
  lines.push(`> **生成时间**: ${new Date().toISOString()}`);
  lines.push(`> **数据来源**: docs/<功能名>/ 下 05/06/07 文件 + git log`);
  lines.push('');

  // Git 统计
  lines.push('## Git 统计');
  lines.push('');
  lines.push(`| 指标 | 数值 |`);
  lines.push(`|------|------|`);
  lines.push(`| 提交数 | ${gitResult.commitCount} |`);
  lines.push(`| 变更文件数 | ${gitResult.filesChanged} |`);
  lines.push(`| 新增行数 | ${gitResult.insertions} |`);
  lines.push(`| 删除行数 | ${gitResult.deletions} |`);
  lines.push('');
  if (gitResult.authors.length > 0) {
    lines.push('**提交者分布**: ' + gitResult.authors.map((a) => `${a.name}(${a.commits})`).join(', '));
    lines.push('');
  }

  // 功能 KPI
  lines.push('## 功能维度 KPI');
  lines.push('');
  if (features.length === 0) {
    lines.push(`> ${note}`);
    lines.push('');
  } else {
    lines.push(`| 功能/案例 | 交付完成率 | P0 通过率 | 防幻觉率 | 修复轮次 | 规则覆盖率 | 维度综合 |`);
    lines.push(`|-----------|-----------|----------|----------|----------|------------|----------|`);
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
    lines.push('**维度判定**: ✅ ≥80%交付/≥90%P0/≤2轮修复 | 🟡 中等区间 | ❌ 未达标');
    lines.push('');

    // 逐功能明细
    lines.push('## 功能明细与证据');
    lines.push('');
    for (const f of features) {
      lines.push(`### ${f.featureName}`);
      lines.push('');
      if (f.evidencePaths.length === 0) {
        lines.push('- 无文档证据（05/06/07 文件不存在）');
      } else {
        f.evidencePaths.forEach((p) => lines.push(`- ${p}`));
      }
      if (f.p0Details.total > 0) {
        lines.push(`- P0 检查项: ${f.p0Details.passed}/${f.p0Details.total} 通过`);
      }
      lines.push('');
    }
  }

  return lines.join('\n');
}

function formatJson(featureResult, gitResult) {
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
    },
    null,
    2
  );
}

// ---------- 主流程 ----------

function main() {
  const args = parseArgs(process.argv);

  let baseDate = new Date();
  if (args.week) {
    const d = new Date(args.week);
    if (isNaN(d.getTime())) {
      console.error(`错误: 无效日期 "${args.week}"`);
      process.exit(2);
    }
    baseDate = d;
  }

  const weekRange = getNaturalWeekRange(baseDate);

  let featureResult = { features: [], note: '跳过 docs/ 扫描' };
  let gitResult = { weekRange, commitCount: 0, filesChanged: 0, insertions: 0, deletions: 0, authors: [] };

  if (!args.gitOnly) {
    featureResult = scanAllFeatures();
  }
  if (!args.docsOnly) {
    gitResult = collectGitStats(weekRange);
  }

  let output = args.json ? formatJson(featureResult, gitResult) : formatMarkdown(featureResult, gitResult);

  if (args.withLogs) {
    const logsScript = path.join(__dirname, 'collect-weekly-logs.js');
    const weekArg = args.week ? `--week ${args.week}` : '';
    let logsOutput;
    try {
      logsOutput = execSync(`node "${logsScript}" ${weekArg}`, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] }).trim();
    } catch (err) {
      console.error(`警告: collect-weekly-logs.js 执行失败: ${err.message}`);
      logsOutput = '';
    }
    if (!logsOutput) {
      console.error('警告: collect-weekly-logs.js 输出为空，可能本周日志文件不存在或解析失败');
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
      output = output + '\n\n---\n\n' + (logsOutput || '> 本周无编排日志数据');
    }
  }

  if (args.output) {
    fs.writeFileSync(args.output, output, 'utf8');
    console.error(`已保存至: ${args.output}`);
  } else {
    console.log(output);
  }
}

main();
