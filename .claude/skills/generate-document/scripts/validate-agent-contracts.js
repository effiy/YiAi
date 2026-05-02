#!/usr/bin/env node

/**
 * validate-agent-contracts
 *
 * Goal: lightweight contract validation, verifying whether agent names referenced in skill files:
 *   1. Have a corresponding .md file in the agents/ directory
 *   2. Are listed in shared/agent-skill-boundaries.md
 *
 * Usage:
 *   node scripts/validate-agent-contracts.js [--fix] [--strict]
 *
 * Options:
 *   --fix     Only output suggested agent name mapping table
 *   --strict  Treat boundaries missing as error (default: warning only)
 *
 * Exit codes:
 *   0 no issues
 *   1 orphaned agent references found
 */

const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '../../..');
const AGENTS_DIR = path.join(PROJECT_ROOT, 'agents');
const SHARED_DIR = path.join(PROJECT_ROOT, 'shared');
const SKILLS_DIR = path.join(PROJECT_ROOT, 'skills');

const BOUNDARIES_FILE = path.join(SHARED_DIR, 'agent-skill-boundaries.md');

// Known non-agent skill/system identifiers (avoid false positives)
const KNOWN_NON_AGENTS = new Set([
  'generate-document', 'implement-code', 'import-docs', 'wework-bot',
  'code-review', 'e2e-testing', 'find-agents', 'find-skills',
  'search-first', 'verification-loop', 'weekly', 'init', 'from-weekly',
  'weekly-analyzer', 'doc-generate-reporter', 'code-impl-reporter',
  'message-pusher', 'mcp-fallback-contract', 'impact-analysis-contract',
  'agent-output-contract', 'document-contracts', 'evidence-and-uncertainty',
  'path-conventions', 'component-contract', 'behavioral-guidelines',
  'mermaid-expert', 'spec-retriever', 'agent-skill-boundaries',
  'orchestration-logging', 'orchestration', 'agent-contract',
  'workflow', 'process-summary', 'artifact-contracts', 'verification-gate',
  'code-implementation', 'implement-code-testing', 'e2e-testing-md',
  'test-page', 'natural-week',
  'document-pipeline', 'code-pipeline', 'default-pipeline',
  'execution-memory', 'self-improve', 'security', 'performance',
  // Common programming keywords/variable names
  'const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while',
  'async', 'await', 'try', 'catch', 'throw', 'new', 'this', 'true', 'false',
  'null', 'undefined', 'typeof', 'instanceof', 'import', 'export', 'default',
  'from', 'as', 'class', 'extends', 'super', 'static', 'get', 'set',
  'is', 'has', 'can', 'should', 'will', 'do', 'did', 'are', 'was', 'were',
  'not', 'and', 'or', 'but', 'with', 'without', 'into', 'onto', 'upon',
  // Common technical terms
  'node', 'npm', 'npx', 'git', 'bash', 'python', 'uv', 'pip', 'pip3',
  'docker', 'kubectl', 'helm', 'terraform', 'ansible',
  'main', 'master', 'develop', 'staging', 'production', 'prod',
  'docs', 'skills', 'agents', 'shared', 'commands', 'eval', 'scripts',
  'src', 'dist', 'build', 'public', 'assets', 'config',
  // HTML/CSS/test attributes
  'data-testid', 'aria-label', 'aria-hidden', 'role', 'class', 'id',
  'type', 'name', 'value', 'placeholder', 'disabled', 'readonly',
  'style', 'href', 'src', 'alt', 'title', 'target', 'rel',
  'ref', 'reactive', 'computed', 'watch', 'emits', 'props', 'slots',
  'window', 'document', 'console', 'localstorage', 'sessionstorage',
  // Common action verbs
  'load', 'save', 'create', 'update', 'delete', 'handle', 'toggle',
  'reset', 'submit', 'fetch', 'send', 'receive', 'parse', 'stringify',
  'format', 'validate', 'sanitize', 'encode', 'decode', 'encrypt', 'decrypt',
  'compress', 'decompress', 'upload', 'download', 'render', 'mount',
  // CLI/config terms
  'command', 'option', 'flag', 'arg', 'args', 'env', 'ext', 'exts',
  'prefix', 'suffix', 'path', 'dir', 'file', 'filename', 'content',
  'list', 'item', 'items', 'entry', 'entries', 'key', 'keys', 'value', 'values',
  'session', 'sessions', 'token', 'tokens', 'header', 'headers',
  'body', 'query', 'params', 'param', 'route', 'router', 'middleware',
  // Status/result words
  'success', 'error', 'failed', 'pending', 'overwritten', 'created',
  'updated', 'deleted', 'skipped', 'ignored', 'included', 'excluded',
  // Other common false positives
  'stage', 'gate', 'notify', 'memory', 'skill', 'agent', 'mcp', 'other',
  'kind', 'case', 'good', 'bad', 'neutral', 'lesson', 'text',
  'scenario', 'operation', 'operations', 'tags', 'description',
  'triggers', 'tools', 'user', 'story', 'model', 'api', 'url', 'uri',
  'json', 'yaml', 'yml', 'xml', 'csv', 'html', 'css', 'js', 'ts', 'md',
  'filesystem', 'browser', 'server', 'client',
  // CSS / testid class names (common false positives)
  'toolbar-container', 'toolbar-download-btn', 'toolbar-filename-input',
  'toolbar-result', 'toolbar-error-msg', 'testid',
]);

