Invoke the `find-skills` skill to discover available skills.

Arguments: `$ARGUMENTS`

Execution requirements:
- Return only skill directory names that actually exist under `.claude/skills/`; do not fabricate.
- Skill names must match directory names exactly; no case changes or aliases.
- Label match results by confidence (high/medium/low) and explain applicability.
- When no match is found, output "no suitable skill found".
