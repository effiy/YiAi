#!/usr/bin/env node

/**
 * 企业微信推送 CLI：正文由调用方（如 agent / message-pusher）写好，本脚本只负责
 * 路由、webhook 解析与请求通知网关（可配置）。
 */

const fs = require('fs');
const https = require('https');
const path = require('path');

/** 与官方浏览器 curl 一致的 keep-alive，匹配 `Connection: keep-alive`。 */
const httpsKeepAliveAgent = new https.Agent({ keepAlive: true, maxSockets: 8 });

const args = process.argv.slice(2);
const SCRIPT_DIR = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(SCRIPT_DIR, '../../../..');
const CLAUDE_ROOT = path.join(PROJECT_ROOT, '.claude');
const DEFAULT_CONFIG_BASE = path.join(CLAUDE_ROOT, 'skills/wework-bot/config.json');
const DEFAULT_API_URL = 'https://api.effiy.cn/wework/send-message';

/** X-Token 仅从系统环境变量 `API_X_TOKEN` 读取，不接受配置文件或其它来源。 */
function readApiXTokenFromEnv() {
  const v = process.env.API_X_TOKEN;
  if (v == null || v === '') return null;
  const t = String(v).trim();
  return t || null;
}

const DEFAULT_BROWSER_UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36';

/**
 * @param {unknown} body
 * @returns {boolean|null}
 */
function bodyIndicatesFailure(body) {
  if (body == null || typeof body !== 'object' || Array.isArray(body)) return null;
  if (body.success === false) return true;
  if (body.success === true) return false;
  if (typeof body.errcode === 'number') {
    return body.errcode !== 0;
  }
  if (typeof body.code === 'number') {
    if (body.code === 0 || body.code === 200 || body.code === 201) return false;
    return true;
  }
  return null;
}

/**
 * @param {string} token
 * @param {number} bodyByteLength
 */
function buildSendMessageHeaders(token, bodyByteLength) {
  return {
    Accept: 'application/json',
    'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8',
    'Cache-Control': 'no-cache',
    Connection: 'keep-alive',
    'Content-Type': 'application/json',
    Origin: 'https://example.com',
    Pragma: 'no-cache',
    Referer: 'https://example.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': DEFAULT_BROWSER_UA,
    'X-Token': token,
    'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'Content-Length': bodyByteLength
  };
}

/** @type {{
 *   token: string|null,
 *   apiUrl: string|null,
 *   config: string|null,
 *   agent: string|null,
 *   robot: string|null,
 *   webhookUrl: string|null,
 *   webhookKey: string|null,
 *   content: string|null,
 *   contentFile: string|null,
 *   name: string|null
 * }} */
const options = {
  token: readApiXTokenFromEnv(),
  apiUrl: process.env.WEWORK_BOT_API_URL || null,
  config: process.env.WEWORK_BOT_CONFIG || null,
  agent: null,
  robot: null,
  webhookUrl: null,
  webhookKey: null,
  content: null,
  contentFile: null,
  name: null,
  noSend: false
};

function readValue(index, flag) {
  const value = args[index + 1];
  if (value === undefined || value === null) {
    console.error(`Error: ${flag} requires a value`);
    process.exit(1);
  }
  if (value.startsWith('-') && value.length > 1 && Number.isNaN(Number(value))) {
    console.error(`Error: ${flag} requires a value`);
    process.exit(1);
  }
  return value;
}

function blockSecretCliFlag(flag) {
  console.error(
    `Error: ${flag} 已禁用。出于安全原因，禁止通过命令行传入 webhook key/url；请在 config.json 中配置 webhook。`
  );
  process.exit(1);
}