function parseArgs(argv) {
  const out = { fix: false, strict: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') {
      console.log(`Usage:
  node scripts/validate-agent-contracts.js [--fix] [--strict]

Options:
  --fix     Only output suggested agent name mapping table
  --strict  Treat boundaries missing as error (default warning only)

Examples:
  node scripts/validate-agent-contracts.js
  node scripts/validate-agent-contracts.js --strict
`);
      process.exit(0);
    } else if (a === '--fix') out.fix = true;
    else if (a === '--strict') out.strict = true;
  }
  return out;
}

function listAgentFiles() {
  if (!fs.existsSync(AGENTS_DIR)) return new Set();
  return new Set(
    fs.readdirSync(AGENTS_DIR)
      .filter((f) => f.endsWith('.md'))
      .map((f) => f.replace(/\.md$/, ''))
  );
}

function extractAgentsFromBoundaries() {
  const agents = new Set();
  if (!fs.existsSync(BOUNDARIES_FILE)) return agents;

  const text = fs.readFileSync(BOUNDARIES_FILE, 'utf8');
  // Match `agent-name` in tables and name in YAML frontmatter
  const tableMatches = text.match(/`([a-z][a-z0-9-]*)`/g) || [];
  tableMatches.forEach((m) => {
    const name = m.slice(1, -1);
    if (!KNOWN_NON_AGENTS.has(name)) agents.add(name);
  });

  return agents;
}

function extractAgentRefsFromFile(filePath) {
  const refs = [];
  if (!fs.existsSync(filePath)) return refs;

  const text = fs.readFileSync(filePath, 'utf8');
  const lines = text.split('\n');

  // Match agent references in Markdown:
  // 1. Backtick-wrapped: `agent-name`
  // 2. Agent names in tables
  // 3. Agent references in skill contracts
  const agentPattern = /`([a-z][a-z0-9-]*)`/g;

  lines.forEach((line, idx) => {
    let m;
    while ((m = agentPattern.exec(line)) !== null) {
      const name = m[1];
      if (KNOWN_NON_AGENTS.has(name)) continue;
      // Filter common non-agent references (file paths, command names)
      if (name.match(/^(node|npm|npx|git|bash|python|uv|pip)$/)) continue;
      if (name.match(/^(docs|skills|agents|shared|commands|eval)$/)) continue;
      refs.push({ name, line: idx + 1, text: line.trim() });
    }
  });

  return refs;
}

function findSkillFiles() {
  const files = [];
  if (!fs.existsSync(SKILLS_DIR)) return files;

  const skillDirs = fs.readdirSync(SKILLS_DIR, { withFileTypes: true })
    .filter((e) => e.isDirectory())
    .map((e) => path.join(SKILLS_DIR, e.name));

  for (const dir of skillDirs) {
    const skillMd = path.join(dir, 'SKILL.md');
    if (fs.existsSync(skillMd)) files.push(skillMd);

    const rulesDir = path.join(dir, 'rules');
    if (fs.existsSync(rulesDir)) {
      fs.readdirSync(rulesDir)
        .filter((f) => f.endsWith('.md'))
        .forEach((f) => files.push(path.join(rulesDir, f)));
    }
  }

  return files;
}

