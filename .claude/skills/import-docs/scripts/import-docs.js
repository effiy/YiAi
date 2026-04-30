#!/usr/bin/env node

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const http = require('https');

/**
 * 从起始目录向上查找 .git 目录，确定项目根目录
 * @param {string} startDir - 起始目录
 * @returns {string} 项目根目录
 */
function findProjectRoot(startDir) {
  let currentDir = path.resolve(startDir);
  let foundRoot = null;
  // 一直向上找，直到文件系统根目录
  while (true) {
    try {
      fs.accessSync(path.join(currentDir, '.git'));
      foundRoot = currentDir; // 记录找到的，但继续往上找
    } catch {
      // 没找到，继续
    }
    const parentDir = path.dirname(currentDir);
    if (parentDir === currentDir) {
      break; // 到达文件系统根目录
    }
    currentDir = parentDir;
  }
  // 如果找到了任何 .git，返回最顶层的那个（最接近文件系统根目录的）
  // 否则返回起始目录
  return foundRoot || startDir;
}

/**
 * 检查当前目录是否在项目根目录的 .claude 下
 * @param {string} cwd - 当前工作目录
 * @param {string} projectRoot - 项目根目录
 * @returns {boolean}
 */
function isInClaudeDir(cwd, projectRoot) {
  const claudeDir = path.join(projectRoot, '.claude');
  const relative = path.relative(claudeDir, cwd);
  return !relative.startsWith('..') && !path.isAbsolute(relative);
}

/**
 * 递归查找文件
 * @param {string} dir - 起始目录
 * @param {string[]} exts - 扩展名列表，为空表示所有文件
 * @returns {Promise<string[]>} 文件路径列表
 */
