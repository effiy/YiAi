#!/usr/bin/env node
// import-docs — Batch sync local documents to remote API help
// 用法: node skills/import-docs/help.mjs 或 /import-docs --help

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
  const pad = Math.max(2, 32 - left.length);
  return `${left}${" ".repeat(pad)}${desc}`;
}

function section(title, entries) {
  return hdr(title) + entries.map(([c, d]) => item(c, d)).join("\n");
}

const help = `
${bold("# import-docs — 文档批量同步到远端")}

${dim("扫描 · 过滤 · 路径映射 · 上传 | rui 管线强制集成")}

${hdr("用法")}
${item("/import-docs --help", "显示此帮助信息")}
${item("/import-docs -h", "同上")}
${item("/import-docs help", "同上")}

${section("调用形态", [
  ["workspace=true", "项目根全量扫描 + 上传 (最常用)"],
  ["dir=<absolute path>", "指定目录扫描 + 上传"],
  ["exts=md,json,yaml", "覆盖默认扩展名 (默认 md)"],
  ["exclude=tmp,build", "追加排除子目录"],
  ["prefix=a,b", "远端路径前缀"],
  ['apiUrl=https://api.example.com', "覆盖默认 API 地址"],
  ["mode=list", "仅枚举不上传，输出文件清单"],
])}

${section("常用场景示例", [
  ["# 全量同步 (rui 管线末端自动触发)", ""],
  ["/import-docs workspace=true", "扫描项目根全部 .md + .claude/ → 上传"],
  ["", ""],
  ["# 同步指定目录", ""],
  ["/import-docs dir=/path/to/docs", "仅同步该目录下的文件"],
  ["", ""],
  ["# 同步多种文件类型", ""],
  ["/import-docs workspace=true exts=md,json,yaml", "同步 .md .json .yaml 文件"],
  ["", ""],
  ["# 排除特定目录", ""],
  ["/import-docs workspace=true exclude=tmp,vendor", "跳过 tmp/ 和 vendor/"],
  ["", ""],
  ["# 预览不上传", ""],
  ["/import-docs workspace=true mode=list", "列出待上传文件清单"],
  ["", ""],
  ["# 带远端前缀上传", ""],
  ["/import-docs workspace=true prefix=docs,api-v2", "远端路径前追加 docs/api-v2/"],
  ["", ""],
  ["# 检查状态 (空输入)", ""],
  ["/import-docs", "检测 token / 远端可达性 / 文件差异"],
])}

${section("扫描规则", [
  [".claude/ 目录", "全量纳入 · 不限扩展名 · 递归全部子目录"],
  ["其他目录", "仅扩展名命中 --exts (默认 md) 的文件"],
  ["默认排除", ".git · node_modules · .claude-plugin"],
  ["语句面板路径", "docs/故事任务面板/ → 远端加故事面板路径映射"],
])}

${section("环境变量", [
  ["API_X_TOKEN", "必填 · 鉴权令牌 · 仅从环境变量读取"],
])}

${section("上传流程", [
  ["① 扫描", "从项目根递归遍历，不受 .gitignore 限制"],
  ["② 过滤", "排除 .git / node_modules / .claude-plugin"],
  ["③ 解析路径", "本地路径 → 远端路径映射"],
  ["④ 拉取已有", "查询远端 sessions 区分 created/overwritten"],
  ["⑤ 上传", "逐文件 POST /write-file (并发 ≤ 4)"],
  ["⑥ 新建 session", "对新增路径追加 create_document"],
  ["⑦ 汇总", "created · overwritten · failed 统计"],
])}

${section("降级与容错", [
  ["API_X_TOKEN 缺失", "静默跳过，不阻断管线 (no-token 降级)"],
  ["单文件失败", "记录错误并继续，最终退出码 1"],
  ["网络超时/不可达", "记录告警不阻断"],
  ["扫描根不存在", "跳过整次同步"],
])}

${section("全局选项", [
  ["--help, -h, help", "显示此帮助信息"],
])}

${dim("详细说明: skills/import-docs/SKILL.md | 集成: skills/rui/SKILL.md §强制集成")}
`;

console.log(help);
