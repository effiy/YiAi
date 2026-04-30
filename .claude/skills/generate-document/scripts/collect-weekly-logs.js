#!/usr/bin/env node

/**
 * collect-weekly-logs
 *
 * 目标：自动读取本周 docs/周报/<周>/ 下的 key-notes.md 和 logs.md，
 * 提取关键节点（里程碑 / 门禁 / 对外通知）与编排会话日志（skill / agent / MCP 交互），
 * 输出结构化汇总供周报复盘使用。
 *
 * 用法：
 *   node scripts/collect-weekly-logs.js [--week <YYYY-MM-DD>] [--json] [--output <path>]
 *
 * 选项：
 *   --week <date>   指定日期，自动归到其所在自然周（默认今天）
 *   --json          输出 JSON 格式（默认 Markdown）
 *   --output <path> 保存到文件（默认 stdout）
 *   --key-only      仅输出关键节点
 *   --logs-only     仅输出编排会话日志
 *
 * 退出码：
 *   0 成功
 *   1 运行错误
 *   2 参数错误
 */

const fs = require('fs');
const path = require('path');
const { getNaturalWeekRange } = require('./natural-week.js');

function printHelp(stream) {
  const out = stream || process.stdout;
  out.write(`用法:
  node scripts/collect-weekly-logs.js [--week <YYYY-MM-DD>] [--json] [--output <path>]

选项:
  --week <date>   指定日期，自动归到其所在自然周（默认今天）
  --json          输出 JSON 格式（默认 Markdown）
  --output <path> 保存到文件（默认 stdout）
  --key-only      仅输出关键节点
  --logs-only     仅输出编排会话日志

示例:
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

// ---------- key-notes.md 解析 ----------

function parseKeyNotes(text) {
  if (!text) return { entries: [], note: '文件不存在' };

  const lines = text.split(/\r?\n/);
  const entries = [];
  let current = null;

  for (const line of lines) {
    // 匹配标题行: ### `ISO` · `category` · Title
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

    const skillMatch = line.match(/^\*\*关联技能\*\*：\s*`([^`]+)`/);
    if (skillMatch) {
      current.skill = skillMatch[1];
      continue;
    }

    // 跳过 "**说明**" 和分隔线
    if (line.match(/^\*\*说明\*\*/)) continue;
    if (line.match(/^---+$/)) continue;

    // 收集 body（去掉开头的 > 引用标记）
    const bodyLine = line.replace(/^\s*>\s?/, '');
    if (bodyLine.trim()) {
      current.body.push(bodyLine);
    }
  }

  if (current) entries.push(current);

  return {
    entries: entries.map((e) => ({ ...e, body: e.body.join('\n').trim() })),
    note: `解析到 ${entries.length} 条关键节点`,
  };
}

// ---------- logs.md 解析 ----------

function parseLogs(text) {
  if (!text) return { entries: [], note: '文件不存在' };

  const lines = text.split(/\r?\n/);
  const entries = [];
  let current = null;
  let inSummary = false;
  let inEval = false;

  for (const line of lines) {
    // 匹配三级标题: ### `ISO` · `category`[ · **badge**]
    // category 格式: skill:kind/name，例如 generate-document:agent/spec-retriever
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

    const scenarioMatch = line.match(/^\*\*操作场景\*\*：\s*(.+)$/);
    if (scenarioMatch) {
      current.scenario = scenarioMatch[1].trim();
      continue;
    }

    // 进入对话与交互摘要区域
    if (line.match(/^\*\*对话与交互摘要\*\*/)) {
      inSummary = true;
      inEval = false;
      continue;
    }

    // 进入评测标注区域
    if (line.match(/^\*\*评测标注\*\*/)) {
      inSummary = false;
      inEval = true;
      continue;
    }

    // 跳过空行和分隔线
    if (line.match(/^---+$/)) continue;

    // 在评测标注区域内解析 case/tags/lesson
    if (inEval) {
      const caseMatch = line.match(/^\s*-\s*\*\*分级\*\*：\s*(\S+)/);
      if (caseMatch) {
        current.case = caseMatch[1];
        continue;
      }
      const tagsMatch = line.match(/^\s*-\s*\*\*标签\*\*：\s*(.+)$/);
      if (tagsMatch) {
        current.tags = tagsMatch[1].split(/[·,，]/).map((t) => t.trim().replace(/^`|`$/g, '')).filter(Boolean);
        continue;
      }
      const lessonMatch = line.match(/^\s*-\s*\*\*后续改进\*\*：\s*(.+)$/);
      if (lessonMatch) {
        current.lesson = lessonMatch[1].trim();
        continue;
      }
    }

    // 收集 summary（去掉开头的 > 引用标记）
    if (inSummary) {
      const bodyLine = line.replace(/^\s*>\s?/, '');
      current.summary.push(bodyLine);
    }
  }

  if (current) entries.push(current);

  return {
    entries: entries.map((e) => ({ ...e, summary: e.summary.join('\n').trim() })),
    note: `解析到 ${entries.length} 条编排日志`,
  };
}

// ---------- 聚合统计 ----------

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

// ---------- 输出格式化 ----------

function formatMarkdown(weekRange, keyNotesResult, logsResult) {
  const lines = [];
  lines.push(`# 关键节点与编排日志汇总（${weekRange.range}）`);
  lines.push('');
  lines.push(`> **生成时间**: ${new Date().toISOString()}`);
  lines.push(`> **数据来源**: docs/周报/${weekRange.range}/key-notes.md + logs.md`);
  lines.push('');

  // 关键节点
  lines.push('## 关键节点统计');
  lines.push('');
  const keyAgg = aggregateKeyNotes(keyNotesResult);
  if (keyAgg.total === 0) {
    lines.push(`> ${keyNotesResult.note}`);
    lines.push('');
  } else {
    lines.push(`| 指标 | 数值 |`);
    lines.push(`|------|------|`);
    lines.push(`| 总节点数 | ${keyAgg.total} |`);
    for (const [cat, count] of Object.entries(keyAgg.byCategory).sort((a, b) => b[1] - a[1])) {
      lines.push(`| 分类 \`${cat}\` | ${count} |`);
    }
    if (Object.keys(keyAgg.bySkill).length > 0) {
      lines.push(`| 关联技能 | ${Object.entries(keyAgg.bySkill).map(([s, c]) => `\`${s}\`(${c})`).join(', ')} |`);
    }
    lines.push('');

    lines.push('### 节点明细');
    lines.push('');
    for (const e of keyNotesResult.entries) {
      lines.push(`- **\`${e.category}\` · ${e.title}**`);
      lines.push(`  - 时间: ${e.timestamp}`);
      if (e.skill) lines.push(`  - 技能: \`${e.skill}\``);
      if (e.body) {
        const bodyPreview = e.body.split('\n')[0].slice(0, 80);
        lines.push(`  - 说明: ${bodyPreview}${e.body.length > 80 ? '...' : ''}`);
      }
      lines.push('');
    }
  }

  // 编排日志
  lines.push('## 编排会话日志统计');
  lines.push('');
  const logAgg = aggregateLogs(logsResult);
  if (logAgg.total === 0) {
    lines.push(`> ${logsResult.note}`);
    lines.push('');
  } else {
    lines.push(`| 指标 | 数值 |`);
    lines.push(`|------|------|`);
    lines.push(`| 总会话数 | ${logAgg.total} |`);
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

    lines.push('### 会话明细');
    lines.push('');
    for (const e of logsResult.entries) {
      const caseBadge = e.case ? `[${e.case}]` : '';
      lines.push(`- **\`${e.kind}\` · ${e.name}** ${caseBadge}`);
      lines.push(`  - 时间: ${e.timestamp}`);
      if (e.scenario) lines.push(`  - 场景: ${e.scenario}`);
      if (e.lesson) lines.push(`  - lesson: ${e.lesson}`);
      if (e.summary) {
        const summaryPreview = e.summary.split('\n')[0].slice(0, 80);
        lines.push(`  - 摘要: ${summaryPreview}${e.summary.length > 80 ? '...' : ''}`);
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
  const weeklyDir = path.resolve('docs', '周报', weekRange.range);

  let keyNotesResult = { entries: [], note: '跳过关键节点' };
  let logsResult = { entries: [], note: '跳过编排日志' };

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
    console.error(`已保存至: ${args.output}`);
  } else {
    console.log(output);
  }
}

main();
