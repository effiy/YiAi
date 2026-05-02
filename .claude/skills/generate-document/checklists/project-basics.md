# Project Basics Checklist

> **Related specs**: [Project Basics Spec](../rules/project-basics.md)

## Basic File Completeness

- `CLAUDE.md`, `README.md`, `docs/architecture.md` exist and are non-empty — P0
- `docs/changelog.md`, `docs/devops.md`, `docs/network.md`, `docs/state-management.md`, `docs/FAQ.md`, `docs/auth.md`, `docs/security.md` exist and are non-empty — P1

## Re-init Update Strategy

- Second run does not skip files with "file exists" omission (fact chapters are refreshed) — P0
- When document description conflicts with code scan, `> To be confirmed (reason: …)` is labeled — P0
- Sentinel blocks are used correctly (inside block is rewritable, outside block human content is preserved) — P1

## Full-Document Numbered Set Completeness

- `docs/project-init/01-07` all exist and are non-empty — P0

## Anti-Hallucination

- File paths referenced in text actually exist in the repository — P0
- Functions / components referenced in text actually exist in code — P0
- Uncertain content is labeled "to be supplemented (reason: …)" rather than fabricated — P0
- No凭空 fabricated tech stacks or dependencies — P0

## CLAUDE.md Specific

- First two fixed header lines reference behavioral-guidelines.md + architecture.md — P0
- Contains tech stack (from package.json), project structure (from actual directories), build and run (from scripts), and key files (from entry and config) chapters — P0
- Referenced files actually exist — P0
- Tech stack and build commands are consistent with package.json — P0
- Directory structure description matches actual directories — P0
- Contains coding standards, prohibitions, and documentation system chapters — P1

## README.md Specific

- Contains project name + description, intro, tech stack table, install/dev/build commands, directory structure, and docs table — P0
- Commands are consistent with package.json scripts — P0
- Directory structure matches actual directories — P0
- Docs table links use relative paths; existing items are linked, non-existing items are labeled "to be supplemented" — P0
- Contains environment requirements, dev server address, and core architecture chapters — P1

## docs/architecture.md Specific

- Contains directory organization (code-block tree, covering first-level and key second-level directories, matching actual directories) — P0
- Contains placement rules (table + prohibitions) — P0
- Contains core architecture patterns (3–5, each with code example or division table, example paths are real) — P0
- Contains module / app structure, matching actual directories — P0
- All paths and functions referenced in text are real — P0

## docs/changelog.md Specific

- Uses Keep a Changelog format, contains `[Unreleased]` section — P0
- Version section format `[version] - YYYY-MM-DD` — P0
- With git, entries come from git log (not fabricated) — P0
- Without git, labeled "to be supplemented (reason: project has no git history)" — P0

## docs/FAQ.md Specific

- Contains quick-troubleshoot index table — P0
- Question categories are dynamically inferred from CLAUDE.md / README.md / docs (fixed examples prohibited) — P0
- Each question contains symptom + cause + troubleshoot steps + fix plan 4 elements — P0
- Troubleshoot steps contain executable commands — P0
- No fabricated error messages — P0

## docs/auth.md Specific

- Contains auth architecture overview, auth flow (Mermaid sequence diagram), and authorization flow (Mermaid flow diagram) — P0
- Contains permission-level table (route / component / API / data level), code paths are real — P0
- Contains authorization self-check rules (P0 table with check method and failure consequence) — P0
- When no auth code exists, keep full template structure and label "to be supplemented" — P0
- Auth scheme matches actual code (not fabricated) — P0

## docs/security.md Specific

- Contains security architecture overview (7-dimension table) — P0
- Contains threat model table (dynamically inferred from project tech stack and code; fixed examples prohibited) — P0
- Contains security self-check rules — P0
- When no security code exists, keep full template structure and label "to be supplemented" — P0

## 06_process-summary Specific

- Contains implementation overview, process record, file list, and verification results — P0
- Contains carryover items and follow-up recommendations — P1

## General Quality

- All document links use relative paths — P0
- Missing files have been generated — P0
- Existing files are not unnecessarily modified — P1