for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg === '--token' || arg === '-t') {
    blockSecretCliFlag(arg);
  } else if (arg === '--api-url' || arg === '-a') {
    options.apiUrl = readValue(i, arg);
    i++;
  } else if (arg === '--config') {
    options.config = readValue(i, arg);
    i++;
  } else if (arg === '--agent') {
    options.agent = readValue(i, arg);
    i++;
  } else if (arg === '--robot' || arg === '-r') {
    options.robot = readValue(i, arg);
    i++;
  } else if (arg === '--webhook-url' || arg === '-w') {
    blockSecretCliFlag(arg);
  } else if (arg === '--webhook-key' || arg === '-k') {
    blockSecretCliFlag(arg);
  } else if (arg === '--content' || arg === '-c') {
    options.content = readValue(i, arg);
    i++;
  } else if (arg === '--content-file' || arg === '-f') {
    options.contentFile = readValue(i, arg);
    i++;
  } else if (arg === '--name' || arg === '-n') {
    options.name = readValue(i, arg);
    i++;
  } else if (arg === '--no-send') {
    options.noSend = true;
  } else if (arg === '--help' || arg === '-h') {
    console.log(`
WeWork Bot — 发送企业微信机器人消息（正文由 agent 生成，直接 POST）

Usage: node .claude/skills/wework-bot/scripts/send-message.js [options]

环境变量:
  API_X_TOKEN           必填，网关 X-Token
  WEWORK_BOT_WEBHOOK_URL 必填，企业微信 Webhook 完整 URL（含 key）
  WEWORK_BOT_API_URL    可选，覆盖默认 ${DEFAULT_API_URL}
  WEWORK_BOT_CONFIG     可选，路由 JSON 路径（默认仓库 skills/wework-bot/config.json）
  
选项:
  --config <path>       路由配置文件
  --agent <name>        按配置映射选择机器人（推荐）
  --robot, -r <name>    直接指定机器人名（慎用，优先 --agent）
  --content, -c <text>   完整正文（单行或多行转义）
  --content-file, -f <path>  从 UTF-8 文件读取正文（推荐长文案）
  --name, -n <name>      故事名称，用于追加消息到 docs/故事任务面板/<name>/09-消息通知列表.md
  --no-send            仅追加消息日志，不实际发送
  --api-url, -a <url>   覆盖发送 API
  --help, -h

已禁用: --token / --webhook-url / --webhook-key（请在 config.json 配 webhook，用 API_X_TOKEN）
`);
    process.exit(0);
  }
}

function resolveUserPath(inputPath) {
  if (!inputPath) return inputPath;
  return path.isAbsolute(inputPath) ? inputPath : path.resolve(process.cwd(), inputPath);
}

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch (error) {
    console.error(`Error: failed to read config ${filePath}: ${error.message}`);
    process.exit(1);
  }
}

function readJsonIfExists(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    }
  } catch (error) {
    console.error(`Error: failed to read config ${filePath}: ${error.message}`);
    process.exit(1);
  }
  return null;
}

function envValue(name) {
  return name ? process.env[name] : null;
}

function applyRobotConfig() {
  let config = null;

  if (options.config) {
    config = readJson(resolveUserPath(options.config));
  } else {
    config = readJsonIfExists(DEFAULT_CONFIG_BASE);
  }

  if (!config) {
    return;
  }

  if (!options.apiUrl && config.api_url) {
    options.apiUrl = config.api_url;
  }

  if (options.robot) {
    console.warn('Warning: --robot is deprecated; prefer --agent for automatic routing.');
  }

  const robotName =
    options.robot ||
    (options.agent && config.agents ? config.agents[options.agent] : null) ||
    config.default_robot;

  if (!robotName) {
    console.error('Error: --agent did not resolve to a robot, and no default_robot is configured');
    process.exit(1);
  }

  const robot = config.robots && config.robots[robotName];
  if (!robot) {
    console.error(`Error: robot "${robotName}" is not defined in config`);
    process.exit(1);
  }

  options.robot = robotName;

  const resolvedWebhookUrl =
    envValue(robot.webhook_url_env) ||
    robot.webhook_url ||
    envValue(config.webhook_url_env) ||
    config.webhook_url;
  const resolvedWebhookKey =
    envValue(robot.webhook_key_env) ||
    robot.webhook_key ||
    envValue(config.webhook_key_env) ||
    config.webhook_key;

  options.webhookUrl = resolvedWebhookUrl || null;
  options.webhookKey = resolvedWebhookKey || null;

  if (robot.api_url && !options.apiUrl) {
    options.apiUrl = robot.api_url;
  }
}

applyRobotConfig();

options.token = readApiXTokenFromEnv();

