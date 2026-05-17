#!/usr/bin/env node
// import-docs sync — scan + filter + upload local documents to remote API
// Triggered by: rui delivery gate step ②, or manual: node skills/import-docs/sync.mjs

import { readFile, readdir, stat } from "node:fs/promises";
import { join, relative, sep, dirname, resolve } from "node:path";
import { existsSync } from "node:fs";

// --- config ----------------------------------------------------------------
const API_URL = process.env.IMPORT_DOCS_API_URL || "https://api.effiy.cn";
const API_X_TOKEN = process.env.API_X_TOKEN || "";
const DEFAULT_EXTS = ["md"];
const DEFAULT_EXCLUDES = new Set([".git", "node_modules", ".claude-plugin"]);
const CONCURRENCY = 4;
const HTTP_TIMEOUT = 30_000;

// --- args ------------------------------------------------------------------
function parseArgs() {
  const args = process.argv.slice(2);
  const opts = { exts: DEFAULT_EXTS, exclude: [], prefix: [], mode: "import" };
  let scanRoot = null;
  let scanDir = null;

  for (const arg of args) {
    if (arg === "--help" || arg === "-h") {
      showHelp();
    }
    const eq = arg.indexOf("=");
    if (eq === -1) continue;
    const key = arg.slice(0, eq);
    const val = arg.slice(eq + 1);
    switch (key) {
      case "workspace": scanRoot = "workspace"; break;
      case "dir": scanDir = val; break;
      case "exts": opts.exts = val.split(",").map(s => s.trim()); break;
      case "exclude": opts.exclude = val.split(",").map(s => s.trim()); break;
      case "prefix": opts.prefix = val.split(",").map(s => s.trim()); break;
      case "apiUrl": opts.apiUrl = val; break;
      case "mode": opts.mode = val; break;
    }
  }

  return { scanRoot, scanDir, ...opts };
}

function showHelp() {
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

  const help = `
${bold("# import-docs sync — 文档批量同步到远端")}

${dim("扫描 · 过滤 · 路径映射 · 上传 | 扫描项目文件并同步到远端 API")}

${section("参数", [
  ["workspace=true", "项目根全量扫描 + 上传 (最常用)"],
  ["dir=<path>", "指定目录扫描 (绝对路径)"],
  ["exts=md,json,yaml", "文件扩展名 (默认: md)"],
  ["exclude=tmp,build", "追加排除目录"],
  ["prefix=a,b", "远端路径前缀"],
  ["apiUrl=<url>", "覆盖 API 地址"],
  ["mode=list", "仅列出文件，跳过上传"],
])}

${section("示例", [
  ["# 全量同步", ""],
  ["workspace=true", "扫描项目根 → 上传全部 .md 文件"],
  ["", ""],
  ["# 同步指定目录", ""],
  ["dir=/path/to/docs exts=md,json", "仅同步该目录下的 md/json 文件"],
  ["", ""],
  ["# 预览不上传", ""],
  ["workspace=true mode=list", "列出待上传文件清单"],
  ["", ""],
  ["# 带远端前缀", ""],
  ["workspace=true prefix=docs,api-v2", "远端路径追加 docs/api-v2/"],
])}

${section("环境变量", [
  ["API_X_TOKEN", "鉴权令牌 (必填 · 缺失时静默降级)"],
  ["IMPORT_DOCS_API_URL", "覆盖默认 API 地址"],
])}

${section("扫描规则", [
  [".claude/ 目录", "全量纳入 · 不限扩展名"],
  ["其他目录", "仅匹配 --exts 的文件"],
  ["默认排除", ".git · node_modules · .claude-plugin"],
])}

${dim("详细: skills/import-docs/SKILL.md | 同步: node skills/import-docs/sync.mjs")}
`;

  console.log(help);
  process.exit(0);
}

// --- project root ----------------------------------------------------------
function findProjectRoot(startDir) {
  let dir = resolve(startDir);
  while (true) {
    if (existsSync(join(dir, ".git")) || existsSync(join(dir, ".claude")))
      return dir;
    const parent = dirname(dir);
    if (parent === dir) return resolve(startDir); // fallback to cwd
    dir = parent;
  }
}

// --- scan ------------------------------------------------------------------
async function scanFiles(root, exts, userExcludes) {
  const result = [];
  const excludes = new Set([...DEFAULT_EXCLUDES, ...userExcludes]);

  async function walk(dir) {
    let entries;
    try { entries = await readdir(dir, { withFileTypes: true }); }
    catch { return; }

    for (const entry of entries) {
      if (excludes.has(entry.name)) continue;
      const full = join(dir, entry.name);
      if (entry.isDirectory()) { await walk(full); continue; }
      if (entry.isFile()) result.push(full);
    }
  }

  await walk(root);

  return result.filter(file => {
    const rel = relative(root, file);
    const parts = rel.split(sep);
    // .claude/ 全量纳入
    if (parts[0] === ".claude") return true;
    // 其他仅匹配扩展名
    const ext = file.split(".").pop()?.toLowerCase();
    return ext && exts.includes(ext);
  });
}

