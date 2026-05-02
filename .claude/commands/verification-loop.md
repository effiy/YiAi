Invoke the `verification-loop` skill to execute a verification loop.

Arguments: `$ARGUMENTS`

Execution requirements:
- Must perform an MCP availability probe before execution; silent degradation is prohibited. Stop and prompt when a required tool is unavailable and no fallback exists.
- Phases 1–3 with blocking items must not enter Phase 4; command names must be taken from `package.json` scripts, never hard-coded.
- Phase 4 executes only once; on failure, do not auto-retry. Provide a "one-time fix checklist" and the re-entry phase.
- Automation degradation must be labeled with ⚠️; do not present degraded results as a full pass.
