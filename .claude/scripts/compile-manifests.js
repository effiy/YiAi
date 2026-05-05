#!/usr/bin/env node

/**
 * compile-manifests
 *
 * The Contract Compiler for the Intent-Pipeline Protocol (IPP).
 *
 * Reads all skill and agent manifests, validates cross-references,
 * checks gate coverage, and auto-generates boundary/index files.
 *
 * Usage:
 *   node scripts/compile-manifests.js [--validate] [--check-gates] [--generate]
 *   node scripts/compile-manifests.js --fix-boundaries
 *
 * Exit codes:
 *   0  All checks passed (or generation succeeded)
 *   1  Validation or gate check failed
 *   2  Argument error
 */

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const SKILLS_DIR = path.join(PROJECT_ROOT, 'skills');
const AGENTS_DIR = path.join(PROJECT_ROOT, 'agents');
const SHARED_DIR = path.join(PROJECT_ROOT, 'shared');
const FRAMEWORK_DIR = path.join(SHARED_DIR, 'framework');
const LIFECYCLE_DIR = path.join(FRAMEWORK_DIR, 'lifecycle-templates');

function parseArgs(argv) {
  const out = { validate: false, checkGates: false, generate: false, fixBoundaries: false, json: false };
  const args = argv.slice(2);
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--help' || a === '-h') {
      console.log(`Usage:
  node scripts/compile-manifests.js [options]

Options:
  --validate        Validate all manifests against the IPP schema
  --check-gates     Verify that every pipeline gate is provided by an agent
  --generate        Generate INDEX.md and shared/agent-skill-boundaries.md
  --fix-boundaries  Regenerate shared/agent-skill-boundaries.md from manifests
  --json            Output results as JSON (default: human-readable text)

Examples:
  node scripts/compile-manifests.js --validate --check-gates
  node scripts/compile-manifests.js --generate
`);
      process.exit(0);
    } else if (a === '--validate') out.validate = true;
    else if (a === '--check-gates') out.checkGates = true;
    else if (a === '--generate') out.generate = true;
    else if (a === '--fix-boundaries') out.fixBoundaries = true;
    else if (a === '--json') out.json = true;
    else {
      console.error(`Unknown option: ${a}`);
      process.exit(2);
    }
  }
  // Default to all checks if no specific flag given
  if (!out.validate && !out.checkGates && !out.generate && !out.fixBoundaries) {
    out.validate = true;
    out.checkGates = true;
    out.generate = true;
  }
  return out;
}

function extractFrontmatter(text) {
  const match = text.match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
  if (!match) return null;
  try {
    return parseYamlSubset(match[1]);
  } catch (e) {
    return { _parseError: e.message, _raw: match[1] };
  }
}

