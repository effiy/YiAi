'use strict';

/**
 * Append "key nodes" as Markdown to `docs/weekly/<natural-week-range>/key-notes.md`.
 * Reused by `log-key-node.js` CLI and scripts that need programmatic disk writes (e.g. send-message).
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
    // new file
  }
  const preamble = `---
log_type: key-node
week: ${weekRange}
---

# Key Nodes · ${weekRange}

This file is appended by \`node .claude/scripts/log-key-node.js\` or orchestration scripts, recording milestones / gates / external notifications and other scannable nodes.

---

`;
  await fsp.writeFile(filePath, preamble, 'utf8');
}

/**
 * @param {string} repoRoot project root (repo root)
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
  const dir = path.join(repoRoot, 'docs', 'weekly', week.range);
  await fsp.mkdir(dir, { recursive: true });
  const filePath = path.join(dir, 'key-notes.md');

  await ensurePreamble(filePath, week.range);

  const iso = new Date().toISOString();
  const categoryRaw = opts.category != null && String(opts.category).trim() !== '' ? String(opts.category).trim() : 'general';
  const cat = categoryRaw.replace(/[^\w一-鿿./-]/g, '_');
  const skillRaw = opts.skill != null ? String(opts.skill).trim() : '';
  const skillLine = skillRaw !== '' ? `**Related Skill**: \`${skillRaw}\`\n\n` : '';

  const safeTitle = escapeHeadingFragment(title);
  const block = `### \`${iso}\` · \`${cat}\` · ${safeTitle}

${skillLine}**Description**

${formatSummaryBody(body)}

---

`;

  await fsp.appendFile(filePath, block, 'utf8');
}

module.exports = { appendKeyNodeRecord };