async function findFiles(dir, exts) {
  const results = [];

  async function traverse(currentDir) {
    const entries = await fsp.readdir(currentDir, { withFileTypes: true });

    for (const entry of entries) {
      if (entry.name === '.git') {
        continue;
      }
      const fullPath = path.join(currentDir, entry.name);

      if (entry.isDirectory() && !entry.isSymbolicLink()) {
        await traverse(fullPath);
      } else if (entry.isFile()) {
        if (exts.length === 0) {
          results.push(fullPath);
        } else {
          const ext = path.extname(entry.name).slice(1).toLowerCase();
          if (exts.includes(ext)) {
            results.push(fullPath);
          }
        }
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

/**
 * 确定导入配置
 * @returns {object} 配置对象
 */
function determineConfig() {
  const args = process.argv.slice(2);
  const config = {
    command: 'import',
    dir: null,
    exts: null,
    token: readApiXTokenFromEnv(),
    apiUrl: 'https://api.effiy.cn',
    prefix: []
  };

  let argStartIndex = 0;
  if (args[0] && !args[0].startsWith('-')) {
    config.command = args[0];
    argStartIndex = 1;
  }

  for (let i = argStartIndex; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--dir' || arg === '-d') {
      config.dir = path.resolve(args[++i]);
    } else if (arg === '--exts' || arg === '-e') {
      config.exts = args[++i].split(',').map(e => e.trim().toLowerCase());
    } else if (arg === '--token' || arg === '-t') {
      console.error('Error: --token 已禁用。出于安全原因，仅允许使用系统环境变量 API_X_TOKEN。');
      process.exit(1);
    } else if (arg === '--api-url' || arg === '-a') {
      config.apiUrl = args[++i];
    } else if (arg === '--prefix' || arg === '-p') {
      config.prefix = args[++i].split(',').map(p => p.trim()).filter(Boolean);
    } else if (arg === '--help' || arg === '-h') {
      printHelp();
      process.exit(0);
    }
  }

  const cwd = process.cwd();
  const projectRoot = findProjectRoot(cwd);
  const inClaudeDir = isInClaudeDir(cwd, projectRoot);

  if (config.dir === null) {
    if (inClaudeDir) {
      const claudeDir = path.join(projectRoot, '.claude');
      try {
        fs.accessSync(claudeDir);
        config.dir = claudeDir;
      } catch {
        config.dir = cwd;
      }
      config.exts = config.exts || [];
    } else {
      config.dir = projectRoot;
      config.exts = config.exts || ['md'];
    }
  } else {
    const dirName = path.basename(config.dir);
    if (['.claude', '.cursor'].includes(dirName)) {
      config.exts = config.exts || [];
    } else {
      config.exts = config.exts || ['md'];
    }
  }

  return { ...config, projectRoot };
}

function printHelp() {
  console.log(`
Document import — sync local files to remote documentation API

Usage:
  node .claude/skills/import-docs/scripts/import-docs.js import [options]
  node .claude/skills/import-docs/scripts/import-docs.js list [options]
  node .claude/skills/import-docs/scripts/import-docs.js [options]   # defaults to import

Options:
  --dir, -d     Directory to import (default: auto-detect)
  --exts, -e    File extensions (comma-separated, default: auto-detect)
  --token, -t   [disabled] use API_X_TOKEN environment variable only
  --api-url, -a API base URL (default: https://api.effiy.cn)
  --prefix, -p  Path prefix (comma-separated, e.g. Projects,YourNamespace)
  --help, -h    Show this help message
`);
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

async function importFile(fullPath, baseDir, projectRoot, apiUrl, token, existingSet, prefix, explicitDir) {
  const relativePath = path.relative(baseDir, fullPath);
  const relativeTargetPath = relativePath
    .split(path.sep)
    .map(part => part.replace(/\s+/g, '_'))
    .join('/');

  const rootDirName = path.basename(projectRoot).replace(/\s+/g, '_');
  const baseDirName = path.basename(baseDir);
  const isRootDir = baseDir === projectRoot && !explicitDir;
  const dirName = isRootDir ? null : baseDirName.replace(/\s+/g, '_');

  const targetPathParts = [];
  if (prefix.length > 0) {
    targetPathParts.push(...prefix.map(part => part.replace(/\s+/g, '_')));
  }
  targetPathParts.push(rootDirName);
  if (dirName) {
    targetPathParts.push(dirName);
  }
  targetPathParts.push(relativeTargetPath);

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

function toSortedRelativePaths(files, baseDir) {
  return files
    .map(file => path.relative(baseDir, file).split(path.sep).join('/'))
    .sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'));
}

async function main() {
  const config = determineConfig();

  if (!['import', 'list'].includes(config.command)) {
    console.error(`Error: unsupported command "${config.command}". Use "import" or "list".`);
    process.exit(1);
  }

  try {
    await fsp.access(config.dir);
  } catch {
    console.error(`Error: directory not found: ${config.dir}`);
    process.exit(1);
  }

  const explicitDir = process.argv.includes('--dir') || process.argv.includes('-d');
  const mode = config.exts.length === 0 ? 'all files' : config.exts.join(', ');

  console.log('=== Document import ===');
  console.log('Command:', config.command);
  console.log('Directory:', config.dir);
  console.log('Mode:', mode);
  if (config.command === 'import') {
    console.log('API:', config.apiUrl);
    if (config.prefix.length > 0) {
      console.log('Prefix:', config.prefix.join('/'));
    }
  }
  console.log();

  const files = await findFiles(config.dir, config.exts);
  console.log(`Found ${files.length} files`);

  if (files.length === 0) {
    console.log('No files to process');
    return;
  }

  if (config.command === 'list') {
    const relativePaths = toSortedRelativePaths(files, config.dir);
    console.log('Files:');
    for (const relativePath of relativePaths) {
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
    const file = files[i];
    const relativePath = path.relative(config.dir, file);
    console.log(`[${i + 1}/${files.length}] Processing: ${relativePath}`);

    try {
      const result = await importFile(file, config.dir, config.projectRoot, config.apiUrl, config.token, existingSet, config.prefix, explicitDir);
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
