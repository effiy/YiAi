#!/usr/bin/env node
// rui-story — Story panel CRUD and sync management help
// 用法: node skills/rui-story/help.mjs 或 /rui-story --help

const { bold, underline, dim } = (() => {
  const e = { bold: (s) => `\x1b[1m${s}\x1b[22m`, underline: (s) => `\x1b[4m${s}\x1b[24m`, dim: (s) => `\x1b[2m${s}\x1b[22m` };
  if (!process.stdout.isTTY) return { bold: (s) => s, underline: (s) => s, dim: (s) => s };
  return e;
})();

const INDENT = "  ";

function hdr(text) {
  return `\n${bold(underline(text))}\n`;
}

function item(cmd, desc) {
  const left = `${INDENT}${cmd}`;
  const pad = Math.max(2, 28 - left.length);
  return `${left}${" ".repeat(pad)}${desc}`;
}

function section(title, entries) {
  return hdr(title) + entries.map(([c, d]) => item(c, d)).join("\n");
}

function line(text) {
  return `${INDENT}${text}`;
}

const help = `
${bold("# rui-story — 故事任务面板管理")}

${dim("扫描 · 创建 · 查看 · 重命名 · 删除 · 同步 | 操作仅限 docs/故事任务面板/")}

${hdr("用法")}
${item("/rui-story --help", "显示此帮助信息")}
${item("/rui-story -h", "同上")}
${item("/rui-story help", "同上")}

${section("只读命令", [
  ["/rui-story", "状态概览：按状态统计 + 最近活动"],
  ["/rui-story list", "进度全景：所有故事的详细表格（从 /rui 迁移）"],
  ["/rui-story show <Project>-<name>", "单故事详情：文件清单/状态/元数据/git 分支"],
])}

${section("写入命令", [
  ["/rui-story create <Project>-<name>", "创建故事目录骨架，可选 --type frontend|backend|fullstack|meta"],
  ["/rui-story delete <Project>-<name>", "删除故事目录（需确认，警告 git 分支）"],
  ["/rui-story sync [<Project>-<name>]", "触发文档同步（委托 import-docs）"],
  ["/rui-story rename <old> <new>", "重命名故事目录（警告 git 分支）"],
])}

${section("常用场景示例", [
  ["# 查看项目整体进度", ""],
  ["/rui-story", "展示状态统计和最近活动"],
  ["", ""],
  ["# 查看所有故事详情", ""],
  ["/rui-story list", "表格形式展示所有故事的完整信息"],
  ["", ""],
  ["# 查看单个故事", ""],
  ["/rui-story show YiWeb-user-login", "展示该故事的所有文件、状态、元数据"],
  ["", ""],
  ["# 创建新故事（仅目录骨架）", ""],
  ["/rui-story create YiWeb-user-login", "创建目录（默认 meta），后续用 /rui doc 生成文档"],
  ["/rui-story create YiWeb-user-login --type fullstack", "指定项目类型为全栈"],
  ["", ""],
  ["# 删除废弃故事", ""],
  ["/rui-story delete YiWeb-user-login", "确认后删除目录（不删 git 分支）"],
  ["", ""],
  ["# 同步故事文档到远端", ""],
  ["/rui-story sync YiWeb-user-login", "委托 import-docs 同步该故事"],
  ["/rui-story sync", "同步全部故事面板"],
  ["", ""],
  ["# 重命名故事", ""],
  ["/rui-story rename YiWeb-user-login YiWeb-auth-login", "重命名目录，警告 git 分支"],
])}

${section("操作边界", [
  ["✅ docs/故事任务面板/", "目录结构管理"],
  ["❌ 不可触及", "源码 · git 分支操作 · 故事文档内容生成"],
])}

${section("核心规则", [
  ["仅管理目录结构", "不创建文档内容（那是 /rui doc）"],
  ["不改源码", "不改源代码或 git 分支"],
  ["delete 必确认", "删除操作必须用户明确确认"],
  ["PascalCase + kebab-case", "Project 大驼峰，name 小写连字符"],
  ["sync 委托 import-docs", "不自行实现同步逻辑"],
])}

${section("全局选项", [
  ["--help, -h, help", "显示此帮助信息"],
])}

${dim("详细说明: skills/rui-story/SKILL.md | 故事面板: docs/故事任务面板/")}
`;

console.log(help);