// --- path mapping ----------------------------------------------------------
function resolveRemotePath(localPath, root, workspaceName, prefix) {
  const rel = relative(root, localPath).split(sep).join("/").replace(/\s/g, "_");
  const segments = [];
  if (prefix.length > 0) segments.push(...prefix);

  // docs/故事任务面板/ 下的文件：故事任务面板为第一层标签，去除前置目录
  // 结果: 故事任务面板/{项目目录}/{故事任务目录}/*
  const panelIdx = rel.indexOf("/docs/故事任务面板/");
  const isPanelRoot = rel.startsWith("docs/故事任务面板/");
  if (isPanelRoot || panelIdx !== -1) {
    const storyRel = isPanelRoot
      ? rel.slice("docs/故事任务面板/".length)
      : rel.slice(panelIdx + "/docs/故事任务面板/".length);
    segments.push("故事任务面板");
    segments.push(storyRel);
  } else {
    segments.push(workspaceName);
    segments.push(rel);
  }

  return segments.join("/");
}

function getTags(remotePath) {
  const parts = remotePath.split("/");
  parts.pop(); // remove filename
  return parts;
}

// --- HTTP helpers ----------------------------------------------------------
async function fetchJson(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), HTTP_TIMEOUT);
  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Token": API_X_TOKEN,
        ...options.headers,
      },
    });
    const text = await res.text();
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${text.slice(0, 500)}`);
    try { return JSON.parse(text); }
    catch { return text; }
  } finally { clearTimeout(timer); }
}

async function querySessions(apiUrl) {
  const body = {
    module_name: "services.database.data_service",
    method_name: "query_documents",
    parameters: { cname: "sessions", limit: 10000 },
  };
  const data = await fetchJson(apiUrl + "/", { method: "POST", body: JSON.stringify(body) });
  const paths = new Set();
  const list = data?.data?.list || data?.list || [];
  for (const item of list) {
    if (item.file_path) paths.add(item.file_path);
  }
  return paths;
}

async function writeFile(apiUrl, remotePath, content) {
  const body = { target_file: remotePath, content, is_base64: false };
  return fetchJson(apiUrl + "/write-file", { method: "POST", body: JSON.stringify(body) });
}

async function createSession(apiUrl, remotePath) {
  const basename = remotePath.split("/").pop();
  const tags = getTags(remotePath);
  const now = Date.now();
  const body = {
    module_name: "services.database.data_service",
    method_name: "create_document",
    parameters: {
      cname: "sessions",
      data: {
        url: `app-session://${now}-${Math.random().toString(36).slice(2, 8)}`,
        title: basename,
        file_path: remotePath,
        messages: [],
        tags,
        isFavorite: false,
        createdAt: now,
        updatedAt: now,
        lastAccessTime: now,
      },
    },
  };
  return fetchJson(apiUrl + "/", { method: "POST", body: JSON.stringify(body) });
}

// --- concurrent upload -----------------------------------------------------
async function uploadAll(files, apiUrl, existingPaths, root, workspaceName, prefix) {
  let created = 0, overwritten = 0, failed = 0;
  const errors = [];

  async function worker(file) {
    const remotePath = resolveRemotePath(file, root, workspaceName, prefix);
    try {
      const content = await readFile(file, "utf-8");
      await writeFile(apiUrl, remotePath, content);
      if (existingPaths.has(remotePath)) { overwritten++; }
      else {
        await createSession(apiUrl, remotePath);
        created++;
      }
    } catch (err) {
      failed++;
      errors.push({ file, remotePath, error: err.message });
    }
  }

  // Run with concurrency limit
  const queue = [...files];
  async function run() {
    while (queue.length > 0) {
      const file = queue.shift();
      await worker(file);
    }
  }
  const workers = Array.from({ length: Math.min(CONCURRENCY, files.length) }, run);
  await Promise.all(workers);

  return { created, overwritten, failed, errors };
}

// --- empty input: recommend ------------------------------------------------
function hasArgs(opts) {
  return opts.scanRoot === "workspace" || opts.scanDir !== null;
}

