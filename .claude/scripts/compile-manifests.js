#!/usr/bin/env node

/**
 * Reads all skill and agent manifests, validates required fields,
 * and cross-references agent declarations.
 *
 * Usage: node scripts/compile-manifests.js [--json]
 */

const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const SKILLS_DIR = path.join(PROJECT_ROOT, 'skills');
const AGENTS_DIR = path.join(PROJECT_ROOT, 'agents');

function extractFrontmatter(text) {
  const match = text.match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
  if (!match) return null;
  try {
    return parseYaml(match[1]);
  } catch (e) {
    return { _parseError: e.message };
  }
}

function parseYaml(raw) {
  const lines = raw.split('\n');
  const root = {};
  const stack = [{ obj: root, indent: -1, mode: 'object' }];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    if (trimmed === '' || trimmed.startsWith('#')) continue;

    const indent = line.length - line.trimStart().length;

    while (stack.length > 1 && indent <= stack[stack.length - 1].indent) stack.pop();

    const parent = stack[stack.length - 1];

    if (trimmed.startsWith('- ')) {
      const itemText = trimmed.slice(2).trim();
      if (parent.mode !== 'array') continue;
      parent.obj.push(itemText.startsWith('[') && itemText.endsWith(']')
        ? itemText.slice(1, -1).split(/,\s*/).map(v => v.trim().replace(/^["'](.*)["']$/, '$1'))
        : itemText.replace(/^["'](.*)["']$/, '$1'));
      continue;
    }

    const keyMatch = line.match(/^(\s*)([\w-]+):\s*(.*)$/);
    if (!keyMatch) continue;

    const key = keyMatch[2];
    let val = keyMatch[3].trim();

    if (val === '' || val === null) {
      const nextLine = lines[i + 1];
      if (nextLine && nextLine.trim().startsWith('- ')) {
        const arr = [];
        parent.obj[key] = arr;
        stack.push({ obj: arr, indent, mode: 'array' });
        continue;
      } else if (nextLine && nextLine.match(/^\s+[\w-]+:/)) {
        const child = {};
        parent.obj[key] = child;
        stack.push({ obj: child, indent, mode: 'object' });
        continue;
      }
      val = null;
    } else if (val.startsWith('[') && val.endsWith(']')) {
      val = val.slice(1, -1).split(/,\s*/).map(v => v.trim().replace(/^["'](.*)["']$/, '$1'));
    } else {
      val = val.replace(/^["'](.*)["']$/, '$1');
    }

    parent.obj[key] = val;
  }
  return root;
}

function listManifests(dir, filename, type) {
  if (!fs.existsSync(dir)) return [];
  const results = [];
  // Check for single-file case (e.g., agents/AGENT.md)
  const flatPath = path.join(dir, filename);
  if (fs.existsSync(flatPath) && fs.statSync(flatPath).isFile()) {
    const text = fs.readFileSync(flatPath, 'utf8');
    const fm = extractFrontmatter(text);
    // Single file may contain multiple agent definitions; extract names from H2 headers
    const h2Match = [...text.matchAll(/^## (\w+) —/gm)];
    if (h2Match.length > 0) {
      for (const m of h2Match) {
        results.push({ file: flatPath, rel: path.relative(PROJECT_ROOT, flatPath), name: m[1], frontmatter: fm || {} });
      }
      return results;
    }
    // Fallback: directory name
    results.push({ file: flatPath, rel: path.relative(PROJECT_ROOT, flatPath), name: path.basename(dir), frontmatter: fm || {} });
    return results;
  }
  // Directory-per-manifest case (e.g., skills/<name>/SKILL.md)
  return fs.readdirSync(dir, { withFileTypes: true })
    .filter(e => e.isDirectory())
    .map(e => path.join(dir, e.name, filename))
    .filter(p => fs.existsSync(p))
    .map(p => {
      const text = fs.readFileSync(p, 'utf8');
      const fm = extractFrontmatter(text);
      const name = path.basename(path.dirname(p));
      return { file: p, rel: path.relative(PROJECT_ROOT, p), name, frontmatter: fm };
    });
}

function validateSkill(skill) {
  const issues = [];
  const fm = skill.frontmatter || {};
  if (fm._parseError) { issues.push(`parse-error: ${fm._parseError}`); return issues; }
  if (!fm.name) issues.push('missing: name');
  if (!fm.description) issues.push('missing: description');
  if (fm.user_invocable == null) issues.push('missing: user_invocable');
  return issues;
}

function validateAgent(agent) {
  const issues = [];
  const fm = agent.frontmatter || {};
  if (fm._parseError) { issues.push(`parse-error: ${fm._parseError}`); return issues; }
  // Single-file agents (e.g., agents/AGENT.md) don't have per-agent frontmatter
  if (!fm.name) return issues;
  if (!fm.description) issues.push('missing: description');
  if (fm.name !== agent.name) issues.push(`name mismatch: "${fm.name}" != "${agent.name}"`);
  return issues;
}

async function main() {
  const json = process.argv.includes('--json');
  const skills = listManifests(SKILLS_DIR, 'SKILL.md', 'skill');
  const agents = listManifests(AGENTS_DIR, 'AGENT.md', 'agent');
  const allIssues = [];

  for (const s of skills) {
    for (const issue of validateSkill(s)) {
      allIssues.push({ file: s.rel, type: 'skill', message: issue });
    }
  }
  for (const a of agents) {
    for (const issue of validateAgent(a)) {
      allIssues.push({ file: a.rel, type: 'agent', message: issue });
    }
  }

  // Cross-reference: agents declared in skills must exist
  const agentNames = new Set(agents.map(a => a.name || a.frontmatter?.name));
  for (const s of skills) {
    const declared = [...(s.frontmatter?.agents?.required || []), ...(s.frontmatter?.agents?.optional || [])];
    for (const name of declared) {
      if (!agentNames.has(name)) {
        allIssues.push({ file: s.rel, type: 'missing-agent', message: `"${name}" not found in agents/` });
      }
    }
  }

  if (json) {
    console.log(JSON.stringify({ skills: skills.length, agents: agents.length, issues: allIssues, passed: allIssues.length === 0 }, null, 2));
  } else {
    console.log(`Skills: ${skills.length}, Agents: ${agents.length}, Issues: ${allIssues.length}`);
    for (const issue of allIssues) {
      console.log(`  ${issue.file}: ${issue.message}`);
    }
    if (allIssues.length === 0) console.log('All checks passed.');
  }

  process.exit(allIssues.length > 0 ? 1 : 0);
}

main().catch(err => { console.error(err); process.exit(1); });
