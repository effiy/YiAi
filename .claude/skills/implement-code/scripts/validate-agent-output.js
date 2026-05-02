#!/usr/bin/env node

/**
 * validate-agent-output
 *
 * Goal: make agent "required answers coverage, structured artifact existence" contracts executable gates.
 * Convention: agent output must contain a ```json fenced code block at the end, field spec see shared/agent-output-contract.md
 *
 * Usage:
 *   node scripts/validate-agent-output.js --agent <name> (--text "<raw>" | --file <path>)
 *
 * Exit codes:
 *   0 passed
 *   1 failed
 *   2 argument error
 */

const fs = require('fs');
const path = require('path');

function printHelp(stream) {
  const out = stream || process.stdout;
  out.write(`Usage:
  node scripts/validate-agent-output.js --agent <agent-name> (--text "<raw>" | --file <path>)

Examples:
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
  // Universal gate
  const agent = requireString(json, 'agent');
  if (!agent) fail('JSON appendix missing required field: agent');
  if (agent !== agentName) {
    fail(`JSON appendix agent mismatch: expected ${agentName}, actual ${agent}`);
  }

  const cv = requireString(json, 'contract_version');
  if (!cv) fail('JSON appendix missing required field: contract_version');
  if (cv !== '1.0') fail(`contract_version not supported: ${cv} (expected 1.0)`);

  const skill = requireString(json, 'task.skill');
  const stage = requireString(json, 'task.stage');
  if (!skill) fail('JSON appendix missing required field: task.skill');
  if (!stage) fail('JSON appendix missing required field: task.stage');

  const requiredAnswers = requireArray(json, 'required_answers');
  if (!requiredAnswers) fail('JSON appendix missing required field: required_answers (array)');
  if (requiredAnswers.length === 0) fail('required_answers cannot be empty');

  const bad = validateRequiredAnswers(requiredAnswers);
  if (bad.length) {
    fail('required_answers not covered or not answered', JSON.stringify(bad, null, 2));
  }

  // Agent-specific gates (only check "structural existence", not content authenticity)
  if (agentName === 'spec-retriever') {
    const rs = json?.artifacts?.required_specs;
    if (!Array.isArray(rs) || rs.length === 0) {
      fail('spec-retriever must provide at least one required spec path in artifacts.required_specs');
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
        'impact-analyst must mark existence of four parts in artifacts.parts: search_terms/impact_chain/closure_summary/uncovered_risks all true'
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
        'architect must mark modules/interface_spec/dataflow/architecture as true in artifacts, and provide conformance string'
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
      fail('code-reviewer must provide p0/p1/p2 arrays in artifacts.issues');
    }
  }

  if (agentName === 'mermaid-expert') {
    const blocks = json?.artifacts?.blocks;
    const ok = Array.isArray(blocks) && blocks.length > 0 && blocks.every((b) => typeof b?.path === 'string');
    if (!ok) {
      fail('mermaid-expert must provide non-empty array in artifacts.blocks, with each item containing path field');
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
      fail('planner must mark scenarios/risks/strategy/dependencies as true in artifacts');
    }
  }
}

function main() {
  const args = parseArgs(process.argv);
  const agentName = normalizeAgentName(args.agent);
  if (!agentName) usage();

  if ((args.text == null || args.text === '') && !args.file) usage();
  if (args.text && args.file) {
    fail('--text and --file cannot be provided simultaneously');
  }

  let raw = args.text;
  if (args.file) {
    const p = path.resolve(process.cwd(), args.file);
    raw = readFileUtf8(p);
  }

  const jsonText = extractLastJsonFence(raw);
  if (!jsonText) fail('No ```json fenced code block found (JSON contract appendix)');

  let parsed;
  try {
    parsed = JSON.parse(jsonText);
  } catch (e) {
    fail('JSON contract appendix parsing failed', e?.message);
  }

  validateByAgent(agentName, parsed);
  process.stdout.write('OK\n');
}

main();
