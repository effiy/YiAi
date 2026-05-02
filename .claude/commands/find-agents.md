Invoke the `find-agents` skill to discover available agents.

Arguments: `$ARGUMENTS`

Execution requirements:
- Return only `.md` file names that actually exist under `.claude/agents/`; do not fabricate.
- Agent list defaults to concurrently invocable; do not imply hidden ordering dependencies.
- Generate "required answers" for each agent, clarifying input and output expectations.
- Agents are candidates only; whether to write them is up to the caller.
