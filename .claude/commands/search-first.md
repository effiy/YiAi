Invoke the `search-first` skill to evaluate candidate solutions before making a technical decision.

Arguments: `$ARGUMENTS`

Execution requirements:
- Must base recommendations on real search data with verifiable sources (URL / package@version).
- Evaluation matrix must cover functional coverage, maintenance activity, community size, and license.
- When results do not match requirements, output "no solution meeting constraints found" — do not fabricate.
- When there is no network access, state "cannot execute search; below is reference based on training data (may be outdated)".
