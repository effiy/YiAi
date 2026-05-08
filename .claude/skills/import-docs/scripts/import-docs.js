#!/usr/bin/env node

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const http = require('https');
const util = require('util');
const { execFile } = require('child_process');
const execFileAsync = util.promisify(execFile);

/**
 * 从起始目录向上查找项目根目录
 * 优先检测 .git，否则检测 .claude/ 目录
 * @param {string} startDir - 起始目录
 * @returns {string} 项目根目录
 */
function findProjectRoot(startDir) {
  let currentDir = path.resolve(startDir);
  while (true) {
    if (fs.existsSync(path.join(currentDir, '.git'))) {
      if (path.basename(currentDir) === '.claude') return path.dirname(currentDir);
      return currentDir;
    }
    if (fs.existsSync(path.join(currentDir, '.claude'))) {
      return currentDir;
    }
    const parentDir = path.dirname(currentDir);
    if (parentDir === currentDir) break;
    currentDir = parentDir;
  }
  return path.resolve(startDir);
}

/**
 * 递归查找 .md 文件，优先使用 git ls-files，回退到文件系统遍历
 * 排除 .git 和 node_modules 目录
 * @param {string} dir - 起始目录
 * @param {string} projectRoot - git 仓库根目录
 * @returns {Promise<string[]>} 文件路径列表
 */
async function findMdFiles(dir, projectRoot) {
  const dirRel = path.relative(projectRoot, dir);
  const canUseGit = projectRoot && !dirRel.startsWith('..') && !path.isAbsolute(dirRel);

  if (canUseGit) {
    try {
      await fsp.access(path.join(projectRoot, '.git'));
      const { stdout } = await execFileAsync('git', ['-c', 'core.quotePath=false', '-C', projectRoot, 'ls-files', '--cached', '--others', '--exclude-standard'], {
        maxBuffer: 50 * 1024 * 1024
      });
      const dirRelPosix = dirRel.split(path.sep).join('/');
      const gitFiles = stdout
        .split('\n')
        .filter(Boolean)
        .filter(file => dirRelPosix === '' || file === dirRelPosix || file.startsWith(dirRelPosix + '/'))
        .filter(file => path.extname(file).toLowerCase() === '.md')
        .filter(file => !file.split('/').some(part => part === '.git' || part === 'node_modules'))
        .map(file => path.join(projectRoot, file))
        .filter(fullPath => {
          try { return fs.statSync(fullPath).isFile(); } catch { return false; }
        });
      if (gitFiles.length > 0) return gitFiles;
    } catch {
      // 回退到文件系统遍历
    }
  }

  const results = [];

  async function traverse(currentDir) {
    const entries = await fsp.readdir(currentDir, { withFileTypes: true });

    for (const entry of entries) {
      if (entry.name === '.git' || entry.name === 'node_modules') {
        continue;
      }
      const fullPath = path.join(currentDir, entry.name);

      if (entry.isDirectory() && !entry.isSymbolicLink()) {
        await traverse(fullPath);
      } else if (entry.isFile() && path.extname(entry.name).toLowerCase() === '.md') {
        results.push(fullPath);
      }
    }
  }

  await traverse(dir);
  return results;
}

/** X-Token 仅从系统环境变量 `API_X_TOKEN` 读取，不接受配置文件或其它来源。 */
function readApiXTokenFromEnv() {
  const v = process.env.API_X_TOKEN;
  if (v == null || v === '') return null;
  const t = String(v).trim();
  return t || null;
}