async function recommendMode(root, workspaceName, opts, apiUrl) {
  const files = await scanFiles(root, opts.exts, opts.exclude);

  console.log("# import-docs 状态检测与推荐\n");

  // API_X_TOKEN 检测
  if (!API_X_TOKEN) {
    console.log("⚠️  API_X_TOKEN: 缺失");
    console.log("   → 推荐: 配置 token 后执行 `/import-docs workspace=true` 全量导入\n");
  } else {
    console.log("✅ API_X_TOKEN: 已配置");
  }

  // 远端可达性检测
  if (API_X_TOKEN) {
    try {
      const existingPaths = await querySessions(apiUrl);
      console.log(`✅ 远端可达: ${existingPaths.size} 个已有 session\n`);
    } catch (err) {
      console.log(`⚠️  远端不可达: ${err.message}`);
      console.log("   → 推荐: 检查网络或 API 地址后重试\n");
    }
  }

  // 文件清单预览
  console.log(`📋 待同步文件: ${files.length} 个`);
  if (files.length > 0) {
    const preview = files.slice(0, 10);
    for (const f of preview) {
      const rp = resolveRemotePath(f, root, workspaceName, opts.prefix);
      console.log(`   ${relative(root, f)} → ${rp}`);
    }
    if (files.length > 10) console.log(`   ... 等 ${files.length - 10} 个文件`);
  }

  // 推荐任务
  console.log("\n## 推荐任务\n");
  if (!API_X_TOKEN) {
    console.log("1. [凭据缺失] 设置 API_X_TOKEN 环境变量");
  }
  console.log("2. [全量导入] `/import-docs workspace=true` 扫描并上传全部文件");
  console.log("3. [增量同步] `/import-docs workspace=true exclude=...` 跳过指定目录");
  console.log("4. [预览检查] `/import-docs workspace=true mode=list` 仅列出不上传");
  console.log("5. [定期巡检] 定期运行空输入检查 token / 远端可达性 / 文件差异");
}

// --- main ------------------------------------------------------------------
async function main() {
  const opts = parseArgs();
  const apiUrl = opts.apiUrl || API_URL;

  const root = (opts.scanRoot === "workspace")
    ? findProjectRoot(process.cwd())
    : opts.scanDir
      ? resolve(opts.scanDir)
      : findProjectRoot(process.cwd());

  if (!existsSync(root)) {
    console.error(`[import-docs] scan root not found: ${root}`);
    process.exit(0);
  }

  const workspaceName = root.split(sep).pop() || "workspace";

  // 空输入 → 推荐模式
  if (!hasArgs(opts)) {
    console.error(`[import-docs] scan root: ${root} (recommend mode)`);
    await recommendMode(root, workspaceName, opts, apiUrl);
    return;
  }

  console.error(`[import-docs] scan root: ${root}`);
  console.error(`[import-docs] workspace: ${workspaceName}`);

  // 硬约束：一级目录标签只能是项目目录名或"故事任务面板"
  const allowedLabels = new Set([workspaceName, "故事任务面板"]);
  if (opts.prefix.length > 0) {
    const firstLabel = opts.prefix[0];
    if (!allowedLabels.has(firstLabel)) {
      console.error(`[import-docs] ERROR: prefix 一级标签 "${firstLabel}" 不允许，只能是 "${workspaceName}" 或 "故事任务面板"`);
      process.exit(1);
    }
  }

  const files = await scanFiles(root, opts.exts, opts.exclude);
  console.error(`[import-docs] found ${files.length} files`);

  // List mode
  if (opts.mode === "list") {
    for (const f of files) {
      const remotePath = resolveRemotePath(f, root, workspaceName, opts.prefix);
      console.log(`${f} → ${remotePath}`);
    }
    console.error(`\n[import-docs] ${files.length} files (list mode, no upload)`);
    return;
  }

  // Import mode
  if (!API_X_TOKEN) {
    console.error("[import-docs] no API_X_TOKEN — no-token 降级，跳过上传");
    return;
  }

  console.error("[import-docs] querying existing sessions...");
  let existingPaths;
  try {
    existingPaths = await querySessions(apiUrl);
    console.error(`[import-docs] existing sessions: ${existingPaths.size}`);
  } catch (err) {
    console.error(`[import-docs] failed to query sessions: ${err.message}`);
    existingPaths = new Set();
  }

  console.error(`[import-docs] uploading ${files.length} files (concurrency=${CONCURRENCY})...`);
  const result = await uploadAll(files, apiUrl, existingPaths, root, workspaceName, opts.prefix);

  // Summary
  const { created, overwritten, failed, errors } = result;
  console.error(`[import-docs] done — created: ${created}, overwritten: ${overwritten}, failed: ${failed}`);
  if (errors.length > 0) {
    for (const e of errors) {
      console.error(`[import-docs] FAILED: ${e.file} → ${e.error}`);
    }
  }

  process.exit(failed > 0 ? 1 : 0);
}

main().catch(err => {
  console.error(`[import-docs] fatal: ${err.message}`);
  process.exit(0); // 不阻断管线
});