function main() {
  const args = parseArgs(process.argv);

  const agentFiles = listAgentFiles();
  const boundariesAgents = extractAgentsFromBoundaries();
  const skillFiles = findSkillFiles();

  if (args.fix) {
    // Output suggested agent name mapping table
    console.log('# Suggested Agent Name Mapping Fixes\n');
    console.log('| Name in file | Suggested change | Reason |');
    console.log('|---|---|---|');

    const knownMappings = {
      'spec-retriever': 'docs-retriever / codes-retriever',
      'impact-analyst': 'doc-impact-analyzer / code-impact-analyzer',
      'architect': 'doc-architect / codes-builder',
      'planner': 'doc-architect / codes-builder',
      'quality-tracker': 'doc-quality-tracker',
      'knowledge-curator': 'docs-builder',
      'impl-reporter': 'code-impl-reporter',
      'generate-reporter': 'doc-generate-reporter',
    };

    for (const [oldName, newName] of Object.entries(knownMappings)) {
      console.log(`| \`${oldName}\` | \`${newName}\` | Inconsistent with actual agent file name |`);
    }
    return;
  }

  const issues = [];
  const warnings = [];

  // 1. Check whether agents listed in boundaries have corresponding files
  for (const name of boundariesAgents) {
    if (!agentFiles.has(name)) {
      issues.push({
        type: 'boundaries-orphan',
        message: `agent-skill-boundaries.md references \`${name}\`, but agents/${name}.md does not exist`,
        file: 'shared/agent-skill-boundaries.md',
      });
    }
  }

  // 2. Check agent references in skill files
  for (const skillFile of skillFiles) {
    const refs = extractAgentRefsFromFile(skillFile);
    const seen = new Set();

    for (const ref of refs) {
      if (seen.has(ref.name)) continue;
      seen.add(ref.name);

      const relPath = path.relative(PROJECT_ROOT, skillFile);

      // Check for corresponding file
      if (!agentFiles.has(ref.name)) {
        // May be a known legacy name
        if (['spec-retriever', 'impact-analyst', 'architect', 'planner', 'quality-tracker', 'knowledge-curator'].includes(ref.name)) {
          issues.push({
            type: 'orphan-legacy',
            message: `\`${ref.name}\` is a legacy name, inconsistent with actual agent file`,
            file: relPath,
            line: ref.line,
          });
        } else {
          issues.push({
            type: 'orphan-unknown',
            message: `References \`${ref.name}\`, but agents/${ref.name}.md does not exist`,
            file: relPath,
            line: ref.line,
          });
        }
      }

      // Check whether listed in boundaries
      if (!boundariesAgents.has(ref.name) && agentFiles.has(ref.name)) {
        warnings.push({
          type: 'boundaries-missing',
          message: `References \`${ref.name}\`, but not listed in agent-skill-boundaries.md`,
          file: relPath,
          line: ref.line,
        });
      }
    }
  }

  // 3. Output results
  console.log('# Agent Contract Validation Report\n');
  console.log(`Scanned files: ${skillFiles.length} skill/rule files`);
  console.log(`agents/ directory: ${agentFiles.size} agent files`);
  console.log(`boundaries registered: ${boundariesAgents.size} agents`);
  console.log('');

  if (issues.length === 0 && warnings.length === 0) {
    console.log('✅ All agent references consistent, no issues.\n');
    process.exit(0);
  }

  if (issues.length > 0) {
    console.log(`## ❌ Errors (${issues.length})\n`);
    for (const issue of issues) {
      const loc = issue.line ? `${issue.file}:${issue.line}` : issue.file;
      console.log(`- [${issue.type}] ${loc} — ${issue.message}`);
    }
    console.log('');
  }

  if (warnings.length > 0) {
    console.log(`## ⚠️ Warnings (${warnings.length})\n`);
    for (const warn of warnings) {
      console.log(`- [${warn.type}] ${warn.file}:${warn.line} — ${warn.message}`);
    }
    console.log('');
  }

  if (issues.some((i) => i.type === 'orphan-legacy')) {
    console.log('💡 Tip: Use `--fix` to view suggested agent name mapping fix table.\n');
  }

  if (args.strict && warnings.length > 0) {
    process.exit(1);
  }

  if (issues.length > 0) {
    process.exit(1);
  }
}

main();