function request(apiUrl, endpoint, method, token, data) {
  return new Promise((resolve, reject) => {
    const url = new URL(endpoint, apiUrl);
    const postData = data ? JSON.stringify(data) : null;

    const requestOptions = {
      hostname: url.hostname,
      port: url.port || 443,
      path: url.pathname + url.search,
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    if (token) {
      requestOptions.headers['X-Token'] = token;
    }

    if (postData) {
      requestOptions.headers['Content-Length'] = Buffer.byteLength(postData);
    }

    const req = http.request(requestOptions, (res) => {
      let body = '';
      res.on('data', (chunk) => {
        body += chunk;
      });
      res.on('end', () => {
        try {
          resolve(JSON.parse(body));
        } catch (e) {
          resolve(body);
        }
      });
    });

    req.on('error', reject);

    if (postData) {
      req.write(postData);
    }

    req.end();
  });
}

async function getExistingSessions(apiUrl, token) {
  const result = await request(apiUrl, '/', 'POST', token, {
    module_name: 'services.database.data_service',
    method_name: 'query_documents',
    parameters: {
      cname: 'sessions',
      limit: 10000
    }
  });

  const sessions = result?.data?.list || [];
  const existingSet = new Set();

  for (const session of sessions) {
    if (session.file_path) {
      existingSet.add(session.file_path);
    }
  }

  return { sessions, existingSet };
}

async function importFile(fullPath, basePath, apiUrl, token, existingSet, prefix) {
  const relativePath = path.relative(basePath, fullPath)
    .split(path.sep)
    .map(part => part.replace(/\s+/g, '_'))
    .join('/');

  const baseDirName = path.basename(basePath).replace(/\s+/g, '_');

  const targetPathParts = [];
  if (prefix.length > 0) {
    targetPathParts.push(...prefix.map(part => part.replace(/\s+/g, '_')));
  }
  targetPathParts.push(baseDirName);
  targetPathParts.push(relativePath);

  const targetPath = targetPathParts.join('/');
  const allParts = targetPath.split('/');
  const title = allParts[allParts.length - 1];
  const tags = allParts.slice(0, -1);
  const isDuplicate = existingSet.has(targetPath);
  const content = await fsp.readFile(fullPath, 'utf-8');

  await request(apiUrl, '/write-file', 'POST', token, {
    target_file: targetPath,
    content,
    is_base64: false
  });

  if (isDuplicate) {
    return { status: 'overwritten', path: targetPath };
  }

  const now = Date.now();
  const random = Math.random().toString(36).slice(2, 11);
  await request(apiUrl, '/', 'POST', token, {
    module_name: 'services.database.data_service',
    method_name: 'create_document',
    parameters: {
      cname: 'sessions',
      data: {
        url: `app-session://${now}-${random}`,
        title,
        file_path: targetPath,
        messages: [],
        tags,
        isFavorite: false,
        createdAt: now,
        updatedAt: now,
        lastAccessTime: now
      }
    }
  });

  existingSet.add(targetPath);
  return { status: 'ok', path: targetPath };
}

function printHelp() {
  console.log(`
Document import — sync local .md files to remote documentation API

Usage:
  node .claude/skills/import-docs/scripts/import-docs.js import [options]
  node .claude/skills/import-docs/scripts/import-docs.js list [options]
  node .claude/skills/import-docs/scripts/import-docs.js [options]   # defaults to import

Options:
  --workspace, -w  Recursively scan all .md files in project (excludes .git, node_modules)
  --dir, -d        Single directory to import (default: auto-detect project root)
  --api-url, -a    API base URL (default: https://api.effiy.cn)
  --prefix, -p     Path prefix (comma-separated, e.g. Projects,YourNamespace)
  --help, -h       Show this help message

Environment:
  API_X_TOKEN      Required for import. Set via system environment variable.
`);
}

async function main() {
  const args = process.argv.slice(2);
  let command = 'import';
  let argStartIndex = 0;

  if (args[0] && !args[0].startsWith('-')) {
    command = args[0];
    argStartIndex = 1;
  }

  if (!['import', 'list'].includes(command)) {
    console.error(`Error: unsupported command "${command}". Use "import" or "list".`);
    process.exit(1);
  }

  const config = {
    command,
    dir: null,
    token: readApiXTokenFromEnv(),
    apiUrl: 'https://api.effiy.cn',
    prefix: [],
    workspace: false
  };

  for (let i = argStartIndex; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--dir' || arg === '-d') {
      config.dir = path.resolve(args[++i]);
    } else if (arg === '--token' || arg === '-t') {
      console.error('Error: --token 已禁用。出于安全原因，仅允许使用系统环境变量 API_X_TOKEN。');
      process.exit(1);
    } else if (arg === '--api-url' || arg === '-a') {
      config.apiUrl = args[++i];
    } else if (arg === '--prefix' || arg === '-p') {
      config.prefix = args[++i].split(',').map(p => p.trim()).filter(Boolean);
    } else if (arg === '--workspace' || arg === '-w') {
      config.workspace = true;
    } else if (arg === '--help' || arg === '-h') {
      printHelp();
      process.exit(0);
    }
  }

  const cwd = process.cwd();
  const projectRoot = findProjectRoot(cwd);
  const scanDir = config.dir || projectRoot;

  console.log('=== Document import ===');
  console.log('Command:', config.command);
  console.log('Mode:', config.workspace ? 'workspace' : 'single');
  console.log('Scan dir:', scanDir);
  if (config.command === 'import') {
    console.log('API:', config.apiUrl);
    if (config.prefix.length > 0) {
      console.log('Prefix:', config.prefix.join('/'));
    }
  }
  console.log();

  const files = await findMdFiles(scanDir, projectRoot);

  if (files.length === 0) {
    console.log('No .md files found');
    return;
  }

  console.log(`Found ${files.length} .md files`);

  if (config.command === 'list') {
    for (const file of files.sort()) {
      const relativePath = path.relative(projectRoot, file).split(path.sep).join('/');
      console.log(`- ${relativePath}`);
    }
    return;
  }

  if (!config.token) {
    console.error('Error: missing API_X_TOKEN environment variable');
    process.exit(1);
  }

  console.log('Querying existing sessions...');
  const { existingSet } = await getExistingSessions(config.apiUrl, config.token);
  console.log(`Found ${existingSet.size} existing sessions with file_path`);
  console.log();

  const stats = { ok: 0, overwritten: 0, failed: 0 };

  for (let i = 0; i < files.length; i++) {
    const fullPath = files[i];
    const relativePath = path.relative(projectRoot, fullPath).split(path.sep).join('/');
    console.log(`[${i + 1}/${files.length}] ${relativePath}`);

    try {
      const result = await importFile(fullPath, projectRoot, config.apiUrl, config.token, existingSet, config.prefix);
      if (result.status === 'ok') {
        console.log(`  ✓ ${result.path} (created)`);
        stats.ok++;
      } else if (result.status === 'overwritten') {
        console.log(`  ✓ ${result.path} (file overwritten, session exists)`);
        stats.overwritten++;
      }
    } catch (error) {
      console.log(`  ✗ ${relativePath} - ${error.message}`);
      stats.failed++;
    }
  }

  console.log();
  console.log(`Done: ${stats.ok} created, ${stats.overwritten} overwritten, ${stats.failed} failed`);

  if (stats.failed > 0) {
    process.exit(1);
  }
}

main().catch(error => {
  console.error('Error:', error.message);
  process.exit(1);
});
