# MCP Fallback Contract

> MCP fallback strategy for `generate-document` and `implement-code`.

## 1. General Principles

- MCP unavailability must not block the flow: every MCP must have a fallback plan.
- Silent degradation is prohibited: all degradation must be recorded in `06_process-summary.md` or `docs/99_agent-runs/`.
- Probe first: stage 0 must detect MCP availability and declare degradation status in advance.
- Degradation record format: `MCP degraded: <name> — <tool> — reason: <reason> — fallback: <plan> — impact: <impact>`

## 2. Fallback Mapping

| MCP | Tool | Fallback Plan | Blocking |
|-----|------|---------------|----------|
| `browser` | Browser operations | Equivalent scriptable automation + human confirmation | No |
| `code-analyzer-mcp` | `analyze_dependencies` | Grep search import/export + Read file headers | No |
| `code-analyzer-mcp` | `find_usages` | Grep full-project identifier search | No |
| `code-analyzer-mcp` | `check_architecture` | Read Store/component registration + human pattern matching | No |
| `code-analyzer-mcp` | `detect_dead_code` | Grep export name + Grep reference count | No |
| `doc-index-mcp` | `search_docs` | Grep search `docs/` contents | No |
| `doc-index-mcp` | `get_doc_structure` | Read file + extract `##` headings | No |
| `doc-index-mcp` | `find_cross_refs` | Grep search `[` and `](` patterns | No |
| `doc-index-mcp` | `validate_links` | Read + Glob verify path existence | No |
| `git-workflow-mcp` | `create_feature_branch` | Bash `git checkout -b feat/<name>` | No |
| `git-workflow-mcp` | `get_diff_summary` | Bash `git diff --stat` + `--name-status` | No |
| `git-workflow-mcp` | `analyze_change_impact` | Revert to `impact-analyst` Grep approach | No |
| `git-workflow-mcp` | `check_branch_status` | Bash `git status` + `git log` | No |
| `effiy-api` | `read_file` | Local `fs.readFile` | No |
| `effiy-api` | `write_file` | Local `fs.writeFile` | No |
| `effiy-api` | `delete_file` | Local `fs.unlink` | No |
| `effiy-api` | `delete_folder` | Local `fs.rmdir` / `fs.rm` | No |
| `effiy-api` | `rename_file` | Local `fs.rename` | No |
| `effiy-api` | `rename_folder` | Local `fs.rename` | No |
| `effiy-api` | `execute_module_get` / `execute_module_post` | Node `child_process` or direct module import | No |
| `effiy-api` | `send_wework_message` | `skills/wework-bot/scripts/send-message.js` | No |
| `effiy-api` | `upload_file` / `upload_image_to_oss` | `skills/observer/scripts/observer-client.js` sandboxed write + manual sync | No |
| `effiy-api` | `create_state_record` | `services/state/state_service.py` direct import + `asyncio.run` | No |
| `effiy-api` | `query_state_records` | `services/state/state_service.py` direct import + `asyncio.run` | No |
| `effiy-api` | `get_state_record` | `services/state/state_service.py` direct import + `asyncio.run` | No |
| `effiy-api` | `update_state_record` | `services/state/state_service.py` direct import + `asyncio.run` | No |
| `effiy-api` | `delete_state_record` | `services/state/state_service.py` direct import + `asyncio.run` | No |
| `effiy-api` | `get_observer_health` | Direct HTTP GET `https://api.effiy.cn/health/observer` via `fetch` | No |

## 3. Probe Checks

Stage 0 must execute a minimal viable probe for each MCP:

| MCP | Probe Method | Pass Condition |
|-----|-------------|----------------|
| `code-analyzer-mcp` | Call `analyze_dependencies` with entry file | Returns non-empty dependency list |
| `doc-index-mcp` | Call `search_docs` searching for `README` | Returns result or "not found" |
| `git-workflow-mcp` | Call `check_branch_status` | Returns current branch info |
| `browser` | Open `about:blank` | Page loads successfully |
| `effiy-api` | `node skills/observer/scripts/observer-client.js --health` | Returns `connected: true` and `ping: ok` |

If passed, use normally; if failed, record reason → activate fallback plan → declare degradation status in stage 0 output.

### 3.1 Observer Fallback Behavior

When `effiy-api` probe fails, scripts and agents must degrade through this priority chain:

1. **Local filesystem** (`fs.readFile`, `fs.writeFile`, etc.) for `read_file`, `write_file`, `delete_file`, `rename_file`, `delete_folder`, `rename_folder`.
2. **Direct Node require/spawn** for `execute_module_get` / `execute_module_post`.
3. **`skills/wework-bot/scripts/send-message.js`** for `send_wework_message`.
4. **Observer throttling still applies** even in fallback mode: use `skills/observer/scripts/observer-client.js` with `baseUrl` pointed to local stub, or apply TokenBucket manually.

## 4. Degradation Record

**Record location**: `06_process-summary.md` "MCP Details" chapter; if stage 7 not reached, write to `docs/99_agent-runs/`

**wework-bot notification**: Normal `🧩 MCP details: <MCP1> ✅ / <MCP2> ✅`; degraded `🧩 MCP details: <MCP1> ⚠️ degraded(<plan>)`

## 5. Relationship with Other Shared Standards

- Degradation records must comply with `evidence-and-uncertainty.md` truth levels (degradation effect is Class C).
- `impact-analyst` must label degradation status in artifacts when using fallback plans.
- `impl-reporter` must mark degraded nodes with dashed boxes in Mermaid diagrams when generating summaries.
