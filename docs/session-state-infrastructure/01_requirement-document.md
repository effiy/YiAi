# Session & State Infrastructure

> **Document Version**: v1.0 | **Last Updated**: 2026-05-03 | **Maintainer**: Claude | **Tool**: Claude Code
>
> **Related Documents**: [Requirement Tasks](./02_requirement-tasks.md) | [Design Document](./03_design-document.md) | [Usage Document](./04_usage-document.md) | [CLAUDE.md](../../CLAUDE.md)
>

[Feature Overview](#feature-overview) | [User Stories](#user-stories) | [Acceptance Criteria](#acceptance-criteria) | [Feature Details](#feature-details)

---

## Feature Overview

YiAi 当前缺乏结构化的状态管理机制。现有的 `sessions` 集合以无模式方式存储会话数据，`data_service.py` 中通过硬编码字段名（如 `pageContent`、`messages`）进行特殊处理，导致数据访问耦合度高、难以扩展。同时，`.claude/skills/` 目录下的技能自改进机制（`execution-memory.js`、`self-improve.js`）仅作为文档管道的 Node.js 脚本运行，未与 FastAPI 后端打通，无法基于运行时数据持续优化。

本功能旨在构建一套完整的状态基础设施：以 MongoDB 为底座的结构化状态仓库（State Store），提供统一的 CRUD 与查询能力；配套 Typer 命令行工具支持离线查询与运维；通过 Pydantic 会话适配器将现有 `sessions` 数据规范化；并为技能执行结果建立持久化记录，奠定技能自我演化的数据基础。

🎯 **统一状态抽象**：将散落的状态访问收敛到单一服务层，消除硬编码字段耦合。

⚡ **可运维性**：提供 CLI 工具，支持在无 HTTP 服务环境下查询、导出和清理状态数据。

📖 **可演化性**：记录技能执行上下文与结果，使技能具备基于历史数据自我改进的数据基础。

---

## User Stories

**Priority**: 🔴 P0 | 🟡 P1 | 🟢 P2

| User Story | Acceptance Criteria | Process-Generated Documents | Output Smart Documents |
|------------|---------------------|----------------------------|------------------------|
| 🔴 As a backend developer, I want a structured state store with CRUD and query APIs, so that I can persist and retrieve application states reliably.<br/><br/>**Main Operation Scenarios**:<br/>- Create a state record via API<br/>- Query state records with filters and pagination<br/>- Update and delete state records | 1. State records support typed schema validation on create/update<br/>2. Query API supports filtering by `record_type`, `tags`, `created_time` range, and full-text search on `title`<br/>3. Pagination defaults to 2000 items per page, max 8000<br/>4. All records expose a stable `key` field | [Requirement Tasks](./02_requirement-tasks.md)<br>[Design Document](./03_design-document.md)<br>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br>[Requirement Document Specification](../../.claude/skills/generate-document/rules/requirement-document.md) |
| 🔴 As a system operator, I want a query CLI for the state store, so that I can inspect and export state data without starting the HTTP server.<br/><br/>**Main Operation Scenarios**:<br/>- Query state records from command line with filters<br/>- Export query results to JSON/CSV<br/>- Show record count by type | 1. CLI supports `list`, `get`, `export`, `stats` subcommands<br/>2. CLI reuses the same query syntax as the HTTP API<br/>3. CLI can run independently using `python -m src.cli.state_query`<br/>4. Output formats: table (default), JSON, CSV | [Requirement Tasks](./02_requirement-tasks.md)<br>[Design Document](./03_design-document.md)<br>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br>[Requirement Document Specification](../../.claude/skills/generate-document/rules/requirement-document.md) |
| 🟡 As a developer, I want session adapters that convert raw session documents to structured records, so that I can validate and migrate existing session data.<br/><br/>**Main Operation Scenarios**:<br/>- Adapt an existing session document to structured schema<br/>- Batch adapt all legacy sessions<br/>- Detect and report incompatible session data | 1. Adapter handles existing fields (`pageContent`, `messages`, `key`, `createdTime`, `updatedTime`)<br/>2. Adapter produces a `SessionState` Pydantic model<br/>3. Batch adaptation exposes progress and error reporting<br/>4. Incompatible data is logged but does not block the batch | [Requirement Tasks](./02_requirement-tasks.md)<br>[Design Document](./03_design-document.md)<br>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br>[Requirement Document Specification](../../.claude/skills/generate-document/rules/requirement-document.md) |
| 🟡 As the system, I want to record skill execution outcomes, so that skills can access historical performance data for self-improvement.<br/><br/>**Main Operation Scenarios**:<br/>- Record a successful skill execution with metrics<br/>- Record a failed skill execution with error context<br/>- Query skill execution history by skill name and time range | 1. Execution outcomes are recorded asynchronously (fire-and-forget)<br/>2. Record schema includes `skill_name`, `status`, `duration_ms`, `input_summary`, `output_summary`, `error_message`, `timestamp`<br/>3. Recording failure must not affect the original execution result<br/>4. Query API supports aggregation by skill and date | [Requirement Tasks](./02_requirement-tasks.md)<br>[Design Document](./03_design-document.md)<br>[Project Report](./07_project-report.md) | [Generate Document Skill](../../.claude/skills/generate-document/SKILL.md)<br>[Requirement Document Specification](../../.claude/skills/generate-document/rules/requirement-document.md) |

---

## Document Specifications

1. **01_requirement-document.md** (this document): Defines what the feature does, scope, and acceptance criteria.
2. **02_requirement-tasks.md**: Breaks down user stories into scenarios, impact analysis, and verifiable tasks.
3. **03_design-document.md**: Architecture, module division, interface specs, and data structure design.
4. **04_usage-document.md**: End-user operation guide for the state store API and CLI.
5. **05_dynamic-checklist.md**: Verifiable checklist items for implementation and testing.
6. **07_project-report.md**: Delivery evidence and change summary.

---

## Acceptance Criteria

### P0 (Core)

- [ ] `StateRecord` schema supports `key`, `record_type`, `title`, `payload` (Dict), `tags` (List[str]), `created_time`, `updated_time`.
- [ ] State store service exposes `create`, `query`, `get`, `update`, `delete` methods with type annotations.
- [ ] Query supports filtering by `record_type`, `tags`, time range, and text search on `title`.
- [ ] CLI implements `list`, `get`, `export`, `stats` with table/JSON/CSV output.
- [ ] CLI runs without requiring the FastAPI server to be active.
- [ ] All new code follows existing project conventions (snake_case, type hints, Google docstrings).

### P1 (Important)

- [ ] `SessionAdapter` converts raw `sessions` collection documents to `SessionState` models.
- [ ] Batch adaptation endpoint/tool reports progress and collects incompatible data warnings.
- [ ] `SkillRecorder` hooks into `execution/executor.py` to record execution outcomes.
- [ ] Skill execution records are queryable by skill name, status, and time range.
- [ ] New collections and config fields are added to `collections.py` and `config.py`.

### P2 (Nice-to-have)

- [ ] State store supports TTL-based automatic cleanup of old records.
- [ ] CLI supports interactive mode (REPL) for ad-hoc queries.
- [ ] Skill execution metrics include memory usage and token counts.

---

## Feature Details

### 1. Structured State Store

**Description**: A MongoDB-backed repository for typed state records. Records are validated via Pydantic before persistence.

**Boundaries and Exceptions**:
- Does not replace the existing `sessions` collection; it coexists and may reference sessions by `key`.
- Does not implement distributed state sharing (Redis remains a future option per `docs/state-management.md`).
- `payload` is schemaless within the record to allow flexibility, but the record envelope is strictly typed.

**Value/Motivation**: Eliminates hardcoded field handling in `data_service.py`, provides a generic state primitive for future features.

### 2. Query CLI

**Description**: A Typer-based command-line interface for operators to query and export state records without HTTP.

**Boundaries and Exceptions**:
- Read-only by default; write operations (`delete`, `cleanup`) require an explicit `--write` flag.
- Does not manage the MongoDB server lifecycle; assumes `mongodb_url` is accessible.

**Value/Motivation**: Enables offline diagnostics, data exports for analysis, and safe operational commands.

### 3. Session Adapters

**Description**: Pydantic models and conversion functions that read raw `sessions` documents and produce validated `SessionState` objects.

**Boundaries and Exceptions**:
- Backward compatible: does not alter existing `sessions` documents unless explicitly requested via a migration tool.
- Handles missing fields gracefully with default values and logs warnings.

**Value/Motivation**: Bridges legacy schemaless data to the new structured state store, enabling validation and analytics.

### 4. Skill Evolution Foundation

**Description**: An asynchronous recorder that captures skill execution metadata (name, status, duration, error) into the state store.

**Boundaries and Exceptions**:
- Recording is best-effort; failures are logged but never raise exceptions to the caller.
- Only records executions triggered through the `/execution` endpoint or `executor.execute_module`.

**Value/Motivation**: Converts the existing docs-pipeline-only self-improve concept into a backend data product, enabling runtime skill optimization.

---

## Usage Scenario Examples

### Scenario 1: Creating and Querying a State Record

📋 **Background**: A chat service wants to persist a conversation summary as a state record.

🎨 **Operation**:
1. POST `/state/records` with `{ "record_type": "conversation_summary", "title": "User onboarding", "payload": { "turns": 12 }, "tags": ["onboarding"] }`.
2. GET `/state/records?record_type=conversation_summary&tags=onboarding`.

📋 **Result**: Returns a paginated list containing the created record with a generated `key`.

### Scenario 2: Using the Query CLI

📋 **Background**: An operator needs to export all failed skill executions from the last 24 hours.

🎨 **Operation**:
1. Run `python -m src.cli.state_query list --record-type skill_execution --status failed --since 1d --format json --output failures.json`.

📋 **Result**: A JSON file `failures.json` containing all matching records.

### Scenario 3: Adapting Legacy Sessions

📋 **Background**: A developer wants to migrate historical session data to the new structured schema.

🎨 **Operation**:
1. Run a batch adaptation script that calls `SessionAdapter.adapt(document)` for each legacy session.
2. Incompatible documents are logged to `adaptation_errors.log`.

📋 **Result**: Valid `SessionState` objects are produced; incompatible data is documented for manual review.

---

## Postscript: Future Planning & Improvements

1. **Distributed State**: If YiAi moves to multi-instance deployment, introduce Redis as a hot cache layer in front of the MongoDB state store.
2. **State Machine Engine**: Extend the state store with state machine semantics (transitions, guards, side effects) for workflow orchestration.
3. **Skill Feedback Loop**: After skill execution data accumulates, implement an automated skill tuning loop that adjusts prompts or parameters based on success rates.
4. **GraphQL Interface**: Consider a GraphQL layer over the state store to allow flexible client queries without frequent API versioning.
5. **Audit Trail**: Add immutable audit logs for all state mutations to support compliance and debugging.
