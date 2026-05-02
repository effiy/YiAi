---
name: import-docs
description: |
  Batch synchronize local documents to remote document API. Mandatory step upon
  generate-document / implement-code completion.
user_invocable: true
lifecycle: default-pipeline
---

# import-docs

## Positioning

Document import skill: auto-detect import source → support `list` to enumerate candidates → execute import → summarize results for `wework-bot` to fill real numbers.

## When to Use

- User requests sync/upload/publish/import documents to remote
- Mandatory step upon `generate-document` / `implement-code` completion
- Do not trigger: only local Markdown generation/modification and user explicitly does not need sync; target is just group notification (use `wework-bot`)

## Input

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--dir` | auto-detect | Import directory |
| `--exts` | auto-detect | Comma-separated extensions |
| `--token` | `API_X_TOKEN` only | **Disabled** CLI parameter, read only from system env |
| `--api-url` | `https://api.effiy.cn` | API address |
| `--prefix` | empty | Remote path prefix, comma-separated |
| `command` | `import` | `import` imports files; `list` only enumerates |

## Auto-Detection Rules

- Under `.claude` → import `.claude` directory, all files
- Otherwise → import project root directory, `.md` files only
- When `--dir` points to `.claude` / `.cursor`, `exts` defaults to empty (import all files)

## Workflow

1. Parameter parsing: extract directory, extensions, prefix from user request
2. Enumerate candidates (optional): `node scripts/import-docs.js list`
3. Security check: do not display token in replies
4. Execute import: `node scripts/import-docs.js --dir docs --exts md`
5. Result summary: files found, created / overwritten / failed counts
6. Return notification summary: `☁️ Document sync: docs → remote (created N, overwritten N, failed N)`

## Standard docs Import (called by upstream skills)

Standard command: `node scripts/import-docs.js --dir docs --exts md`

- Directory exists → execute import, result written to wework-bot notification
- Directory does not exist → skip, notification writes `docs does not exist, skipping import`
- Import failure → does not block main flow, note failure count
- `API_X_TOKEN` missing → record "`API_X_TOKEN` not detected, can manually sync later"

## Constraints

- Default auto-detection unless user specifies `--dir` / `--exts`
- Do not write token to repository files, logs, or documents
- Script overwrites remote files at same path
- Always ignore `.git`, do not follow symlinks

## Supporting Files

- `rules/import-contract.md`: path generation, deduplication, security constraints
- `scripts/import-docs.js`: CLI implementation
