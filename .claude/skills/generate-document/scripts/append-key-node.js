'use strict';

/**
 * 将「关键节点」以 Markdown 追加写入 `docs/周报/<自然周范围>/key-notes.md`。
 * 供 `log-key-node.js` CLI 与需程序化落盘的脚本（如 send-message）复用。
 */

const fsp = require('fs').promises;
const path = require('path');
const { getNaturalWeekRange } = require('./natural-week.js');

/**
 * @param {string} body
 */
function formatSummaryBody(body) {
  return body.split('\n').map((line) => `> ${line}`).join('\n');
}

/**
 * @param {string} title
 */
function escapeHeadingFragment(title) {
  return String(title)
    .replace(/\r?\n/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/`/g, "'");
}

/**
 * @param {string} filePath
 * @param {string} weekRange YYYY-MM-DD~YYYY-MM-DD
 */
async function ensurePreamble(filePath, weekRange) {
  try {
    const st = await fsp.stat(filePath);
    if (st.size > 0) return;
  } catch {
    // 新建
  }
  const preamble = `---
log_type: key-node
week: ${weekRange}
---

# 关键节点 · ${weekRange}

本文件由 \`node .claude/scripts/log-key-node.js\` 或编排脚本追加写入，记录里程碑 / 门禁 / 对外通知等可扫描节点。

---

`;
  await fsp.writeFile(filePath, preamble, 'utf8');
}

/**
 * @param {string} repoRoot 项目根（仓库根）
 * @param {{
 *   title: string,
 *   body: string,
 *   category?: string|null,
 *   skill?: string|null
 * }} opts
 * @returns {Promise<void>}
 */
async function appendKeyNodeRecord(repoRoot, opts) {
  const title = opts.title != null ? String(opts.title).trim() : '';
  if (!title) {
    throw new Error('appendKeyNodeRecord: title is required');
  }
  const body = opts.body != null ? String(opts.body).trim() : '';
  if (!body) {
    throw new Error('appendKeyNodeRecord: body is required');
  }

  const week = getNaturalWeekRange(new Date());
  const dir = path.join(repoRoot, 'docs', '周报', week.range);
  await fsp.mkdir(dir, { recursive: true });
  const filePath = path.join(dir, 'key-notes.md');

  await ensurePreamble(filePath, week.range);

  const iso = new Date().toISOString();
  const categoryRaw = opts.category != null && String(opts.category).trim() !== '' ? String(opts.category).trim() : 'general';
  const cat = categoryRaw.replace(/[^\w\u4e00-\u9fff./-]/g, '_');
  const skillRaw = opts.skill != null ? String(opts.skill).trim() : '';
  const skillLine = skillRaw !== '' ? `**关联技能**：\`${skillRaw}\`\n\n` : '';

  const safeTitle = escapeHeadingFragment(title);
  const block = `### \`${iso}\` · \`${cat}\` · ${safeTitle}

${skillLine}**说明**

${formatSummaryBody(body)}

---

`;

  await fsp.appendFile(filePath, block, 'utf8');
}

module.exports = { appendKeyNodeRecord };