if (!options.apiUrl) {
  options.apiUrl = DEFAULT_API_URL;
}

if (!options.token) {
  console.error('Error: missing API_X_TOKEN environment variable');
  process.exit(1);
}

/** 将字面量 \\n / \\t 还原为换行与制表符（从 JSON 多拷贝一层时常见）。 */
function normalizeMessageText(text) {
  if (!text || typeof text !== 'string') return text;
  return text
    .replace(/\\r\\n/g, '\n')
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, '\t');
}

function formatTimestamp() {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  const hh = String(now.getHours()).padStart(2, '0');
  const min = String(now.getMinutes()).padStart(2, '0');
  const ss = String(now.getSeconds()).padStart(2, '0');
  return `【${yyyy}-${mm}-${dd} ${hh}:${min}:${ss}】`;
}

function appendToStoryNotificationLog(name, content) {
  const storyDir = path.join(PROJECT_ROOT, 'docs', '故事任务面板', name);
  const logFile = path.join(storyDir, '09-消息通知列表.md');
  fs.mkdirSync(storyDir, { recursive: true });
  const timestamp = formatTimestamp();
  const entry = `\n${timestamp}\n\n${content}\n`;
  fs.appendFileSync(logFile, entry, 'utf-8');
}

if (options.contentFile) {
  try {
    options.content = fs.readFileSync(resolveUserPath(options.contentFile), 'utf-8');
  } catch (error) {
    console.error(`Error: failed to read --content-file: ${error.message}`);
    process.exit(1);
  }
}

if (options.content) {
  options.content = normalizeMessageText(options.content);
}

if (!options.content || !String(options.content).trim()) {
  console.error('Error: --content or --content-file is required with non-empty body');
  process.exit(1);
}

options.content = String(options.content).trimEnd();

if (options.name) {
  appendToStoryNotificationLog(options.name, options.content);
}

if (options.noSend) {
  console.log('--no-send: message appended to log, skipping send.');
  process.exit(0);
}

if (!options.webhookUrl && options.webhookKey) {
  options.webhookUrl = `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=${options.webhookKey}`;
}

if (!options.webhookUrl) {
  console.error(
    'Error: missing webhook configuration (config.json webhook mapping or webhook_url / webhook_key fields)'
  );
  process.exit(1);
}

try {
  new URL(options.webhookUrl);
} catch (error) {
  console.error(`Error: invalid webhook_url after resolution: ${options.webhookUrl}`);
  process.exit(1);
}

function request(apiUrl, token, data) {
  return new Promise((resolve, reject) => {
    const url = new URL(apiUrl);
    const postData = JSON.stringify(data);
    const bodyLen = Buffer.byteLength(postData, 'utf8');
    const requestOptions = {
      agent: httpsKeepAliveAgent,
      hostname: url.hostname,
      port: url.port || 443,
      path: url.pathname + url.search,
      method: 'POST',
      headers: buildSendMessageHeaders(token, bodyLen)
    };

    const req = https.request(requestOptions, (res) => {
      let body = '';
      res.on('data', (chunk) => {
        body += chunk;
      });
      res.on('end', () => {
        let parsed = body;
        try {
          parsed = JSON.parse(body);
        } catch (error) {
          // Keep raw text if the service does not return JSON.
        }
        resolve({ statusCode: res.statusCode, body: parsed, rawBody: body });
      });
    });

    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

(async function main() {
  /** 网关 API：请求体字段名为 `webhook_url`（完整 webhook URL）。 */
  const payload = {
    webhook_url: options.webhookUrl,
    content: options.content
  };

  try {
    const result = await request(options.apiUrl, options.token, payload);
    console.log('=== WeWork Bot Result ===');
    console.log('Status:', result.statusCode);
    console.log('Response:', typeof result.body === 'string' ? result.body : JSON.stringify(result.body));

    const httpFail = result.statusCode < 200 || result.statusCode >= 300;
    const contentFail = bodyIndicatesFailure(result.body) === true;
    if (httpFail || contentFail) {
      if (!httpFail && contentFail) {
        console.error('Error: API returned HTTP success but content-level failure (check errcode/code/message in response)');
      }
      process.exit(1);
    }

  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
})();
