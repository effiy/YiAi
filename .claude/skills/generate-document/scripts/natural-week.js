'use strict';

/**
 * @param {Date} [date]
 * @returns {string}
 */
function formatLocalDate(date = new Date()) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/**
 * 自然周：周一 ~ 周日（基于本地时区）。
 * @param {Date} [baseDate]
 * @returns {{ start: string, end: string, range: string }}
 */
function getNaturalWeekRange(baseDate = new Date()) {
  const cur = new Date(baseDate);
  cur.setHours(0, 0, 0, 0);
  const day = cur.getDay(); // 0=Sun ... 6=Sat
  const deltaToMonday = day === 0 ? -6 : 1 - day;

  const monday = new Date(cur);
  monday.setDate(cur.getDate() + deltaToMonday);

  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);

  const start = formatLocalDate(monday);
  const end = formatLocalDate(sunday);
  return { start, end, range: `${start}~${end}` };
}

module.exports = { formatLocalDate, getNaturalWeekRange };