function parseYamlSubset(raw) {
  const lines = raw.split('\n');
  const root = {};
  const stack = [{ obj: root, indent: -1, key: null, mode: 'object' }];

  function parseInlineArray(s) {
    const inner = s.slice(1, -1).trim();
    if (!inner) return [];
    return inner.split(/,\s*/).map(v => v.trim().replace(/^["'](.*)["']$/, '$1'));
  }

  function parseInlineObject(s) {
    const inner = s.slice(1, -1).trim();
    const out = {};
    if (!inner) return out;
    // Very basic inline object parsing: "key: value, key2: value2"
    const pairs = inner.split(/,\s*(?=[\w-]+\s*:)/);
    for (const p of pairs) {
      const idx = p.indexOf(':');
      if (idx > 0) {
        const k = p.slice(0, idx).trim();
        const v = p.slice(idx + 1).trim().replace(/^["'](.*)["']$/, '$1');
        out[k] = v;
      }
    }
    return out;
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    if (trimmed === '' || trimmed.startsWith('#')) continue;

    const indent = line.length - line.trimStart().length;

    // Pop stack until we find the right parent
    while (stack.length > 1 && indent <= stack[stack.length - 1].indent) {
      stack.pop();
    }

    const parent = stack[stack.length - 1];

    // Array item
    if (trimmed.startsWith('- ')) {
      const itemText = trimmed.slice(2).trim();
      if (parent.mode !== 'array') {
        // Should not happen if structure is well-formed
        continue;
      }
      let item;
      if (itemText.startsWith('[') && itemText.endsWith(']')) {
        item = parseInlineArray(itemText);
      } else if (itemText.startsWith('{') && itemText.endsWith('}')) {
        item = parseInlineObject(itemText);
      } else if (itemText.includes(':')) {
        // Inline object in array item: "- name: foo  agents: [a, b]"
        item = parseYamlSubset(itemText.replace(/^-?\s*/, ''));
      } else {
        item = itemText.replace(/^["'](.*)["']$/, '$1');
      }
      parent.obj.push(item);

      // If this array item is an object, push it as a new context for nested keys
      if (item && typeof item === 'object' && !Array.isArray(item)) {
        stack.push({ obj: item, indent: indent, key: null, mode: 'object' });
      }
      continue;
    }

    // Key: value line
    const keyMatch = line.match(/^(\s*)([\w-]+):\s*(.*)$/);
    if (!keyMatch) continue;

    const key = keyMatch[2];
    let val = keyMatch[3].trim();

    if (val === '|' || val === '>') {
      // Multi-line string
      const baseIndent = indent + 2;
      const parts = [];
      i++;
      while (i < lines.length) {
        const nextLine = lines[i];
        if (nextLine.trim() === '') {
          parts.push('');
          i++;
          continue;
        }
        const nextIndent = nextLine.length - nextLine.trimStart().length;
        if (nextIndent < baseIndent) { i--; break; }
        parts.push(nextLine.slice(baseIndent));
        i++;
      }
      val = parts.join('\n');
    } else if (val === '' || val === null) {
      // Peek next line to determine array or object
      const nextLine = lines[i + 1];
      if (nextLine && nextLine.trim().startsWith('- ')) {
        const arr = [];
        parent.obj[key] = arr;
        stack.push({ obj: arr, indent: indent, key: key, mode: 'array' });
        continue;
      } else if (nextLine && nextLine.match(/^\s+[\w-]+:/)) {
        const child = {};
        parent.obj[key] = child;
        stack.push({ obj: child, indent: indent, key: key, mode: 'object' });
        continue;
      } else {
        val = null;
      }
    } else if (val.startsWith('[') && val.endsWith(']')) {
      val = parseInlineArray(val);
    } else if (val.startsWith('{') && val.endsWith('}')) {
      val = parseInlineObject(val);
    } else {
      val = val.replace(/^["'](.*)["']$/, '$1');
    }

    parent.obj[key] = val;
  }

  return root;
}

function listSkillFiles() {
  if (!fs.existsSync(SKILLS_DIR)) return [];
  const dirs = fs.readdirSync(SKILLS_DIR, { withFileTypes: true })
    .filter(e => e.isDirectory())
    .map(e => path.join(SKILLS_DIR, e.name, 'SKILL.md'))
    .filter(p => fs.existsSync(p));
  return dirs;
}

function listAgentFiles() {
  if (!fs.existsSync(AGENTS_DIR)) return [];
  return fs.readdirSync(AGENTS_DIR)
    .filter(f => f.endsWith('.md'))
    .map(f => path.join(AGENTS_DIR, f));
}

function loadManifests(files, type) {
  const out = [];
  for (const file of files) {
    const text = fs.readFileSync(file, 'utf8');
    const fm = extractFrontmatter(text);
    const name = path.basename(file, '.md');
    const rel = path.relative(PROJECT_ROOT, file);
    out.push({ file, rel, name, frontmatter: fm, type, text });
  }
  return out;
}

function validateSkillManifest(skill) {
  const issues = [];
  const fm = skill.frontmatter || {};

  if (fm._parseError) {
    issues.push({ file: skill.rel, type: 'parse-error', message: `Frontmatter parse error: ${fm._parseError}` });
    return issues;
  }

  if (!fm.name) issues.push({ file: skill.rel, type: 'missing-field', message: 'Missing required field: name' });
  if (!fm.description) issues.push({ file: skill.rel, type: 'missing-field', message: 'Missing required field: description' });
  if (fm.user_invocable == null) issues.push({ file: skill.rel, type: 'missing-field', message: 'Missing required field: user_invocable' });
  if (!fm.lifecycle) issues.push({ file: skill.rel, type: 'missing-field', message: 'Missing required field: lifecycle' });

  // Validate lifecycle template exists
  if (fm.lifecycle) {
    const lifecyclePath = path.join(LIFECYCLE_DIR, `${fm.lifecycle}.md`);
    if (!fs.existsSync(lifecyclePath)) {
      issues.push({ file: skill.rel, type: 'bad-lifecycle', message: `Lifecycle template not found: ${fm.lifecycle}` });
    }
  }

  // Validate pipeline structure (required for complex lifecycles)
  const complexLifecycles = new Set(['document-pipeline', 'code-pipeline']);
  const requiresPipeline = fm.lifecycle && complexLifecycles.has(fm.lifecycle);
  const stages = fm.pipeline?.stages || [];
  if (requiresPipeline && (!Array.isArray(stages) || stages.length === 0)) {
    issues.push({ file: skill.rel, type: 'missing-pipeline', message: 'Missing or empty pipeline.stages' });
  }
  if (Array.isArray(stages) && stages.length > 0) {
    const ids = new Set();
    for (const stage of stages) {
      if (!stage.id) issues.push({ file: skill.rel, type: 'missing-stage-id', message: 'Stage missing id' });
      else if (ids.has(stage.id)) issues.push({ file: skill.rel, type: 'duplicate-stage-id', message: `Duplicate stage id: ${stage.id}` });
      else ids.add(stage.id);

      if (!stage.name) issues.push({ file: skill.rel, type: 'missing-stage-name', message: `Stage ${stage.id} missing name` });
      if (!stage.agents && !stage.skills) {
        issues.push({ file: skill.rel, type: 'empty-stage', message: `Stage ${stage.id} has no agents or skills` });
      }
    }
  }

  // Validate agents declared
  const requiredAgents = new Set(fm.agents?.required || []);
  const optionalAgents = new Set(fm.agents?.optional || []);
  const declaredAgents = new Set([...requiredAgents, ...optionalAgents]);

  for (const stage of stages) {
    for (const agentName of (stage.agents || [])) {
      if (!declaredAgents.has(agentName)) {
        issues.push({
          file: skill.rel,
          type: 'undeclared-agent',
          message: `Stage ${stage.id} references agent "${agentName}" not listed in agents.required/optional`
        });
      }
    }
  }

  return issues;
}

function validateAgentManifest(agent) {
  const issues = [];
  const fm = agent.frontmatter || {};

  if (fm._parseError) {
    issues.push({ file: agent.rel, type: 'parse-error', message: `Frontmatter parse error: ${fm._parseError}` });
    return issues;
  }

  if (!fm.name) issues.push({ file: agent.rel, type: 'missing-field', message: 'Missing required field: name' });
  if (!fm.description) issues.push({ file: agent.rel, type: 'missing-field', message: 'Missing required field: description' });
  if (!fm.role) issues.push({ file: agent.rel, type: 'missing-field', message: 'Missing required field: role' });
  if (!fm.user_story) issues.push({ file: agent.rel, type: 'missing-field', message: 'Missing required field: user_story' });
  if (!fm.tools || !Array.isArray(fm.tools) || fm.tools.length === 0) {
    issues.push({ file: agent.rel, type: 'missing-field', message: 'Missing or empty tools array' });
  }

  // Name must match filename
  if (fm.name && fm.name !== agent.name) {
    issues.push({ file: agent.rel, type: 'name-mismatch', message: `Frontmatter name "${fm.name}" does not match filename "${agent.name}"` });
  }

  // Contract validation (new schema)
  const contract = fm.contract || {};
  if (!contract.required_answers || !Array.isArray(contract.required_answers)) {
    issues.push({ file: agent.rel, type: 'weak-contract', message: 'Missing or invalid contract.required_answers' });
  } else if (contract.required_answers.length === 0 && (!contract.artifacts || contract.artifacts.length === 0)) {
    issues.push({ file: agent.rel, type: 'weak-contract', message: 'Empty contract.required_answers with no artifacts (unmigrated agent?)' });
  }

  return issues;
}

function checkGates(skills, agents) {
  const issues = [];

  // Build gate registry: gateId -> [agentName]
  const gateProviders = {};
  for (const agent of agents) {
    const fm = agent.frontmatter || {};
    const gates = fm.contract?.gates_provided || [];
    for (const g of gates) {
      if (!gateProviders[g]) gateProviders[g] = [];
      gateProviders[g].push(fm.name || agent.name);
    }
  }

  for (const skill of skills) {
    const fm = skill.frontmatter || {};
    const stages = fm.pipeline?.stages || [];
    for (const stage of stages) {
      for (const gate of (stage.gates || [])) {
        if (!gateProviders[gate]) {
          issues.push({
            file: skill.rel,
            type: 'orphan-gate',
            message: `Stage ${stage.id} gate "${gate}" is not provided by any agent`
          });
        } else if (stage.agents) {
          // Check that at least one agent in this stage provides the gate
          const stageAgents = new Set(stage.agents);
          const providers = gateProviders[gate].filter(a => stageAgents.has(a));
          if (providers.length === 0) {
            issues.push({
              file: skill.rel,
              type: 'gate-mismatch',
              message: `Stage ${stage.id} gate "${gate}" is provided by [${gateProviders[gate].join(', ')}], none of which are in this stage`
            });
          }
        }
      }
    }
  }

  return { issues, gateProviders };
}

function generateIndex(skills, agents) {
  const lines = [];
  lines.push('# IPP Dependency Index');
  lines.push('');
  lines.push('> Auto-generated by `scripts/compile-manifests.js`. Do not edit manually.');
  lines.push('');

  lines.push('## Skills');
  lines.push('');
  lines.push('| Skill | Invocable | Lifecycle | Stages | Required Agents |');
  lines.push('|-------|-----------|-----------|--------|-----------------|');
  for (const skill of skills) {
    const fm = skill.frontmatter || {};
    const stages = (fm.pipeline?.stages || []).length;
    const agents = (fm.agents?.required || []).join(', ') || '—';
    lines.push(`| ${fm.name || skill.name} | ${fm.user_invocable ? 'Yes' : 'No'} | ${fm.lifecycle || '—'} | ${stages} | ${agents} |`);
  }
  lines.push('');

  lines.push('## Agents');
  lines.push('');
  lines.push('| Agent | Role | Tools | Gates Provided |');
  lines.push('|-------|------|-------|----------------|');
  for (const agent of agents) {
    const fm = agent.frontmatter || {};
    const role = (fm.role || '—').replace(/\|/g, '\\|');
    const tools = (fm.tools || []).join(', ') || '—';
    const gates = (fm.contract?.gates_provided || []).join(', ') || '—';
    lines.push(`| ${fm.name || agent.name} | ${role} | ${tools} | ${gates} |`);
  }
  lines.push('');

  lines.push('## Pipeline Stage Map');
  lines.push('');
  for (const skill of skills) {
    const fm = skill.frontmatter || {};
    lines.push(`### ${fm.name || skill.name}`);
    lines.push('');
    lines.push('| Stage | Name | Agents | Gates | Optional | Parallel |');
    lines.push('|-------|------|--------|-------|----------|----------|');
    for (const stage of (fm.pipeline?.stages || [])) {
      const agents = (stage.agents || []).join(', ') || (stage.skills || []).join(', ') || '—';
      const gates = (stage.gates || []).join(', ') || '—';
      lines.push(`| ${stage.id || '—'} | ${stage.name || '—'} | ${agents} | ${gates} | ${stage.optional ? 'Yes' : 'No'} | ${stage.parallel ? 'Yes' : 'No'} |`);
    }
    lines.push('');
  }

  return lines.join('\n');
}

function generateBoundaries(skills, agents) {
  const lines = [];
  lines.push('# Skill / Agent Boundaries');
  lines.push('');
  lines.push('> Auto-generated by `scripts/compile-manifests.js` from manifest frontmatter.');
  lines.push('');

  lines.push('## Agent Inventory');
  lines.push('');
  lines.push('| Agent | Role | Triggers |');
  lines.push('|-------|------|----------|');
  for (const agent of agents) {
    const fm = agent.frontmatter || {};
    const role = (fm.role || '—').replace(/\|/g, '\\|');
    const triggers = (fm.triggers || []).join(', ') || '—';
    lines.push(`| \`${fm.name || agent.name}\` | ${role} | ${triggers} |`);
  }
  lines.push('');

  lines.push('## Skill / Agent Pairings');
  lines.push('');
  lines.push('| Skill | Stage | Agent | Purpose |');
  lines.push('|-------|-------|-------|---------|');
  for (const skill of skills) {
    const fm = skill.frontmatter || {};
    for (const stage of (fm.pipeline?.stages || [])) {
      for (const agentName of (stage.agents || [])) {
        const agent = agents.find(a => (a.frontmatter?.name || a.name) === agentName);
        const role = agent?.frontmatter?.role || '—';
        lines.push(`| \`${fm.name || skill.name}\` | ${stage.id} (${stage.name}) | \`${agentName}\` | ${role.replace(/\|/g, '\\|')} |`);
      }
    }
  }
  lines.push('');

  lines.push('## Gate Coverage');
  lines.push('');
  lines.push('| Gate | Provided By | Consumed By |');
  lines.push('|------|-------------|-------------|');

  // Recompute gateProviders and consumers
  const gateProviders = {};
  const gateConsumers = {};
  for (const agent of agents) {
    const fm = agent.frontmatter || {};
    for (const g of (fm.contract?.gates_provided || [])) {
      if (!gateProviders[g]) gateProviders[g] = [];
      gateProviders[g].push(fm.name || agent.name);
    }
  }
  for (const skill of skills) {
    const fm = skill.frontmatter || {};
    for (const stage of (fm.pipeline?.stages || [])) {
      for (const g of (stage.gates || [])) {
        if (!gateConsumers[g]) gateConsumers[g] = [];
        gateConsumers[g].push(`${fm.name || skill.name}::${stage.id}`);
      }
    }
  }

  const allGates = new Set([...Object.keys(gateProviders), ...Object.keys(gateConsumers)]);
  for (const g of [...allGates].sort()) {
    const providers = (gateProviders[g] || ['(none)']).join(', ');
    const consumers = (gateConsumers[g] || ['(none)']).join(', ');
    lines.push(`| ${g} | ${providers} | ${consumers} |`);
  }
  lines.push('');

  return lines.join('\n');
}

async function main() {
  const args = parseArgs(process.argv);

  const skillFiles = listSkillFiles();
  const agentFiles = listAgentFiles();

  const skills = loadManifests(skillFiles, 'skill');
  const agents = loadManifests(agentFiles, 'agent');

  const allIssues = [];

  if (args.validate) {
    for (const skill of skills) {
      allIssues.push(...validateSkillManifest(skill));
    }
    for (const agent of agents) {
      allIssues.push(...validateAgentManifest(agent));
    }
  }

  let gateResult = { issues: [], gateProviders: {} };
  if (args.checkGates) {
    gateResult = checkGates(skills, agents);
    allIssues.push(...gateResult.issues);
  }

  // Agent existence check (cross-reference)
  const agentNames = new Set(agents.map(a => a.frontmatter?.name || a.name));
  for (const skill of skills) {
    const fm = skill.frontmatter || {};
    for (const agentName of (fm.agents?.required || [])) {
      if (!agentNames.has(agentName)) {
        allIssues.push({
          file: skill.rel,
          type: 'missing-agent-file',
          message: `Required agent "${agentName}" has no file in agents/`
        });
      }
    }
    for (const agentName of (fm.agents?.optional || [])) {
      if (!agentNames.has(agentName)) {
        allIssues.push({
          file: skill.rel,
          type: 'missing-agent-file',
          message: `Optional agent "${agentName}" has no file in agents/`
        });
      }
    }
  }

  if (args.json) {
    const out = {
      skills: skills.length,
      agents: agents.length,
      issues: allIssues,
      passed: allIssues.length === 0
    };
    console.log(JSON.stringify(out, null, 2));
  } else {
    console.log('# Contract Compiler Report\n');
    console.log(`Skills scanned: ${skills.length}`);
    console.log(`Agents scanned: ${agents.length}`);
    console.log(`Issues found: ${allIssues.length}\n`);

    if (allIssues.length > 0) {
      const byType = {};
      for (const issue of allIssues) {
        if (!byType[issue.type]) byType[issue.type] = [];
        byType[issue.type].push(issue);
      }
      for (const [type, issues] of Object.entries(byType)) {
        console.log(`## ${type} (${issues.length})`);
        for (const issue of issues) {
          console.log(`- ${issue.file}: ${issue.message}`);
        }
        console.log('');
      }
    } else {
      console.log('All checks passed.');
    }
  }

  if (args.generate || args.fixBoundaries) {
    const indexContent = generateIndex(skills, agents);
    const boundariesContent = generateBoundaries(skills, agents);

    const indexPath = path.join(PROJECT_ROOT, 'INDEX.md');
    const boundariesPath = path.join(SHARED_DIR, 'agent-skill-boundaries.md');

    await fsp.writeFile(indexPath, indexContent, 'utf8');
    await fsp.writeFile(boundariesPath, boundariesContent, 'utf8');

    if (!args.json) {
      console.log(`Generated: ${path.relative(PROJECT_ROOT, indexPath)}`);
      console.log(`Generated: ${path.relative(PROJECT_ROOT, boundariesPath)}`);
    }
  }

  if (allIssues.some(i => !['weak-contract'].includes(i.type))) {
    process.exit(1);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
