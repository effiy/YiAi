# implement-code-checklist-sync — Usage Document

> **Document Version**: v1.0 | **Last Updated**: 2026-05-02 | **Maintainer**: kimi-k2.6

## Usage Overview

This document guides process maintainers and AI agents in ensuring `05_dynamic-checklist.md` remains synchronized with `06_process-summary.md` verification results.

## For implement-code Deliveries

After Gate B smoke tests complete:

1. Process summary agent reads `06_process-summary.md` §4 (Verification Results).
2. For each P0 item, copy the final status (✅/❌) to `05_dynamic-checklist.md`.
3. Append evidence in the format: `(stage, YYYY-MM-DD, method)`.
4. Save `05_dynamic-checklist.md`.
5. Run consistency check:
   ```bash
   # Conceptual check
   # - Every P0 in 05 marked ✅ must have matching ✅ in 06
   # - Every P0 in 05 marked ❌ must have matching ❌ in 06
   ```
6. If mismatch, block and report before `wework-bot`.

## For generate-document init Deliveries

After document generation completes:

1. Perform document quality checks:
   - Path verification (all referenced files exist)
   - Mermaid syntax check
   - Structure compliance (required chapters present)
2. Update `05_dynamic-checklist.md` statuses based on check results.
3. Append evidence to each updated item.
4. Save `05_dynamic-checklist.md` before `import-docs` and `wework-bot`.

## For Manual Override

If a known mismatch must be accepted:

1. Document the override reason in `06_process-summary.md` §5.
2. Update `05_dynamic-checklist.md` with explicit `⚠️ override (reason: ...)`.
3. Proceed to notification with override logged.

## Postscript: Future Planning & Improvements

- Add automated consistency check script to reduce manual effort.
