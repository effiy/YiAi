#!/usr/bin/env node

/**
 * validate-agent-output
 *
 * 目标：把 agent 的“必答问题覆盖、结构化产物存在性”等契约做成可执行门禁。
 * 约定：agent 输出末尾必须包含一个 ```json fenced code block，字段规范见 shared/agent-output-contract.md
 *
 * 用法：
 *   node scripts/validate-agent-output.js --agent <name> (--text "<raw>" | --file <path>)
 *
 * 退出码：
 *   0 通过
 *   1 未通过
 *   2 参数错误
 */

const fs = require('fs');
const path = require('path');

function printHelp(stream) {
  const out = stream || process.stdout;
  out.write(`用法:
  node scripts/validate-agent-output.js --agent <agent-name> (--text "<raw>" | --file <path>)

示例:
  node scripts/validate-agent-output.js --agent spec-retriever --file /tmp/out.txt
  node scripts/validate-agent-output.js --agent architect --text "$(cat /tmp/out.txt)"
`);
}

function usage() {
  printHelp(process.stderr);
  process.exit(2);
}

function parseArgs(argv) {
  const out = { agent: null, text: null, file: null };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') {
      printHelp();
      process.exit(0);
    }
    else if (a === '--agent') out.agent = argv[++i];
    else if (a === '--text') out.text = argv[++i] || '';
    else if (a === '--file') out.file = argv[++i];
    else usage();
  }
  return out;
}

function readFileUtf8(p) {
  return fs.readFileSync(p, 'utf8');
}

function extractLastJsonFence(raw) {
  const s = String(raw ?? '');
  const re = /```json\s*([\s\S]*?)\s*```/g;
  let m;
  let last = null;
  while ((m = re.exec(s))) last = m[1];
  return last;
}

function fail(msg, details) {
  console.error(`validate-agent-output: ${msg}`);
  if (details) console.error(details);
  process.exit(1);
}

function normalizeAgentName(name) {
  return String(name ?? '').trim();
}

function requireString(obj, keyPath) {
  const parts = keyPath.split('.');
  let cur = obj;
  for (const p of parts) {
    if (cur == null || typeof cur !== 'object' || !(p in cur)) return null;
    cur = cur[p];
  }
  return typeof cur === 'string' ? cur : null;
}

function requireArray(obj, keyPath) {
  const parts = keyPath.split('.');
  let cur = obj;
  for (const p of parts) {
    if (cur == null || typeof cur !== 'object' || !(p in cur)) return null;
    cur = cur[p];
  }
  return Array.isArray(cur) ? cur : null;
}

function validateRequiredAnswers(arr) {
  const bad = [];
  for (const item of arr) {
    if (!item || typeof item !== 'object') {
      bad.push({ reason: 'item_not_object' });
      continue;
    }
    const id = typeof item.id === 'string' ? item.id : '';
    const answered = item.answered === true;
    if (!id) bad.push({ id, reason: 'missing_id' });
    if (!answered) bad.push({ id: id || '(missing)', reason: 'not_answered' });
  }
  return bad;
}

function validateByAgent(agentName, json) {
  // 通用门禁
  const agent = requireString(json, 'agent');
  if (!agent) fail('JSON 附录缺少必填字段 agent');
  if (agent !== agentName) {
    fail(`JSON 附录 agent 不匹配：期望 ${agentName}，实际 ${agent}`);
  }

  const cv = requireString(json, 'contract_version');
  if (!cv) fail('JSON 附录缺少必填字段 contract_version');
  if (cv !== '1.0') fail(`contract_version 不受支持：${cv}（期望 1.0）`);

  const skill = requireString(json, 'task.skill');
  const stage = requireString(json, 'task.stage');
  if (!skill) fail('JSON 附录缺少必填字段 task.skill');
  if (!stage) fail('JSON 附录缺少必填字段 task.stage');

  const requiredAnswers = requireArray(json, 'required_answers');
  if (!requiredAnswers) fail('JSON 附录缺少必填字段 required_answers（数组）');
  if (requiredAnswers.length === 0) fail('required_answers 不能为空');

  const bad = validateRequiredAnswers(requiredAnswers);
  if (bad.length) {
    fail('required_answers 未覆盖或未回答', JSON.stringify(bad, null, 2));
  }

  // agent 特定门禁（仅校验”结构存在性”，不校验内容真伪）
  if (agentName === 'spec-retriever') {
    const rs = json?.artifacts?.required_specs;
    if (!Array.isArray(rs) || rs.length === 0) {
      fail('spec-retriever 需在 artifacts.required_specs 提供至少一个必选规范路径');
    }
  }

  if (agentName === 'impact-analyst') {
    const parts = json?.artifacts?.parts;
    const ok =
      parts &&
      typeof parts === 'object' &&
      parts.search_terms === true &&
      parts.impact_chain === true &&
      parts.closure_summary === true &&
      parts.uncovered_risks === true;
    if (!ok) {
      fail(
        'impact-analyst 需在 artifacts.parts 标注四部分存在性：search_terms/impact_chain/closure_summary/uncovered_risks 均为 true'
      );
    }
  }

  if (agentName === 'architect') {
    const ok =
      json?.artifacts &&
      json.artifacts.modules === true &&
      json.artifacts.interface_spec === true &&
      json.artifacts.dataflow === true &&
      json.artifacts.architecture === true &&
      typeof json.artifacts.conformance === 'string' &&
      json.artifacts.conformance.length > 0;
    if (!ok) {
      fail(
        'architect 需在 artifacts 标注 modules/interface_spec/dataflow/architecture 为 true，且提供 conformance 字符串'
      );
    }
  }

  if (agentName === 'code-reviewer') {
    const issues = json?.artifacts?.issues;
    const ok =
      issues &&
      typeof issues === 'object' &&
      Array.isArray(issues.p0) &&
      Array.isArray(issues.p1) &&
      Array.isArray(issues.p2);
    if (!ok) {
      fail('code-reviewer 需在 artifacts.issues 提供 p0/p1/p2 数组');
    }
  }

  if (agentName === 'mermaid-expert') {
    const blocks = json?.artifacts?.blocks;
    const ok = Array.isArray(blocks) && blocks.length > 0 && blocks.every((b) => typeof b?.path === 'string');
    if (!ok) {
      fail('mermaid-expert 需在 artifacts.blocks 提供非空数组，且每项含 path 字段');
    }
  }

  if (agentName === 'planner') {
    const ok =
      json?.artifacts &&
      json.artifacts.scenarios === true &&
      json.artifacts.risks === true &&
      json.artifacts.strategy === true &&
      json.artifacts.dependencies === true;
    if (!ok) {
      fail('planner 需在 artifacts 标注 scenarios/risks/strategy/dependencies 为 true');
    }
  }
}

function main() {
  const args = parseArgs(process.argv);
  const agentName = normalizeAgentName(args.agent);
  if (!agentName) usage();

  if ((args.text == null || args.text === '') && !args.file) usage();
  if (args.text && args.file) {
    fail('--text 与 --file 不可同时提供');
  }

  let raw = args.text;
  if (args.file) {
    const p = path.resolve(process.cwd(), args.file);
    raw = readFileUtf8(p);
  }

  const jsonText = extractLastJsonFence(raw);
  if (!jsonText) fail('未找到 ```json fenced code block（JSON 契约附录）');

  let parsed;
  try {
    parsed = JSON.parse(jsonText);
  } catch (e) {
    fail('JSON 契约附录解析失败', e?.message);
  }

  validateByAgent(agentName, parsed);
  process.stdout.write('OK\n');
}

main();

